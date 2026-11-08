"""New NEUMANN meta-language composition and two-attempt safe hybrid."""
from neumann1 import NeumannEngine,RegistryEngine
from neumann1.relational_grid_inventor import RelationalGridInventor,grid
from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor


def test_invents_two_spatial_rules_with_new_parallel_composition_operator():
    demo=[
       ([[1,2],[0,0]],[[5,6],[0,0]]),
       ([[0,1],[2,0]],[[0,5],[6,0]])]
    engine=RelationalGridInventor()
    solved=engine.solve(demo)
    assert solved.source_fit
    assert solved.method["kind"]=="parallel_relational_rewrites"
    assert len(solved.method["parts"])==2
    assert engine.apply(solved,[[2,0],[1,2]])==grid([[6,0],[5,6]])


def test_two_attempt_union_preserves_original_classical_macro():
    # In this task the old language can represent identity with a fixed
    # recoloring. The hybrid retains that candidate even when the new
    # representation also discovers a rewrite.
    demo=[
       ([[1,2],[0,0]],[[5,6],[0,0]]),
       ([[0,1],[2,0]],[[0,5],[6,0]])]
    result=HybridArcGridInventor().solve(demo,[[[2,0],[1,2]]])
    assert len(result.candidates)<=2
    assert result.new_source_fit and result.old_source_fit
    assert any(c.outputs==(grid([[6,0],[5,6]]),) for c in result.candidates)
    assert result.old_candidate_checks>0


def test_end_to_end_real_neumann_engine_returns_bounded_candidate_set():
    engine=NeumannEngine(None,[],None)
    demo=[
       ([[0,8,0],[2,8,2]],[[0,5,0],[2,5,2]]),
       ([[8,8,0],[3,0,3]],[[5,5,0],[3,0,3]])]
    r=engine.synthesize_arc_grid(demo,[[[7,8],[0,8]]])
    assert len(r.candidates)<=2
    assert r.new_source_fit
    assert any(candidate.outputs==(grid([[7,5],[0,5]]),)
               for candidate in r.candidates)


def test_real_registry_engine_degraded_classical_mode():
    engine=RegistryEngine(None,None)
    # Rotation from the previous frozen ARC grammar without recolor.
    demo=[
       ([[1,2],[3,4]],[[3,1],[4,2]]),
       ([[0,5],[8,7]],[[8,0],[7,5]])]
    r=engine.synthesize_arc_grid(demo,[[[2,4],[6,8]]])
    assert r.old_source_fit
    assert len(r.candidates)<=2
    assert any(c.outputs==(grid([[6,2],[8,4]]),) for c in r.candidates)
