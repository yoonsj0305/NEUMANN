import numpy as np
from scipy.sparse import csr_matrix

from neumann1.repeated_matrix_v053 import interleaved_replicas
from neumann1.reuse_ablation_v054 import run_trial


if __name__ == "__main__":
    matrix, rhs, truth = interleaved_replicas(csr_matrix(np.array([[5., -1.], [-1., 4.]])), 4)
    assert run_trial(matrix, rhs, truth, "SPLIT_NO_REUSE").factorizations == 4
    assert run_trial(matrix, rhs, truth, "EXACT_REUSE").factorizations == 1
    print("split versus reuse mechanism contract smoke PASS")
