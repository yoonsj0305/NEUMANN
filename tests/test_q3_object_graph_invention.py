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
    # A new unseen non-background token not present in the learned
    # observation -> output identity (not fabricated perfect SOURCE fit).
    changed=source(label=5,origin=(0,0))[0]
    run=runner.evaluate(factors[0].program,[changed])
    assert run.status=="EXECUTED"
    assert source_same_value(run.outputs[0],changed)
