import numpy as np
import pytest
from scipy.sparse import csr_matrix

from neumann1.repeated_matrix_v053 import interleaved_replicas, run_trial, summarize


def test_reuse_verifies_original_interleaved_system():
    base = csr_matrix(np.array([[6., -1., 0.], [-1., 5., -2.], [0., -2., 7.]]))
    matrix, rhs, truth = interleaved_replicas(base, 4)
    for policy in ("NATURAL", "COLAMD", "REUSE"):
        trial = run_trial(matrix, rhs, truth, policy)
        assert trial.valid
        assert trial.backward_error < 1e-12
        assert trial.unique_factors == 1
    assert matrix[0, 4] == -1


def test_protocol_rejects_unplanned_variants():
    with pytest.raises(ValueError):
        interleaved_replicas(csr_matrix(np.eye(2)), 3)
    with pytest.raises(ValueError):
        summarize([])
