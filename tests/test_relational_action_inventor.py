"""Q3 genuine relational-action AST invention: source-only multi-object rules."""
from random import Random
import pytest
from neumann1.relational_action_inventor import (
    RelationalActionInventor,RelationalAction)
from neumann1.scene_graph_inventor import ObjectGrammarInventor


def construct(seed,*,operation="move",paint="source",other_axis="right"):
    rng=Random(seed)
    h,w=16,20
    g=[[0]*w for _ in range(h)]
    bg=0
    ac,mc,dc=rng.sample(range(1,10),3)
    ar=rng.choice((3,5,7,8))
    acol=rng.choice((5,7,9))
    ah=rng.choice((2,3))
    aw=rng.choice((3,4))
    for r in range(ar,ar+ah):
        for c in range(acol,acol+aw):
            g[r][c]=ac
    # Nontrivial distracting component with area 4.
    for r in (12,13):
        for c in (16,17):
            g[r][c]=dc
    mover_r,mover_c=rng.choice((0,1,14)),rng.choice((1,3))
    g[mover_r][mover_c]=mc
    # Each source pair requires a changing reference object position/size.
    if other_axis=="right":
        dest_r=ar
        dest_c=acol+aw
    elif other_axis=="below":
        dest_r=ar+ah
        dest_c=acol
    else:
        raise ValueError(other_axis)
    output=[row[:] for row in g]
    if operation=="move":output[mover_r][mover_c]=0
    output[dest_r][dest_c]=mc if paint=="source" else ac
    return (tuple(tuple(row) for row in g),
            tuple(tuple(row) for row in output))


def solve_family(operation="move",paint="source",other_axis="right"):
    src=[construct(i,operation=operation,paint=paint,other_axis=other_axis)
         for i in (7,19,23)]
    checks=[construct(i,operation=operation,paint=paint,other_axis=other_axis)
            for i in (41,59)]
    held=[construct(i,operation=operation,paint=paint,other_axis=other_axis)
          for i in range(100,150)]
    solver=RelationalActionInventor(max_source_ms=1500)
    model=solver.invent(src,verification=checks)
    return model,src,checks,held


def test_new_action_move_to_reference_right_synthesized():
    model,src,checks,held=solve_family()
    assert model.source_fit
    assert model.rules[0].ast[0]=="relational_action"
    assert model.rules[0].ast[2][0]=="learned_entity_selector"
    for x,y in held:
        assert y in tuple(rule.apply(x) for rule in model.rules)


def test_new_action_copy_to_reference_below_synthesized():
    model,src,checks,held=solve_family(operation="copy",other_axis="below")
    assert model.source_fit
    for x,y in held:
        assert y in tuple(rule.apply(x) for rule in model.rules)


def test_recolor_moving_object_from_reference_anchor_synthesized():
    model,src,checks,held=solve_family(paint="anchor")
    assert model.source_fit
    for x,y in held:
        assert y in tuple(rule.apply(x) for rule in model.rules)


def test_old_one_object_grammar_cannot_express_relational_translation():
    src=[construct(i) for i in (7,19,23)]
    checks=[construct(i) for i in (41,59)]
    old=ObjectGrammarInventor(max_source_ms=1200).invent(
        src,verification=checks)
    assert not old.source_fit
    new=RelationalActionInventor(max_source_ms=1500).invent(
        src,verification=checks)
    assert new.source_fit


def test_missing_independent_source_verifier_fails_closed():
    src=[construct(i) for i in (7,19)]
    with pytest.raises(ValueError):
        RelationalActionInventor().invent(src,verification=[])
    with pytest.raises(ValueError):
        RelationalActionInventor().invent(src[:1],verification=src)


def test_wrong_semantics_on_check_rejects_invented_action():
    src=[construct(i) for i in (7,19,23)]
    bad_x,bad_y=construct(41)
    altered=[list(row) for row in bad_y]
    altered[15][19]=9
    checks=[(bad_x,tuple(tuple(row) for row in altered))]
    result=RelationalActionInventor(max_source_ms=1500).invent(
        src,verification=checks)
    assert not result.source_fit


def test_source_fits_do_not_prove_arbitrary_hidden_exception():
    model,src,checks,held=solve_family()
    assert model.source_fit
    x,y=held[0]
    modified=[list(row) for row in y]
    modified[15][19]=9
    fake_output=tuple(tuple(row) for row in modified)
    assert fake_output not in tuple(r.apply(x) for r in model.rules)
