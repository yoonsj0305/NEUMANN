"""Q3/Q4 production hot path: classical-first, source-original proof then invention."""
import pytest
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.object_gap_router import ObjectGapRouter
from neumann1 import arc2_meta_grid_reasoner as old


def specimen(seed):
    colors=(1+(seed*3)%9,1+(seed*5+1)%9,1+(seed*7+3)%9)
    # Keep colors distinct for this intentional source-domain design.
    colors=tuple(dict.fromkeys(colors))
    if len(colors)<3:
        colors=(2,5,7)
    g=[[0]*14 for _ in range(12)]
    for color,(r,c,h,w) in zip(colors,((0,0,1,1),(3,4,2,2),(8,9,3,3))):
        for y in range(r,r+h):
            for x in range(c,c+w):
                g[y][x]=color
    return (tuple(tuple(row) for row in g),
            ((colors[1],colors[1]),(colors[1],colors[1])))


def test_live_engines_never_invent_if_classical_matches_source():
    xs=[specimen(n)[0] for n in (1,3,5,7)]
    f=lambda x:old.d4(x,"rotate90")
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        r=engine.invent_arc_object_only_on_classical_gap(
            [(x,f(x)) for x in xs[:2]],
            [(xs[2],f(xs[2]))],
            (xs[3],))
        assert r.origin=="SOURCE_VERIFIED_PRIOR"
        assert r.object_inventor_invocations==0
        assert (f(xs[3]),) in r.candidates


def test_live_engines_invent_object_program_at_actual_source_gap():
    src=[specimen(n) for n in (11,23,41)]
    source_checks=[specimen(n) for n in (71,89)]
    targets=[specimen(n) for n in (130,131,132,133)]
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        r=engine.invent_arc_object_only_on_classical_gap(
            src,source_checks,[x for x,y in targets])
        assert r.origin=="SOURCE_VERIFIED_NEW_OBJECT_RULE"
        assert r.object_inventor_invocations==1
        assert tuple(y for x,y in targets) in r.candidates
        assert r.invented_programs


def test_original_verifier_absence_is_hard_failure():
    src=[specimen(n) for n in (11,23)]
    with pytest.raises(ValueError):
        ObjectGapRouter().solve(src,(),(specimen(41)[0],))


def test_no_hidden_target_gold_required():
    src=[specimen(n) for n in (11,23,41)]
    verifier=[specimen(71)]
    result=ObjectGapRouter().solve(
        src,verifier,[specimen(190)[0]])
    assert result.solved_source
    assert result.origin in (
        "SOURCE_VERIFIED_PRIOR","SOURCE_VERIFIED_NEW_OBJECT_RULE")
    assert len(result.candidates[0])==1


def test_live_routers_invent_new_multiobject_causal_grammar_at_real_gap():
    """No classical or one-object source rule can move a source entity
    based on ANOTHER entity's dynamically changing anchor position."""
    from random import Random
    def relation_input(seed):
        rng=Random(seed)
        h,w=16,20
        colors=rng.sample(range(1,10),3)
        ar=rng.choice((3,5,7,8))
        acol=rng.choice((5,7,9))
        ah=rng.choice((2,3))
        aw=rng.choice((3,4))
        x=[[0]*w for _ in range(h)]
        for rr in range(ar,ar+ah):
            for cc in range(acol,acol+aw):
                x[rr][cc]=colors[0]
        for rr in (12,13):
            for cc in (16,17):
                x[rr][cc]=colors[2]
        mover_r,mover_c=rng.choice((0,1,14)),rng.choice((1,3))
        x[mover_r][mover_c]=colors[1]
        y=[row[:] for row in x]
        y[mover_r][mover_c]=0
        y[ar][acol+aw]=colors[1]
        return tuple(map(tuple,x)),tuple(map(tuple,y))
    train=[relation_input(i) for i in (7,19,23)]
    source_verify=[relation_input(i) for i in (41,59)]
    withheld=[relation_input(i) for i in range(100,109)]
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        r=engine.invent_arc_object_only_on_classical_gap(
            train,source_verify,[x for x,y in withheld])
        assert r.origin=="SOURCE_VERIFIED_NEW_CAUSAL_RELATION"
        assert r.object_inventor_invocations==2
        assert tuple(y for x,y in withheld) in r.candidates
        assert r.invented_programs[0].ast[0]=="relational_action"


def test_new_program_grammar_is_reused_on_different_task_without_discovery():
    """Same learned causal AST transfers across independent source families.

    The second task has new colors, placements and source verification data.
    Only the PROGRAM is remembered. No answer table or hidden target gold.
    """
    from random import Random
    def pair(seed):
        rng=Random(seed)
        g=[[0]*20 for _ in range(16)]
        color_a,color_b,color_d=rng.sample(range(1,10),3)
        row,col=rng.choice((3,5,7,8)),rng.choice((5,7,9))
        ah,aw=rng.choice((2,3)),rng.choice((3,4))
        for y in range(row,row+ah):
            for x in range(col,col+aw):g[y][x]=color_a
        for y in (12,13):
            for x in (16,17):g[y][x]=color_d
        mr,mc=rng.choice((0,1,14)),rng.choice((1,3))
        g[mr][mc]=color_b
        out=[v[:] for v in g]
        out[mr][mc]=0
        out[row][col+aw]=color_b
        return tuple(map(tuple,g)),tuple(map(tuple,out))
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        first=engine.invent_arc_object_only_on_classical_gap(
            [pair(s) for s in (7,19,23)],
            [pair(s) for s in (41,59)],
            [pair(151)[0]])
        assert first.origin=="SOURCE_VERIFIED_NEW_CAUSAL_RELATION"
        assert len(engine._q3_relation_memory)>=1
        later=engine.invent_arc_object_only_on_classical_gap(
            [pair(s) for s in (213,217,241)],
            [pair(s) for s in (251,269)],
            [pair(s)[0] for s in (301,307,311,317)])
        assert later.origin=="SOURCE_VERIFIED_REUSED_CAUSAL_RELATION"
        assert later.object_inventor_invocations==0
        assert tuple(pair(s)[1] for s in (301,307,311,317)) in later.candidates


def test_source_counterexample_revokes_reuse_instead_of_hiding_failure():
    from neumann1.relational_action_inventor import RelationalAction
    bogus=RelationalAction(
        ("area","min"),("area","max"),"move","source",
        ("anchor_low",0),("anchor_next",0))
    src=[specimen(n) for n in (11,23,41)]
    checks=[specimen(71)]
    result=ObjectGapRouter(known_causal_rules=[bogus]).solve(
        src,checks,[specimen(89)[0]])
    assert result.origin!="SOURCE_VERIFIED_REUSED_CAUSAL_RELATION"


def _bulk_q3_example(seed):
    from random import Random
    rng=Random(seed)
    colors=rng.sample(range(1,9),4)
    g=[[0]*22 for _ in range(16)]
    ar,ac=2+seed%3,7+seed%4
    for r in range(ar,ar+3):
        for c in range(ac,ac+3):
            g[r][c]=colors[0]
    for r in (12,13):
        for c in (15,16):
            g[r][c]=colors[1]
    g[1][1]=colors[2]
    g[13][3]=colors[3]
    y=[list(row) for row in g]
    y[1][1]=9
    y[13][3]=9
    return tuple(map(tuple,g)),tuple(map(tuple,y))


def test_both_live_engines_autonomously_invent_and_reuse_bulk_object_grammar():
    first=[_bulk_q3_example(s) for s in (7,11,19)]
    validation=[_bulk_q3_example(s) for s in (29,41)]
    withheld=[_bulk_q3_example(s) for s in (101,103,107,109)]
    second=[_bulk_q3_example(s) for s in (203,211,223)]
    second_verify=[_bulk_q3_example(s) for s in (227,229)]
    second_withheld=[_bulk_q3_example(s) for s in (251,257,263)]
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        invented=engine.invent_arc_object_only_on_classical_gap(
            first,validation,[x for x,y in withheld])
        assert invented.origin=="SOURCE_VERIFIED_NEW_BULK_RULE"
        assert invented.object_inventor_invocations==3
        assert tuple(y for x,y in withheld) in invented.candidates
        assert invented.invented_programs[0].ast[0]=="parallel_map_objects"
        assert engine._q3_bulk_memory
        reused=engine.invent_arc_object_only_on_classical_gap(
            second,second_verify,[x for x,y in second_withheld])
        assert reused.origin=="SOURCE_VERIFIED_REUSED_BULK_RULE"
        assert reused.object_inventor_invocations==0
        assert tuple(y for x,y in second_withheld) in reused.candidates
