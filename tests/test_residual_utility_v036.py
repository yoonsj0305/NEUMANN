from __future__ import annotations

from dataclasses import replace

from neumann1.compression_utility_dataset import (
    v035_calibration_examples,
    v035_final_examples,
)
from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
)
from neumann1.residual_utility import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    certified_target_leaf_state,
    observe_cheap_first_residual_utility,
)
from neumann1.residual_utility_dataset import (
    V036_DEVELOPMENT_EXAMPLES_PER_CELL,
    v036_development_examples,
)
from neumann1.stopping_gauntlet import (
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


def test_v036_development_is_disjoint_from_all_prior_data():
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
    prior.update(
        _signatures(v035_calibration_examples())
    )
    prior.update(
        _signatures(v035_final_examples())
    )

    development = _signatures(
        v036_development_examples()
    )
    assert development.isdisjoint(prior)


def test_v036_development_cardinality_is_frozen():
    assert len(v036_development_examples()) == (
        8 * V036_DEVELOPMENT_EXAMPLES_PER_CELL
    )


def test_v036_target_leaf_threshold_is_frozen():
    assert FROZEN_TARGET_LEAF_THRESHOLD == 0.10


def test_v036_cheap_state_and_residual_path_verify():
    frozen = fit_frozen_v033_scorer()

    for example in v036_development_examples()[:2]:
        cheap = certified_target_leaf_state(
            example,
            frozen_scorer=frozen,
        )
        residual = observe_cheap_first_residual_utility(
            example,
            frozen_scorer=frozen,
        )

        assert cheap.materialized.verified
        assert cheap.materialized.ground_truth_equivalent
        assert residual.cheap_verified
        assert residual.final_verified
        assert residual.residual_additional_savings >= 0
        assert (
            residual.residual_positive_gain_sum
            == residual.residual_additional_savings
        )


def test_v036_residual_policy_does_not_use_core_dimension_metadata():
    frozen = fit_frozen_v033_scorer()
    example = v036_development_examples()[0]

    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(1, example.core_dimension - 1)
        ),
    )

    original = observe_cheap_first_residual_utility(
        example,
        frozen_scorer=frozen,
    )
    changed = observe_cheap_first_residual_utility(
        shadow,
        frozen_scorer=frozen,
    )

    assert original.cheap_solver_ops == (
        changed.cheap_solver_ops
    )
    assert original.residual_solver_ops == (
        changed.residual_solver_ops
    )
    assert original.cheap_accepted_count == (
        changed.cheap_accepted_count
    )
    assert original.residual_accepted_count == (
        changed.residual_accepted_count
    )
    assert original.residual_trial_materializations == (
        changed.residual_trial_materializations
    )


def test_v036_residual_trial_accounting_is_closed():
    frozen = fit_frozen_v033_scorer()
    example = v036_development_examples()[0]
    row = observe_cheap_first_residual_utility(
        example,
        frozen_scorer=frozen,
    )

    assert (
        row.residual_successful_trial_materializations
        + row.residual_invalid_trial_materializations
        == row.residual_trial_materializations
    )
