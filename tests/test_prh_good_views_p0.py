"""Contract and anti-leakage tests for P0 synthetic mechanism probe."""
import numpy as np

from experiments.prh_good_views_p0 import (
    CONTRACT, normalize, observations, orthogonal, procrustes, run, top1,
)


def test_orthogonal_and_exact_rotation():
    a, b = orthogonal(10, 5), orthogonal(11, 5)
    np.testing.assert_allclose(a.T @ a, np.eye(5), atol=1e-12)
    x = normalize(np.random.default_rng(2).normal(size=(100, 5)))
    y = x @ a.T @ b
    recovered = procrustes(x, y)
    np.testing.assert_allclose(x @ recovered, y, atol=1e-10)


def test_full_pool_is_permutation_invariant():
    x = normalize(np.random.default_rng(11).normal(size=(40, 6)))
    r1 = top1(x, x, np.eye(6), permutation_seed=1)
    r2 = top1(x, x, np.eye(6), permutation_seed=2)
    assert r1["correct"] == r2["correct"] == 40


def test_views_share_state_but_not_noise():
    a = np.eye(6)
    x1, y1 = observations(10, 1, a, a, .04)
    x2, y2 = observations(10, 1, a, a, .04)
    np.testing.assert_array_equal(x1, x2)
    np.testing.assert_array_equal(y1, y2)
    assert not np.array_equal(x1, y1)


def test_invalid_pair_inputs_rejected():
    try:
        procrustes(np.ones((2, 3)), np.ones((3, 3)))
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched training pairs accepted")


def test_contract_preserves_all_global_gates():
    assert list(CONTRACT["prior_global_gates"].values()) == ["OPEN"] * 7
    result = run()
    assert result["q1_to_q7"] == "OPEN"
    assert set(result["cells"]) == {"iid", "sparse-structure", "new-sensor"}
    assert result["energy_joule"] is None
    assert result["flops"] is None
    assert result["monetary_cost_usd"] is None
