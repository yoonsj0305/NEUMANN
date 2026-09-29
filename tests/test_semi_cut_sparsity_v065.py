import numpy as np
import pytest

pytest.importorskip("highspy")

from benchmark_v064 import sparsify_valid_cut


def test_dropped_coefficients_relax_cut_at_every_box_corner():
    row = np.array([-2e-12, 3e-12, -2.0])
    lower = np.array([0.0, -5.0, 0.0])
    upper = np.array([100.0, 7.0, 1.0])
    rhs = 0.25
    reduced, relaxed = sparsify_valid_cut(row, rhs, lower, upper)
    assert np.array_equal(reduced, [0.0, 0.0, -2.0])
    for a in (lower[0], upper[0]):
        for b in (lower[1], upper[1]):
            for c in (lower[2], upper[2]):
                x = np.array([a, b, c])
                assert reduced @ x - relaxed <= row @ x - rhs + 1e-14


def test_unbounded_dropped_coefficient_is_rejected():
    with pytest.raises(ValueError, match="cannot bound"):
        sparsify_valid_cut(np.array([1e-12]), 0.0,
                           np.array([0.0]), np.array([np.inf]))
