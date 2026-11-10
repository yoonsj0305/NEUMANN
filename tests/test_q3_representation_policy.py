"""Q3 causal representation-policy learning from SOURCE-only prior errors.

All grids in these unit fixtures are constructed and synthetic. They prove
that an independently certified method-refutation learner changes the
discovery policy, NOT global independent-author Q3 capability.
"""
from __future__ import annotations

import pytest

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_object_graph_invention import induce_object_graph_factors
from neumann1.q3_single_discovery_core import (
    SourceMethodMemory,SingleDiscoveryCore)
from neumann1.q3_structural_invention import StructuralInventionPolicy
from neumann1.q3_representation_policy import LearnedRepresentationPrior, FeatureOutcome


def scene(top_color,bottom_color,*,top_r=1,swapped=False):
    h,w=10,12
    x=[[0]*w for _ in range(h)]
    y=[[0]*w for _ in range(h)]
    if swapped:
        top=[(top_r,2),(top_r+1,2)]
        bottom=[(top_r+4,7),(top_r+4,8)]
    else:
        top=[(top_r,2),(top_r,3)]
        bottom=[(top_r+4,7),(top_r+5,7)]
    for r,c in top:
        x[r][c]=top_color
        y[r][c+1]=top_color
    for r,c in bottom:
        x[r][c]=bottom_color
        y[r][c-1]=bottom_color
    return x,y


def graph_certified_source_episodes():
    runner=IsolatedPython(max_seconds=8)
    library=SourceMethodMemory(runner)
    for index,(a,b) in enumerate(((1,2),(3,4),(5,6))):
        train=[
            scene(a,b,top_r=1),
            scene(a,b,top_r=2),
        ]
        independent=[scene(a,b,top_r=1,swapped=True)]
        graph=induce_object_graph_factors(train,max_candidates=12)
        assert len(graph)>=2
        assert graph[0].representation.endswith("/bbox_aspect")
        fitted=[f for f in graph if f.representation.endswith("/category")]
        assert fitted
        library.admit("graph_source_"+str(index),train,independent,
                      fitted[0].program)
    library.freeze()
    return runner,library


def test_learned_representation_preference_from_actual_verified_source_refutations():
    runner,library=graph_certified_source_episodes()
    prior=LearnedRepresentationPrior.learn(library.episodes,runner)
    stats={o.name:(o.successful_transfer,o.falsified_transfer)
           for o in prior.outcomes}
    assert stats["category"]==(3,0)
    assert stats["bbox_aspect"]==(0,3)
    assert prior.score("source-inferred-graph-rewrite/category") > (
        prior.score("source-inferred-graph-rewrite/bbox_aspect"))
    assert prior.check_executions>=6
    assert prior.evidence()["target_gold_read"] is False
    assert prior.evidence()["transfer_observations"]>=6

    # New symbols and positions. Both controls receive EXACTLY the same
    # SOURCE training and one independent SOURCE verifier; only learned
    # discovery policy differs. Budget fixed at ONE proposed program.
    train=[scene(7,8,top_r=1),scene(7,8,top_r=2)]
    checks=[scene(7,8,top_r=1,swapped=True)]
    base=StructuralInventionPolicy(max_candidates=12)
    learned=StructuralInventionPolicy(
        max_candidates=12,representation_prior=prior)
    a=SingleDiscoveryCore(base,runner,max_proposals=1).discover(
        train,checks,reuse_memory=False).discovery
    c=SingleDiscoveryCore(learned,runner,max_proposals=1).discover(
        train,checks,reuse_memory=False).discovery
    assert a.verified is False
    assert c.verified is True
    assert c.program not in {e.program for e in library.episodes}
    assert "mapping=" in c.program
    verified=runner.evaluate(c.program,[x for x,y in checks])
    assert verified.status=="EXECUTED"
    assert all(source_same_value(v,y)
               for v,(_,y) in zip(verified.outputs,checks))


def test_untrusted_or_corrupt_teacher_does_not_update_learned_representation():
    runner,library=graph_certified_source_episodes()
    class Altered:
        def __init__(self,old):
            self.source_id=old.source_id
            self.identity=old.identity
            self.program="def transform(x):\n    return x"
            self.source_pairs=old.source_pairs
            self.independent_pairs=old.independent_pairs
    with pytest.raises(ValueError,match="recertification"):
        LearnedRepresentationPrior.learn(
            [Altered(library.episodes[0])],runner)

    class NoExecutor:
        def evaluate(self,program,inputs):
            raise RuntimeError("sandbox offline")
    with pytest.raises(RuntimeError,match="offline"):
        LearnedRepresentationPrior.learn(
            library.episodes,NoExecutor())


def test_refuted_representation_cannot_outrank_unobserved_hypothesis():
    """Posterior evidence must be SIGNED, not merely positive probability."""
    prior=LearnedRepresentationPrior((
        FeatureOutcome("always_refuted",0,12),
        FeatureOutcome("independently_verified",4,0),
        FeatureOutcome("partial_but_wrong",0,8,8),
    ),(),24)
    assert prior.score("always_refuted") < prior.score("unobserved") == 0
    assert prior.score("independently_verified") > prior.score("unobserved")
    assert prior.score("partial_but_wrong") < 0


def test_source_trial_policy_now_observes_coordinate_morphism_family():
    """Unit contract only. Independent original AUTHOR transfer is separate."""
    def pair(a,b):
        return [[a,b]], [[a,b,a,b]]
    train=[pair(1,2),pair(3,4)]
    checks=[pair(5,6)]
    prior=LearnedRepresentationPrior.learn_source_trials(
        [("synthetic-coordinate-contract",train,checks)],
        IsolatedPython(max_seconds=8),max_episodes=1)
    coordinate=[
        x for x in prior.outcomes
        if x.name.startswith("source-inferred-coordinate/")
    ]
    assert coordinate, "coordinate hypotheses must enter learned evidence"
    assert any(x.successful_transfer>0 for x in coordinate)
    assert prior.evidence()["target_gold_read"] is False
