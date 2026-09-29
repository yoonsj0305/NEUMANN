import numpy as np
from scipy.sparse import csr_matrix

from neumann1.repeated_matrix_v053 import interleaved_replicas, run_trial


if __name__ == "__main__":
    base = csr_matrix(np.array([[5., -1.], [-1., 4.]]))
    matrix, rhs, truth = interleaved_replicas(base, 4)
    assert run_trial(matrix, rhs, truth, "REUSE").valid
    print("real-matrix reuse original-equation contract smoke PASS")
