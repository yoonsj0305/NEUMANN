from __future__ import annotations

from dataclasses import replace

from neumann1.residual_headroom import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    target_leaf_checked,
)
from neumann1.residual_predictor import (
    POLICIES,
    RESIDUAL_FEATURE_DIMENSION,
    TRIAL_BUDGET_PER_STATE,
    build_teacher_training_matrix,
    fit_residual_models,
    policy_footprint,
    residual_state_features,
    run_bounded_residual_policy,
    select_smallest_adequate_policy,
)
from neumann1.residual_predictor_dataset import (
    V037_FINAL_EXAMPLES_PER_CELL,
    V037_TRAIN_EXAMPLES_PER_CELL,
    V037_VALIDATION_EXAMPLES_PER_CELL,
    prior_v037_signatures,
    v037_final_examples,
    v037_train_examples,
    v037_validation_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.structural_compression import (
    solve_exact_gauss_jordan,
)
from neumann1.learned_compression import (
    enumerate_affine_candidates,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v037_splits_are_disjoint_from_prior_and_each_other():
    train = _signatures(v037_train_examples())
    validation = _signatures(
        v037_validation_examples()
    )
    final = _signatures(v037_final_examples())
    prior = prior_v037_signatures()

    assert train.isdisjoint(prior)
    assert validation.isdisjoint(prior)
    assert final.isdisjoint(prior)
    assert train.isdisjoint(validation)
    assert train.isdisjoint(final)
    assert validation.isdisjoint(final)


def test_v037_split_cardinality_is_frozen():
    assert len(v037_train_examples()) == (
        8 * V037_TRAIN_EXAMPLES_PER_CELL
    )
    assert len(v037_validation_examples()) == (
        8 * V037_VALIDATION_EXAMPLES_PER_CELL
    )
    assert len(v037_final_examples()) == (
        8 * V037_FINAL_EXAMPLES_PER_CELL
    )


def test_v037_frozen_architecture_constants():
    assert FROZEN_TARGET_LEAF_THRESHOLD == 0.10
    assert TRIAL_BUDGET_PER_STATE == 4
    assert RESIDUAL_FEATURE_DIMENSION == 28
    assert POLICIES == (
        "state_target_leaf",
        "state_markowitz",
        "ridge",
        "mlp8",
    )


def test_v037_features_do_not_use_core_dimension_metadata():
    frozen = fit_frozen_v033_scorer()
    example = v037_train_examples()[0]
    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(1, example.core_dimension - 1)
        ),
    )

    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen,
    )
    shadow_initial = target_leaf_checked(
        shadow,
        frozen_scorer=frozen,
    )
    accepted = tuple(initial.accepted_candidates)
    shadow_accepted = tuple(
        shadow_initial.accepted_candidates
    )
    assert accepted == shadow_accepted

    feasible = tuple(
        candidate
        for candidate in enumerate_affine_candidates(
            example.full_system
        )
        if not any(
            candidate.row_index == chosen.row_index
            or candidate.target == chosen.target
            for chosen in accepted
        )
    )
    assert feasible

    _, baseline_counts = solve_exact_gauss_jordan(
        example.full_system
    )
    _, shadow_baseline_counts = solve_exact_gauss_jordan(
        shadow.full_system
    )

    candidate = feasible[0]
    original_features = residual_state_features(
        example,
        accepted,
        initial.materialized,
        candidate,
        feasible,
        baseline_solver_ops=(
            baseline_counts.arithmetic_ops
        ),
    )
    shadow_features = residual_state_features(
        shadow,
        shadow_accepted,
        shadow_initial.materialized,
        candidate,
        feasible,
        baseline_solver_ops=(
            shadow_baseline_counts.arithmetic_ops
        ),
    )

    assert len(original_features) == 28
    assert original_features == shadow_features


def test_v037_teacher_targets_are_bounded_and_nontrivial():
    frozen = fit_frozen_v033_scorer()
    X, y = build_teacher_training_matrix(
        v037_train_examples()[:4],
        frozen_scorer=frozen,
    )

    assert X.shape[1] == 28
    assert len(y) == len(X)
    assert (y >= 0.0).all()
    assert (y <= 1.0).all()
    assert (y > 0.0).any()


def test_v037_model_footprints_are_frozen():
    frozen = fit_frozen_v033_scorer()
    models = fit_residual_models(
        v037_train_examples()[:4],
        frozen_scorer=frozen,
    )

    ridge = policy_footprint(
        "ridge",
        models,
    )
    mlp = policy_footprint(
        "mlp8",
        models,
    )

    assert ridge.input_dimension == 28
    assert ridge.fitted_weight_bias_scalars == 29
    assert ridge.scaler_state_scalars == 56
    assert ridge.weighted_sum_terms_per_candidate == 28

    assert mlp.input_dimension == 28
    assert mlp.fitted_weight_bias_scalars == 241
    assert mlp.scaler_state_scalars == 56
    assert mlp.weighted_sum_terms_per_candidate == 232


def test_v037_bounded_policy_never_accepts_nonpositive_gain():
    frozen = fit_frozen_v033_scorer()
    models = fit_residual_models(
        v037_train_examples()[:4],
        frozen_scorer=frozen,
    )
    example = v037_validation_examples()[0]

    for method in POLICIES:
        row = run_bounded_residual_policy(
            example,
            method,
            frozen_scorer=frozen,
            models=models,
        )
        assert row.final_verified
        assert row.nonpositive_accepted_count == 0
        assert row.final_solver_ops <= (
            row.target_leaf_solver_ops
        )


def test_v037_selection_prefers_adequate_deterministic_policy():
    base = {
        "adequate": False,
        "mean_exact_trials": 10.0,
        "mean_final_solver_ops": 100.0,
    }
    aggregates = {
        method: dict(base)
        for method in POLICIES
    }
    aggregates["state_target_leaf"].update(
        {
            "adequate": True,
            "mean_exact_trials": 4.0,
            "mean_final_solver_ops": 80.0,
        }
    )
    aggregates["ridge"].update(
        {
            "adequate": True,
            "mean_exact_trials": 1.0,
            "mean_final_solver_ops": 10.0,
        }
    )

    assert (
        select_smallest_adequate_policy(
            aggregates
        )
        == "state_target_leaf"
    )


def test_v037_selection_prefers_ridge_before_mlp():
    base = {
        "adequate": False,
        "mean_exact_trials": 10.0,
        "mean_final_solver_ops": 100.0,
    }
    aggregates = {
        method: dict(base)
        for method in POLICIES
    }
    aggregates["ridge"]["adequate"] = True
    aggregates["mlp8"]["adequate"] = True

    assert (
        select_smallest_adequate_policy(
            aggregates
        )
        == "ridge"
    )
