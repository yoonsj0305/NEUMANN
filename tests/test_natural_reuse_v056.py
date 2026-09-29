import numpy as np
from scipy.sparse import block_diag, csr_matrix

from neumann1.natural_reuse_v056 import numerically_valid


def test_corrective_tolerance_is_explicit_and_bounded():
    assert numerically_valid(3.48e-16, 1.0526328239712942e-7)
    assert not numerically_valid(1.1e-10, 1e-8)
    assert not numerically_valid(1e-16, 1.1e-6)
    assert not numerically_valid(np.nan, 1e-8)


def test_same_candidate_verifies_duplicate_blocks():
    part = csr_matrix(np.array([[4., -1.], [-1., 5.]]))
    matrix = block_diag((part, part), format="csr")
    # use the candidate directly: this synthetic case is only a smoke.
    from neumann1.natural_reuse_v055 import run_trial
    truth = np.sin(np.arange(4.) + 1.)
    result = run_trial(matrix, matrix @ truth, truth, "GATED_REUSE")
    assert result.valid and result.components == 2 and result.distinct_blocks == 1
