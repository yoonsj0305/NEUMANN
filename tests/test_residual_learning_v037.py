from __future__ import annotations

from dataclasses import replace

from neumann1.residual_learning import (
    LEARNED_THRESHOLD_GRID,
    RESIDUAL_FEATURE_DIMENSION,
    aggregate_residual_policy,
    fit_residual_models,
    inspect_residual_model,
    observe_exact_residual_teacher,
    observe_learned_residual_policy,
    residual_state_features,
)
from neumann1.residual_learning_dataset import (
    V037_FINAL_EXAMPLES_PER_CELL,
    V037_TRAIN_EXAMPLES_PER_CELL,
    V037_VALIDATION_EXAMPLES_PER_CELL,
    prior_v037_signatures,
    v037_final_examples,
    v037_train_examples,
    v037_validation_examples,
)
from neumann1.residual_headroom import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    target_leaf_checked,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v037_split_cardinality_and_disjointness():
    train = v037_train_examples()
    validation = v037_validation_examples()
    final = v037_final_examples()

    assert len(train) == (
        8 * V037_TRAIN_EXAMPLES_PER_CELL
    )
    assert len(validation) == (
        8 * V037_VALIDATION_EXAMPLES_PER_CELL
    )
    assert len(final) == (
        8 * V037_FINAL_EXAMPLES_PER_CELL
    )

    train_sig = _signatures(train)
    validation_sig = _signatures(validation)
    final_sig = _signatures(final)
    prior = prior_v037_signatures()

    assert train_sig.isdisjoint(prior)
    assert validation_sig.isdisjoint(prior)
    assert final_sig.isdisjoint(prior)
    assert train_sig.isdisjoint(validation_sig)
    assert train_sig.isdisjoint(final_sig)
    assert validation_sig.isdisjoint(final_sig)


def test_v037_first_stage_threshold_remains_frozen():
    assert FROZEN_TARGET_LEAF_THRESHOLD == 0.10


def test_v037_state_feature_contract_is_22_and_k_blind():
    frozen = fit_frozen_v033_scorer()
    example = v037_train_examples()[0]
    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen,
    )
    accepted = initial.accepted_candidates
    candidates = [
        candidate
        for candidate in __import__(
            "neumann1.learned_compression",
            fromlist=["enumerate_affine_candidates"],
        ).enumerate_affine_candidates(
            example.full_system
        )
        if not any(
            candidate.row_index == chosen.row_index
            or candidate.target == chosen.target
            for chosen in accepted
        )
    ]
    if not candidates:
        return

    baseline_ops = __import__(
        "neumann1.structural_compression",
        fromlist=["solve_exact_gauss_jordan"],
    ).solve_exact_gauss_jordan(
        example.full_system
    )[1].arithmetic_ops

    candidate = candidates[0]
    features = residual_state_features(
        example,
        accepted,
        initial.materialized,
        candidate,
        feasible_candidate_count=len(candidates),
        initial_candidate_count=len(candidates),
        baseline_solver_ops=baseline_ops,
    )
    assert len(features) == RESIDUAL_FEATURE_DIMENSION

    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if example.core_dimension + 1
            < example.apparent_dimension
            else max(1, example.core_dimension - 1)
        ),
    )
    shadow_features = residual_state_features(
        shadow,
        accepted,
        initial.materialized,
        candidate,
        feasible_candidate_count=len(candidates),
        initial_candidate_count=len(candidates),
        baseline_solver_ops=baseline_ops,
    )
    assert features == shadow_features


def test_v037_teacher_is_safe_on_sample():
    frozen = fit_frozen_v033_scorer()
    for example in v037_validation_examples()[:2]:
        row = observe_exact_residual_teacher(
            example,
            frozen_scorer=frozen,
        )
        assert row.final_verified
        assert row.unsafe_accepted_reductions == 0
        assert row.final_solver_ops <= (
            row.target_leaf_solver_ops
        )


def test_v037_models_fit_and_have_pre_registered_footprints():
    frozen = fit_frozen_v033_scorer()
    models, rows = fit_residual_models(
        v037_train_examples()[:2],
        frozen_scorer=frozen,
    )
    assert rows

    ridge = inspect_residual_model(models["ridge"])
    mlp = inspect_residual_model(models["tiny_mlp"])

    assert ridge.input_feature_dimension == 22
    assert ridge.fitted_weight_bias_scalars == 23
    assert ridge.hidden_units == 0

    assert mlp.input_feature_dimension == 22
    assert mlp.fitted_weight_bias_scalars == 193
    assert mlp.hidden_units == 8


def test_v037_learned_policy_is_deterministic_and_safe_on_sample():
    frozen = fit_frozen_v033_scorer()
    models, _ = fit_residual_models(
        v037_train_examples()[:2],
        frozen_scorer=frozen,
    )
    example = v037_validation_examples()[0]

    first = observe_learned_residual_policy(
        example,
        models["ridge"],
        LEARNED_THRESHOLD_GRID[1],
        frozen_scorer=frozen,
    )
    second = observe_learned_residual_policy(
        example,
        models["ridge"],
        LEARNED_THRESHOLD_GRID[1],
        frozen_scorer=frozen,
    )

    assert first == second
    assert first.final_verified
    assert first.unsafe_accepted_reductions == 0


def test_v037_aggregate_preserves_verification():
    frozen = fit_frozen_v033_scorer()
    rows = tuple(
        observe_exact_residual_teacher(
            example,
            frozen_scorer=frozen,
        )
        for example in v037_validation_examples()[:2]
    )
    aggregate = aggregate_residual_policy(rows)
    assert aggregate["verified_retention"] == 1.0
    assert aggregate[
        "unsafe_accepted_reduction_count"
    ] == 0
