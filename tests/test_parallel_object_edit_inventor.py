"""Q3: synthesize NEW map-over-multiple-objects DSL from source edits."""
from random import Random
import pytest

from neumann1.parallel_object_edit_inventor import ParallelObjectEditInventor
from neumann1.scene_graph_inventor import ObjectGrammarInventor


def bulk_case(seed,*,paint="constant"):
    rng=Random(seed)
    colors=rng.sample(range(1,9),4)
    g=[[0]*22 for _ in range(16)]
    large_r,large_c=2+seed%3,7+seed%4
    for r in range(large_r,large_r+3):
        for c in range(large_c,large_c+3):
            g[r][c]=colors[0]
    for r in (12,13):
        for c in (15,16):
            g[r][c]=colors[1]
    g[1][1]=colors[2]
    g[13][3]=colors[3]
    original=tuple(map(tuple,g))
    changed=[row[:] for row in g]
    new_color=9 if paint=="constant" else colors[0]
    changed[1][1]=changed[13][3]=new_color
    return original,tuple(map(tuple,changed))


def learn(paint="constant"):
    train=[bulk_case(s,paint=paint) for s in (7,11,19)]
    verify=[bulk_case(s,paint=paint) for s in (29,41)]
    model=ParallelObjectEditInventor(max_source_ms=1400).invent(
        train,verification=verify)
    return model,train,verify


def test_invents_parallel_recolor_of_multiple_objects():
    model,train,verify=learn()
    assert model.solved_source
    assert model.positive_objects==6
    assert model.negative_objects==6
    assert model.programs[0].ast[0]=="parallel_map_objects"
    held=[bulk_case(s) for s in range(100,150)]
    for x,y in held:
        assert y in tuple(p.apply(x) for p in model.programs)


def test_invents_dynamic_color_role_from_other_object():
    model,train,verify=learn("from_largest")
    assert model.solved_source
    assert all(p.output_color_expr[0]!="constant" for p in model.programs)
    for seed in range(100,150):
        x,y=bulk_case(seed,paint="from_largest")
        assert y in tuple(p.apply(x) for p in model.programs)


def test_single_object_grammar_cannot_recolor_two_independently_colored_objects():
    model,train,verify=learn()
    old=ObjectGrammarInventor(max_source_ms=1300).invent(
        train,verification=verify)
    assert not old.source_fit
    assert model.solved_source


def test_verification_counterexample_causes_safe_abstention():
    train=[bulk_case(s) for s in (7,11,19)]
    x,y=bulk_case(29)
    altered=[list(row) for row in y]
    altered[14][21]=9   # modifies background, invalid object edit
    checks=[(x,tuple(map(tuple,altered)))]
    result=ParallelObjectEditInventor().invent(
        train,verification=checks)
    assert not result.solved_source


def test_nonuniform_component_output_is_rejected():
    train=[bulk_case(s) for s in (7,11,19)]
    x,y=train[0]
    bad=[list(row) for row in y]
    bad[3][10]=9  # change background or part of unrelated component
    train[0]=(x,tuple(map(tuple,bad)))
    r=ParallelObjectEditInventor().invent(
        train,verification=[bulk_case(29)])
    assert not r.solved_source


def test_training_and_independent_source_inputs_must_be_disjoint():
    train=[bulk_case(s) for s in (7,11)]
    with pytest.raises(ValueError):
        ParallelObjectEditInventor().invent(train,verification=train)
    with pytest.raises(ValueError):
        ParallelObjectEditInventor().invent(train,verification=[])


def test_zero_changes_do_not_promote_new_execution_semantics():
    originals=[bulk_case(i)[0] for i in (7,11,19,29)]
    train=[(x,x) for x in originals[:3]]
    r=ParallelObjectEditInventor().invent(
        train,verification=[(originals[3],originals[3])])
    assert not r.solved_source
