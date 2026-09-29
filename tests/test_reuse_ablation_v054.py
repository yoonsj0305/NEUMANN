import numpy as np
import pytest
from scipy.sparse import csr_matrix

from neumann1.repeated_matrix_v053 import interleaved_replicas
from neumann1.reuse_ablation_v054 import run_trial, summarize


def test_split_and_reuse_are_both_exact_and_pay_correct_factors():
    base = csr_matrix(np.array([[6., -1., 0.], [-1., 5., -2.], [0., -2., 7.]]))
    matrix, rhs, truth = interleaved_replicas(base, 4)
    split = run_trial(matrix, rhs, truth, "SPLIT_NO_REUSE")
    reuse = run_trial(matrix, rhs, truth, "EXACT_REUSE")
    assert split.valid and reuse.valid
    assert split.factorizations == 4
    assert reuse.factorizations == 1
    assert split.total_factor_nnz == 4 * reuse.total_factor_nnz


def test_protocol_rejects_missing_cases():
    with pytest.raises(ValueError):
        summarize([])
