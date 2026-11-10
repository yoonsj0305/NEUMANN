"""Q3 latent object-relation program discovery.

Synthetic fixtures validate the SINGLE general discovery core plus actual
no-network Docker SOURCE verifier, NOT a global Q3 capability result.
Fixtures vary independent heldout positions, object category and geometry.
"""
from __future__ import annotations

import pytest

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_object_graph_invention import (
    induce_object_graph_factors,_pair_nodes,_choose_law)
from neumann1.q3_structural_invention import StructuralInventionPolicy
from neumann1.q3_single_discovery_core import SingleDiscoveryCore


def canvas(items,h=8,w=10):
    result=[[0 for _ in range(w)] for _ in range(h)]
    for color,cells in items:
        for r,c in cells:
            if result[r][c]!=0:raise ValueError("colliding synthetic example")
            result[r][c]=color
    return result


def source(label=1,shift_a=(0,1),shift_b=(0,-1),origin=(1,1)):
    ar,ac=origin
    first=[(ar,ac),(ar,ac+1)]
    second=[(ar+4,ac+5),(ar+4,ac+6)]
    inp=canvas([(label,first),(2,second)])
    out=canvas([
        (label,[(r+shift_a[0],c+shift_a[1]) for r,c in first]),
        (2,[(r+shift_b[0],c+shift_b[1]) for r,c in second]),
    ])
    return inp,out


def certify(train,checks):
    policy=StructuralInventionPolicy(
        max_states=6500,max_evaluations=250000,max_candidates=12)
    runner=IsolatedPython(max_seconds=8)
    output=SingleDiscoveryCore(
        policy,runner,max_proposals=12).discover(
        train,checks,reuse_memory=False).discovery
    return policy,output


def test_generic_object_graph_infers_two_separate_relation_actions_not_one_whole_grid():
    src=[
        source(origin=(1,0)),
        source(origin=(2,0)),
    ]
    held=[
        source(origin=(0,1)),
    ]
    factors=induce_object_graph_factors(src)
    assert len(factors)==1
    assert factors[0].representation.startswith("source-inferred-graph-rewrite/")
    assert factors[0].representation.endswith("category")
    assert "mapping=" in factors[0].program
    p,o=certify(src,held)
    assert o.verified and "mapping=" in o.program
    assert p.receipt.evaluated_expressions<=250000
    assert p.receipt.unique_semantics<=6500+12


def test_one_rule_depends_on_measured_object_area_not_benchmark_name():
    def make(r):
        one=[(r,1),(r,2)]
        two=[(r+3,5),(r+3,6),(r+4,5)]
        inp=canvas([(7,one),(7,two)])
        out=canvas([(7,[(y+1,x) for y,x in one]),
                    (7,[(y,x-1) for y,x in two])])
        return inp,out
    src=[make(0),make(1)]
    held=[make(2)]
    factors=induce_object_graph_factors(src)
    assert len(factors)==1
    assert "graph-rewrite/area" in factors[0].representation
    p,o=certify(src,held)
    assert o.verified
    assert "mapping=" in o.program


def test_changed_shape_or_ambiguous_categorical_rule_fails_closed():
    inp=canvas([(1,[(1,1),(1,2)])])
    out=canvas([(1,[(1,1),(1,2),(2,1)])])
    assert induce_object_graph_factors([(inp,out),(inp,out)])==()
    # Same observable category maps to two different actions. Cannot induce
    # a deterministic per-category transformation from this evidence.
    a=source(origin=(1,0))
    b=source(shift_a=(1,0),origin=(2,0))
    inferred=induce_object_graph_factors([a,b])
    assert all(not factor.representation.endswith("/category")
               for factor in inferred)


def test_insufficient_repeated_evidence_cannot_memorize_object_positions():
    a=source(origin=(0,0))
    # Single SOURCE example and unconstrained parameters are not proof.
    with pytest.raises(ValueError,match="bounded"):
        induce_object_graph_factors([a])
    runner=IsolatedPython(max_seconds=8)
    p=StructuralInventionPolicy(max_states=6500)
    p.prepare([a,a])
    assert p.receipt.candidates
    # All hypotheses are SOURCE-derived. Independent checks are NOT passed
    # to preparation, only to sandbox certification at final core.
    q=StructuralInventionPolicy(max_states=6500)
    q.prepare([a,a])
    assert q.receipt.candidates==p.receipt.candidates


def test_frozen_source_graph_rewrite_degrades_on_unseen_feature_class():
    known=[source(origin=(1,0)),source(origin=(2,0))]
    factors=induce_object_graph_factors(known)
    assert factors
    runner=IsolatedPython(max_seconds=8)
    # This training cohort contains two equal-shape objects whose actions
    # differ. Category is essential, so unseen categories must degrade.
    unseen_input,unseen_expected=source(label=5,origin=(0,0))
    run=runner.evaluate(factors[0].program,[unseen_input])
    assert run.status=="EXECUTED"
    assert source_same_value(run.outputs[0],unseen_input)
    # Unknown geometric feature class must fail safely to original input,
    # never claim a verified transformation from unsupported morphology.
    alien=canvas([(7,[(0,0)]),(2,[(5,7),(6,7)])])
    unknown=runner.evaluate(factors[0].program,[alien])
    assert unknown.status=="EXECUTED"
    assert source_same_value(unknown.outputs[0],alien)



def test_source_invents_orientation_of_one_object_without_rotating_unrelated_objects():
    from neumann1.q3_object_graph_invention import _symmetry_points
    def framed(r,c,other_col):
        shape=((0,0),(1,0),(1,1))
        rotated=_symmetry_points(shape,"turn90")
        first=[(r+y,c+x) for y,x in shape]
        first_output=[(r+y,c+2+x) for y,x in rotated]
        anchor=[(6,other_col),(6,other_col+1)]
        return (
            canvas([(3,first),(2,anchor)]),
            canvas([(3,first_output),(2,anchor)])
        )
    source_train=[
        framed(1,1,7),
        framed(2,2,6),
    ]
    heldout=[
        framed(0,3,1),
    ]
    factors=induce_object_graph_factors(source_train)
    assert factors
    assert "turn90" in factors[0].program
    policy,result=certify(source_train,heldout)
    assert result.verified
    assert result.program not in ("def transform(x):\n    return x",)
    assert "mapping=" in result.program



def test_one_general_rewrite_invents_object_duplication_with_source_proof():
    def scene(r,c):
        item=[(r,c),(r,c+1)]
        copy=[(r,c+3),(r,c+4)]
        anchor=[(5,8),(6,8)]
        return (
            canvas([(1,item),(2,anchor)]),
            canvas([(1,item),(1,copy),(2,anchor)]))
    train=[scene(1,0),scene(2,1)]
    check=[scene(3,0)]
    rules=induce_object_graph_factors(train)
    assert rules
    assert rules[0].representation.startswith("source-inferred-graph-rewrite/")
    # Shape-conditioned rules may be strictly better than literal color
    # memories; do not artificially force the weaker category hypothesis.
    assert "for dr,dc,color_role,orientation in mapping[val]" in rules[0].program
    p,d=certify(train,check)
    assert d.verified
    # A different, shorter SOURCE-derived representation (e.g. a leaf
    # category substitution for deletion) may solve the same observations.
    # Verify the graph rewrite itself independently rather than requiring
    # the shared core to prefer the more complicated hypothesis.
    verified=IsolatedPython(max_seconds=8).evaluate(
        rules[0].program,[x for x,y in check])
    assert verified.status=="EXECUTED"
    assert all(source_same_value(v,y)
               for v,(_,y) in zip(verified.outputs,check))


def test_one_general_rewrite_invents_object_deletion_from_source_differences():
    def scene(r,c):
        deleted=[(r,c),(r,c+1)]
        keep=[(5,8),(6,8)]
        return (canvas([(1,deleted),(2,keep)]),
                canvas([(2,keep)]))
    train=[scene(1,0),scene(2,1)]
    check=[scene(3,0)]
    rules=induce_object_graph_factors(train)
    assert rules
    assert rules[0].representation.startswith("source-inferred-graph-rewrite/")
    p,d=certify(train,check)
    assert d.verified
    # A different, shorter SOURCE-derived representation (e.g. a leaf
    # category substitution for deletion) may solve the same observations.
    # Verify the graph rewrite itself independently rather than requiring
    # the shared core to prefer the more complicated hypothesis.
    verified=IsolatedPython(max_seconds=8).evaluate(
        rules[0].program,[x for x,y in check])
    assert verified.status=="EXECUTED"
    assert all(source_same_value(v,y)
               for v,(_,y) in zip(verified.outputs,check))


def test_no_graph_rule_claim_without_executable_source_reconstruction():
    # Same source object identity, inconsistent creation/deletion on two
    # independent SOURCE demonstrations. Must not fabricate a fit.
    inp=canvas([(1,[(1,1),(1,2)]),(2,[(5,7),(6,7)])])
    out1=canvas([(2,[(5,7),(6,7)])])
    out2=canvas([(1,[(1,1),(1,2)]),(2,[(5,7),(6,7)])])
    assert induce_object_graph_factors([(inp,out1),(inp,out2)])==()



def test_causal_geometry_rule_is_equivariant_to_unseen_literal_colors():
    # When shape, not color, predicts the action, SOURCE-induced method must
    # generalize an entirely unseen category using a relative output role.
    def make(r,color):
        first=[(r,1),(r,2)]
        shifted=[(r,2),(r,3)]
        second=[(5,8),(6,8)]
        second_shift=[(5,7),(6,7)]
        return (
            canvas([(color,first),(2,second)]),
            canvas([(color,shifted),(2,second_shift)]))
    train=[make(0,1),make(1,1)]
    check=[make(2,5)]
    plans=induce_object_graph_factors(train)
    assert plans
    assert "source" in plans[0].program
    p,d=certify(train,check)
    assert d.verified
    assert "graph-rewrite" not in d.program  # standalone executable, no domain calls
