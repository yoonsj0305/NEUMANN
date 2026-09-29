import numpy as np
import pytest
from scipy.sparse import csr_matrix

from neumann1.numeric_order_v052 import POLICIES, original_residual, run_trial, summarize


def test_original_equation_and_unpermuted_solution():
    matrix = csr_matrix(np.array([[8., -1., 0., 0.], [-1., 7., -2., 0.],
                                  [0., -2., 9., -1.], [0., 0., -1., 6.]]))
    truth = np.array([0.7, -1.2, 2., -0.3])
    rhs = matrix @ truth
    for policy in POLICIES:
        result = run_trial(matrix, rhs, truth, policy)
        assert result.valid
        assert result.factor_nnz >= 8
        assert result.backward_error < 1e-12
    wrong = truth[::-1]
    assert original_residual(matrix, wrong, rhs, truth)[0] > 1e-3


def test_unknown_policy_rejected():
    matrix = csr_matrix(np.eye(2))
    with pytest.raises(ValueError):
        run_trial(matrix, np.ones(2), np.ones(2), "oracle")


def test_summary_requires_pinned_cases():
    with pytest.raises(ValueError):
        summarize([])
