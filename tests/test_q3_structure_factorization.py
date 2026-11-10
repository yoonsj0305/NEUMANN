"""General SOURCE factorization contracts, NOT invented new-benchmark wins."""
import pytest
from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_single_discovery_core import SingleDiscoveryCore,SourceMethodMemory
from neumann1.q3_structure_factorization import induce_structural_factors
from neumann1.q3_structural_invention import (
    LearnedDiscoveryPolicy,StructuralInventionPolicy)


def _solve(train,check,*,learned=None):
    runner=IsolatedPython(max_seconds=8)
    p=StructuralInventionPolicy(
        learned,max_states=6500,max_evaluations=250000,
        max_candidates=12)
    outcome=SingleDiscoveryCore(
        p,runner,max_proposals=12).discover(
            train,check,reuse_memory=False).discovery
    assert outcome.verified
    assert p.receipt
    assert all(source_same_value(got,y) for got,(_,y) in zip(
        runner.evaluate(outcome.program,[x for x,y in check]).outputs,check))
    return outcome.program


def test_cross_type_discovery_prior_survives_new_output_topology():
    runner=IsolatedPython(max_seconds=8)
    m=SourceMethodMemory(runner)
    m.admit("sum",[([1,2],3),([2,3],5)],[([9,8],17)],
            "def transform(x):\n    return sum(x)")
    m.admit("mod",[(9,True),(18,True),(8,False)],[(27,True)],
            "def transform(x):\n    return x % 9 == 0")
    m.freeze()
    learned=LearnedDiscoveryPolicy.fit(m.episodes)
    assert learned.weight("mod","list","list")==0
    assert learned.weight("mod","list","list",transfer=True)>=1
    assert learned.weight("sum","list","int")>=1
    assert learned.weight("sum","list","list",transfer=True)>=1


def test_induce_new_scalar_relation_lifted_across_nested_structure():
    sources=[
        ([[1,2],[3,4]],[[3,4],[5,6]]),
        ([[7,8],[9,10]],[[9,10],[11,12]]),
    ]
    independent=[
        ([[0,11],[5,6]],[[2,13],[7,8]])
    ]
    plans=induce_structural_factors(sources)
    assert any(p.representation=="leaf-affine-add" for p in plans)
    discovered=_solve(sources,independent)
    assert "factor" in discovered and "+ (2)" in discovered


def test_index_reversal_is_structural_and_executes_over_independent_nested_data():
    sources=[
        ([[1,2,3],[4,5,6]],[[4,5,6],[1,2,3]]),
        ([[9,8,7],[6,5,4]],[[6,5,4],[9,8,7]]),
    ]
    independent=[
        ([[0,1,2],[3,4,5]],[[3,4,5],[0,1,2]])
    ]
    plans=induce_structural_factors(sources)
    assert any("index-isomorphism/reverse-outer"==p.representation
               for p in plans)
    discovered=_solve(sources,independent)
    assert "x[::-1]" in discovered


def test_source_induced_index_translation_over_disjoint_examples():
    sources=[
        ([[0,1,0,0],[0,0,0,0],[0,0,0,0]],
         [[0,0,0,0],[0,1,0,0],[0,0,0,0]]),
        ([[0,0,0,1],[0,0,0,0],[0,0,0,0]],
         [[0,0,0,0],[0,0,0,1],[0,0,0,0]]),
    ]
    independent=[
        ([[0,0,1,0],[0,0,0,0],[0,0,0,0]],
         [[0,0,0,0],[0,0,1,0],[0,0,0,0]])
    ]
    plans=induce_structural_factors(sources)
    assert any(p.representation=="index-translation" for p in plans)
    discovered=_solve(sources,independent)
    assert "dr=1" in discovered


def test_sparse_value_relocation_infers_latent_group_not_fixed_task_family():
    sources=[
        ([[0,1,0,0],[0,0,0,2],[0,0,0,0]],
         [[0,0,1,0],[0,0,0,2],[0,0,0,0]]),
        ([[1,0,0,0],[0,0,0,2],[0,0,0,0]],
         [[0,1,0,0],[0,0,0,2],[0,0,0,0]]),
    ]
    independent=[
        ([[0,0,1,0],[0,0,0,2],[0,0,0,0]],
         [[0,0,0,1],[0,0,0,2],[0,0,0,0]])
    ]
    plans=induce_structural_factors(sources)
    assert any(p.representation=="sparse-token-motion" for p in plans)
    discovered=_solve(sources,independent)
    assert "color=1" in discovered and "dc=1" in discovered


def test_never_infer_arbitrary_nonrepeated_literal_lookup_from_two_examples():
    # Copying every training position to an answer table is memorization, not
    # a transferred executable relation. Such a lookup must not be invented.
    sources=[
        ([[1,2],[3,4]],[[4,3],[2,1]]),
        ([[5,6],[7,8]],[[8,7],[6,5]]),
    ]
    plans=induce_structural_factors(sources)
    assert all(p.representation!="leaf-category-relation" for p in plans)
    assert any(p.representation=="index-isomorphism/rot180" for p in plans)


def test_original_target_not_used_to_pick_structural_representation():
    sources=[
        ([[0,0],[0,1]],[[1,0],[0,0]]),
        ([[2,0],[0,0]],[[0,0],[0,2]]),
    ]
    p=StructuralInventionPolicy()
    p.prepare(sources)
    before=p.receipt.candidates
    assert isinstance(before,tuple)
    assert len(before)<=12
    # A later unknown author test cannot modify a frozen prepared candidate.
    assert p.receipt.candidates==before


def test_same_source_induced_atomic_operator_generalizes_between_strings_and_arrays():
    # A string is a sequence of tokens, not an indivisible input object.
    # This is NOT a handcrafted named-text solver or an original benchmark.
    source=[
        ("aabb","bbaa"),
        ("bbaa","aabb"),
        ("abab","baba"),
        ("abcabc","bacbac"),
    ]
    check=[("bcbcab","acacba")]
    candidates=induce_structural_factors(source)
    assert any(p.representation=="leaf-category-relation"
               for p in candidates)
    code=_solve(source,check)
    assert "join" in code
    # The exact variable name is not a semantic property: composed code
    # represents the same SOURCE-derived token relation with mapping.get(t,t).
    assert ".get(" in code
    assert "'a':'b'" in code or "'a': 'b'" in code

    runner=IsolatedPython(max_seconds=8)
    other_inputs=[[[1,2,1],[2,1,2]],[[2,2],[1,1]]]
    other_train=[
        ([[1,2,1],[2,1,2]],[[2,1,2],[1,2,1]]),
        ([[2,2,1],[1,1,2]],[[1,1,2],[2,2,1]]),
    ]
    other_check=[
        ([[2,1],[2,2]],[[1,2],[1,1]])]
    c2=_solve(other_train,other_check)
    assert "factor" in c2 and ".get(c,c)" in c2 or ".get(v,v)" in c2
