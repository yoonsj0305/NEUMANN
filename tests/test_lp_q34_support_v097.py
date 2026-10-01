import numpy as np
import pytest

highspy = pytest.importorskip("highspy")

from neumann1.lp_q34_support_v097 import adaptive_support_checked, restricted_original_checked


def tiny_lp():
    # min x0 + 2*x1 + 4*x2, x0+x1+x2=1, x>=0; optimum x0=1.
    return {
        "A": np.array([[1.0, 1.0, 1.0]]),
        "b": np.array([1.0]),
        "c": np.array([1.0, 2.0, 4.0]),
    }


def test_restricted_support_is_accepted_only_on_original_lp():
    raw = tiny_lp()
    good = restricted_original_checked(**raw, indices=[0], budget_s=2.0)
    assert good["accepted"] is True
    bad = restricted_original_checked(**raw, indices=[1], budget_s=2.0)
    assert bad["accepted"] is False
    assert bad["native"]["accepted"] is True
    assert bad["original_certificate"]["accepted"] is False


def test_adaptive_expands_then_falls_back_safely():
    raw = tiny_lp()
    # m=1, first support is wrong; 2m includes optimum and should certify.
    result = adaptive_support_checked(**raw, ranking=[1, 0, 2], budget_s=2.0)
    assert result["accepted"] is True
    assert len(result["attempts"]) == 2
    assert result["attempts"][0]["result"]["accepted"] is False
    assert result["attempts"][1]["result"]["accepted"] is True
    assert result["fallback"] is None


def test_invalid_support_or_ranking_fails_closed():
    raw = tiny_lp()
    with pytest.raises(ValueError):
        restricted_original_checked(**raw, indices=[0, 0], budget_s=2.0)
    with pytest.raises(ValueError):
        adaptive_support_checked(**raw, ranking=[0, 1, 1], budget_s=2.0)
