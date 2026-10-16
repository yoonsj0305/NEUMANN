import random
import pytest

# Specialized research proof dependency is not required by the base NEUMANN runtime.
# The focused CORE-34 workflow explicitly installs SymPy and executes these tests.
pytest.importorskip("sympy", reason="optional CORE-34 symbolic research dependency")
from experiment import fold, observes, proof, direct_solve, proof_explicit, generate, PROBES, candidate_rhs


def test_true_theorem_universal_and_finite():
    p=(1,1,0,0)
    assert proof(p)
    assert proof_explicit(p)==(True,True)
    rng=random.Random(20261016)
    for _ in range(120):
        z=rng.randrange(-40,41)
        a=tuple(rng.randrange(-20,21) for _ in range(rng.randrange(9)))
        b=tuple(rng.randrange(-20,21) for _ in range(rng.randrange(9)))
        assert fold(z,a+b)==candidate_rhs(p,z,a,b)


def test_wrong_candidates_rejected():
    for p in [(1,0,0,0),(0,1,1,0),(1,1,0,1),(1,1,1,0)]:
        assert not proof(p)


def test_source_mutation_fails_closed_and_can_be_repaired():
    assert not proof((1,1,0,0),offset=1)
    assert proof((1,1,0,-1),offset=1)
    assert direct_solve(offset=1)==(1,1,0,-1)


def test_matched_space_and_strong_classical():
    matches=[p for p in generate() if observes(p)]
    assert matches==[(1,1,0,0)]
    assert direct_solve()==matches[0]
    assert all(proof(p) for p in matches)


def test_typed_probe_count():
    assert len(PROBES)==4
