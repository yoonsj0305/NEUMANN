from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean
from typing import Iterable

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .learned_compression import (
    AffineCandidate,
    MaterializedReduction,
    candidate_features,
    enumerate_affine_candidates,
    materialize_reduction,
)
from .learned_compression_dataset import (
    LearnedCompressionExample,
)
from .residual_headroom import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    target_leaf_checked,
)
from .stopping_gauntlet import (
    FrozenV033Scorer,
)
from .structural_compression import (
    solve_exact_gauss_jordan,
)


STATIC_FEATURE_DIMENSION = 16
STATE_FEATURE_DIMENSION = 12
RESIDUAL_FEATURE_DIMENSION = (
    STATIC_FEATURE_DIMENSION + STATE_FEATURE_DIMENSION
)
TRIAL_BUDGET_PER_STATE = 4
RIDGE_ALPHA = 1e-3
MLP_HIDDEN_UNITS = 8
MLP_ALPHA = 1e-3
MLP_RANDOM_STATE = 37

POLICIES = (
    "state_target_leaf",
    "state_markowitz",
    "ridge",
    "mlp8",
)


@dataclass(frozen=True)
class ResidualTeacherSample:
    features: tuple[float, ...]
    target: float


@dataclass(frozen=True)
class ExactResidualTeacherObservation:
    core_dimension: int
    apparent_dimension: int
    target_leaf_solver_ops: int
    final_solver_ops: int
    residual_additional_savings: int
    accepted_residual_count: int
    exact_trials: int
    successful_trials: int
    invalid_trials: int
    successful_trial_solver_ops: int
    final_verified: bool


@dataclass(frozen=True)
class ResidualPolicyObservation:
    method: str
    core_dimension: int
    apparent_dimension: int
    target_leaf_solver_ops: int
    final_solver_ops: int
    residual_additional_savings: int
    accepted_residual_count: int
    exact_trials: int
    successful_trials: int
    invalid_trials: int
    nonpositive_trials: int
    successful_trial_solver_ops: int
    degraded_mode: bool
    final_verified: bool
    nonpositive_accepted_count: int


@dataclass(frozen=True)
class ResidualModelFootprint:
    method: str
    input_dimension: int
    fitted_weight_bias_scalars: int
    scaler_state_scalars: int
    weighted_sum_terms_per_candidate: int


@dataclass(frozen=True)
class FittedResidualModels:
    ridge: Pipeline
    mlp8: Pipeline
    ridge_footprint: ResidualModelFootprint
    mlp8_footprint: ResidualModelFootprint
    training_sample_count: int
    positive_training_sample_count: int


def _target_index(candidate: AffineCandidate) -> int:
    return int(candidate.target[1:])


def _feasible_candidates(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
) -> tuple[AffineCandidate, ...]:
    output = []
    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        if any(
            candidate.row_index == chosen.row_index
            or candidate.target == chosen.target
            for chosen in accepted
        ):
            continue
        output.append(candidate)
    return tuple(output)


def _active_state_statistics(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    candidate: AffineCandidate,
    feasible: tuple[AffineCandidate, ...],
) -> tuple[float, ...]:
    system = example.full_system
    n = system.dimension

    removed_rows = {
        item.row_index
        for item in accepted
    }
    eliminated = {
        item.target
        for item in accepted
    }
    retained_rows = tuple(
        row_index
        for row_index in range(n)
        if row_index not in removed_rows
    )
    retained_variables = tuple(
        variable
        for variable in system.variables
        if variable not in eliminated
    )
    retained_dimension = len(retained_variables)
    retained_row_count = len(retained_rows)

    retained_variable_set = set(retained_variables)
    target_index = system.variables.index(candidate.target)

    active_row_nnz = sum(
        1
        for column, value in enumerate(
            system.A[candidate.row_index]
        )
        if (
            value != 0
            and system.variables[column]
            in retained_variable_set
        )
    )

    active_target_incidence = sum(
        1
        for row_index in retained_rows
        if system.A[row_index][target_index] != 0
    )

    dependency_names = [
        name
        for name, _ in candidate.coefficients
    ]
    dependency_active_incidences = []
    eliminated_dependency_count = 0

    for dependency in dependency_names:
        if dependency in eliminated:
            eliminated_dependency_count += 1
            dependency_active_incidences.append(0)
            continue

        dependency_index = system.variables.index(
            dependency
        )
        dependency_active_incidences.append(
            sum(
                1
                for row_index in retained_rows
                if system.A[row_index][
                    dependency_index
                ]
                != 0
            )
        )

    if dependency_active_incidences:
        dependency_incidence_mean = mean(
            dependency_active_incidences
        )
        dependency_incidence_max = max(
            dependency_active_incidences
        )
    else:
        dependency_incidence_mean = 0.0
        dependency_incidence_max = 0.0

    feasible_count = max(1, len(feasible))

    target_as_dependency_count = sum(
        1
        for other in feasible
        if any(
            dependency == candidate.target
            for dependency, _ in other.coefficients
        )
    )

    target_frequency_by_name: dict[str, int] = {}
    for other in feasible:
        target_frequency_by_name[other.target] = (
            target_frequency_by_name.get(
                other.target,
                0,
            )
            + 1
        )

    dependency_target_frequencies = [
        target_frequency_by_name.get(
            dependency,
            0,
        )
        for dependency in dependency_names
    ]
    mean_dependency_target_frequency = (
        mean(dependency_target_frequencies)
        if dependency_target_frequencies
        else 0.0
    )

    same_row_count = sum(
        1
        for other in feasible
        if other.row_index == candidate.row_index
    )
    same_target_count = sum(
        1
        for other in feasible
        if other.target == candidate.target
    )

    dependency_count = max(
        1,
        len(dependency_names),
    )

    features = (
        retained_dimension / max(1.0, float(n)),
        len(accepted) / max(1.0, float(n)),
        active_row_nnz
        / max(1.0, float(retained_dimension)),
        active_target_incidence
        / max(1.0, float(retained_row_count)),
        dependency_incidence_mean
        / max(1.0, float(retained_row_count)),
        dependency_incidence_max
        / max(1.0, float(retained_row_count)),
        eliminated_dependency_count
        / float(dependency_count),
        target_as_dependency_count
        / float(feasible_count),
        mean_dependency_target_frequency
        / float(feasible_count),
        same_row_count / float(feasible_count),
        same_target_count / float(feasible_count),
    )
    if len(features) != 11:
        raise AssertionError(
            "internal residual state feature drift"
        )
    return tuple(float(value) for value in features)


def residual_state_features(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    current: MaterializedReduction,
    candidate: AffineCandidate,
    feasible: tuple[AffineCandidate, ...],
) -> tuple[float, ...]:
    static = candidate_features(
        example.full_system,
        candidate,
    )
    active = _active_state_statistics(
        example,
        accepted,
        candidate,
        feasible,
    )
    current_ratio = (
        current.solver_counts.arithmetic_ops
        / max(
            1.0,
            float(example.full_system.dimension ** 3),
        )
    )

    features = static + (
        current_ratio,
    ) + active

    if len(features) != RESIDUAL_FEATURE_DIMENSION:
        raise AssertionError(
            "residual feature contract dimension drift"
        )
    if not all(math.isfinite(value) for value in features):
        raise ValueError(
            "non-finite residual state feature"
        )
    return tuple(float(value) for value in features)


def _teacher_step(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    current: MaterializedReduction,
    *,
    collect_samples: bool,
) -> tuple[
    AffineCandidate | None,
    MaterializedReduction | None,
    int,
    int,
    int,
    int,
    tuple[ResidualTeacherSample, ...],
]:
    feasible = _feasible_candidates(
        example,
        accepted,
    )
    if not feasible:
        return (
            None,
            None,
            0,
            0,
            0,
            0,
            (),
        )

    current_ops = current.solver_counts.arithmetic_ops
    best_candidate = None
    best_materialized = None
    best_gain = 0

    trials = 0
    successful = 0
    invalid = 0
    successful_solver_ops = 0
    samples: list[ResidualTeacherSample] = []

    for candidate in feasible:
        features = residual_state_features(
            example,
            accepted,
            current,
            candidate,
            feasible,
        )

        trials += 1
        materialized = materialize_reduction(
            example,
            tuple(accepted + (candidate,)),
        )

        if materialized is None:
            invalid += 1
            gain = 0
        else:
            successful += 1
            trial_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            successful_solver_ops += trial_ops
            gain = max(
                0,
                current_ops - trial_ops,
            )

            if (
                gain > best_gain
                or (
                    gain == best_gain
                    and gain > 0
                    and best_candidate is not None
                    and (
                        candidate.row_index,
                        _target_index(candidate),
                    )
                    < (
                        best_candidate.row_index,
                        _target_index(best_candidate),
                    )
                )
            ):
                best_candidate = candidate
                best_materialized = materialized
                best_gain = gain

        if collect_samples:
            target = (
                gain
                / max(1.0, float(current_ops))
            )
            samples.append(
                ResidualTeacherSample(
                    features=features,
                    target=float(target),
                )
            )

    return (
        best_candidate,
        best_materialized,
        trials,
        successful,
        invalid,
        successful_solver_ops,
        tuple(samples),
    )


def run_exact_residual_teacher(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
    collect_samples: bool = False,
) -> tuple[
    ExactResidualTeacherObservation,
    tuple[ResidualTeacherSample, ...],
]:
    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen_scorer,
    )
    accepted = tuple(initial.accepted_candidates)
    current = initial.materialized
    target_leaf_ops = (
        current.solver_counts.arithmetic_ops
    )
    residual_accepted = 0
    trials = 0
    successful = 0
    invalid = 0
    successful_solver_ops = 0
    all_samples: list[ResidualTeacherSample] = []

    while True:
        (
            best_candidate,
            best_materialized,
            step_trials,
            step_successful,
            step_invalid,
            step_successful_solver_ops,
            step_samples,
        ) = _teacher_step(
            example,
            accepted,
            current,
            collect_samples=collect_samples,
        )

        trials += step_trials
        successful += step_successful
        invalid += step_invalid
        successful_solver_ops += (
            step_successful_solver_ops
        )
        all_samples.extend(step_samples)

        if (
            best_candidate is None
            or best_materialized is None
        ):
            break

        accepted = accepted + (best_candidate,)
        current = best_materialized
        residual_accepted += 1

    final_ops = (
        current.solver_counts.arithmetic_ops
    )
    verified = (
        current.verified
        and current.ground_truth_equivalent
    )

    return (
        ExactResidualTeacherObservation(
            core_dimension=example.core_dimension,
            apparent_dimension=example.apparent_dimension,
            target_leaf_solver_ops=target_leaf_ops,
            final_solver_ops=final_ops,
            residual_additional_savings=(
                target_leaf_ops - final_ops
            ),
            accepted_residual_count=(
                residual_accepted
            ),
            exact_trials=trials,
            successful_trials=successful,
            invalid_trials=invalid,
            successful_trial_solver_ops=(
                successful_solver_ops
            ),
            final_verified=verified,
        ),
        tuple(all_samples),
    )


def build_teacher_training_matrix(
    examples: Iterable[LearnedCompressionExample],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[np.ndarray, np.ndarray]:
    samples: list[ResidualTeacherSample] = []

    for example in examples:
        observation, example_samples = (
            run_exact_residual_teacher(
                example,
                frozen_scorer=frozen_scorer,
                collect_samples=True,
            )
        )
        if not observation.final_verified:
            raise AssertionError(
                "teacher training example failed verification"
            )
        samples.extend(example_samples)

    if not samples:
        raise ValueError(
            "teacher corpus produced no candidate samples"
        )

    X = np.asarray(
        [sample.features for sample in samples],
        dtype=float,
    )
    y = np.asarray(
        [sample.target for sample in samples],
        dtype=float,
    )

    if X.shape[1] != RESIDUAL_FEATURE_DIMENSION:
        raise AssertionError(
            "teacher matrix feature dimension drift"
        )
    return X, y


def fit_residual_models(
    examples: Iterable[LearnedCompressionExample],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> FittedResidualModels:
    X, y = build_teacher_training_matrix(
        tuple(examples),
        frozen_scorer=frozen_scorer,
    )

    ridge = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "ridge",
                Ridge(
                    alpha=RIDGE_ALPHA,
                    random_state=None,
                ),
            ),
        ]
    )
    ridge.fit(X, y)

    mlp8 = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=(
                        MLP_HIDDEN_UNITS,
                    ),
                    activation="tanh",
                    solver="lbfgs",
                    alpha=MLP_ALPHA,
                    max_iter=1200,
                    random_state=MLP_RANDOM_STATE,
                ),
            ),
        ]
    )
    mlp8.fit(X, y)

    return FittedResidualModels(
        ridge=ridge,
        mlp8=mlp8,
        ridge_footprint=ResidualModelFootprint(
            method="ridge",
            input_dimension=(
                RESIDUAL_FEATURE_DIMENSION
            ),
            fitted_weight_bias_scalars=29,
            scaler_state_scalars=56,
            weighted_sum_terms_per_candidate=28,
        ),
        mlp8_footprint=ResidualModelFootprint(
            method="mlp8",
            input_dimension=(
                RESIDUAL_FEATURE_DIMENSION
            ),
            fitted_weight_bias_scalars=241,
            scaler_state_scalars=56,
            weighted_sum_terms_per_candidate=232,
        ),
        training_sample_count=int(X.shape[0]),
        positive_training_sample_count=int(
            np.count_nonzero(y > 0.0)
        ),
    )


def _active_heuristic_score(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    candidate: AffineCandidate,
    feasible: tuple[AffineCandidate, ...],
    *,
    method: str,
) -> float:
    system = example.full_system
    n = system.dimension
    removed_rows = {
        item.row_index
        for item in accepted
    }
    eliminated = {
        item.target
        for item in accepted
    }
    retained_rows = tuple(
        row_index
        for row_index in range(n)
        if row_index not in removed_rows
    )
    retained_variables = {
        variable
        for variable in system.variables
        if variable not in eliminated
    }
    retained_dimension = max(
        1,
        len(retained_variables),
    )

    row_nnz = sum(
        1
        for column, value in enumerate(
            system.A[candidate.row_index]
        )
        if (
            value != 0
            and system.variables[column]
            in retained_variables
        )
    )
    target_index = system.variables.index(
        candidate.target
    )
    target_count = sum(
        1
        for row_index in retained_rows
        if system.A[row_index][target_index] != 0
    )

    if method == "state_target_leaf":
        score = (
            1.0
            - target_count
            / max(1.0, float(len(retained_rows)))
        )
    elif method == "state_markowitz":
        markowitz_count = (
            max(0, row_nnz - 1)
            * max(0, target_count - 1)
        )
        score = 1.0 / (
            1.0 + float(markowitz_count)
        )
    else:
        raise ValueError(
            f"unknown residual heuristic: {method}"
        )

    return float(score)


def _policy_scores(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    current: MaterializedReduction,
    feasible: tuple[AffineCandidate, ...],
    *,
    method: str,
    models: FittedResidualModels | None,
) -> tuple[tuple[float, AffineCandidate], ...]:
    output: list[tuple[float, AffineCandidate]] = []

    if method in {
        "ridge",
        "mlp8",
    }:
        if models is None:
            raise ValueError(
                "learned residual policy requires fitted models"
            )
        X = np.asarray(
            [
                residual_state_features(
                    example,
                    accepted,
                    current,
                    candidate,
                    feasible,
                )
                for candidate in feasible
            ],
            dtype=float,
        )
        pipeline = (
            models.ridge
            if method == "ridge"
            else models.mlp8
        )
        predictions = pipeline.predict(X)

        for score, candidate in zip(
            predictions,
            feasible,
        ):
            output.append(
                (
                    float(score),
                    candidate,
                )
            )
    else:
        for candidate in feasible:
            output.append(
                (
                    _active_heuristic_score(
                        example,
                        accepted,
                        candidate,
                        feasible,
                        method=method,
                    ),
                    candidate,
                )
            )

    if not all(
        math.isfinite(score)
        for score, _ in output
    ):
        raise FloatingPointError(
            "non-finite residual policy score"
        )

    output.sort(
        key=lambda item: (
            -item[0],
            item[1].row_index,
            _target_index(item[1]),
        )
    )
    return tuple(output)


def run_bounded_residual_policy(
    example: LearnedCompressionExample,
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
    models: FittedResidualModels | None = None,
) -> ResidualPolicyObservation:
    if method not in POLICIES:
        raise ValueError(
            f"unknown residual policy: {method}"
        )

    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen_scorer,
    )
    accepted = tuple(initial.accepted_candidates)
    current = initial.materialized
    target_leaf_ops = (
        current.solver_counts.arithmetic_ops
    )
    accepted_residual = 0
    exact_trials = 0
    successful_trials = 0
    invalid_trials = 0
    nonpositive_trials = 0
    successful_trial_solver_ops = 0
    nonpositive_accepted_count = 0
    degraded_mode = False

    while True:
        feasible = _feasible_candidates(
            example,
            accepted,
        )
        if not feasible:
            break

        try:
            ranked = _policy_scores(
                example,
                accepted,
                current,
                feasible,
                method=method,
                models=models,
            )
        except (
            FloatingPointError,
            ValueError,
        ):
            if method in {
                "ridge",
                "mlp8",
            }:
                degraded_mode = True
                break
            raise

        accepted_this_state = False
        current_ops = (
            current.solver_counts.arithmetic_ops
        )

        for _, candidate in ranked[
            :TRIAL_BUDGET_PER_STATE
        ]:
            exact_trials += 1
            materialized = materialize_reduction(
                example,
                tuple(accepted + (candidate,)),
            )
            if materialized is None:
                invalid_trials += 1
                continue

            successful_trials += 1
            trial_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            successful_trial_solver_ops += trial_ops
            gain = current_ops - trial_ops

            if gain <= 0:
                nonpositive_trials += 1
                continue

            accepted = accepted + (candidate,)
            current = materialized
            accepted_residual += 1
            accepted_this_state = True
            break

        if not accepted_this_state:
            break

    final_ops = (
        current.solver_counts.arithmetic_ops
    )
    verified = (
        current.verified
        and current.ground_truth_equivalent
    )

    return ResidualPolicyObservation(
        method=method,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        target_leaf_solver_ops=target_leaf_ops,
        final_solver_ops=final_ops,
        residual_additional_savings=(
            target_leaf_ops - final_ops
        ),
        accepted_residual_count=(
            accepted_residual
        ),
        exact_trials=exact_trials,
        successful_trials=successful_trials,
        invalid_trials=invalid_trials,
        nonpositive_trials=nonpositive_trials,
        successful_trial_solver_ops=(
            successful_trial_solver_ops
        ),
        degraded_mode=degraded_mode,
        final_verified=verified,
        nonpositive_accepted_count=(
            nonpositive_accepted_count
        ),
    )


def _teacher_aggregate(
    rows: tuple[ExactResidualTeacherObservation, ...],
) -> dict[str, float | int]:
    return {
        "count": len(rows),
        "mean_final_solver_ops": mean(
            row.final_solver_ops
            for row in rows
        ),
        "mean_residual_additional_savings": mean(
            row.residual_additional_savings
            for row in rows
        ),
        "mean_exact_trials": mean(
            row.exact_trials
            for row in rows
        ),
        "mean_accepted_residual_count": mean(
            row.accepted_residual_count
            for row in rows
        ),
        "mean_successful_trial_solver_ops": mean(
            row.successful_trial_solver_ops
            for row in rows
        ),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
    }


def aggregate_policy_against_teacher(
    policy_rows: Iterable[ResidualPolicyObservation],
    teacher_rows: Iterable[ExactResidualTeacherObservation],
    *,
    fitted_parameter_count: int,
    scaler_state_count: int,
    weighted_sum_terms_per_candidate: int,
) -> dict[str, object]:
    policy = tuple(policy_rows)
    teacher = tuple(teacher_rows)
    if not policy or len(policy) != len(teacher):
        raise ValueError(
            "policy and teacher rows must be non-empty and aligned"
        )

    mean_policy_savings = mean(
        row.residual_additional_savings
        for row in policy
    )
    mean_teacher_savings = mean(
        row.residual_additional_savings
        for row in teacher
    )
    recovery = (
        mean_policy_savings / mean_teacher_savings
        if mean_teacher_savings > 0
        else None
    )

    mean_policy_trials = mean(
        row.exact_trials
        for row in policy
    )
    mean_teacher_trials = mean(
        row.exact_trials
        for row in teacher
    )
    trial_reduction = (
        1.0
        - mean_policy_trials / mean_teacher_trials
        if mean_teacher_trials > 0
        else 0.0
    )

    verified_retention = mean(
        1.0 if row.final_verified else 0.0
        for row in policy
    )
    unsafe = sum(
        0 if row.final_verified else row.accepted_residual_count
        for row in policy
    )
    nonpositive_accepted = sum(
        row.nonpositive_accepted_count
        for row in policy
    )

    adequate = (
        verified_retention == 1.0
        and unsafe == 0
        and nonpositive_accepted == 0
        and recovery is not None
        and recovery >= 0.80
        and trial_reduction >= 0.75
    )

    grouped: dict[
        tuple[int, int],
        list[int],
    ] = {}
    for index, row in enumerate(policy):
        grouped.setdefault(
            (
                row.core_dimension,
                row.apparent_dimension,
            ),
            [],
        ).append(index)

    cells = []
    for (k, n), indices in sorted(grouped.items()):
        cell_policy_savings = mean(
            policy[index].residual_additional_savings
            for index in indices
        )
        cell_teacher_savings = mean(
            teacher[index].residual_additional_savings
            for index in indices
        )
        cell_recovery = (
            cell_policy_savings / cell_teacher_savings
            if cell_teacher_savings > 0
            else None
        )
        cell_policy_trials = mean(
            policy[index].exact_trials
            for index in indices
        )
        cell_teacher_trials = mean(
            teacher[index].exact_trials
            for index in indices
        )
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(indices),
                "mean_final_solver_ops": mean(
                    policy[index].final_solver_ops
                    for index in indices
                ),
                "mean_policy_residual_savings": (
                    cell_policy_savings
                ),
                "mean_teacher_residual_savings": (
                    cell_teacher_savings
                ),
                "residual_savings_recovery": (
                    cell_recovery
                ),
                "mean_policy_exact_trials": (
                    cell_policy_trials
                ),
                "mean_teacher_exact_trials": (
                    cell_teacher_trials
                ),
                "exact_trial_reduction": (
                    1.0
                    - cell_policy_trials
                    / cell_teacher_trials
                    if cell_teacher_trials > 0
                    else 0.0
                ),
            }
        )

    return {
        "method": policy[0].method,
        "count": len(policy),
        "mean_target_leaf_solver_ops": mean(
            row.target_leaf_solver_ops
            for row in policy
        ),
        "mean_final_solver_ops": mean(
            row.final_solver_ops
            for row in policy
        ),
        "mean_residual_additional_savings": (
            mean_policy_savings
        ),
        "mean_teacher_residual_additional_savings": (
            mean_teacher_savings
        ),
        "residual_savings_recovery": recovery,
        "mean_exact_trials": mean_policy_trials,
        "mean_teacher_exact_trials": (
            mean_teacher_trials
        ),
        "exact_trial_reduction": (
            trial_reduction
        ),
        "mean_accepted_residual_count": mean(
            row.accepted_residual_count
            for row in policy
        ),
        "mean_invalid_trials": mean(
            row.invalid_trials
            for row in policy
        ),
        "mean_nonpositive_trials": mean(
            row.nonpositive_trials
            for row in policy
        ),
        "mean_successful_trial_solver_ops": mean(
            row.successful_trial_solver_ops
            for row in policy
        ),
        "verified_retention": (
            verified_retention
        ),
        "unsafe_accepted_reduction_count": (
            unsafe
        ),
        "nonpositive_accepted_count": (
            nonpositive_accepted
        ),
        "degraded_mode_count": sum(
            1
            for row in policy
            if row.degraded_mode
        ),
        "fitted_parameter_count": (
            fitted_parameter_count
        ),
        "scaler_state_count": (
            scaler_state_count
        ),
        "weighted_sum_terms_per_candidate": (
            weighted_sum_terms_per_candidate
        ),
        "adequate": adequate,
        "cells": cells,
    }


def evaluate_teacher(
    examples: Iterable[LearnedCompressionExample],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[ExactResidualTeacherObservation, ...]:
    return tuple(
        run_exact_residual_teacher(
            example,
            frozen_scorer=frozen_scorer,
            collect_samples=False,
        )[0]
        for example in examples
    )


def evaluate_policy(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
    models: FittedResidualModels | None,
) -> tuple[ResidualPolicyObservation, ...]:
    return tuple(
        run_bounded_residual_policy(
            example,
            method,
            frozen_scorer=frozen_scorer,
            models=models,
        )
        for example in examples
    )


def policy_footprint(
    method: str,
    models: FittedResidualModels,
) -> ResidualModelFootprint:
    if method in {
        "state_target_leaf",
        "state_markowitz",
    }:
        return ResidualModelFootprint(
            method=method,
            input_dimension=0,
            fitted_weight_bias_scalars=0,
            scaler_state_scalars=0,
            weighted_sum_terms_per_candidate=0,
        )
    if method == "ridge":
        return models.ridge_footprint
    if method == "mlp8":
        return models.mlp8_footprint
    raise ValueError(
        f"unknown residual policy: {method}"
    )


def select_smallest_adequate_policy(
    validation_aggregates: dict[
        str,
        dict[str, object],
    ],
) -> str | None:
    deterministic = [
        method
        for method in (
            "state_target_leaf",
            "state_markowitz",
        )
        if bool(
            validation_aggregates[method][
                "adequate"
            ]
        )
    ]
    if deterministic:
        fixed_order = {
            "state_target_leaf": 0,
            "state_markowitz": 1,
        }
        return min(
            deterministic,
            key=lambda method: (
                float(
                    validation_aggregates[method][
                        "mean_exact_trials"
                    ]
                ),
                float(
                    validation_aggregates[method][
                        "mean_final_solver_ops"
                    ]
                ),
                fixed_order[method],
            ),
        )

    if bool(
        validation_aggregates["ridge"][
            "adequate"
        ]
    ):
        return "ridge"

    if bool(
        validation_aggregates["mlp8"][
            "adequate"
        ]
    ):
        return "mlp8"

    return None


def teacher_aggregate(
    rows: Iterable[ExactResidualTeacherObservation],
) -> dict[str, float | int]:
    return _teacher_aggregate(tuple(rows))
