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
    assert "falsified" in policy.prompts[1]
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
