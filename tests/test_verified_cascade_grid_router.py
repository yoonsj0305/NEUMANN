"""Zero-investment verified cascade and output-identical classical acceleration."""
import random
import pytest
from neumann1 import arc2_meta_grid_reasoner as old
from neumann1.classical_grid_fast import fit_all, classical_candidates
from neumann1.relational_grid_inventor import grid
from neumann1.source_learned_grid_router import _classical
from neumann1.verified_cascade_grid_router import VerifiedCascadeGridRouter

ROTATE = [([[1, 2], [3, 4]], [[3, 1], [4, 2]]),
          ([[0, 5], [8, 7]], [[8, 0], [7, 5]])]
RECOLOR_REL = [([[0, 8, 0], [2, 8, 2]], [[0, 5, 0], [2, 5, 2]]),
               ([[8, 8, 0], [3, 0, 3]], [[5, 5, 0], [3, 0, 3]])]


def _g(demo):
    return [(grid(a), grid(b)) for a, b in demo]


def _full(demo):
    return old.fit_task(demo, range(len(old.PROGRAMS)), len(old.PROGRAMS),
                        max_hits=len(old.PROGRAMS))


def test_fast_fit_identical_on_handmade_cases():
    cases = [ROTATE, RECOLOR_REL,
             [([[1, 0], [0, 0]], [[1, 1], [1, 1]])],                # shape kept
             [([[1, 2]], [[1, 2], [1, 2]])],                        # shape grows
             [([[3, 0, 0], [0, 0, 0]], [[3]])],                     # crop
             [([[1, 2], [3, 4]], [[5, 6], [7, 8]])]]                # recolor only
    for demo in cases:
        assert fit_all(_g(demo)) == _full(_g(demo))


def test_fast_fit_identical_on_random_grids():
    rnd = random.Random(20261111)
    for _ in range(60):
        h, w = rnd.randint(1, 5), rnd.randint(1, 5)
        demo = []
        for _ in range(rnd.randint(1, 3)):
            x = [[rnd.choice((0, 0, 1, 2, 3)) for _ in range(w)] for _ in range(h)]
            op = rnd.choice(old.PROGRAMS)
            y = old.predict(grid(x), op)
            if y is None or rnd.random() < 0.3:
                y = grid([[rnd.randint(0, 3) for _ in range(w)] for _ in range(h)])
            demo.append((grid(x), y))
        assert fit_all(demo) == _full(demo)


def test_fast_candidates_identical_to_router_classical():
    for demo in (ROTATE, RECOLOR_REL):
        d = _g(demo)
        inputs = [grid([[2, 4], [6, 8]])]
        assert classical_candidates(d, inputs) == _classical(d, inputs)


def test_classical_first_stops_without_relational():
    r = VerifiedCascadeGridRouter().solve(ROTATE, [[[2, 4], [6, 8]]])
    assert r.engines_run == ("classical",)
    assert r.stopped_by == "classical"
    assert not r.relational_source_fit
    assert any(c.outputs == (grid([[6, 2], [8, 4]]),) for c in r.candidates)
    assert len(r.candidates) <= 2


def test_escalates_only_when_train_inconsistent():
    # Border cells recoloured: not expressible in the 626-program grammar.
    demo = [([[1, 1, 1], [1, 1, 1], [1, 1, 1]],
             [[2, 2, 2], [2, 1, 2], [2, 2, 2]]),
            ([[1] * 4] * 4,
             [[2, 2, 2, 2], [2, 1, 1, 2], [2, 1, 1, 2], [2, 2, 2, 2]])]
    assert fit_all(_g(demo))[0] == []
    r = VerifiedCascadeGridRouter().solve(demo, [[[1] * 5] * 3])
    assert r.engines_run == ("classical", "relational")
    assert r.stopped_by == "relational"
    assert r.relational_source_fit
    assert r.candidates[0].outputs == (grid(
        [[2, 2, 2, 2, 2], [2, 1, 1, 1, 2], [2, 2, 2, 2, 2]]),)


def test_order_and_attempt_contract():
    for bad in ((), ("classical", "classical"), ("oracle",)):
        with pytest.raises(ValueError):
            VerifiedCascadeGridRouter(bad)
    with pytest.raises(ValueError):
        VerifiedCascadeGridRouter(max_attempts=3)
    with pytest.raises(ValueError):
        VerifiedCascadeGridRouter().solve([], [[[1]]])


def test_no_family_metadata_required_open_set():
    # The source-learned family router refuses unseen families; the cascade
    # has no family argument at all and still answers.
    r = VerifiedCascadeGridRouter(("relational", "classical")).solve(
        RECOLOR_REL, [[[7, 8], [0, 8]]])
    assert r.engines_run[0] == "relational"
    assert r.candidates
