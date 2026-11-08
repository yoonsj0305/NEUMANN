"""Q3/Q6 source-only proof-of-scope: same invention controller on unrelated data types.

This is a development experiment on author-created black boxes, NOT a
global independent-author Q3/Q6 result or cost win against matched synthesis.
"""
from __future__ import annotations

from fractions import Fraction
from random import Random

import pytest
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.composition_meta_inventor import (
    CallablePrimitive, CompositionInventor, exact_polynomial_residual)
from neumann1 import arc2_meta_grid_reasoner as old
from neumann1.relational_grid_inventor import RelationalGridInventor, predict


def numeric_sources():
    target=lambda x:3*x*x+11
    train=[(x,target(x)) for x in (-7,-5,-3,-2,1,3,5,7)]
    checks=[(x,target(x)) for x in (-11,-9,-1,2,4,6,9,12)]
    target_x=[Fraction(k,3) for k in range(-60,61) if k%3]
    return target,train,checks,target_x


def numeric_options():
    ident=CallablePrimitive("identity",lambda x:x)
    return ([ident], [ident, CallablePrimitive("square",lambda x:x*x),
                      CallablePrimitive("neg",lambda x:-x)])


def grid_sample(h,w,r,c,a,b):
    matrix=[[0]*w for _ in range(h)]
    matrix[r][c]=a
    matrix[r][c+1]=b
    matrix[r+1][c]=a
    return tuple(tuple(z) for z in matrix)


def grid_target(x):
    g=old.d4(x,"rotate90")
    points=[(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row) if v]
    r0=min(p[0] for p in points)
    r1=max(p[0] for p in points)
    c0=min(p[1] for p in points)
    c1=max(p[1] for p in points)
    role=min({p[2] for p in points},
             key=lambda v:(-sum(p[2]==v for p in points),v))
    result=[list(row) for row in g]
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):
            if result[r][c]==0:result[r][c]=role
    return tuple(tuple(row) for row in result)


def grid_sources():
    xs=[
        grid_sample(5,6,1,2,2,3),
        grid_sample(6,5,2,1,6,8),
        grid_sample(7,6,3,2,4,9),
        grid_sample(5,7,2,3,7,1),
    ]
    checks=[
        grid_sample(8,6,2,1,9,2),
        grid_sample(6,8,2,3,7,5),
        grid_sample(8,7,3,2,1,4),
    ]
    rng=Random(13847)
    holdout=[]
    for i in range(48):
        h=rng.randint(5,9);w=rng.randint(5,9)
        r=rng.randint(1,h-3);c=rng.randint(1,w-3)
        a,b=rng.sample(range(1,10),2)
        holdout.append(grid_sample(h,w,r,c,a,b))
    return ([(x,grid_target(x)) for x in xs],
            [(x,grid_target(x)) for x in checks],holdout)


def grid_residual(pairs):
    if any(len(x)!=len(y) or len(x[0])!=len(y[0]) for x,y in pairs):
        return None
    fit=RelationalGridInventor(max_search_ms=450).solve(pairs)
    if not fit.source_fit or fit.method is None:return None
    return lambda x: predict(x,fit.method)


def grid_options():
    ident=CallablePrimitive("identity",lambda x:x)
    return ([ident], [ident,
            CallablePrimitive("rotate90",lambda x:old.d4(x,"rotate90")),
            CallablePrimitive("flip_lr",lambda x:old.d4(x,"flip_lr")),
            CallablePrimitive("transpose",lambda x:old.d4(x,"transpose"))])


def test_one_unchanged_controller_invents_exact_numeric_and_grid_compositions():
    controller=CompositionInventor()
    target,train,checks,held=numeric_sources()
    classic,pre=numeric_options()
    numeric=controller.discover(
        train,checks,classical_candidates=classic,
        pre_candidates=pre,learn_residual=lambda data:
        exact_polynomial_residual(data,max_degree=1))
    assert numeric.status=="SOURCE_VERIFIED_NEW_COMPOSITION"
    assert numeric.executable.ast[0]=="compose"
    assert numeric.executable.pre.name=="square"
    assert all(numeric.apply(x)==target(x) for x in held)
    assert len(held)==80

    source,validation,grid_held=grid_sources()
    classics,pre=grid_options()
    spatial=controller.discover(
        source,validation,classical_candidates=classics,
        pre_candidates=pre,learn_residual=grid_residual)
    assert spatial.status=="SOURCE_VERIFIED_NEW_COMPOSITION"
    assert spatial.executable.ast[0]=="compose"
    assert spatial.executable.pre.name=="rotate90"
    assert all(spatial.apply(x)==grid_target(x) for x in grid_held)
    assert len(grid_held)==48
    # Same controller class + instance, two incompatible primitive types.
    # But both domain-specific residual constructors were human-provided.
    assert numeric.executable.pre.name!=spatial.executable.pre.name


def test_classical_first_skips_residual_model_and_research_budget():
    controller=CompositionInventor()
    target,train,checks,_=numeric_sources()
    count=[]
    def forbidden(data):
        count.append(1)
        raise AssertionError("needlessly inventor called")
    classical=CallablePrimitive("known_exact",target)
    result=controller.discover(
        train,checks,classical_candidates=[classical],
        pre_candidates=[],learn_residual=forbidden)
    assert result.status=="CLASSICAL_VERIFIED"
    assert result.residual_attempts==0
    assert not count


def test_fresh_source_counterexample_rejects_false_program():
    controller=CompositionInventor()
    target,train,checks,_=numeric_sources()
    # A degree-one fit to just one source branch can look correct, but
    # validation on a different point must refuse to promote it.
    bad=lambda observations:(lambda z:observations[0][1])
    classic,pre=numeric_options()
    result=controller.discover(
        train,checks,classical_candidates=classic,
        pre_candidates=pre,learn_residual=bad)
    assert result.status=="ABSTAIN_UNSUPPORTED"
    with pytest.raises(ValueError):
        result.apply(123)


def test_unseen_one_cell_exception_breaks_unconditional_generalization():
    target,train,checks,held=numeric_sources()
    controller=CompositionInventor()
    classic,pre=numeric_options()
    r=controller.discover(train,checks,classical_candidates=classic,
                          pre_candidates=pre,
                          learn_residual=lambda rows:
                          exact_polynomial_residual(rows,max_degree=1))
    x=held[0]
    exceptional=lambda v:target(v)+(1 if v==x else 0)
    assert r.status=="SOURCE_VERIFIED_NEW_COMPOSITION"
    assert all(exceptional(v)==target(v) for v,y in train+checks)
    assert r.apply(x)!=exceptional(x)


def test_typed_bad_source_oracle_and_limits_fail_closed():
    controller=CompositionInventor(max_pre_candidates=1)
    with pytest.raises(ValueError):
        controller.discover([(1,2)],[(3,4)],classical_candidates=[],
            pre_candidates=[],learn_residual=lambda rows:None)
    with pytest.raises(ValueError):
        CompositionInventor(max_pre_candidates=0)
    target,train,checks,_=numeric_sources()
    classic,pre=numeric_options()
    r=controller.discover(train,checks,classical_candidates=classic,
         pre_candidates=pre,
         learn_residual=lambda rows:
         exact_polynomial_residual(rows,max_degree=1))
    assert r.status=="ABSTAIN_UNSUPPORTED"


def test_engine_plugin_interface_never_auto_assumes_semantics():
    # Smoke both live engines: no name-based routing. The caller selects
    # trusted typed primitives, source verification and the residual plugin.
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        target,train,checks,held=numeric_sources()
        classic,pre=numeric_options()
        result=engine.synthesize_composed_semantics(
            train,checks,classical_candidates=classic,
            pre_candidates=pre,
            learn_residual=lambda rows:
            exact_polynomial_residual(rows,max_degree=1))
        assert result.status=="SOURCE_VERIFIED_NEW_COMPOSITION"
        assert result.apply(held[0])==target(held[0])


def test_strong_classical_degree_two_interpolation_wins_numeric_before_invention():
    """Conventional interpolation is a fully adequate competitor on this task.

    Do not misreport a degree-one-composition gain over an intentionally weak
    identity-only classical list as an ORIGINAL novel capability.
    """
    target,train,checks,held=numeric_sources()
    specialist=exact_polynomial_residual(train,max_degree=2)
    assert specialist is not None
    assert all(specialist(x)==target(x) for x in held)
    called=[]
    def forbidden_residual(rows):
        called.append(rows)
        raise AssertionError("do not invent when classical interpolation solves")
    result=CompositionInventor().discover(
        train,checks,
        classical_candidates=[
            CallablePrimitive("classical-exact-polynomial-interpolation-degree2",
                              specialist)],
        pre_candidates=[],
        learn_residual=forbidden_residual)
    assert result.status=="CLASSICAL_VERIFIED"
    assert result.residual_attempts==0
    assert result.exact_source_checks==len(train)+len(checks)
    assert not called
