"""Q3 latent-hypothesis inference contract. NOT external generalization proof."""
import pytest
from neumann1.q3_latent_hypothesis_policy import LatentCausalHypothesisPolicy
from neumann1.open_program_inventor import GenerativeProgramInventor,IsolatedPython
from neumann1.q3_prompt_contract import SourceContextOverflow


def test_single_shared_policy_generates_its_own_latent_and_full_program():
    class OneModel:
        def __init__(self):
            self.hypotheses=[]
            self.code_prompts=[]
        def hypothesize(self,prompt):
            self.hypotheses.append(prompt)
            return '{"latent_variables":["x"],"invariant":"constant increase",'+(
                '"transformation":"x+1","uncertainty":"unknown"}')
        def propose(self,prompt):
            self.code_prompts.append(prompt)
            return "def transform(x):\n    return x+1"
    model=OneModel()
    policy=LatentCausalHypothesisPolicy(model)
    result=GenerativeProgramInventor(
        policy,IsolatedPython(max_seconds=8),
        max_proposals=1).discover(
            [(2,3),(4,5)],independent_source_checks=[(6,7)])
    assert result.verified
    assert len(model.hypotheses)==len(model.code_prompts)==1
    assert "Model-proposed, UNVERIFIED" in model.code_prompts[0]
    assert "constant increase" in model.code_prompts[0]
    assert "SOURCE" in model.code_prompts[0]


def test_no_hypothesis_abstains_and_never_queries_unseen_verifier():
    class NoHypothesis:
        def hypothesize(self,prompt):
            return ""
        def propose(self,prompt):
            raise AssertionError("cannot generate code without hypothesis")
    class NoRunner:
        def evaluate(self,program,inputs):
            raise AssertionError("must not open sealed SOURCE")
    result=GenerativeProgramInventor(
        LatentCausalHypothesisPolicy(NoHypothesis()),NoRunner(),
        max_proposals=2).discover(
            [(2,3)],independent_source_checks=[(4,5)])
    assert result.status=="ABSTAIN_CONTEXT_OVERFLOW"
    assert not result.verified


def test_no_prior_domain_operator_is_allowed():
    with pytest.raises(ValueError,match="one shared model"):
        LatentCausalHypothesisPolicy(object())
    with pytest.raises(ValueError,match="finite"):
        LatentCausalHypothesisPolicy(
            type("X",(),{"hypothesize":lambda self,p:p,
                        "propose":lambda self,p:p})(),
            max_hypothesis_chars=999999)
