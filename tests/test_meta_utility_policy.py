"""Q3/Q4 production utility: keep only discoveries with positive source net value.

These checks exercise the two real engines. Numbers from a source-only
developer cohort are a calibration fixture, not a new frontier evaluation.
"""
import math
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.structural_meta_invention import StructuralMetaInventor
from neumann1.meta_utility_policy import (
    MetaUtilityEvidence, decide_meta_method)


def arg(i):
    return ("arg",i)


def selector(n):
    t=arg(0)
    for i in range(1,n):
        x=arg(i)
        t=("ite",("lt",t,x),x,t)
    return t


def original(t, n, case="max"):
    def run(expr, values):
        op=expr[0]
        if op=="arg":return values[expr[1]]
        items=[run(x,values) for x in expr[1:]]
        if op=="lt":return items[0]<items[1]
        if op=="ite":return items[1] if items[0] else items[2]
        return False
    import itertools
    return all(run(t,x)==(max(x) if case=="max" else min(x))
        for x in itertools.product((-2,0,3),repeat=n))


def source_fixture(**changes):
    data={
        "discovery_wall_seconds":61.50174,
        "discovery_candidate_checks":158635,
        "validation_tasks":128,
        "validation_cold_candidate_checks":79169,
        "validation_learned_candidate_checks":79099,
        "validation_cold_solved":0,
        "validation_learned_solved":0,
        "intended_future_tasks":120,
    }
    data.update(changes)
    return MetaUtilityEvidence(**data)


def as_engine_source(evidence):
    return {key:value for key,value in evidence.__dict__.items()
            if key!='source_only'}


def test_arc2_source_cost_cannot_pay_for_frozen_method():
    # Both validator arms share an exhaustive same-language grammar;
    # this fixture isolates utility decision, not the ARC2 answer rate.
    ans=decide_meta_method(source_fixture())
    assert ans.route=="CLASSICAL_FIRST"
    assert ans.reason=="NO_POSITIVE_SOURCE_NET_UTILITY"
    assert 290000 < ans.estimate_break_even_tasks < 291000
    assert 0.024 < ans.estimate_future_savings_seconds < 0.027
    assert ans.estimate_net_benefit_seconds < -61
    assert ans.evidence_level.endswith("ESTIMATE")


def test_live_core_deletes_unprofitable_candidate_generation_but_not_evidence():
    engine=NeumannEngine(None,[],None)
    for n in (2,3):
        assert engine.synthesize_program("economic.max",n,
            verify=lambda p,n=n:original(p,n),
            classical=lambda n,params:selector(n))
    assert engine.meta_inventor.methods
    record=engine.admit_meta_method_utility(
        "economic.max",
        **as_engine_source(source_fixture()))
    assert record.route=="CLASSICAL_FIRST"
    old=sum(m.verifier_queries for m in engine.meta_inventor.methods.values())
    actual=[]
    def cold(n,params):
        actual.append(n)
        return selector(n)
    result=engine.synthesize_program("economic.max",4,
        verify=lambda p:original(p,4),classical=cold)
    assert result and result["verified"]
    assert result["origin"]=="classical_verified_then_learned"
    assert result["method_queries"]==0
    assert actual==[4]
    assert sum(m.verifier_queries for m in engine.meta_inventor.methods.values())==old
    # The verified result still enriches the source library, rather than
    # disabling NEUMANN's learning altogether.
    assert 4 in engine.meta_inventor.observations["economic.max"]
    assert engine.synthesize_program("economic.max",5,
        verify=lambda p:original(p,5),classical=None) is None


def test_utility_enabled_methods_still_solve_without_classic_calls():
    engine=RegistryEngine(None,None)
    for n in (2,3):
        engine.synthesize_program("profit.max",n,
            verify=lambda p,n=n:original(p,n),
            classical=lambda n,params:selector(n))
    ans=engine.admit_meta_method_utility("profit.max",**{
        "discovery_wall_seconds":.001,
        "discovery_candidate_checks":100,
        "validation_tasks":10,
        "validation_cold_candidate_checks":1000,
        "validation_learned_candidate_checks":100,
        "validation_cold_solved":8,
        "validation_learned_solved":8,
        "intended_future_tasks":120})
    assert ans.use_invented_first
    result=engine.synthesize_program("profit.max",4,
        verify=lambda p:original(p,4),
        classical=lambda n,p:(_ for _ in ()).throw(
            AssertionError("classic should be skipped")))
    assert result["origin"]=="self_invented_method"
    assert result["classical_invocations"]==0


def test_source_capability_priority_and_fail_closed_incorrect():
    a=decide_meta_method(source_fixture(
        validation_cold_solved=4,validation_learned_solved=5))
    assert a.use_invented_first
    assert a.reason=="VERIFIED_SOURCE_CAPABILITY_GAIN"
    b=decide_meta_method(source_fixture(
        validation_cold_solved=5,validation_learned_solved=4))
    assert not b.use_invented_first
    assert b.reason=="CAPABILITY_REGRESSION"
    try:
        MetaUtilityEvidence(**{**source_fixture().__dict__,"source_only":False})
        assert False
    except ValueError:
        pass


def test_economic_decision_survives_method_inventory_checkpoint():
    engine=NeumannEngine(None,[],None)
    result=engine.admit_meta_method_utility("persist.policy",
        **as_engine_source(source_fixture()))
    checkpoint=engine.meta_inventor.checkpoint()
    loaded=StructuralMetaInventor.from_checkpoint(checkpoint)
    decision=loaded.meta_utility_decision("persist.policy")
    assert decision==result
    assert decision.route=="CLASSICAL_FIRST"
    # A direct overwrite with forged favorable decision is impossible;
    # admission is recomputed from validated source counts and time.
    assert "source_only_meta_utility" in checkpoint
