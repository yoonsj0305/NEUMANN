"""Q6: cross-encoding transport of the SAME source-invented AST."""
from random import Random
import pytest

from neumann1.parallel_object_edit_inventor import (
    ParallelObjectEditInventor,atom_true)
from neumann1.scene_graph_inventor import extract,attribute
from neumann1.typed_representation_transfer import (
    EntityRecord,apply_learned_selector)


def source(seed):
    rng=Random(seed)
    colors=rng.sample(range(1,9),4)
    g=[[0]*22 for _ in range(16)]
    r,c=2+seed%3,7+seed%4
    for y in range(r,r+3):
        for x in range(c,c+3):g[y][x]=colors[0]
    for y in (12,13):
        for x in (15,16):g[y][x]=colors[1]
    g[1][1]=colors[2]
    g[13][3]=colors[3]
    out=[row[:] for row in g]
    out[1][1]=out[13][3]=9
    return tuple(map(tuple,g)),tuple(map(tuple,out))


def test_q6_exact_ast_transfer_grid_to_unrelated_graph_and_table_encodings():
    training=[source(s) for s in (7,11,19)]
    independent=[source(s) for s in (29,41)]
    discovery=ParallelObjectEditInventor(max_source_ms=1400).invent(
        training,verification=independent)
    assert discovery.solved_source
    program=discovery.programs[0]
    assert program.ast[0]=="parallel_map_objects"
    assert len(program.clauses)>=1
    used={atom[1] for clause in program.clauses for atom in clause}
    map_graph={key:"node_"+key for key in used}
    map_table={key:"column_"+key for key in used}
    # 200 previously unseen source structures, 2 dissimilar encodings.
    # Gold for graph/table is independently recomputed from primitive
    # feature semantics, not from a copied image answer.
    for seed in range(1000,1200):
        x,y=source(seed)
        objects=extract(x,0,diagonal=False,mixed_colors=False)
        shape=len(x),len(x[0])
        gold=tuple(str(i) for i,o in enumerate(objects)
                   if any(all(atom_true(a,o,objects,shape) for a in clause)
                          for clause in program.clauses))
        graph=[EntityRecord(str(i),{
            "node_"+f:attribute(o,f,objects,shape) for f in used})
            for i,o in enumerate(objects)]
        table=[EntityRecord(str(i),{
            "column_"+f:attribute(o,f,objects,shape) for f in used})
            for i,o in enumerate(objects)]
        assert apply_learned_selector(
            program,graph,feature_map=map_graph)==gold
        assert apply_learned_selector(
            program,table,feature_map=map_table)==gold
        assert program.apply(x)==y
    # No retraining on graph or table, exact AST identity.
    assert program.ast==discovery.programs[0].ast


def test_q6_rejects_undeclared_interface_and_invalid_data():
    training=[source(s) for s in (7,11,19)]
    checks=[source(s) for s in (29,41)]
    p=ParallelObjectEditInventor(max_source_ms=1400).invent(
        training,verification=checks).programs[0]
    with pytest.raises(ValueError):
        apply_learned_selector(p,[EntityRecord("a",{"area":2})],
                               feature_map={})
    used={atom[1] for clause in p.clauses for atom in clause}
    with pytest.raises(ValueError):
        apply_learned_selector(p,[EntityRecord("a",{f:"bad" for f in used})],
                               feature_map={f:f for f in used})
    with pytest.raises(ValueError):
        apply_learned_selector(p,[EntityRecord("a",{f:1 for f in used}),
                                  EntityRecord("a",{f:2 for f in used})],
                               feature_map={f:f for f in used})
