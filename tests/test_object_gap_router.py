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
