"""Contract tests: one learned hypothesis policy, no task-family generator."""
from hashlib import sha256
import json
import pytest

from neumann1.q3_latent_hypothesis_policy import (
    HypothesisConditionedPolicy, completion, hypothesis_prompt,
    parse_hypothesis_proposal, recertified_hypothesis_repair_row,
)
from neumann1.open_program_inventor import UnsafeProposal


CODE="def transform(x):\n    return x"
HYP="A hidden relation preserves every observed input value."


class DummyPolicy:
    def __init__(self):
        self.prompts=[]
    def propose(self,prompt):
        self.prompts.append(prompt)
        return completion(HYP,CODE)


def test_same_policy_proposes_explanation_and_executable_method():
    base=DummyPolicy()
    policy=HypothesisConditionedPolicy(base)
    assert policy.propose("original observations") == CODE
    assert policy.propose("second observations") == CODE
    assert len(base.prompts)==2
    assert HYP in base.prompts[1]
    assert "original observations" in base.prompts[0]
    assert "latent" in base.prompts[0]
    assert policy.hypothesis_attempts[0]["provenance"]=="MODEL_AUTHORED_NOT_VERIFIED_CONCEPT"
    assert policy.hypothesis_attempts[0]["program_sha256"]==sha256(CODE.encode()).hexdigest()


def test_reject_missing_hypothesis_and_unbounded_or_unsafe_code():
    with pytest.raises(UnsafeProposal):
        parse_hypothesis_proposal(json.dumps({"program":CODE}))
    with pytest.raises(UnsafeProposal):
        parse_hypothesis_proposal(json.dumps({"hypothesis":HYP,"program":"import os"}))
    with pytest.raises(UnsafeProposal):
        parse_hypothesis_proposal("not JSON")


def test_repair_training_requires_model_authorship_and_real_refutation(monkeypatch):
    from neumann1 import q3_latent_hypothesis_policy as mod
    row={"hypothesis_provenance":"MODEL_AUTHORED",
         "corrected_hypothesis":HYP,
         "repair_prior_hypothesis":HYP,
         "repair_prior_hypothesis_provenance":"MODEL_AUTHORED",
         "repair_prior_hypothesis_sha256":sha256(HYP.encode()).hexdigest(),
         "corrected_hypothesis_sha256":sha256(HYP.encode()).hexdigest(),
         "program":CODE}
    seen=[]
    def genuine_repair(r,runner):
        seen.append(r)
        return "actual refuted program and observed counterexample", "TRAIN_SOURCE"
    monkeypatch.setattr(mod,"recertified_repair_prompt",genuine_repair)
    prompt,answer,phase=recertified_hypothesis_repair_row(row,object())
    assert prompt==hypothesis_prompt("actual refuted program and observed counterexample",HYP)
    assert parse_hypothesis_proposal(answer)==(HYP,CODE)
    assert phase=="TRAIN_SOURCE"
    assert seen==[row]
    with pytest.raises(ValueError):
        recertified_hypothesis_repair_row({**row,"hypothesis_provenance":"HUMAN"},object())
    with pytest.raises(ValueError):
        recertified_hypothesis_repair_row({**row,"corrected_hypothesis_sha256":"0"*64},object())
