import numpy as np

from benchmark_v066 import Grid
from benchmark_v067 import connected_outages, execute


def test_batched_and_scalar_recover_identical_original_angles():
    grid = Grid(np.array([0, 1, 0]), np.array([1, 2, 2]),
                np.array([2.0, 3.0, 5.0]),
                np.array([0.0, 1.0, -1.0]), 0)
    query = connected_outages(grid)
    scalar, x = execute(grid, query, "scalar")
    batch, y = execute(grid, query, "batch")
    assert scalar["fallback"] == batch["fallback"] == 0
    for key in query:
        np.testing.assert_allclose(x[key], y[key], atol=1e-12)


def test_parallel_edge_is_not_false_bridge_and_router_charges_dispatch():
    grid = Grid(np.array([0, 0, 1]), np.array([1, 1, 2]),
                np.array([2.0, 4.0, 3.0]),
                np.array([0.0, 1.0, -1.0]), 0)
    assert connected_outages(grid) == [0, 1]
    routed, _ = execute(grid, [0], "router", threshold=1)
    assert routed["mode"] == "scalar"
    assert routed["max_original_residual"] < 1e-12
