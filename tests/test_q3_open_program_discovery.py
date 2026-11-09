"""Minimal Q3 open-program contract, not a generalization benchmark."""
import hashlib
import json

import pytest

from neumann1.open_program_inventor import (
    GenerativeProgramInventor,IsolatedPython,UnsafeProposal,
    source_training_example,validate_code)
from neumann1.q3_trainable_code_policy import source_training_rows


class ScriptedSourcePolicy:
    """Diagnostic stand-in; NOT a trained model or Q3 invention evidence."""
    def __init__(self,candidates):
        self.candidates=iter(candidates)
        self.prompts=[]

    def propose(self,prompt):
        self.prompts.append(prompt)
        return next(self.candidates)


def test_source_refutation_and_proposal_revision_in_sandbox(tmp_path):
    old="def transform(x):\n    return x"
    new="def transform(x):\n    return [v*v for v in x]"
    policy=ScriptedSourcePolicy((old,new))
    runner=IsolatedPython(max_seconds=12)
    source=[([1,2,3],[1,4,9]),([2,4],[4,16])]
    independent=[([5,6,7],[25,36,49])]
    record=GenerativeProgramInventor(
        policy,runner,max_proposals=2).discover(
            source,independent_source_checks=independent)
    assert record.status=="SOURCE_VERIFIED_OPEN_PROGRAM",record
    assert record.verified and len(record.attempts)==2
    assert record.attempts[0].source_correct==0
    assert record.attempts[1].source_correct==2
    assert "Observed SOURCE failure kind: source" in policy.prompts[1]
    assert old in policy.prompts[1]
    assert "Original-semantics SOURCE feedback:" in policy.prompts[1]
    assert record.apply([3,8],runner)==[9,64]
    sample=source_training_example(source,record)
    saved=tmp_path/"source.jsonl"
    saved.write_text(json.dumps(sample)+"\n")
    rows,source_sha=source_training_rows(saved)
    assert len(rows)==1
    assert rows[0]["sha256"]==hashlib.sha256(new.encode()).hexdigest()
    assert len(source_sha)==64


def test_cannot_run_imports_reflection_or_other_host_code():
    for bad in (
        "import os\ndef transform(x):\n    return x",
        "def transform(x):\n    return x.__class__",
        "def transform(x):\n    return open('/etc/passwd')",
        "def transform(x):\n    return eval('2+2')",
        "def transform(x):\n    return x\nraise RuntimeError()",
    ):
        with pytest.raises(UnsafeProposal):
            validate_code(bad)


def test_missing_sandbox_fails_closed(monkeypatch):
    monkeypatch.setattr(
        "neumann1.open_program_inventor.shutil.which",lambda name:None)
    policy=ScriptedSourcePolicy((
        "def transform(x):\n    return x+1",))
    r=GenerativeProgramInventor(
        policy,IsolatedPython(),max_proposals=1).discover(
            [(1,2)],independent_source_checks=[(2,3)])
    assert r.status=="ABSTAIN_NO_SOURCE_PROGRAM"
    assert r.attempts[0].status=="ABSTAIN_NO_SANDBOX"
    assert not r.verified
    with pytest.raises(UnsafeProposal):
        r.apply(7,IsolatedPython())


def test_no_unverified_model_outputs_promoted_into_training(tmp_path):
    example={
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "pairs":[([1,2],[3,4])],
        "program":"def transform(x):\n    return x",
        "sha256":"not_the_actual_sha",
        "independent_checks":1,
        "provenance":"ORIGINAL_SOURCE_ONLY"}
    source=tmp_path/"incorrect.jsonl"
    source.write_text(json.dumps(example)+"\n")
    with pytest.raises(ValueError,match="tampered"):
        source_training_rows(source)


def test_executable_model_code_is_not_discarded_for_harmless_wrapper():
    candidate=(
        "Here is the implementation:\n"
        "def transform(x):\n"
        "    if isinstance(x, list):\n"
        "        return sum(x)\n"
        "    return x\n"
        "\nThis concludes the answer.")
    extracted=validate_code(candidate)
    assert extracted.startswith("def transform(x):")
    assert "This concludes" not in extracted


def test_recursive_pure_helper_remains_in_isolated_runtime():
    candidate=(
        "def transform(x):\n"
        "    def walk(seq):\n"
        "        if not seq:\n"
        "            return 0\n"
        "        return seq[0] + walk(seq[1:])\n"
        "    return walk(x)")
    outcome=IsolatedPython(max_seconds=12).evaluate(
        candidate,[[2,5,7],[1,3,9]])
    assert outcome.status=="EXECUTED",outcome
    assert outcome.outputs==(14,13)


def test_preflight_refutation_is_given_to_generator_without_target_gold():
    bad="def transform(x):\n    return open('secret')"
    correct="def transform(x):\n    return x"
    policy=ScriptedSourcePolicy((bad,correct))
    result=GenerativeProgramInventor(
        policy,IsolatedPython(max_seconds=12),max_proposals=2
    ).discover(
        [([1,2],[1,2])],
        independent_source_checks=[([5,6],[5,6])])
    assert result.verified and result.program==correct
    assert len(result.attempts)==2
    assert result.attempts[0].status=="REJECTED"
    assert "unknown builtin or helper" in policy.prompts[1]



def test_disjoint_source_counterexample_carries_actual_failed_program():
    """The previous real model was asked to revise a program it could not see."""
    first="def transform(x):"+chr(10)+"    return x[0]"
    repaired="def transform(x):"+chr(10)+"    return min(x)"
    class RequiresPriorHypothesis:
        def __init__(self):
            self.history=[]
        def propose(self,prompt):
            self.history.append(prompt)
            if len(self.history)==1:
                return first
            assert first in prompt
            assert "Observed SOURCE failure kind: independent_source" in prompt
            assert '"previous_observed":9' in prompt
            assert '"source_expected":1' in prompt
            assert "TARGET outputs are UNKNOWN" in prompt
            return repaired
    policy=RequiresPriorHypothesis()
    solver=GenerativeProgramInventor(
        policy,IsolatedPython(max_seconds=10),max_proposals=2)
    result=solver.discover(
        [([1,2],1),([3,4],3)],
        independent_source_checks=[([9,1],1)])
    assert result.verified
    assert result.program==repaired
    assert result.attempts[0].source_correct==2
    assert len(policy.history)==2


def test_preflight_rejection_includes_rejected_model_code_not_just_error():
    unsafe="def transform(x):"+chr(10)+"    return eval('2+2')"
    good="def transform(x):"+chr(10)+"    return x + 1"
    policy=ScriptedSourcePolicy((unsafe,good))
    result=GenerativeProgramInventor(
        policy,IsolatedPython(max_seconds=10),max_proposals=2).discover(
        [(1,2)],independent_source_checks=[(2,3)])
    assert result.verified
    assert "Observed SOURCE failure kind: preflight" in policy.prompts[1]
    assert unsafe in policy.prompts[1]
    assert "unknown builtin or helper" in policy.prompts[1]


def test_repair_prompt_forgets_older_failures_but_keeps_current_source():
    from neumann1.q3_prompt_contract import source_discovery_prompt,source_revision_prompt
    base=source_discovery_prompt([(1,2)])
    first=source_revision_prompt(base,"def transform(x): return x",
                                  [{"expected":2,"got":1}],kind="source")
    second=source_revision_prompt(base,"def transform(x): return x+3",
                                   [{"expected":2,"got":4}],kind="source")
    assert "def transform(x): return x" in first
    assert "def transform(x): return x+3" in second
    assert '"got":1' not in second
    assert '"got":4' in second
    assert base in second
    assert len(second) < len(base)+650



def test_incumbent_5_of_6_is_not_discarded_by_later_rejected_hypothesis():
    """Replays observed 5/6 -> REJECTED failure mechanism from real CodeARC."""
    partial="def transform(x):"+chr(10)+"    return x[0]"
    broken="def transform(x):"+chr(10)+"    return eval('untrusted')"
    complete="def transform(x):"+chr(10)+"    return min(x)"
    class RequiresIncumbent:
        def __init__(self):
            self.prompts=[]
        def propose(self,prompt):
            self.prompts.append(prompt)
            if len(self.prompts)==1:return partial
            if len(self.prompts)==2:return broken
            assert partial in prompt
            assert "SOURCE observations" in prompt
            assert "below retained" not in prompt or "hypothesis" in prompt
            assert "TARGET outputs are UNKNOWN" in prompt
            return complete
    p=RequiresIncumbent()
    samples=[
        ([1,2],1),([3,5],3),([4,8],4),
        ([6,9],6),([7,8],7),([9,1],1)]
    outcome=GenerativeProgramInventor(
        p,IsolatedPython(max_seconds=10),max_proposals=3).discover(
            samples,independent_source_checks=[([8,2],2)])
    assert outcome.verified
    assert len(outcome.attempts)==3
    assert outcome.attempts[0].source_correct==5
    assert outcome.attempts[1].status=="REJECTED"
    assert outcome.program==complete
    assert partial in p.prompts[2]
    assert "preflight" in p.prompts[2]
