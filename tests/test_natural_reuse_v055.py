import numpy as np
import pytest
from scipy.sparse import block_diag, csr_matrix

from neumann1.natural_reuse_v055 import detect_repeats, run_trial, summarize


def test_exact_reuse_and_safe_abstention_on_original_equation():
    a = csr_matrix(np.array([[4., -1.], [-1., 5.]]))
    b = csr_matrix(np.array([[7., -2.], [-2., 9.]]))
    for parts, expected_distinct, expected_factors in (
        (block_diag((a, a), format="csr"), 1, 1),
        (block_diag((a, b), format="csr"), 2, 1),
        (a, 1, 1),
    ):
        truth = np.sin(np.arange(parts.shape[0]) + 1.)
        trial = run_trial(parts, parts @ truth, truth, "GATED_REUSE")
        assert trial.valid and trial.distinct_blocks == expected_distinct
        assert trial.factorizations == expected_factors
        assert detect_repeats(parts)[1] == expected_distinct


def test_invalid_policy_and_missing_corpus_fail_closed():
    a = csr_matrix(np.eye(2))
    with pytest.raises(ValueError):
        run_trial(a, np.ones(2), np.ones(2), "ORACLE")
    with pytest.raises(ValueError):
        summarize([])
