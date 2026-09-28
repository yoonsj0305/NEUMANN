from __future__ import annotations

from neumann1.compression_economics import (
    aggregate_economics_observations,
    audit_checker_economics,
)
from neumann1.stopping_gauntlet import (
    calibrate_threshold,
    fit_frozen_v033_scorer,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


def _observation(method: str, example_index: int = 0):
    frozen = fit_frozen_v033_scorer()
    calibration = calibrate_threshold(
        v034_calibration_examples()[:48],
        method,
        frozen_scorer=frozen,
    )
    return audit_checker_economics(
        v034_final_examples()[example_index],
        method,
        calibration.threshold,
        frozen_scorer=frozen,
    )


def test_v035_mirrored_checker_matches_frozen_checker():
    for method in (
        "learned_mlp",
        "target_leaf",
        "markowitz",
    ):
        observation = _observation(method)
        assert observation.checker_parity
        assert observation.final_verified
        assert observation.unsafe_accepted_reductions == 0


def test_v035_successful_path_lower_bound_contains_final_work():
    observation = _observation("target_leaf", example_index=1)

    assert (
        observation.successful_tentative_materializations
        == observation.accepted_count
    )
    assert (
        observation.successful_tentative_materializations
        + observation.final_materializations
        == observation.accepted_count + 1
    )
    assert (
        observation.successful_path_lb_solver_ops
        >= observation.final_solver_ops
    )
    assert (
        observation.successful_path_lb_reconstruction_ops
        >= observation.final_reconstruction_ops
    )
    assert (
        observation.successful_path_lb_verification_ops
        >= observation.final_verification_ops
    )
    assert (
        observation.successful_path_lb_total_arithmetic
        == observation.successful_path_lb_solver_ops
        + observation.successful_path_lb_reconstruction_ops
        + observation.successful_path_lb_verification_ops
    )
    assert observation.successful_path_lb_ratio > 0.0


def test_v035_aggregate_preserves_ratio_definition():
    rows = (
        _observation("markowitz", example_index=0),
        _observation("markowitz", example_index=1),
    )
    aggregate = aggregate_economics_observations(rows)

    assert aggregate["count"] == 2
    assert aggregate["checker_parity_rate"] == 1.0
    assert aggregate["verified_retention"] == 1.0
    assert aggregate["unsafe_accepted_reduction_count"] == 0
    assert (
        0.0
        <= aggregate["fraction_lb_ratio_lt_1"]
        <= 1.0
    )
    assert (
        0.0
        <= aggregate["fraction_lb_ratio_ge_1"]
        <= 1.0
    )
    assert (
        aggregate["fraction_lb_ratio_lt_1"]
        + aggregate["fraction_lb_ratio_ge_1"]
        == 1.0
    )
