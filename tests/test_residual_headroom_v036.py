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
from neumann1.residual_headroom import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    aggregate_residual_headroom,
    observe_residual_headroom,
    target_leaf_checked,
)
from neumann1.residual_headroom_dataset import (
    V036_FINAL_EXAMPLES_PER_CELL,
    prior_v036_signatures,
    v036_final_examples,
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


def test_v036_threshold_is_frozen_from_v035():
    assert FROZEN_TARGET_LEAF_THRESHOLD == 0.10


def test_v036_final_is_disjoint_from_all_prior_data():
    final = _signatures(v036_final_examples())
    assert final.isdisjoint(
        prior_v036_signatures()
    )

    explicit_prior = _signatures(
        learned_compression_training_examples()
    )
    explicit_prior.update(
        _signatures(
            learned_compression_validation_examples()
        )
    )
    explicit_prior.update(
        _signatures(
            learned_compression_final_examples()
        )
    )
    explicit_prior.update(
        _signatures(v034_calibration_examples())
    )
    explicit_prior.update(
        _signatures(v034_final_examples())
    )
    explicit_prior.update(
        _signatures(v035_calibration_examples())
    )
    explicit_prior.update(
        _signatures(v035_final_examples())
    )
    assert final.isdisjoint(explicit_prior)


def test_v036_final_cardinality_is_frozen():
    assert len(v036_final_examples()) == (
        8 * V036_FINAL_EXAMPLES_PER_CELL
    )


def test_v036_target_leaf_does_not_use_core_dimension_metadata():
    frozen = fit_frozen_v033_scorer()
    example = v036_final_examples()[0]
    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(1, example.core_dimension - 1)
        ),
    )

    original = target_leaf_checked(
        example,
        frozen_scorer=frozen,
    )
    changed = target_leaf_checked(
        shadow,
        frozen_scorer=frozen,
    )

    assert original.accepted_candidates == (
        changed.accepted_candidates
    )
    assert (
        original.materialized.solver_counts.arithmetic_ops
        == changed.materialized.solver_counts.arithmetic_ops
    )


def test_v036_residual_path_is_safe_and_telescopes():
    frozen = fit_frozen_v033_scorer()

    for example in v036_final_examples()[:2]:
        row = observe_residual_headroom(
            example,
            frozen_scorer=frozen,
        )
        assert row.final_verified
        assert row.residual_solver_ops <= (
            row.target_leaf_solver_ops
        )
        assert row.residual_additional_solver_savings >= 0
        assert row.residual_selected_gain_sum == (
            row.residual_additional_solver_savings
        )


def test_v036_residual_path_does_not_use_core_dimension_metadata():
    frozen = fit_frozen_v033_scorer()
    example = v036_final_examples()[0]
    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(1, example.core_dimension - 1)
        ),
    )

    original = observe_residual_headroom(
        example,
        frozen_scorer=frozen,
    )
    changed = observe_residual_headroom(
        shadow,
        frozen_scorer=frozen,
    )

    assert original.target_leaf_solver_ops == (
        changed.target_leaf_solver_ops
    )
    assert original.full_dynamic_solver_ops == (
        changed.full_dynamic_solver_ops
    )
    assert original.residual_solver_ops == (
        changed.residual_solver_ops
    )
    assert original.residual_trial_materializations == (
        changed.residual_trial_materializations
    )


def test_v036_aggregate_gate_is_well_formed_on_sample():
    frozen = fit_frozen_v033_scorer()
    rows = tuple(
        observe_residual_headroom(
            example,
            frozen_scorer=frozen,
        )
        for example in v036_final_examples()[:2]
    )
    result = aggregate_residual_headroom(rows)

    assert result["continuation_decision"] in {
        "PROCEED_LEARNED_RESIDUAL",
        "HOLD_SCALE_ROUTER",
        "DELETE_LEARNED_RESIDUAL",
    }
    assert 0 <= result[
        "continuation_gate_pass_count"
    ] <= 3
