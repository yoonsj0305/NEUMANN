"""Q3: new composed geometric+relational semantics beyond fixed 626 grammar.

All tests are AUTHOR-CREATED and cannot prove frontier original Q3/Q6.
Original trained output never participates in prediction on a heldout input.
"""
from __future__ import annotations

from random import Random

import pytest

from neumann1 import NeumannEngine,RegistryEngine
from neumann1 import arc2_meta_grid_reasoner as old
from neumann1.composed_grid_inventor import ComposedGridInventor
from neumann1.relational_grid_inventor import RelationalGridInventor


def example(h,w,row,col,a,b):
    assert 1<=row<h-2 and 1<=col<w-2 and a!=b
    canvas=[[0]*w for _ in range(h)]
    canvas[row][col]=a
    canvas[row][col+1]=b
    canvas[row+1][col]=a
    return tuple(tuple(z) for z in canvas)


def oracle(g):
    rotated=old.d4(g,"rotate90")
    cells=[(r,c,v) for r,row in enumerate(rotated) for c,v in enumerate(row) if v]
    lo_r=min(x[0] for x in cells);hi_r=max(x[0] for x in cells)
    lo_c=min(x[1] for x in cells);hi_c=max(x[1] for x in cells)
    majority=min(set(z[2] for z in cells),
                 key=lambda color:(-sum(z[2]==color for z in cells),color))
    result=[list(row) for row in rotated]
    for r in range(lo_r,hi_r+1):
        for c in range(lo_c,hi_c+1):
            if result[r][c]==0:
                result[r][c]=majority
    return tuple(tuple(row) for row in result)


def training():
    xs=[example(5,6,1,2,2,3),
        example(6,5,2,1,6,8),
        example(7,6,3,2,4,9),
        example(5,7,2,3,7,1)]
    return tuple((x,oracle(x)) for x in xs)


def heldout(n=48):
    rng=Random(13847)
    out=[]
    for _ in range(n):
        h=rng.randint(4,9)
        w=rng.randint(4,9)
        r=rng.randint(1,h-3)
        c=rng.randint(1,w-3)
        a,b=rng.sample(range(1,10),2)
        out.append(example(h,w,r,c,a,b))
    return tuple(out)


def test_strong_frozen_626_grammar_lacks_joint_source_operator():
    demo=training()
    old_fit,_=old.fit_task(demo,range(len(old.PROGRAMS)),
                           len(old.PROGRAMS),max_hits=len(old.PROGRAMS))
    assert not old_fit
    assert not RelationalGridInventor().solve(demo).source_fit


def test_new_program_invented_outside_frozen_626_and_transfers():
    demo=training()
    xs=heldout()
    result=ComposedGridInventor(
        max_geometries=12,max_relational_ms=450).solve(demo,xs)
    assert result.fixed_program_checks==len(old.PROGRAMS)
    assert not result.fixed_626_source_fit
    assert result.invented_source_fit
    assert result.invented_program is not None
    assert result.relational_invention_attempts>=1
    assert tuple(oracle(x) for x in xs) in result.candidates
    assert all(result.invented_program.apply(x)==oracle(x) for x in xs)


def test_both_live_engines_expose_source_only_composition():
    xs=heldout(8)
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        result=engine.synthesize_composed_arc_grid(
            training(),xs,max_relational_ms=450)
        assert result.invented_source_fit
        assert all(result.predict(x)==oracle(x) for x in xs)


def test_classical_exact_source_stops_new_language_invention():
    a=example(5,6,1,2,2,3)
    b=example(6,5,2,1,6,8)
    demo=((a,old.d4(a,"rotate90")),(b,old.d4(b,"rotate90")))
    xs=heldout(10)
    result=ComposedGridInventor().solve(demo,xs)
    assert result.fixed_626_source_fit
    assert not result.invented_source_fit
    assert result.relational_invention_attempts==0
    assert tuple(old.d4(x,"rotate90") for x in xs) in result.candidates


def test_missing_geometry_cannot_claim_success():
    demo=training()
    # Target input unknown to training; wrong dimensions cannot be predicted
    # merely by copying a source output.
    with pytest.raises(ValueError):
        ComposedGridInventor().solve(demo,())
    with pytest.raises(ValueError):
        ComposedGridInventor(max_geometries=0)
    with pytest.raises(ValueError):
        ComposedGridInventor(max_relational_ms=0)


def test_one_source_cannot_invent_rule():
    demo=training()
    with pytest.raises(ValueError):
        ComposedGridInventor().solve(demo[:1],(demo[1][0],))


def test_arbitrary_one_cell_exception_not_universally_identifiable():
    demo=training()
    x=heldout(1)[0]
    invented=ComposedGridInventor(max_relational_ms=450).solve(demo,(x,))
    assert invented.invented_source_fit
    y=oracle(x)
    exception=tuple(tuple(9 if (r,c)==(0,0) else v
                          for c,v in enumerate(row))
                    for r,row in enumerate(y))
    assert invented.predict(x)!=exception
