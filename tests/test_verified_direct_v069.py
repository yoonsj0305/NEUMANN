from fractions import Fraction
from unittest.mock import patch

import numpy as np

import benchmark_v069
from neumann1.structural_compression import ExactLinearSystem
from neumann1.verified_direct import solve_verified_numeric_or_exact


def _system(A, b, truth):
    n = len(b)
    return ExactLinearSystem(
        variables=tuple(f"v{i}" for i in range(n)),
        A=tuple(tuple(row) for row in A),
        b=tuple(b),
        ground_truth=tuple(truth),
    )


def test_verified_integer_proposal_does_not_consult_ground_truth():
    case = _system(((2, 1), (1, 2)), (4, 5), (999, 999))
    result = solve_verified_numeric_or_exact(case)
    assert result.proposal_status == "exact_integer_verified"
    assert not result.used_exact_fallback
    assert result.answer == {"v0": Fraction(1), "v1": Fraction(2)}


def test_nonintegral_answer_falls_back_to_exact():
    case = _system(((2,),), (1,), (0,))
    result = solve_verified_numeric_or_exact(case)
    assert result.used_exact_fallback
    assert result.proposal_status == "nonintegral_proposal"
    assert result.answer == {"v0": Fraction(1, 2)}


def test_invalid_numeric_candidate_is_rejected_exactly():
    case = _system(((2,),), (4,), (0,))
    with patch("neumann1.verified_direct.np.linalg.solve",
               return_value=np.asarray([3.0])):
        result = solve_verified_numeric_or_exact(case)
    assert result.used_exact_fallback
    assert result.proposal_status == "exact_equation_rejected"
    assert result.answer == {"v0": Fraction(2)}


def test_nonfinite_candidate_uses_exact_fallback():
    case = _system(((1,),), (7,), (0,))
    with patch("neumann1.verified_direct.np.linalg.solve",
               return_value=np.asarray([float("nan")])):
        result = solve_verified_numeric_or_exact(case)
    assert result.used_exact_fallback
    assert result.answer == {"v0": Fraction(7)}


def test_new_holdout_disjoint_from_v068():
    with patch.object(benchmark_v069, "CASES_PER_CELL", 1):
        cases = benchmark_v069._cases()
    assert len(cases) == len(benchmark_v069.learned_scale_grid())
    assert {case.signature for case in cases}.isdisjoint(
        case.signature for case in benchmark_v069.benchmark_v068._cases()
    )
