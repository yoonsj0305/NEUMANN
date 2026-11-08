"""Q3/Q4/Q6 route only the SOURCE-selected family method and conserve work."""
from neumann1 import NeumannEngine,RegistryEngine
from neumann1.source_learned_grid_router import SourceLearnedGridRouter
from neumann1.relational_grid_inventor import grid

def test_classical_only_calls_no_relational_inventor():
    # The exact original rotation should be found by frozen old grammar.
    demo=[([[1,2],[3,4]],[[3,1],[4,2]]),
          ([[0,5],[8,7]],[[8,0],[7,5]])]
    r=NeumannEngine(None,[],None).synthesize_arc_grid_cost_aware(
        "orientation",demo,[[[2,4],[6,8]]],
        source_policy={"orientation":"classical_only"})
    assert r.strategy=="classical_only"
    assert r.classical_program_checks>0
    assert not r.relational_source_fit
    assert any(c.outputs==(grid([[6,2],[8,4]]),) for c in r.candidates)

def test_relational_only_skips_entire_classical_candidate_language():
    demo=[([[0,8,0],[2,8,2]],[[0,5,0],[2,5,2]]),
          ([[8,8,0],[3,0,3]],[[5,5,0],[3,0,3]])]
    r=RegistryEngine(None,None).synthesize_arc_grid_cost_aware(
        "recolor",demo,[[[7,8],[0,8]]],
        source_policy={"recolor":"relational_only"})
    assert r.strategy=="relational_only"
    assert r.classical_program_checks==0
    assert r.relational_source_fit
    assert len(r.candidates)<=2
    assert any(c.outputs==(grid([[7,5],[0,5]]),) for c in r.candidates)

def test_nonlisted_family_fails_closed_no_unfounded_guess():
    learned=SourceLearnedGridRouter({"x":"hybrid"})
    try:
        learned.solve("unseen",[],[])
        assert False
    except ValueError:
        pass

def test_source_policy_is_typed_and_two_attempt_cap():
    for bad in ({},{"x":"unknown"},{"": "classical_only"}):
        try:
            SourceLearnedGridRouter(bad)
            assert False
        except ValueError:
            pass
    try:
        SourceLearnedGridRouter({"x":"classical_only"},max_attempts=3)
        assert False
    except ValueError:
        pass

def test_hybrid_proposal_uses_prior_and_new_semantics():
    demo=[([[1,2],[3,4]],[[3,1],[4,2]]),
          ([[0,5],[8,7]],[[8,0],[7,5]])]
    r=SourceLearnedGridRouter({"a":"hybrid"}).solve(
        "a",demo,[[[2,4],[6,8]]])
    assert r.strategy=="hybrid"
    assert len(r.candidates)<=2
    assert r.classical_program_checks>0
    assert any(c.outputs==(grid([[6,2],[8,4]]),) for c in r.candidates)
