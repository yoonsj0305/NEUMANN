from __future__ import annotations

from dataclasses import replace

from neumann1.compression_utility import (
    calibrate_utility_threshold,
    observe_dynamic_greedy_utility,
    observe_static_isolated_utility,
)
from neumann1.compression_utility_dataset import (
    V035_CALIBRATION_EXAMPLES_PER_CELL,
    V035_FINAL_EXAMPLES_PER_CELL,
    v035_calibration_examples,
    v035_final_examples,
)
from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
)
from neumann1.stopping_gauntlet import (
    THRESHOLD_GRID,
    fit_frozen_v033_scorer,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v035_splits_are_disjoint_from_all_prior_splits():
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
        _signatures(v034_calibration_examples())
    )
    prior.update(
        _signatures(v034_final_examples())
    )

    calibration = _signatures(
        v035_calibration_examples()
    )
    final = _signatures(v035_final_examples())

    assert calibration.isdisjoint(prior)
    assert final.isdisjoint(prior)
    assert calibration.isdisjoint(final)


def test_v035_split_cardinality_is_frozen():
    assert len(v035_calibration_examples()) == (
        8 * V035_CALIBRATION_EXAMPLES_PER_CELL
    )
    assert len(v035_final_examples()) == (
        8 * V035_FINAL_EXAMPLES_PER_CELL
    )


def test_v035_utility_threshold_calibration_is_deterministic():
    frozen = fit_frozen_v033_scorer()
    examples = v035_calibration_examples()[:8]

    first = calibrate_utility_threshold(
        examples,
        "target_leaf",
        frozen_scorer=frozen,
    )
    second = calibrate_utility_threshold(
        examples,
        "target_leaf",
        frozen_scorer=frozen,
    )

    assert first == second
    assert first.threshold in THRESHOLD_GRID


def test_v035_static_and_dynamic_oracles_verify_original_problem():
    examples = v035_final_examples()[:2]

    for example in examples:
        static = observe_static_isolated_utility(
            example
        )
        dynamic = observe_dynamic_greedy_utility(
            example
        )

        assert static.final_verified
        assert dynamic.final_verified
        assert static.solver_savings >= 0
        assert dynamic.solver_savings >= 0
        assert (
            dynamic.positive_marginal_gain_sum
            == dynamic.solver_savings
        )


def test_v035_utility_oracles_do_not_use_core_dimension_metadata():
    example = v035_final_examples()[0]
    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(1, example.core_dimension - 1)
        ),
    )

    original_static = observe_static_isolated_utility(
        example
    )
    shadow_static = observe_static_isolated_utility(
        shadow
    )
    original_dynamic = observe_dynamic_greedy_utility(
        example
    )
    shadow_dynamic = observe_dynamic_greedy_utility(
        shadow
    )

    assert original_static.method_solver_ops == (
        shadow_static.method_solver_ops
    )
    assert original_static.accepted_count == (
        shadow_static.accepted_count
    )
    assert original_dynamic.method_solver_ops == (
        shadow_dynamic.method_solver_ops
    )
    assert original_dynamic.accepted_count == (
        shadow_dynamic.accepted_count
    )
    assert original_dynamic.trial_materializations == (
        shadow_dynamic.trial_materializations
    )


def test_v035_static_trial_accounting_matches_candidate_count():
    example = v035_final_examples()[0]
    observation = observe_static_isolated_utility(
        example
    )

    assert observation.trial_materializations == (
        observation.candidate_count
    )
    assert (
        observation.successful_trial_materializations
        + observation.invalid_trial_materializations
        == observation.trial_materializations
    )
