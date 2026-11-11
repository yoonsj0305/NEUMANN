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
        # Both evidence queries refer to one externally identified mechanism.
        # This identity is not a solution, label or algorithm family.
        "source_episode_bindings":{
            "train_query":"original-author-episode-1",
            "sealed_query":"original-author-episode-1",
        },
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
        "source_queries"],sealed_queries={"sealed_query"},
        episode_bindings=fixture_problem().metadata[
            "source_episode_bindings"])
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
            sealed_queries={"sealed_query"},
            episode_bindings=fixture_problem().metadata[
                "source_episode_bindings"])


def test_unrelated_source_worlds_cannot_certify_a_target_mechanism():
    """This is the exact Q3/Q6 error from previous external-original tests."""
    policy=AdaptiveFixturePolicy()
    core=CausalExperienceCore(policy,max_hypotheses=2)
    former=ExperienceStructureFormer(core)
    problem=fixture_problem()
    # Two unrelated original stories are domain examples, not causal
    # interventions into the same latent mechanism.
    problem.metadata["source_episode_bindings"]={
        "train_query":"unrelated-story-A",
        "sealed_query":"unrelated-story-B",
    }
    response=former.form(problem,CostLedger())
    assert response.kind==IRKind.UNKNOWN
    assert response.confidence==0.0
    assert core.task_id is None
    with pytest.raises(ValueError,match="same-mechanism"):
        core.start(
            "example.source",{"raw":[1,2]},
            problem.metadata["source_queries"],
            sealed_queries={"sealed_query"},
            episode_bindings=problem.metadata["source_episode_bindings"])
    assert policy.learn_calls==0


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
    # An actually model-authored hypothesis which is refuted must now
    # receive a proposal-distribution penalty, not only prediction loss.
    policy.max_updates=3
    policy._last_latent_text="hypothetical latent learned by the neural proposer"
    prior=policy.model.weight.detach().clone()
    rejected=policy.learn_from_counterexample((e2,))
    assert rejected["refuted_model_authored_latent_penalty"] is True
    assert rejected["reinforced_model_authored_latent"] is False
    assert rejected["actual_trainable_weight_delta_l1"]>0
    assert not torch.equal(prior,policy.model.weight.detach())
    # Even when NO hypothesis could initially be formatted, the SAME
    # trainable neural weights can absorb a verified observation directly.
    policy.max_updates=4
    before_unformed=policy.model.weight.detach().clone()
    receipt3=policy.learn_grounded_source_without_hypothesis(
        task_id="example.source",context={"observations":[1,2]},
        query={"input":"observed source transition"},
        observed={"effect":"new source observation"},
        evidence_id="source-only-authorized-proof")
    assert receipt3["updates"]==4
    assert receipt3["new_causal_concept_proven"] is False
    assert receipt3["actual_trainable_weight_delta_l1"]>0
    assert not torch.equal(before_unformed,policy.model.weight.detach())


def test_invalid_first_model_hypothesis_can_learn_authorized_source_and_revise():
    """The real zero-gradient blocker: invalid model JSON no longer kills learning."""
    from neumann1.causal_experience import LatentHypothesisFormatError

    class InitiallyUnformedPolicy:
        def __init__(self):
            self.learned=0
            self.attempts=0

        def hypotheses(self,context,source_history,queries):
            self.attempts+=1
            if self.learned==0:
                raise LatentHypothesisFormatError(
                    "model copied a JSON placeholder, not SOURCE query IDs")
            assert source_history[-1]["scope"]=="TRUSTED_SOURCE_ONLY"
            return [Hypothesis(
                name="model-authored-after-source",
                kind="neumann.latent",
                latent_variables={"relation":"revised"},
                relations={"from_source":"an empirical candidate only"},
                predictions={"train_query":"revised",
                             "sealed_query":"revised"})]

        def learn_grounded_source_without_hypothesis(
                self,*,task_id,context,query,observed,evidence_id):
            assert task_id=="example.source"
            assert query=={"input":"train_query"}
            assert observed=="revised"
            assert evidence_id=="train_query.signed"
            self.learned+=1
            return {
                "updates":self.learned,
                "TRAINABLE_SOURCE_POLICY_STATE_CHANGED":True,
                "new_concept_proven":False,
            }

    policy=InitiallyUnformedPolicy()
    core=CausalExperienceCore(policy)
    former=ExperienceStructureFormer(
        core,allow_grounded_bootstrap=True)
    engine=NeumannEngine(
        former,[FixtureSolver()],FixtureVerifier(),min_confidence=0.8)
    before=engine.solve(fixture_problem())
    assert not before.verified
    assert core.hypotheses==()
    assert core.select_query()=="train_query"
    with pytest.raises(ValueError,match="reserved independent SOURCE"):
        engine.observe_source_experience(
            "sealed_query","revised",
            evidence_id="sealed_query.signed",
            verify_source=source_observation_verifier)
    assert policy.learned==0
    with pytest.raises(ValueError,match="unverified"):
        engine.observe_source_experience(
            "train_query","wrong",
            evidence_id="train_query.signed",
            verify_source=source_observation_verifier)
    assert policy.learned==0
    receipts=engine.observe_source_experience(
        "train_query","revised",
        evidence_id="train_query.signed",
        verify_source=source_observation_verifier,
        revise_context={"source_observation_verified":True})
    assert policy.learned==1
    assert len(receipts)==1
    assert receipts[0].hypothesis_sha256=="UNFORMED"
    assert receipts[0].predicted is None
    assert receipts[0].contradicted is False
    assert receipts[0].learning_receipt["updates"]==1
    with pytest.raises(ValueError,match="repeat"):
        engine.observe_source_experience(
            "train_query","revised",
            evidence_id="train_query.signed",
            verify_source=source_observation_verifier)
    assert len(core.hypotheses)==1
    assert core.hypotheses[0].latent_variables["relation"]=="revised"
    assert engine.certify_source_representation(
        "sealed_query","revised",
        evidence_id="sealed_query.signed",
        verify_source=source_observation_verifier)
    after=engine.solve(fixture_problem())
    assert after.verified
    assert after.answer=="revised"
    assert policy.attempts==2


def test_invalid_initial_hypothesis_does_not_silently_enable_bootstrap():
    from neumann1.causal_experience import LatentHypothesisFormatError

    class RefusingPolicy:
        def hypotheses(self,*args):
            raise LatentHypothesisFormatError(
                "no valid model-authored latent hypothesis")
        def learn_grounded_source_without_hypothesis(self,**kwargs):
            raise AssertionError("must not receive unauthorized SOURCE")

    core=CausalExperienceCore(RefusingPolicy())
    with pytest.raises(LatentHypothesisFormatError):
        core.start(
            "example.source",fixture_problem().metadata["observations"],
            fixture_problem().metadata["source_queries"],
            sealed_queries={"sealed_query"},
            episode_bindings=fixture_problem().metadata[
                "source_episode_bindings"])
    assert core.task_id is None


def test_concept_and_predictions_have_independent_model_generation_channels():
    """Transport proof only: no handcrafted grammar or multi-grid JSON gate."""
    torch=pytest.importorskip("torch")
    from neumann1.q3_latent_world_policy import TrainableLatentWorldPolicy

    class Tokenizer:
        eos_token="!"
        eos_token_id=33
        chat_template=None
        def __call__(self,text,add_special_tokens=False,truncation=False):
            assert truncation is False
            return {"input_ids":[ord(char) for char in text]}
        def decode(self,ids,skip_special_tokens=True):
            return "".join(chr(int(t)) for t in ids)

    tok=Tokenizer()
    class TextOnlyModel:
        calls=[]
        def eval(self):
            return self
        def generate(self,*,input_ids,attention_mask,max_new_tokens,
                     do_sample,temperature,top_p,pad_token_id):
            prompt=tok.decode(input_ids[0])
            self.calls.append(prompt)
            if "single_authorized_query" not in prompt:
                # This free-form model hypothesis is deliberately NOT JSON.
                answer="A previously unnamed hidden relation regulates outputs."
            elif '"probe"' in prompt:
                answer='{"effect":42}'
            else:
                answer='{"effect":43}'
            extension=torch.tensor([[ord(c) for c in answer]],
                                   dtype=torch.long)
            return torch.cat((input_ids,extension),dim=1)

    policy=TrainableLatentWorldPolicy.__new__(TrainableLatentWorldPolicy)
    policy.torch=torch
    policy.tokenizer=tok
    policy.model=TextOnlyModel()
    policy.device="cpu"
    policy.seed=1007
    policy.max_context_tokens=4096
    policy.max_new_tokens=500
    proposed=policy.hypotheses(
        {"SOURCE_demo":{"input":[1,2],"output":[3,4]}},(),
        {"probe":{"input":[2,3]},"sealed":{"input":[9,7]}})
    assert len(proposed)==1
    item=proposed[0]
    assert item["kind"]=="neumann.latent"
    assert "previously unnamed" in item["relations"]["model_authored_falsifiable_claim"]
    assert item["predictions"]["probe"]=={"effect":42}
    assert item["predictions"]["sealed"]=={"effect":43}
    assert len(policy.model.calls)==3
    assert "previously unnamed" in policy._last_latent_text
    # The SAME prompt that generated the SOURCE prediction must be used
    # for its supervised observation loss; no off-policy teacher shortcut.
    event={
        "scope":"TRUSTED_SOURCE_ONLY","query_id":"probe",
        "query":{"input":[2,3]},"observed":{"effect":99},
        "hypothesis":item,"predicted":{"effect":42},
    }
    loss_prefix,target=policy._world_teacher(event)
    assert loss_prefix==policy.model.calls[1]
    assert target=='{"effect":99}'
    with pytest.raises(ValueError,match="query changed"):
        policy._world_teacher(dict(event,query={"input":[7,7]}))
    forged=dict(item,latent_variables={
        "proposed_internal_causal_concept":"human-inserted claim"})
    with pytest.raises(ValueError,match="differs"):
        policy._world_teacher(dict(event,hypothesis=forged))


def test_refuted_model_concept_probability_actually_decreases():
    """Gradient sign check on tiny neural logits, NOT an intelligence claim."""
    torch=pytest.importorskip("torch")
    from types import SimpleNamespace
    from neumann1.q3_latent_world_policy import TrainableLatentWorldPolicy

    class Tokenizer:
        eos_token="!"
        chat_template=None
        def __call__(self,text,add_special_tokens=False,truncation=False):
            assert truncation is False
            return {"input_ids":[ord(c)%128 for c in text]}

    class TinyLM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.logits=torch.nn.Parameter(torch.zeros(128))
        def forward(self,input_ids,labels):
            import torch.nn.functional as F
            n,m=input_ids.shape
            logits=self.logits.view(1,1,128).expand(n,m,128)
            return SimpleNamespace(loss=F.cross_entropy(
                logits[:,:-1,:].transpose(1,2),labels[:,1:],
                ignore_index=-100))

    policy=TrainableLatentWorldPolicy.__new__(TrainableLatentWorldPolicy)
    policy.torch=torch
    policy.tokenizer=Tokenizer()
    policy.model=TinyLM()
    policy.device="cpu"
    policy.optimizer=torch.optim.AdamW(policy.model.parameters(),lr=0.05)
    policy.max_context_tokens=3072
    policy.max_updates=1
    policy.update_count=0
    policy._last_latent_prefix="Model invented a hypothesis:"
    policy._last_latent_text="zzzzzzzzzzzzzzzz"
    event={
        "scope":"TRUSTED_SOURCE_ONLY",
        "task_id":"one_coherent_source_world",
        "query_id":"source_counterexample",
        "evidence_id":"verified_source_only",
        "query":{"intervention":"original"},
        "hypothesis":{"name":"model-drawn","kind":"neumann.latent",
            "latent_variables":{"concept":"zzzz"},
            "relations":{},"predictions":{"source_counterexample":"wrong"}},
        "predicted":"wrong",
        "observed":"xxxxxxxxxx",
        "contradicted":True,
    }
    before=float(policy._loss(policy._last_latent_prefix,
                              policy._last_latent_text).detach())
    result=policy.learn_from_counterexample((event,))
    after=float(policy._loss(policy._last_latent_prefix,
                             policy._last_latent_text).detach())
    assert result["refuted_model_authored_latent_penalty"] is True
    assert result["actual_trainable_weight_delta_l1"]>0
    assert after>before, "refuted model concept must actually become less likely"


def test_same_model_revision_receives_only_verified_source_counterexample_witness():
    """Projection of already authorized evidence, NOT a new task experiment."""
    from neumann1.q3_latent_world_policy import TrainableLatentWorldPolicy
    history=[
        {
            "scope":"TRUSTED_SOURCE_ONLY","task_id":"one_author_episode",
            "query":{"intervention":"measure again"},
            "observed":{"value":17},"predicted":{"value":12},
            "contradicted":True,
            "hypothesis":{
                "latent_variables":{
                    "proposed_internal_causal_concept":
                        "an invented but incorrect causal relation"}},
            "learning_receipt":{"huge_optimizer_log":"unrelated metadata"},
        },
    ]
    witnesses=TrainableLatentWorldPolicy._source_witnesses(history)
    assert len(witnesses)==1
    row=witnesses[0]
    assert row["source_identity"]=="one_author_episode"
    assert row["verified_observation"]=={"value":17}
    assert row["incorrect_prediction"]=={"value":12}
    assert row["refuted_model_hypothesis"]==(
        "an invented but incorrect causal relation")
    assert "learning_receipt" not in str(row)
    assert "huge_optimizer_log" not in str(witnesses)
    with pytest.raises(ValueError,match="non-SOURCE"):
        TrainableLatentWorldPolicy._source_witnesses([
            dict(history[0],scope="ORIGINAL_TARGET_GOLD")])


def test_single_model_authored_hypothesis_can_autonomously_choose_a_falsification():
    """Q3 active sensing cannot depend on a second competing candidate."""
    class SinglePolicy:
        def hypotheses(self,context,history,queries):
            return [{
                "name":"one-model-authored-candidate",
                "kind":"neumann.latent",
                "latent_variables":{"invented_causal_factor":"unverified"},
                "relations":{"mechanism":"unverified"},
                "predictions":{"train_query":"initial",
                               "sealed_query":"initial"},
            }]
    core=CausalExperienceCore(SinglePolicy())
    meta=fixture_problem().metadata
    core.start("example.source",{"raw":[1,2]},meta["source_queries"],
               sealed_queries={"sealed_query"},
               episode_bindings=meta["source_episode_bindings"])
    assert len(core.hypotheses)==1
    assert core.select_query()=="train_query"
    assert core._evaluated_queries==set()
    # Once the only nonsealed SOURCE intervention is consumed, no repeated
    # tuning and no access to the reserved sealed verifier.
    core._evaluated_queries.add("train_query")
    assert core.select_query() is None
