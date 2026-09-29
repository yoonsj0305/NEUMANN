import numpy as np
from scipy.sparse import block_diag, csr_matrix

from neumann1.natural_reuse_v055 import run_trial


if __name__ == "__main__":
    part = csr_matrix(np.array([[4., -1.], [-1., 5.]]))
    matrix = block_diag((part, part), format="csr")
    truth = np.sin(np.arange(4) + 1.)
    trial = run_trial(matrix, matrix @ truth, truth, "GATED_REUSE")
    assert trial.valid and trial.factorizations == 1 and trial.components == 2
    print("natural-matrix abstention and reuse contract smoke PASS")
