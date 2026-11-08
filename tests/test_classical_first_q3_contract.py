"""Regression contract: classical first by default, discovery only for real gaps.

This does NOT prove universal self-invention. It prevents paying for discovery
on obligations with an original-verified classic solver available.
"""
from __future__ import annotations

from itertools import product

import pytest

from neumann1 import NeumannEngine, RegistryEngine
from neumann1.classical_kernels import (
    DIRECTED_REACHABILITY, classical_directed_reachability)
from neumann1.induced_fixpoint_grammar import (
    CompiledRule, InsufficientEvidence)
from neumann1.structural_meta_invention import (
    CertifiedProgram, StructuralMetaInventor)
from neumann1.meta_utility_policy import MetaUtilityEvidence


def sum_expr(n):
    out=("arg",0)
    for i in range(1,n):
        out=("add",out,("arg",i))
    return out


def seeded():
    inventor=StructuralMetaInventor()
    inventor.observe(CertifiedProgram(
        "f",2,sum_expr(2),certificate="original2"),verify=lambda _:True)
    learned=inventor.observe(CertifiedProgram(
        "f",3,sum_expr(3),certificate="original3"),verify=lambda _:True)
    assert learned
    return inventor


def test_default_classical_first_even_with_previously_invented_method():
    inventor=seeded()
    cold=[]
    def classical(n,params):
        cold.append(n)
        return sum_expr(n)
    result=inventor.solve_or_discover("f",4,
        verify=lambda p:p==sum_expr(4),classical=classical)
    assert result["origin"]=="classical_verified_then_learned"
    assert result["method_queries"]==0
    assert result["classical_invocations"]==1
    assert cold==[4]
    assert all(m.verifier_queries==0 for m in inventor.methods.values())


def test_classical_fails_then_invention_enters_gap():
    inventor=seeded()
    invocations=[]
    def cold(n,params):
        invocations.append(n)
        return None
    result=inventor.solve_or_discover("f",4,
        verify=lambda p:p==sum_expr(4),classical=cold)
    assert result["origin"]=="self_invented_method"
    assert result["classical_invocations"]==1
    assert result["method_queries"]>=1
    assert invocations==[4]


def test_favorable_source_cost_may_override_default():
    inventor=seeded()
    study=MetaUtilityEvidence(
        discovery_wall_seconds=0.001,discovery_candidate_checks=100,
        validation_tasks=10,validation_cold_candidate_checks=1000,
        validation_learned_candidate_checks=100,
        validation_cold_solved=9,validation_learned_solved=9,
        intended_future_tasks=100)
    assert inventor.admit_meta_method_utility("f",study).use_invented_first
    result=inventor.solve_or_discover(
        "f",4,verify=lambda p:p==sum_expr(4),
        classical=lambda n,params:(_ for _ in ()).throw(
            AssertionError("classical should be skipped after source admission")))
    assert result["origin"]=="self_invented_method"
    assert result["classical_invocations"]==0


def test_negative_cost_gate_prohibits_invented_search_even_if_cold_fails():
    inventor=seeded()
    study=MetaUtilityEvidence(
        discovery_wall_seconds=100,discovery_candidate_checks=100,
        validation_tasks=10,validation_cold_candidate_checks=100,
        validation_learned_candidate_checks=100,
        validation_cold_solved=10,validation_learned_solved=10,
        intended_future_tasks=1)
    assert not inventor.admit_meta_method_utility("f",study).use_invented_first
    out=inventor.solve_or_discover("f",4,
        verify=lambda p:p==sum_expr(4),classical=lambda n,p:None)
    assert out is None
    assert all(m.verifier_queries==0 for m in inventor.methods.values())


def test_false_classical_result_does_not_bypass_original_verifier():
    inventor=seeded()
    result=inventor.solve_or_discover(
        "f",4,verify=lambda p:p==sum_expr(4),
        classical=lambda n,p:("arg",n-1))
    assert result and result["origin"]=="self_invented_method"
    assert result["classical_invocations"]==1
    assert result["method_queries"]>=1


def test_missing_checker_cannot_trigger_classical_or_discovery():
    inventor=seeded()
    result=inventor.solve_or_discover(
        "f",4,verify=None,
        classical=lambda n,p:(_ for _ in ()).throw(
            AssertionError("should not be called")))
    assert result is None


def test_both_engines_direct_classical_path_never_construct_invention_state():
    task={"nodes":tuple(range(100)),
          "edges":tuple((i,i+1) for i in range(99)),
          "seeds":(0,)}
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        result=engine.solve_known_classical(
            task,semantics=DIRECTED_REACHABILITY)
        assert result==frozenset(range(100))
        assert not hasattr(engine,"_recursive_grammar")
        assert not hasattr(engine,"_invented_grammar")
        with pytest.raises(InsufficientEvidence):
            engine.solve_known_classical(task,semantics="arbitrary_graph_question")


def test_known_reachability_uses_bfs_after_invented_equivalence():
    train=[
        {"nodes":(0,1,2,3,4),"edges":((0,1),(1,2),(2,3)),
         "seeds":(0,),"answer":(0,1,2,3)},
        {"nodes":tuple("abcdef"),"edges":(("a","b"),("b","c"),("c","d")),
         "seeds":("a",),"answer":tuple("abcd")}]
    verify=[
        {"nodes":tuple(range(8)),
         "edges":tuple((i,i+1) for i in range(7)),
         "seeds":(0,),"answer":tuple(range(8))}]
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        rule=engine.learn_recursive_control(
            train,independent_source_checks=verify)
        assert rule.verified_for_all_finite_graphs
        large={"nodes":tuple(range(256)),
               "edges":tuple((i,i+1) for i in range(255)),
               "seeds":(0,)}
        assert engine.execute_recursive_control(large)==frozenset(range(256))


def test_nofreelunch_constructive_counterexample_no_universal_extrapolation():
    # For ANY observed strict subset of a finite table, two complete
    # sources can agree on it and differ on one unobserved pair.
    finite=tuple(range(6))
    original={(a,b):(a+b)%6 for a,b in product(finite,repeat=2)}
    observed={(a,b) for a in finite[:2] for b in finite}
    unseen=next((a,b) for a,b in original if (a,b) not in observed)
    alternate=dict(original)
    alternate[unseen]=(alternate[unseen]+1)%6
    assert all(original[x]==alternate[x] for x in observed)
    assert original[unseen]!=alternate[unseen]
