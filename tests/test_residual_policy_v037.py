from __future__ import annotations

from dataclasses import replace
import math

from neumann1.learned_compression import (
    enumerate_affine_candidates,
)
from neumann1.residual_policy import (
    RESIDUAL_FEATURE_DIMENSION,
    fit_residual_tree,
    prepare_initial_state,
    residual_state_features,
    rollout_residual_policy,
    teacher_rows_for_example,
)
from neumann1.residual_policy_dataset import (
    V037_CALIBRATION_EXAMPLES_PER_CELL,
    V037_FINAL_EXAMPLES_PER_CELL,
    V037_TRAIN_EXAMPLES_PER_CELL,
    prior_v037_signatures,
    v037_calibration_examples,
    v037_final_examples,
    v037_train_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v037_splits_are_disjoint_from_prior_and_each_other():
    train = _signatures(
        v037_train_examples()
    )
    calibration = _signatures(
        v037_calibration_examples()
    )
    final = _signatures(
        v037_final_examples()
    )
    prior = prior_v037_signatures()

    assert train.isdisjoint(prior)
    assert calibration.isdisjoint(prior)
    assert final.isdisjoint(prior)
    assert train.isdisjoint(calibration)
    assert train.isdisjoint(final)
    assert calibration.isdisjoint(final)


def test_v037_split_cardinality_is_frozen():
    assert len(v037_train_examples()) == (
        8 * V037_TRAIN_EXAMPLES_PER_CELL
    )
    assert len(v037_calibration_examples()) == (
        8 * V037_CALIBRATION_EXAMPLES_PER_CELL
    )
    assert len(v037_final_examples()) == (
        8 * V037_FINAL_EXAMPLES_PER_CELL
    )


def test_v037_feature_contract_is_state_aware_and_core_metadata_free():
    frozen = fit_frozen_v033_scorer()
    example = v037_train_examples()[0]
    initial = prepare_initial_state(
        example,
        frozen_scorer=frozen,
    )

    accepted_rows = {
        item.row_index
        for item in initial.accepted
    }
    accepted_targets = {
        item.target
        for item in initial.accepted
    }
    candidate = next(
        item
        for item in enumerate_affine_candidates(
            example.full_system
        )
        if (
            item.row_index not in accepted_rows
            and item.target not in accepted_targets
        )
    )

    features = residual_state_features(
        example,
        initial.accepted,
        initial.materialized,
        candidate,
    )
    assert len(features) == (
        RESIDUAL_FEATURE_DIMENSION
    )
    assert all(
        math.isfinite(value)
        for value in features
    )

    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(
                1,
                example.core_dimension - 1,
            )
        ),
    )
    shadow_initial = prepare_initial_state(
        shadow,
        frozen_scorer=frozen,
    )
    shadow_features = residual_state_features(
        shadow,
        shadow_initial.accepted,
        shadow_initial.materialized,
        candidate,
    )
    assert features == shadow_features


def test_v037_teacher_rows_are_finite_and_tree_fit_is_deterministic():
    frozen = fit_frozen_v033_scorer()
    states = tuple(
        prepare_initial_state(
            example,
            frozen_scorer=frozen,
        )
        for example in v037_train_examples()[:4]
    )
    rows = tuple(
        row
        for state in states
        for row in teacher_rows_for_example(
            state
        )
    )
    assert rows
    assert all(
        math.isfinite(
            row.relative_vor
        )
        for row in rows
    )

    first = fit_residual_tree(
        rows,
        max_depth=2,
    )
    second = fit_residual_tree(
        rows,
        max_depth=2,
    )

    X = [
        row.features
        for row in rows[:8]
    ]
    assert (
        first.regressor.predict(X).tolist()
        == second.regressor.predict(X).tolist()
    )
    assert (
        first.fitted_node_count
        == second.fitted_node_count
    )


def test_v037_positive_utility_guard_never_worsens_target_leaf_sample():
    frozen = fit_frozen_v033_scorer()

    for example in v037_final_examples()[:4]:
        initial = prepare_initial_state(
            example,
            frozen_scorer=frozen,
        )
        row = rollout_residual_policy(
            initial,
            method="residual_random",
            threshold=0.0,
        )
        assert row.final_verified
        assert row.final_solver_ops <= (
            row.target_leaf_solver_ops
        )
        assert (
            row.residual_additional_solver_savings
            >= 0
        )


def test_v037_rollout_does_not_use_core_dimension_metadata():
    frozen = fit_frozen_v033_scorer()
    example = v037_final_examples()[0]
    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(
                1,
                example.core_dimension - 1,
            )
        ),
    )

    first_initial = prepare_initial_state(
        example,
        frozen_scorer=frozen,
    )
    second_initial = prepare_initial_state(
        shadow,
        frozen_scorer=frozen,
    )

    first = rollout_residual_policy(
        first_initial,
        method="residual_markowitz",
        threshold=0.05,
    )
    second = rollout_residual_policy(
        second_initial,
        method="residual_markowitz",
        threshold=0.05,
    )

    assert first.final_solver_ops == (
        second.final_solver_ops
    )
    assert (
        first.proposal_materializations
        == second.proposal_materializations
    )
