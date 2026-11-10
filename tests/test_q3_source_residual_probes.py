"""Q3 partial-causal representation learning under typed, disjoint SOURCE.

Synthetic contracts are NOT independent original wins; the actual model
SOURCE-only teacher evidence must come from frozen ARC2 author tasks.
"""
import pytest
from neumann1.q3_source_residual_probes import (
    source_edit_f1,induce_source_residual_probes)
from neumann1.q3_representation_policy import LearnedRepresentationPrior
from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_single_discovery_core import SingleDiscoveryCore
from neumann1.q3_structural_invention import StructuralInventionPolicy


def samples():
    return [
        ([[0,1,0],[0,0,0]],[[0,2,0],[0,3,0]]),
        ([[1,0,0],[0,0,0]],[[2,0,0],[0,4,0]]),
        ([[0,0,1],[0,0,0]],[[0,0,2],[0,5,0]]),
    ]


def test_partial_error_provides_training_signal_but_never_counts_as_full_proof():
    train=samples()[:2]
    checks=samples()[2:]
    proposals=induce_source_residual_probes(train,max_probes=8)
    assert proposals
    assert any(p.representation=="probe/atomic-relation" for p in proposals)
    runner=IsolatedPython(max_seconds=8)
    has_partial=False
    has_exact=False
    for probe in proposals:
        result=runner.evaluate(probe.program,[x for x,y in checks])
        assert result.status=="EXECUTED"
        candidate=result.outputs[0]
        if source_edit_f1(checks[0][0],checks[0][1],candidate)>0:
            has_partial=True
        has_exact |= source_same_value(candidate,checks[0][1])
    assert has_partial
    assert not has_exact
    policy=LearnedRepresentationPrior.learn_source_trials(
        [("original_1",train,checks)],runner)
    evidence=policy.evidence()
    assert evidence["transfer_observations"]>0
    assert evidence["real_verifier_executions"]>0
    assert sum(o.partial_transfer for o in policy.outcomes)>0
    assert all(o.successful_transfer==0 for o in policy.outcomes)
    assert evidence["target_gold_read"] is False


def test_degraded_mode_returns_abstain_on_not_source_certified_partial():
    train=samples()[:2]
    checks=samples()[2:]
    policy=StructuralInventionPolicy(max_states=6500,max_candidates=12)
    out=SingleDiscoveryCore(
        policy,IsolatedPython(max_seconds=8),max_proposals=12).discover(
        train,checks,reuse_memory=False).discovery
    # Do not reward a partially correct SOURCE program as perfect.
    assert out.verified is False
    assert out.program is None


def test_partial_source_posterior_rejects_test_gold_tamper_and_frozen_provenance():
    runner=IsolatedPython(max_seconds=8)
    prior=LearnedRepresentationPrior.learn_source_trials(
        [("source_id",samples()[:2],samples()[2:])],runner)
    snapshot=prior.source_snapshot()
    restored=LearnedRepresentationPrior.from_source_snapshot(snapshot)
    assert restored==prior
    # Partial-only results are independently refuted complete programs.
    # They must NOT outrank never-tried exact representations.
    assert prior.score("probe/atomic-relation")<prior.score(
        "probe/undiscovered-no-evidence")
    snapshot["outcomes"][0]["partial_transfer"]=10000000
    with pytest.raises(ValueError,match="corrupted"):
        LearnedRepresentationPrior.from_source_snapshot(snapshot)
    with pytest.raises(ValueError,match="overlap"):
        LearnedRepresentationPrior.learn_source_trials(
            [("duplicate",(samples()[0],samples()[1]),(samples()[1],))],
            runner)
    with pytest.raises(ValueError,match="duplicate"):
        LearnedRepresentationPrior.learn_source_trials(
            [("id",samples()[:2],samples()[2:]),
             ("id",samples()[:2],samples()[2:])],runner)


def test_strict_source_edit_score_prevents_background_and_boolean_coercion():
    x=[[0,1],[0,0]]
    gold=[[0,2],[3,0]]
    candidate=[[0,2],[0,0]]
    assert source_edit_f1(x,gold,x)==0
    assert source_edit_f1(x,gold,candidate)==pytest.approx(2/3)
    assert source_edit_f1(x,gold,gold)==1.0
    assert source_edit_f1([0,0],[False,False],[0,0])==0.0
