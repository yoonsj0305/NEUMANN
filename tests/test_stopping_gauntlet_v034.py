from __future__ import annotations

from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
)
from neumann1.stopping_gauntlet import (
    METHODS,
    THRESHOLD_GRID,
    calibrate_threshold,
    fit_frozen_v033_scorer,
    observe_stopping_method,
    score_candidates,
)
from neumann1.stopping_gauntlet_dataset import (
    V034_CALIBRATION_EXAMPLES_PER_CELL,
    V034_FINAL_EXAMPLES_PER_CELL,
    v034_calibration_examples,
    v034_final_examples,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v034_new_splits_are_disjoint_from_v033_and_each_other():
    v033 = _signatures(
        learned_compression_training_examples()
    )
    v033.update(
        _signatures(
            learned_compression_validation_examples()
        )
    )
    v033.update(
        _signatures(
            learned_compression_final_examples()
        )
    )

    calibration = _signatures(
        v034_calibration_examples()
    )
    final = _signatures(v034_final_examples())

    assert calibration.isdisjoint(v033)
    assert final.isdisjoint(v033)
    assert calibration.isdisjoint(final)


def test_v034_split_cardinality_is_frozen():
    assert len(v034_calibration_examples()) == (
        8 * V034_CALIBRATION_EXAMPLES_PER_CELL
    )
    assert len(v034_final_examples()) == (
        8 * V034_FINAL_EXAMPLES_PER_CELL
    )


def test_v034_frozen_learned_scorer_matches_v033_capacity():
    frozen = fit_frozen_v033_scorer()

    assert frozen.footprint.input_feature_dimension == 16
    assert frozen.footprint.hidden_units == 16
    assert (
        frozen.footprint.fitted_weight_bias_scalars
        == 289
    )
    assert (
        frozen.footprint
        .weighted_sum_terms_per_candidate
        == 272
    )


def test_v034_all_scorers_are_bounded_and_share_candidate_universe():
    frozen = fit_frozen_v033_scorer()
    example = v034_calibration_examples()[0]

    expected_keys = None
    for method in METHODS:
        scored = score_candidates(
            example,
            method,
            frozen_scorer=frozen,
        )
        keys = tuple(
            item.candidate.key
            for item in scored
        )
        if expected_keys is None:
            expected_keys = set(keys)
        else:
            assert set(keys) == expected_keys

        assert all(
            0.0 <= item.score <= 1.0
            for item in scored
        )


def test_v034_threshold_calibration_is_deterministic_and_on_grid():
    frozen = fit_frozen_v033_scorer()
    examples = v034_calibration_examples()[:48]

    first = calibrate_threshold(
        examples,
        "learned_mlp",
        frozen_scorer=frozen,
    )
    second = calibrate_threshold(
        examples,
        "learned_mlp",
        frozen_scorer=frozen,
    )

    assert first == second
    assert first.threshold in THRESHOLD_GRID


def test_v034_final_stopping_does_not_force_oracle_cardinality():
    frozen = fit_frozen_v033_scorer()
    calibration = calibrate_threshold(
        v034_calibration_examples(),
        "learned_mlp",
        frozen_scorer=frozen,
    )

    observations = [
        observe_stopping_method(
            example,
            "learned_mlp",
            calibration,
            frozen_scorer=frozen,
        )
        for example in v034_final_examples()[:32]
    ]

    assert any(
        row.proposed_count
        != (
            row.apparent_dimension
            - row.core_dimension
        )
        for row in observations
    )


def test_v034_checker_preserves_verified_retention_on_sample():
    frozen = fit_frozen_v033_scorer()
    calibration_examples = (
        v034_calibration_examples()
    )
    final_examples = v034_final_examples()[:16]

    for method in (
        "learned_mlp",
        "sparsity_incidence",
        "markowitz",
        "structural_combo",
    ):
        calibration = calibrate_threshold(
            calibration_examples,
            method,
            frozen_scorer=frozen,
        )
        for example in final_examples:
            observation = observe_stopping_method(
                example,
                method,
                calibration,
                frozen_scorer=frozen,
            )
            assert observation.final_verified
            assert (
                observation.unsafe_accepted_reductions
                == 0
            )
