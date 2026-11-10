"""Q3 actual executable-code repair learning, no human task solver branch.

These constructed SOURCE examples verify that a generative policy can
receive its own failed program + causal counterexample and that *the same
inference text* is recovered from independently reexecuted evidence for
gradient training. Mechanism tests only, not first-seen Q3 PASS.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from neumann1.open_program_inventor import (
    GenerativeProgramInventor, IsolatedPython, source_training_example,
)
from neumann1.q3_source_repair_learning import recertified_repair_prompt
from neumann1.q3_trainable_code_policy import (
    source_training_rows, recertify_source_rows,
)
from neumann1.q3_prompt_contract import model_training_ids,model_prefix


class RecordedScriptPolicy:
    def __init__(self, guesses):
        self.guesses=iter(guesses)
        self.prompts=[]
    def propose(self,prompt):
        self.prompts.append(prompt)
        return next(self.guesses)


@pytest.mark.parametrize("first,correction,train,checks,phase", [
    (
      "def transform(x):\n    return x",
      "def transform(x):\n    return x*x",
      [(2,4),(3,9)],[(5,25)],
      "TRAIN_SOURCE",
    ),
    (
      "def transform(x):\n    return x if x%2==0 else 0",
      "def transform(x):\n    return x",
      [(2,2),(4,4)],[(3,3),(5,5)],
      "INDEPENDENT_SOURCE",
    ),
])
def test_exact_inference_repair_prompt_recovered_from_real_sandbox(
        first,correction,train,checks,phase,tmp_path):
    runner=IsolatedPython(max_seconds=12)
    policy=RecordedScriptPolicy((first,correction))
    discovery=GenerativeProgramInventor(
        policy,runner,max_proposals=2).discover(
            train,independent_source_checks=checks)
    assert discovery.verified
    assert discovery.program==correction
    assert len(policy.prompts)==2
    assert first in policy.prompts[1], "the previous broken code must be visible"
    assert "source" in policy.prompts[1].lower()
    teacher=source_training_example(
        train,discovery,independent_source_checks=checks,
        source_identity="constructed-source-proof-"+phase)
    assert len(teacher["pairs"])==len(train)+len(checks)
    assert teacher["independent_checks"]==len(checks)
    assert teacher["repair_phase"]==phase
    assert teacher["repair_prior_sha256"]==hashlib.sha256(first.encode()).hexdigest()
    path=tmp_path/"teacher.jsonl"
    path.write_text(json.dumps(teacher,sort_keys=True)+"\n")
    loaded,digest=source_training_rows(path)
    assert len(loaded)==1 and len(digest)==64
    verified=recertify_source_rows(loaded,runner=runner)
    assert len(verified)==1
    exact_training_prompt,observed_phase=recertified_repair_prompt(
        loaded[0],runner)
    assert exact_training_prompt==policy.prompts[1]
    assert observed_phase==phase
    assert "TARGET" not in exact_training_prompt


def test_unverified_or_fabricated_repair_is_never_training_evidence():
    runner=IsolatedPython(max_seconds=12)
    policy=RecordedScriptPolicy((
        "def transform(x):\n    return x",
        "def transform(x):\n    return x*x",
    ))
    train=[(2,4),(3,9)];checks=[(5,25)]
    discovery=GenerativeProgramInventor(
        policy,runner,max_proposals=2).discover(
            train,independent_source_checks=checks)
    with pytest.raises(ValueError,match="actual independent SOURCE"):
        source_training_example(train,discovery,
                                source_identity="no-hidden-checks")
    row=source_training_example(
        train,discovery,independent_source_checks=checks,
        source_identity="real-independent-checks")
    forged=dict(row)
    forged["repair_prior_sha256"]="0"*64
    with pytest.raises(ValueError,match="SHA tampered"):
        recertified_repair_prompt(forged,runner)
    fabricated=dict(row)
    fabricated["repair_prior_program"]=discovery.program
    fabricated["repair_prior_sha256"]=discovery.frozen_sha256
    with pytest.raises(ValueError,match="no fresh sealed SOURCE"):
        recertified_repair_prompt(fabricated,runner)
    false_labels=dict(row)
    false_labels["pairs"]=list(row["pairs"])
    false_labels["pairs"][-1]=[5,999]
    with pytest.raises(Exception):
        recertify_source_rows([false_labels],runner=runner)


def test_clean_one_shot_success_not_misreported_as_repair():
    runner=IsolatedPython(max_seconds=12)
    policy=RecordedScriptPolicy(("def transform(x):\n    return x+1",))
    source=[(1,2),(2,3)];checks=[(4,5)]
    d=GenerativeProgramInventor(
        policy,runner,max_proposals=1).discover(
            source,independent_source_checks=checks)
    assert d.verified
    row=source_training_example(
        source,d,independent_source_checks=checks,
        source_identity="one-shot")
    assert "repair_prior_program" not in row
    with pytest.raises(ValueError,match="genuine failed prior"):
        recertified_repair_prompt(row,runner)


def test_single_sealed_source_check_is_never_used_as_adaptive_oracle():
    """A failed final SOURCE check is a terminal ABSTAIN, not a new prompt."""
    runner=IsolatedPython(max_seconds=12)
    before="def transform(x):\n    return x if x%2==0 else 0"
    after="def transform(x):\n    return x"
    policy=RecordedScriptPolicy((before,after))
    discovery=GenerativeProgramInventor(
        policy,runner,max_proposals=2).discover(
            [(2,2),(4,4)],independent_source_checks=[(3,3)])
    assert discovery.status=="ABSTAIN_SEALED_SOURCE_REFUTED"
    assert discovery.verified is False
    assert discovery.program is None
    assert len(discovery.attempts)==1
    assert len(policy.prompts)==1, "the sealed check must never be reused"


def test_revision_prompt_keeps_only_latest_witness_not_accumulated_history():
    """Three sequential hypotheses share one bounded feedback interface."""
    from neumann1.open_program_inventor import IsolatedPython
    runner=IsolatedPython(max_seconds=12)
    p1="def transform(x):\n    return x"
    p2="def transform(x):\n    return x+1"
    p3="def transform(x):\n    return x*x"
    policy=RecordedScriptPolicy((p1,p2,p3))
    d=GenerativeProgramInventor(
        policy,runner,max_proposals=3).discover(
            [(2,4),(3,9)],independent_source_checks=[(5,25)])
    assert d.verified
    assert len(policy.prompts)==3
    assert "\n    return x\n" not in policy.prompts[2]
    assert p2 in policy.prompts[2]
    assert policy.prompts[2].count("The exact prior program to REVISE") == 1
    assert len(policy.prompts[2]) < len(policy.prompts[1])+100


def test_context_overflow_abstains_without_ever_querying_sealed_source():
    """The fallback on unsupported prompt capacity is ABSTAIN, not fake PASS."""
    from neumann1.q3_prompt_contract import SourceContextOverflow
    class OverflowPolicy:
        attempts=0
        def propose(self,prompt):
            self.attempts+=1
            raise SourceContextOverflow("token capacity exceeded")
    class NoExecutor:
        def evaluate(self,program,inputs):
            raise AssertionError("SOURCE verification must never run")
    policy=OverflowPolicy()
    d=GenerativeProgramInventor(
        policy,NoExecutor(),max_proposals=8).discover(
            [(1,2)],independent_source_checks=[(3,4)])
    assert policy.attempts==1
    assert d.status=="ABSTAIN_CONTEXT_OVERFLOW"
    assert not d.verified and d.program is None
