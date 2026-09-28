from __future__ import annotations

from dataclasses import replace
import math

from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.utility_compression_dataset import (
    UTILITY_CALIBRATION_EXAMPLES_PER_CELL,
    UTILITY_FINAL_EXAMPLES_PER_CELL,
    UTILITY_TRAIN_EXAMPLES_PER_CELL,
    utility_calibration_examples,
    utility_final_examples,
    utility_training_examples,
)
from neumann1.utility_compression import (
    UTILITY_THRESHOLD_GRID,
    calibrate_utility_threshold,
    fit_utility_tree_once,
    one_step_utility,
    observe_utility_policy,
    score_utility_method,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v035_splits_are_new_and_mutually_disjoint():
    prior = _signatures(
        learned_compression_training_examples()
    )
    prior.update(
        _signatures(
            learned_compression_validation_examples()
        )
    )
    prior.update(
        _signatures(
            learned_compression_final_examples()
        )
    )
    prior.update(
        _signatures(
            v034_calibration_examples()
        )
    )
    prior.update(
        _signatures(
            v034_final_examples()
        )
    )

    training = _signatures(
        utility_training_examples()
    )
    calibration = _signatures(
        utility_calibration_examples()
    )
    final = _signatures(
        utility_final_examples()
    )

    assert training.isdisjoint(prior)
    assert calibration.isdisjoint(prior)
    assert final.isdisjoint(prior)
    assert training.isdisjoint(calibration)
    assert training.isdisjoint(final)
    assert calibration.isdisjoint(final)


def test_v035_split_cardinality_is_frozen():
    assert len(utility_training_examples()) == (
        8 * UTILITY_TRAIN_EXAMPLES_PER_CELL
    )
    assert len(utility_calibration_examples()) == (
        8 * UTILITY_CALIBRATION_EXAMPLES_PER_CELL
    )
    assert len(utility_final_examples()) == (
        8 * UTILITY_FINAL_EXAMPLES_PER_CELL
    )


def test_v035_one_step_utility_is_bounded():
    example = utility_training_examples()[0]
    candidates = score_utility_method(
        example,
        "oracle_one_step_utility",
        utility_tree=fit_utility_tree_once(
            utility_training_examples()[:8]
        ),
        frozen_reference_scorer=(
            fit_frozen_v033_scorer()
        ),
    )
    assert candidates

    for item in candidates:
        value = one_step_utility(
            example,
            item.candidate,
        )
        assert math.isfinite(value)
        assert 0.0 <= value <= 1.0


def test_v035_utility_tree_replays_exactly():
    training = utility_training_examples()[:8]
    first = fit_utility_tree_once(training)
    second = fit_utility_tree_once(training)

    assert (
        first.footprint().fitted_state_sha256
        == second.footprint().fitted_state_sha256
    )

    example = utility_calibration_examples()[0]
    assert first.score(example) == second.score(example)


def test_v035_utility_scoring_does_not_use_core_dimension_metadata():
    tree = fit_utility_tree_once(
        utility_training_examples()[:64]
    )
    frozen = fit_frozen_v033_scorer()
    example = utility_calibration_examples()[0]

    shadow_core = (
        example.core_dimension + 1
        if example.core_dimension + 1
        < example.apparent_dimension
        else max(1, example.core_dimension - 1)
    )
    shadow = replace(
        example,
        core_dimension=shadow_core,
    )

    assert score_utility_method(
        example,
        "utility_tree",
        utility_tree=tree,
        frozen_reference_scorer=frozen,
    ) == score_utility_method(
        shadow,
        "utility_tree",
        utility_tree=tree,
        frozen_reference_scorer=frozen,
    )


def test_v035_calibration_is_deterministic_on_subset():
    tree = fit_utility_tree_once(
        utility_training_examples()[:64]
    )
    frozen = fit_frozen_v033_scorer()
    examples = utility_calibration_examples()[:2]

    first = calibrate_utility_threshold(
        examples,
        "utility_tree",
        utility_tree=tree,
        frozen_reference_scorer=frozen,
    )
    second = calibrate_utility_threshold(
        examples,
        "utility_tree",
        utility_tree=tree,
        frozen_reference_scorer=frozen,
    )

    assert first == second
    assert first.threshold in UTILITY_THRESHOLD_GRID


def test_v035_checker_keeps_sample_verified():
    tree = fit_utility_tree_once(
        utility_training_examples()[:64]
    )
    frozen = fit_frozen_v033_scorer()
    calibration_examples = (
        utility_calibration_examples()[:2]
    )

    for method in (
        "utility_tree",
        "reference_mlp",
        "target_leaf",
        "markowitz",
    ):
        calibration = calibrate_utility_threshold(
            calibration_examples,
            method,
            utility_tree=tree,
            frozen_reference_scorer=frozen,
        )
        observation = observe_utility_policy(
            utility_final_examples()[0],
            method,
            calibration,
            utility_tree=tree,
            frozen_reference_scorer=frozen,
        )

        assert observation.final_verified
        assert (
            observation.unsafe_accepted_reductions
            == 0
        )
        assert (
            observation.checker_cost_lower_bound
            .materialization_trials
            >= 0
        )
