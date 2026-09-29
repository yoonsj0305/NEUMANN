import numpy as np
import pytest

from benchmark_v066 import Grid, _connected_outages, _verify, execute


def test_triangle_contingencies_match_direct_original_equations():
    grid = Grid(np.array([0, 1, 0]), np.array([1, 2, 2]),
                np.array([2.0, 3.0, 5.0]),
                np.array([0.0, 1.0, -1.0]), 0)
    direct, expected = execute(grid, "native")
    reused, actual = execute(grid, "reuse")
    assert direct["connected"] == reused["connected"] == 3
    assert reused["fallback"] == 0
    assert max(direct["max_original_residual"], reused["max_original_residual"]) < 1e-12
    for k in expected:
        np.testing.assert_allclose(actual[k], expected[k], atol=1e-12)
    broken = actual[0].copy()
    broken[1] += 0.01
    with pytest.raises(ValueError, match="residual failed"):
        _verify(grid, broken, 0)


def test_bridge_is_excluded_from_connected_outage_capability():
    grid = Grid(np.array([0, 1]), np.array([1, 2]),
                np.array([2.0, 3.0]), np.array([0.0, 1.0, -1.0]), 0)
    assert _connected_outages(grid) == []
