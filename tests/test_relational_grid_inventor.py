"""Executable example-based relational operator induction in NEUMANN core."""
from neumann1.relational_grid_inventor import RelationalGridInventor,grid,predict
from neumann1 import NeumannEngine,RegistryEngine


def test_self_invents_color_predicate_not_in_old_grid_macro_language():
    demo=[
     ([[0,8,0],[2,8,2]],[[0,5,0],[2,5,2]]),
     ([[8,8,0],[3,0,3]],[[5,5,0],[3,0,3]]),
    ]
    engine=NeumannEngine(None,[],None)
    held=[[7,8],[0,8]]
    got=engine.synthesize_relational_grid(demo,held)
    assert got["source_fit"] and got["method"]
    assert got["method"]["kind"]=="cell_relational_rewrite"
    assert got["prediction"]==grid([[7,5],[0,5]])
    assert got["method"]["program"]["guard"]


def test_infer_color_role_without_constant_from_two_source_examples():
    miner=RelationalGridInventor()
    src=miner.solve([
      ([[1,1,2],[1,3,3]],[[1]]),
      ([[5,5,5],[3,4,4]],[[5]])
    ])
    assert src.source_fit
    assert src.method["kind"]=="select_color_role"
    assert miner.apply(src,[[7,7,7],[2,2,3]])==grid([[7]])


def test_works_through_real_registry_dispatcher():
    reg=RegistryEngine(None,None)
    demo=[
      ([[8,1],[3,8]],[[5,1],[3,5]]),
      ([[2,8,8],[8,9,7]],[[2,5,5],[5,9,7]]),
    ]
    outcome=reg.synthesize_relational_grid(demo,[[8,6],[7,8]])
    assert outcome["source_fit"]
    assert outcome["prediction"]==grid([[5,6],[7,5]])


def test_absent_relation_fails_closed():
    miner=RelationalGridInventor()
    # Contradictory source labels on exact same input.
    out=miner.solve([
      ([[2,2],[2,2]],[[3,3],[3,3]]),
      ([[2,2],[2,2]],[[4,4],[4,4]])
    ])
    assert not out.source_fit
    assert miner.apply(out,[[2,2]]) is None
