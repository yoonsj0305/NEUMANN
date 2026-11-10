"""First-principles experience -> latent representation -> future policy loop.

These are *mechanism integration tests*, NOT evidence of Q3/Q6 generality.
Only the test fixture contains a trivial learned scalar and toy executor.
Production code has no domain-specific answer grammar or solver.
"""
import pytest

from neumann1.causal_experience import CausalExperienceCore,Hypothesis
from neumann1.representation import ExperienceStructureFormer,ExplicitStructureFormer
from neumann1.engine import NeumannEngine
from neumann1.types import Problem,IRKind,CostLedger,VerificationResult


class AdaptiveFixturePolicy:
    """Small policy proves that feedback CHANGES the next latent proposal."""
    def __init__(self):
        self.scalar=0
        self.learn_calls=0
        self.last_events=None

    def hypotheses(self,context,source_history,allowed_queries):
        value="initial" if not self.scalar else "revised"
        return [
            Hypothesis(
                name="new-model-authored-variable",
                kind="neumann.latent",
                latent_variables={"relation":value,"context":context},
                relations={"proposed_dependency":"unknown"},
                predictions={"train_query":value,"sealed_query":"revised"}),
            Hypothesis(
                name="different-causal-prediction",
                kind="neumann.latent",
                latent_variables={"other":"unverified"},
                relations={},
                predictions={"train_query":"different",
                             "sealed_query":"different"}),
        ]

    def learn_from_counterexample(self,events):
        self.learn_calls+=1
        self.last_events=events
        assert all(e["scope"]=="TRUSTED_SOURCE_ONLY" for e in events)
        assert any(e["contradicted"] for e in events)
        self.scalar+=1
        return {"actual_policy_parameter_updated":self.scalar}


def source_observation_verifier(task,query_id,query,actual,evidence_id):
    """In real use, this callback MUST verify measurement provenance."""
    return (task=="example.source" and
            query_id in ("train_query","sealed_query") and
            query=={"input":query_id} and actual=="revised" and
            evidence_id==query_id+".signed")


def fixture_problem():
    return Problem(raw_text="unspecified unseen causal relation",metadata={
        "source_identity":"example.source",
        "source_queries":{
            "train_query":{"input":"train_query"},
            "sealed_query":{"input":"sealed_query"},
        },
        "sealed_source_query_ids":["sealed_query"],
        "observations":{"raw":[1,2,3]},
    })


class FixtureSolver:
    name="generic_verification_fixture"
    def supports(self,rep):
        return rep.kind=="neumann.latent"
    def solve(self,rep,ledger):
        ledger.solver_steps+=1
        return rep.payload["latent_variables"]["relation"]


class FixtureVerifier:
    def verify(self,problem,rep,answer,ledger):
        ledger.verification_steps+=1
        return VerificationResult(
            answer=="revised","fixture only: original downstream check")


def test_one_engine_learns_a_new_latent_state_from_real_source_feedback():
    policy=AdaptiveFixturePolicy()
    core=CausalExperienceCore(policy,max_hypotheses=2)
    former=ExperienceStructureFormer(core)
    engine=NeumannEngine(
        former,[FixtureSolver()],FixtureVerifier(),min_confidence=0.8)
    # The new learned causal core does not instantiate the historical
    # human-defined AST synthesis grammar anywhere in its hot path.
    assert engine._meta_inventor is None
    p=fixture_problem()

    before=engine.solve(p)
    assert before.solver_name=="fallback_required"
    assert not before.verified
    assert before.representation.kind=="neumann.latent"
    assert before.representation.payload["latent_variables"]["relation"]=="initial"
    assert policy.learn_calls==0
    assert core.select_query()=="train_query"

    receipts=engine.observe_source_experience(
        "train_query","revised",
        evidence_id="train_query.signed",
        verify_source=source_observation_verifier,
        revise_context={"revised_after_real_measured_counterexample":True})
    assert len(receipts)==2
    assert receipts[0].contradicted
    assert receipts[0].learning_receipt["actual_policy_parameter_updated"]==1
    assert policy.scalar==1
    assert core.representation().payload["latent_variables"]["relation"]=="revised"

    # This is a previously UNOBSERVED, SEALED SOURCE prediction and therefore
    # cannot update the policy after it is checked.
    frozen_before=policy.learn_calls
    assert engine.certify_source_representation(
        "sealed_query","revised",
        evidence_id="sealed_query.signed",
        verify_source=source_observation_verifier)
    assert policy.learn_calls==frozen_before
    after=engine.solve(p)
    assert after.solver_name=="generic_verification_fixture"
    assert after.verified
    assert after.answer=="revised"
    assert after.representation.kind=="neumann.latent"
    assert after.representation.confidence==1.0
    assert "not calibrated probability" in after.representation.rationale
    # New concept came from the model, not candidate_ir metadata.
    assert "candidate_ir" not in p.metadata
    assert engine._meta_inventor is None


def test_sealed_source_is_unusable_for_learning_or_adaptive_retesting():
    policy=AdaptiveFixturePolicy()
    core=CausalExperienceCore(policy,max_hypotheses=2)
    core.start("example.source",{"raw":[1,2]},fixture_problem().metadata[
        "source_queries"],sealed_queries={"sealed_query"})
    with pytest.raises(ValueError,match="reserved independent SOURCE"):
        core.observe("sealed_query","revised",evidence_id="sealed_query.signed",
                     verify_source=source_observation_verifier)
    assert policy.learn_calls==0
    core.freeze()
    # A heldout check alone, without even one independently trusted
    # training SOURCE observation, cannot certify a latent causal state.
    assert not core.certify_sealed_source(
        "sealed_query","revised",
        evidence_id="sealed_query.signed",
        verify_source=source_observation_verifier)
    assert core.representation().confidence==0.0
    with pytest.raises(ValueError,match="one-shot"):
        core.certify_sealed_source(
            "sealed_query","revised",
            evidence_id="sealed_query.signed",
            verify_source=source_observation_verifier)
    with pytest.raises(ValueError,match="frozen"):
        core.observe("train_query","revised",
                     evidence_id="train_query.signed",
                     verify_source=source_observation_verifier)


def test_refutation_must_be_source_verified_and_cannot_reopen_after_revision():
    policy=AdaptiveFixturePolicy()
    core=CausalExperienceCore(policy,max_hypotheses=2)
    former=ExperienceStructureFormer(core)
    former.form(fixture_problem(),CostLedger())
    with pytest.raises(ValueError,match="unverified"):
        former.observe_source(
            "train_query","wrong",evidence_id="train_query.signed",
            verify_source=source_observation_verifier)
    assert policy.learn_calls==0
    former.observe_source(
        "train_query","revised",evidence_id="train_query.signed",
        verify_source=source_observation_verifier,revise_context={"x":0})
    with pytest.raises(ValueError,match="repeat"):
        former.observe_source(
            "train_query","revised",evidence_id="train_query.signed",
            verify_source=source_observation_verifier)
    assert policy.learn_calls==1



def test_source_contradiction_cannot_be_cleared_by_lucky_sealed_match():
    policy=AdaptiveFixturePolicy()
    core=CausalExperienceCore(policy,max_hypotheses=2)
    former=ExperienceStructureFormer(core)
    former.form(fixture_problem(),CostLedger())
    # The source prediction was "initial", but actual = "revised".
    # Force no revision after learning; the old representation stays wrong.
    former.observe_source(
        "train_query","revised",evidence_id="train_query.signed",
        verify_source=source_observation_verifier)
    assert policy.learn_calls==1
    assert core.representation().payload["latent_variables"]["relation"]=="initial"
    assert not former.certify_source(
        "sealed_query","revised",evidence_id="sealed_query.signed",
        verify_source=source_observation_verifier)
    assert core.representation().confidence==0.0


def test_missing_experience_and_unauthorized_prediction_fail_closed():
    policy=AdaptiveFixturePolicy()
    core=CausalExperienceCore(policy,max_hypotheses=2)
    former=ExperienceStructureFormer(core)
    p=Problem(raw_text="no observation",metadata={})
    result=former.form(p,CostLedger())
    assert result.kind==IRKind.UNKNOWN
    assert result.confidence==0.0
    class InvalidPolicy:
        def hypotheses(self,context,history,allowed_queries):
            return [{"name":"h","kind":"neumann.latent",
                     "latent_variables":{"x":1},"relations":{},
                     "predictions":{"NOT_ALLOWED":4}}]
    illegal=CausalExperienceCore(InvalidPolicy())
    with pytest.raises(ValueError,match="unauthorized"):
        illegal.start("example.source",{},{
            "train_query":{"input":"train_query"},
            "sealed_query":{"input":"sealed_query"}},
            sealed_queries={"sealed_query"})


def test_old_fixed_ir_scaffold_remains_available_as_degraded_mode():
    legacy=ExplicitStructureFormer()
    unknown=legacy.form(Problem("anything"),CostLedger())
    assert unknown.kind==IRKind.UNKNOWN
    valid=legacy.form(Problem("arithmetic",metadata={
        "candidate_ir":{"kind":"arithmetic",
                        "payload":{"expression":"2+2"}}}),CostLedger())
    assert valid.kind==IRKind.ARITHMETIC


def test_genuine_torch_gradient_changes_world_learning_weights_without_code():
    torch=pytest.importorskip("torch")
    from types import SimpleNamespace
    from neumann1.q3_latent_world_policy import TrainableLatentWorldPolicy

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
        def forward(self,input_ids,labels):
            import torch.nn.functional as F
            n,m=input_ids.shape
            logits=self.weight.view(1,1,128).expand(n,m,128)
            loss=F.cross_entropy(logits[:,:-1,:].transpose(1,2),
                labels[:,1:],ignore_index=-100)
            return SimpleNamespace(loss=loss)

    policy=TrainableLatentWorldPolicy.__new__(TrainableLatentWorldPolicy)
    policy.torch=torch
    policy.tokenizer=Tokenizer()
    policy.model=TinyLM()
    policy.device="cpu"
    policy.optimizer=torch.optim.AdamW(policy.model.parameters(),lr=0.05)
    policy.max_context_tokens=3072
    policy.max_updates=2
    policy.update_count=0
    policy._last_latent_prefix="Example SOURCE; propose new latent"
    e={
        "scope":"TRUSTED_SOURCE_ONLY",
        "task_id":"original.source",
        "query_id":"causal_intervention_1",
        "evidence_id":"original.source.sign1",
        "query":{"allowed_input":1},
        "hypothesis":{"name":"model invented latent factor",
            "kind":"neumann.latent",
            "latent_variables":{"causal_factor":"a_new_variable"},
            "relations":{},"predictions":{
                "causal_intervention_1":{"changed":True}}},
        "predicted":{"changed":True},
        "observed":{"changed":True},
        "contradicted":False,
    }
    before=policy.model.weight.detach().clone()
    receipt=policy.learn_from_counterexample((e,))
    assert receipt["updates"]==1
    assert receipt["reinforced_model_authored_latent"] is True
    assert receipt["actual_trainable_weight_delta_l1"]>0
    assert not torch.equal(before,policy.model.weight.detach())
    e2=dict(e,predicted={"changed":False},contradicted=True,
            evidence_id="original.source.sign2")
    receipt2=policy.learn_from_counterexample((e2,))
    assert receipt2["reinforced_model_authored_latent"] is False
    assert receipt2["actual_trainable_weight_delta_l1"]>0
    assert policy.learn_from_counterexample((e2,)) is None
