import numpy as np
from scipy.sparse import csr_matrix

from neumann1.numeric_order_v052 import POLICIES, run_trial


if __name__ == "__main__":
    matrix = csr_matrix(np.array([[8., -1., 0.], [-1., 7., -2.], [0., -2., 9.]]))
    truth = np.array([0.7, -1.2, 2.])
    for policy in POLICIES:
        assert run_trial(matrix, matrix @ truth, truth, policy).valid
    print("numeric order original-equation contract smoke PASS")
