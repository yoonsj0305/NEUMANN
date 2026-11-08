"""Q3: source-programmed object selection rather than fixed grid operations."""
from random import Random

from neumann1.scene_graph_inventor import ObjectGrammarInventor
from neumann1 import arc2_meta_grid_reasoner as old
from neumann1 import NeumannEngine, RegistryEngine


def sample(seed,task="crop"):
    rng=Random(seed)
    g=[[0]*14 for _ in range(12)]
    colors=rng.sample(range(1,10),3)
    positions=[(0,0,1,1),(3,4,2,2),(8,9,3,3)]
    for color,(r,c,h,w) in zip(colors,positions):
        for y in range(r,r+h):
            for x in range(c,c+w):
                g[y][x]=color
    x=tuple(tuple(row) for row in g)
    if task=="crop":
        y=((colors[1],colors[1]),(colors[1],colors[1]))
    elif task=="erase":
        out=[list(row) for row in x]
        for row in (3,4):
            for col in (4,5):
                out[row][col]=0
        y=tuple(tuple(row) for row in out)
    elif task=="keep":
        out=[[0]*14 for _ in range(12)]
        for row in (3,4):
            for col in (4,5):
                out[row][col]=colors[1]
        y=tuple(tuple(row) for row in out)
    else:raise ValueError(task)
    return x,y


def demonstrate(task):
    return [sample(x,task) for x in (11,23,41)], [
        sample(x,task) for x in (71,89)]


def test_middle_area_object_induction_outside_frozen_626():
    train,verify=demonstrate("crop")
    old_winners,_=old.fit_task(train,range(len(old.PROGRAMS)),
                              len(old.PROGRAMS),max_hits=len(old.PROGRAMS))
    assert not old_winners
    r=ObjectGrammarInventor().invent(train,verification=verify)
    assert r.source_fit
    assert r.programs
    for seed in range(110,180):
        x,y=sample(seed,"crop")
        assert y in r.apply(x)


def test_erase_and_keep_source_infer_object_programs():
    for task in ("erase","keep"):
        train,verify=demonstrate(task)
        r=ObjectGrammarInventor().invent(train,verification=verify)
        assert r.source_fit,task
        for seed in range(110,125):
            x,y=sample(seed,task)
            assert y in r.apply(x),task


def test_object_selector_distinguishes_color_from_area():
    train,verify=demonstrate("crop")
    r=ObjectGrammarInventor().invent(train,verification=verify)
    assert r.programs
    # Color ordering varies across independent source examples.
    assert any(p.feature in ("area","height","width")
               for p in r.programs)


def test_finite_candidate_budget_and_no_empty_source():
    train,verify=demonstrate("crop")
    r=ObjectGrammarInventor(max_candidates=1).invent(
        train,verification=verify)
    assert r.source_checks<=2
    try:
        ObjectGrammarInventor().invent(train[:1],verification=verify)
        assert False,"must reject fewer than 2 source demonstrations"
    except ValueError: pass
    try:
        ObjectGrammarInventor().invent(train,verification=())
        assert False,"must reject absent independent source verifier"
    except ValueError: pass


def test_new_language_does_not_infer_source_unseen_arbitrary_exception():
    train,verify=demonstrate("crop")
    r=ObjectGrammarInventor().invent(train,verification=verify)
    x,y=sample(901,"crop")
    wrong=((9,9),(9,9))
    assert y in r.apply(x)
    if y==wrong:
        wrong=((8,8),(8,8))
    assert wrong not in r.apply(x)
