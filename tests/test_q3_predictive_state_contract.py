"""Predictive-world SOURCE gradient contracts, fixtures NOT Q3/Q6 evidence."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from neumann1.q3_predictive_state import PredictiveStatePolicy


def make_tiny_policy():
    torch=pytest.importorskip("torch")
    class Tokenizer:
        eos_token="!"
        eos_token_id=33
        chat_template=None
        def __call__(self,text,add_special_tokens=False,truncation=False):
            assert truncation is False
            return {"input_ids":[ord(x)%128 for x in text]}
    class TinyLM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight=torch.nn.Parameter(torch.zeros(128))
        def forward(self,input_ids):
            n,m=input_ids.shape
            logits=self.weight.view(1,1,128).expand(n,m,128)
            return SimpleNamespace(logits=logits)
    p=PredictiveStatePolicy.__new__(PredictiveStatePolicy)
    p.torch=torch
    p.tokenizer=Tokenizer()
    p.model=TinyLM()
    p.optimizer=torch.optim.AdamW(p.model.parameters(),lr=0.05)
    p.device="cpu"
    p.max_context_tokens=4096
    p.max_updates=2
    p.update_count=0
    return p


def test_source_outcome_updates_actual_same_neural_policy_without_json_hypothesis():
    p=make_tiny_policy()
    before=p.model.weight.detach().clone()
    ctx={"demonstration":{"input":"observed SOURCE","label":"Yes"}}
    q={"scenario":"unknown causal relation","answer_set":["Yes","No"]}
    result_before=p.predict(ctx,[],q)
    assert result_before["prediction"] in ("Yes","No")
    assert result_before["explicit_new_concept_discovered"] is False
    assert result_before["hypothesis_intervention_revision_learned"] is False
    assert result_before["representation"]=="PRETRAINED_HIDDEN_STATE_OPTION_SCORING"
    receipt=p.learn_source(ctx,[],q,"Yes",evidence_id="signed-SOURCE-1")
    assert receipt["update"]==1
    assert receipt["actual_trainable_weight_delta_l1"]>0
    assert receipt["scope"]=="TRUSTED_SOURCE_ONLY"
    assert receipt["learning_objective"]=="OBSERVED_LABEL_CROSS_ENTROPY"
    assert receipt["independent_concept_invention_demonstrated"] is False
    assert not p.torch.equal(before,p.model.weight.detach())
    result_after=p.predict(ctx,[],q)
    assert result_after["prediction"] in ("Yes","No")
    assert result_before["raw_relative_loglik"]!=result_after[
        "raw_relative_loglik"]
    assert p.learn_source(ctx,[],q,"No",
                          evidence_id="signed-SOURCE-2")["update"]==2
    assert p.learn_source(ctx,[],q,"No",
                          evidence_id="signed-SOURCE-3") is None


def test_source_provenance_and_answer_alternatives_are_strict():
    p=make_tiny_policy()
    ctx={"context":"unseen"}
    q={"scenario":"new","answer_set":["True","False","Unknown"]}
    with pytest.raises(ValueError,match="outside declared"):
        p.learn_source(ctx,[],q,"TARGET_EXAMPLE",evidence_id="source-proof")
    with pytest.raises(ValueError,match="signed SOURCE"):
        p.learn_source(ctx,[],q,"True",evidence_id="")
    with pytest.raises(ValueError,match="no TARGET"):
        p.predict(ctx,[{"scope":"HIDDEN_TARGET","observed":"True"}],q)
    with pytest.raises(ValueError,match="invalid answer category"):
        p.predict(ctx,[],{"answer_set":["Yes","Yes"]})


def test_two_unrelated_domains_use_same_core_no_handwritten_transformation():
    p=make_tiny_policy()
    logical=p.predict(
        {"source":"some premises"},[],
        {"premises":["If X then Y","X"],
         "conclusion":"Y","answer_set":["True","False","Uncertain"]})
    causal=p.predict(
        {"source":"observed interventions"},[],
        {"scenario":"Does it cause Y?","answer_set":["Yes","No"]})
    assert logical["representation"]==causal["representation"]
    assert logical["no_human_authored_domain_answer_rule"]
    assert causal["no_human_authored_domain_answer_rule"]
