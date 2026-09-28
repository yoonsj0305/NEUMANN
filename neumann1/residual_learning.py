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
    score_candidates,
)
from .structural_compression import (
    solve_exact_gauss_jordan,
)


RESIDUAL_FEATURE_DIMENSION = 22
LEARNED_THRESHOLD_GRID = (
    -0.05,
    0.00,
    0.01,
    0.02,
    0.05,
    0.10,
    0.20,
)
DETERMINISTIC_THRESHOLD_GRID = tuple(
    i / 20.0
    for i in range(1, 20)
)
DETERMINISTIC_RESIDUAL_METHODS = (
    "target_leaf",
    "markowitz",
    "dependency_contrast",
    "structural_combo",
)
LEARNED_RESIDUAL_METHODS = (
    "ridge",
    "tiny_mlp",
)
MLP_HIDDEN_UNITS = 8
MLP_RANDOM_STATE = 37
RIDGE_ALPHA = 1.0


@dataclass(frozen=True)
class ResidualTeacherRow:
    features: tuple[float, ...]
    target: float
    exact_gain: int
    valid: bool


@dataclass(frozen=True)
class ResidualTeacherTrace:
    initial_target_leaf_count: int
    residual_added_count: int
    target_leaf_solver_ops: int
    final_solver_ops: int
    residual_additional_savings: int
    trial_materializations: int
    successful_trial_materializations: int
    invalid_trial_materializations: int
    successful_trial_solver_ops: int
    rows: tuple[ResidualTeacherRow, ...]
    final_materialized: MaterializedReduction


@dataclass(frozen=True)
class ResidualModelFootprint:
    method: str
    input_feature_dimension: int
    fitted_weight_bias_scalars: int
    scaler_state_scalars: int
    weighted_sum_terms_per_candidate: int
    hidden_units: int


@dataclass(frozen=True)
class ResidualPolicyObservation:
    method: str
    threshold: float
    core_dimension: int
    apparent_dimension: int
    target_leaf_solver_ops: int
    final_solver_ops: int
    residual_additional_savings: int
    target_leaf_accepted_count: int
    residual_accepted_count: int
    attempted_proposals: int
    candidate_scores_computed: int
    final_verified: bool
    unsafe_accepted_reductions: int


@dataclass(frozen=True)
class ResidualCalibration:
    method: str
    threshold: float
    mean_residual_additional_savings: float
    mean_final_solver_ops: float
    mean_attempted_proposals: float


@dataclass(frozen=True)
class ResidualModelSelection:
    learned_method: str
    learned_threshold: float
    learned_validation_recovery: float | None
    learned_validation_status: str
    best_learned_validation_recovery: float | None
    deterministic_method: str
    deterministic_threshold: float
    deterministic_validation_recovery: float | None
    teacher_validation_additional_savings: float


class ResidualRegressor:
    def __init__(self, method: str) -> None:
        if method not in LEARNED_RESIDUAL_METHODS:
            raise ValueError(
                f"unknown residual regressor: {method}"
            )
        self.method = method
        if method == "ridge":
            estimator = Ridge(
                alpha=RIDGE_ALPHA,
                fit_intercept=True,
            )
        else:
            estimator = MLPRegressor(
                hidden_layer_sizes=(MLP_HIDDEN_UNITS,),
                activation="tanh",
                solver="lbfgs",
                alpha=1e-3,
                max_iter=1600,
                random_state=MLP_RANDOM_STATE,
            )
        self.pipeline = Pipeline(
            [
                ("scale", StandardScaler()),
                ("regressor", estimator),
            ]
        )

    def fit(
        self,
        rows: Iterable[ResidualTeacherRow],
    ) -> "ResidualRegressor":
        rows = tuple(rows)
        if not rows:
            raise ValueError(
                "residual training rows are required"
            )
        X = np.asarray(
            [row.features for row in rows],
            dtype=float,
        )
        y = np.asarray(
            [row.target for row in rows],
            dtype=float,
        )
        self.pipeline.fit(X, y)
        return self

    def predict(
        self,
        features: Iterable[tuple[float, ...]],
    ) -> tuple[float, ...]:
        X = tuple(features)
        if not X:
            return ()
        values = self.pipeline.predict(
            np.asarray(X, dtype=float)
        )
        return tuple(
            float(value)
            for value in values
        )


def _target_index(
    candidate: AffineCandidate,
) -> int:
    return int(candidate.target[1:])


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def _candidate_pool(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
) -> tuple[AffineCandidate, ...]:
    candidates = enumerate_affine_candidates(
        example.full_system
    )
    output = [
        candidate
        for candidate in candidates
        if not any(
            candidate.row_index == chosen.row_index
            or candidate.target == chosen.target
            for chosen in accepted
        )
    ]
    output.sort(
        key=lambda candidate: (
            candidate.row_index,
            _target_index(candidate),
        )
    )
    return tuple(output)


def residual_state_features(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    current_materialized: MaterializedReduction,
    candidate: AffineCandidate,
    *,
    feasible_candidate_count: int,
    initial_candidate_count: int,
    baseline_solver_ops: int,
) -> tuple[float, ...]:
    base = candidate_features(
        example.full_system,
        candidate,
    )
    n = float(example.full_system.dimension)
    accepted_targets = {
        item.target
        for item in accepted
    }
    dependency_names = {
        name
        for name, _ in candidate.coefficients
    }

    accepted_fraction = len(accepted) / n
    current_solver_fraction = (
        current_materialized.solver_counts.arithmetic_ops
        / max(1.0, float(baseline_solver_ops))
    )
    feasible_fraction = (
        feasible_candidate_count
        / max(1.0, float(initial_candidate_count))
    )
    dependency_eliminated_fraction = (
        len(
            dependency_names.intersection(
                accepted_targets
            )
        )
        / max(1.0, float(len(dependency_names)))
    )

    accepted_using_target = sum(
        1
        for item in accepted
        if candidate.target
        in {
            name
            for name, _ in item.coefficients
        }
    )
    accepted_depend_on_target_fraction = (
        accepted_using_target
        / max(1.0, float(len(accepted)))
    )
    target_used_by_any_accepted = (
        1.0
        if accepted_using_target
        else 0.0
    )

    features = base + (
        accepted_fraction,
        current_solver_fraction,
        feasible_fraction,
        dependency_eliminated_fraction,
        accepted_depend_on_target_fraction,
        target_used_by_any_accepted,
    )
    if len(features) != RESIDUAL_FEATURE_DIMENSION:
        raise AssertionError(
            "residual feature dimension drift"
        )
    if not all(math.isfinite(value) for value in features):
        raise ValueError(
            "non-finite residual state feature"
        )
    return tuple(float(value) for value in features)


def residual_teacher_trace(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
    collect_rows: bool,
) -> ResidualTeacherTrace:
    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen_scorer,
    )
    accepted = tuple(initial.accepted_candidates)
    current = initial.materialized
    target_leaf_ops = (
        current.solver_counts.arithmetic_ops
    )
    baseline_ops = _baseline_solver_ops(example)
    initial_candidate_count = len(
        enumerate_affine_candidates(
            example.full_system
        )
    )

    rows: list[ResidualTeacherRow] = []
    trials = 0
    successful = 0
    invalid = 0
    successful_solver_ops = 0
    added = 0

    while True:
        pool = _candidate_pool(
            example,
            accepted,
        )
        if not pool:
            break

        current_ops = (
            current.solver_counts.arithmetic_ops
        )
        best_candidate = None
        best_materialized = None
        best_gain = 0

        for candidate in pool:
            trials += 1
            features = residual_state_features(
                example,
                accepted,
                current,
                candidate,
                feasible_candidate_count=len(pool),
                initial_candidate_count=(
                    initial_candidate_count
                ),
                baseline_solver_ops=baseline_ops,
            )
            tentative = materialize_reduction(
                example,
                accepted + (candidate,),
            )
            if tentative is None:
                invalid += 1
                gain = 0
                target = -1.0
                valid = False
            else:
                successful += 1
                trial_ops = (
                    tentative.solver_counts.arithmetic_ops
                )
                successful_solver_ops += trial_ops
                gain = current_ops - trial_ops
                target = max(
                    -1.0,
                    min(
                        1.0,
                        gain / max(1.0, float(current_ops)),
                    ),
                )
                valid = True

            if collect_rows:
                rows.append(
                    ResidualTeacherRow(
                        features=features,
                        target=float(target),
                        exact_gain=int(gain),
                        valid=valid,
                    )
                )

            if tentative is not None and (
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
                best_materialized = tentative
                best_gain = gain

        if (
            best_candidate is None
            or best_materialized is None
            or best_gain <= 0
        ):
            break

        accepted = accepted + (best_candidate,)
        current = best_materialized
        added += 1

    final_ops = current.solver_counts.arithmetic_ops
    return ResidualTeacherTrace(
        initial_target_leaf_count=len(
            initial.accepted_candidates
        ),
        residual_added_count=added,
        target_leaf_solver_ops=target_leaf_ops,
        final_solver_ops=final_ops,
        residual_additional_savings=(
            target_leaf_ops - final_ops
        ),
        trial_materializations=trials,
        successful_trial_materializations=successful,
        invalid_trial_materializations=invalid,
        successful_trial_solver_ops=(
            successful_solver_ops
        ),
        rows=tuple(rows),
        final_materialized=current,
    )


def build_residual_training_rows(
    examples: Iterable[LearnedCompressionExample],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[ResidualTeacherRow, ...]:
    rows: list[ResidualTeacherRow] = []
    for example in examples:
        trace = residual_teacher_trace(
            example,
            frozen_scorer=frozen_scorer,
            collect_rows=True,
        )
        rows.extend(trace.rows)
    if not rows:
        raise ValueError(
            "residual teacher produced no training rows"
        )
    return tuple(rows)


def fit_residual_models(
    examples: Iterable[LearnedCompressionExample],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[
    dict[str, ResidualRegressor],
    tuple[ResidualTeacherRow, ...],
]:
    rows = build_residual_training_rows(
        examples,
        frozen_scorer=frozen_scorer,
    )
    models = {
        method: ResidualRegressor(method).fit(rows)
        for method in LEARNED_RESIDUAL_METHODS
    }
    return models, rows


def inspect_residual_model(
    model: ResidualRegressor,
) -> ResidualModelFootprint:
    scaler: StandardScaler = (
        model.pipeline.named_steps["scale"]
    )
    estimator = model.pipeline.named_steps[
        "regressor"
    ]
    scaler_state = int(
        scaler.mean_.size
        + scaler.scale_.size
    )

    if model.method == "ridge":
        parameter_count = int(
            estimator.coef_.size + 1
        )
        weighted_sum_terms = int(
            estimator.coef_.size
        )
        hidden_units = 0
    else:
        parameter_count = sum(
            int(weights.size)
            for weights in estimator.coefs_
        ) + sum(
            int(bias.size)
            for bias in estimator.intercepts_
        )
        weighted_sum_terms = sum(
            int(weights.size)
            for weights in estimator.coefs_
        )
        hidden_units = MLP_HIDDEN_UNITS

    return ResidualModelFootprint(
        method=model.method,
        input_feature_dimension=(
            RESIDUAL_FEATURE_DIMENSION
        ),
        fitted_weight_bias_scalars=parameter_count,
        scaler_state_scalars=scaler_state,
        weighted_sum_terms_per_candidate=(
            weighted_sum_terms
        ),
        hidden_units=hidden_units,
    )


def observe_learned_residual_policy(
    example: LearnedCompressionExample,
    model: ResidualRegressor,
    threshold: float,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualPolicyObservation:
    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen_scorer,
    )
    accepted = tuple(initial.accepted_candidates)
    current = initial.materialized
    target_leaf_ops = (
        current.solver_counts.arithmetic_ops
    )
    baseline_ops = _baseline_solver_ops(example)
    initial_candidate_count = len(
        enumerate_affine_candidates(
            example.full_system
        )
    )

    residual_accepted = 0
    attempts = 0
    scores_computed = 0

    while True:
        pool = _candidate_pool(
            example,
            accepted,
        )
        if not pool:
            break

        features = [
            residual_state_features(
                example,
                accepted,
                current,
                candidate,
                feasible_candidate_count=len(pool),
                initial_candidate_count=(
                    initial_candidate_count
                ),
                baseline_solver_ops=baseline_ops,
            )
            for candidate in pool
        ]
        predictions = model.predict(features)
        scores_computed += len(pool)

        ranked = sorted(
            zip(pool, predictions),
            key=lambda item: (
                -item[1],
                item[0].row_index,
                _target_index(item[0]),
            ),
        )

        state_advanced = False
        for candidate, score in ranked:
            if score < threshold:
                break
            attempts += 1
            tentative = materialize_reduction(
                example,
                accepted + (candidate,),
            )
            if tentative is None:
                continue
            accepted = accepted + (candidate,)
            current = tentative
            residual_accepted += 1
            state_advanced = True
            break

        if not state_advanced:
            break

    final_verified = (
        current.verified
        and current.ground_truth_equivalent
    )
    final_ops = current.solver_counts.arithmetic_ops
    return ResidualPolicyObservation(
        method=model.method,
        threshold=threshold,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        target_leaf_solver_ops=target_leaf_ops,
        final_solver_ops=final_ops,
        residual_additional_savings=(
            target_leaf_ops - final_ops
        ),
        target_leaf_accepted_count=len(
            initial.accepted_candidates
        ),
        residual_accepted_count=residual_accepted,
        attempted_proposals=attempts,
        candidate_scores_computed=scores_computed,
        final_verified=final_verified,
        unsafe_accepted_reductions=(
            0
            if final_verified
            else residual_accepted
        ),
    )


def observe_deterministic_residual_policy(
    example: LearnedCompressionExample,
    method: str,
    threshold: float,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualPolicyObservation:
    if method not in DETERMINISTIC_RESIDUAL_METHODS:
        raise ValueError(
            f"unknown deterministic residual method: {method}"
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

    scored = score_candidates(
        example,
        method,
        frozen_scorer=frozen_scorer,
    )
    score_map = {
        item.candidate.key: item.score
        for item in scored
    }

    residual_accepted = 0
    attempts = 0
    scores_computed = 0

    while True:
        pool = _candidate_pool(
            example,
            accepted,
        )
        if not pool:
            break
        ranked = sorted(
            (
                (
                    candidate,
                    score_map[candidate.key],
                )
                for candidate in pool
            ),
            key=lambda item: (
                -item[1],
                item[0].row_index,
                _target_index(item[0]),
            ),
        )
        scores_computed += len(pool)

        state_advanced = False
        for candidate, score in ranked:
            if score < threshold:
                break
            attempts += 1
            tentative = materialize_reduction(
                example,
                accepted + (candidate,),
            )
            if tentative is None:
                continue
            accepted = accepted + (candidate,)
            current = tentative
            residual_accepted += 1
            state_advanced = True
            break

        if not state_advanced:
            break

    final_verified = (
        current.verified
        and current.ground_truth_equivalent
    )
    final_ops = current.solver_counts.arithmetic_ops
    return ResidualPolicyObservation(
        method=method,
        threshold=threshold,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        target_leaf_solver_ops=target_leaf_ops,
        final_solver_ops=final_ops,
        residual_additional_savings=(
            target_leaf_ops - final_ops
        ),
        target_leaf_accepted_count=len(
            initial.accepted_candidates
        ),
        residual_accepted_count=residual_accepted,
        attempted_proposals=attempts,
        candidate_scores_computed=scores_computed,
        final_verified=final_verified,
        unsafe_accepted_reductions=(
            0
            if final_verified
            else residual_accepted
        ),
    )


def observe_exact_residual_teacher(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualPolicyObservation:
    trace = residual_teacher_trace(
        example,
        frozen_scorer=frozen_scorer,
        collect_rows=False,
    )
    verified = (
        trace.final_materialized.verified
        and trace.final_materialized.ground_truth_equivalent
    )
    return ResidualPolicyObservation(
        method="exact_residual_teacher",
        threshold=0.0,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        target_leaf_solver_ops=(
            trace.target_leaf_solver_ops
        ),
        final_solver_ops=trace.final_solver_ops,
        residual_additional_savings=(
            trace.residual_additional_savings
        ),
        target_leaf_accepted_count=(
            trace.initial_target_leaf_count
        ),
        residual_accepted_count=(
            trace.residual_added_count
        ),
        attempted_proposals=(
            trace.trial_materializations
        ),
        candidate_scores_computed=(
            trace.trial_materializations
        ),
        final_verified=verified,
        unsafe_accepted_reductions=(
            0
            if verified
            else trace.residual_added_count
        ),
    )


def aggregate_residual_policy(
    rows: Iterable[ResidualPolicyObservation],
) -> dict[str, object]:
    rows = tuple(rows)
    if not rows:
        raise ValueError(
            "at least one residual policy observation is required"
        )

    grouped: dict[
        tuple[int, int],
        list[ResidualPolicyObservation],
    ] = {}
    for row in rows:
        grouped.setdefault(
            (
                row.core_dimension,
                row.apparent_dimension,
            ),
            [],
        ).append(row)

    cells = []
    for (k, n), cell_rows in sorted(grouped.items()):
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(cell_rows),
                "mean_target_leaf_solver_ops": mean(
                    row.target_leaf_solver_ops
                    for row in cell_rows
                ),
                "mean_final_solver_ops": mean(
                    row.final_solver_ops
                    for row in cell_rows
                ),
                "mean_residual_additional_savings": mean(
                    row.residual_additional_savings
                    for row in cell_rows
                ),
                "mean_residual_accepted_count": mean(
                    row.residual_accepted_count
                    for row in cell_rows
                ),
                "verified_retention": mean(
                    1.0 if row.final_verified else 0.0
                    for row in cell_rows
                ),
            }
        )

    return {
        "method": rows[0].method,
        "threshold": rows[0].threshold,
        "count": len(rows),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            row.unsafe_accepted_reductions
            for row in rows
        ),
        "mean_target_leaf_solver_ops": mean(
            row.target_leaf_solver_ops
            for row in rows
        ),
        "mean_final_solver_ops": mean(
            row.final_solver_ops
            for row in rows
        ),
        "mean_residual_additional_savings": mean(
            row.residual_additional_savings
            for row in rows
        ),
        "mean_target_leaf_accepted_count": mean(
            row.target_leaf_accepted_count
            for row in rows
        ),
        "mean_residual_accepted_count": mean(
            row.residual_accepted_count
            for row in rows
        ),
        "mean_attempted_proposals": mean(
            row.attempted_proposals
            for row in rows
        ),
        "mean_candidate_scores_computed": mean(
            row.candidate_scores_computed
            for row in rows
        ),
        "cells": cells,
    }


def _calibration_from_rows(
    method: str,
    threshold: float,
    rows: tuple[ResidualPolicyObservation, ...],
) -> ResidualCalibration:
    return ResidualCalibration(
        method=method,
        threshold=threshold,
        mean_residual_additional_savings=mean(
            row.residual_additional_savings
            for row in rows
        ),
        mean_final_solver_ops=mean(
            row.final_solver_ops
            for row in rows
        ),
        mean_attempted_proposals=mean(
            row.attempted_proposals
            for row in rows
        ),
    )


def calibrate_learned_residual(
    examples: Iterable[LearnedCompressionExample],
    model: ResidualRegressor,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualCalibration:
    examples = tuple(examples)
    candidates: list[ResidualCalibration] = []
    for threshold in LEARNED_THRESHOLD_GRID:
        rows = tuple(
            observe_learned_residual_policy(
                example,
                model,
                threshold,
                frozen_scorer=frozen_scorer,
            )
            for example in examples
        )
        candidates.append(
            _calibration_from_rows(
                model.method,
                threshold,
                rows,
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.mean_residual_additional_savings,
            -item.mean_final_solver_ops,
            -item.mean_attempted_proposals,
            item.threshold,
        ),
    )


def calibrate_deterministic_residual(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualCalibration:
    examples = tuple(examples)
    candidates: list[ResidualCalibration] = []
    for threshold in DETERMINISTIC_THRESHOLD_GRID:
        rows = tuple(
            observe_deterministic_residual_policy(
                example,
                method,
                threshold,
                frozen_scorer=frozen_scorer,
            )
            for example in examples
        )
        candidates.append(
            _calibration_from_rows(
                method,
                threshold,
                rows,
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.mean_residual_additional_savings,
            -item.mean_final_solver_ops,
            -item.mean_attempted_proposals,
            item.threshold,
        ),
    )


def _recovery(
    savings: float,
    teacher_value: float,
) -> float | None:
    if teacher_value <= 0:
        return None
    return savings / teacher_value


def select_residual_models(
    validation_examples: Iterable[
        LearnedCompressionExample
    ],
    models: dict[str, ResidualRegressor],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[
    ResidualModelSelection,
    dict[str, ResidualCalibration],
    dict[str, ResidualCalibration],
]:
    validation_examples = tuple(
        validation_examples
    )

    teacher_rows = tuple(
        observe_exact_residual_teacher(
            example,
            frozen_scorer=frozen_scorer,
        )
        for example in validation_examples
    )
    teacher_value = mean(
        row.residual_additional_savings
        for row in teacher_rows
    )

    learned_calibrations = {
        method: calibrate_learned_residual(
            validation_examples,
            models[method],
            frozen_scorer=frozen_scorer,
        )
        for method in LEARNED_RESIDUAL_METHODS
    }
    learned_recoveries = {
        method: _recovery(
            calibration.mean_residual_additional_savings,
            teacher_value,
        )
        for method, calibration
        in learned_calibrations.items()
    }

    finite_learned = {
        method: recovery
        for method, recovery in learned_recoveries.items()
        if recovery is not None
    }
    if finite_learned:
        best_learned_recovery = max(
            finite_learned.values()
        )
    else:
        best_learned_recovery = None

    adequate_methods = []
    for method in LEARNED_RESIDUAL_METHODS:
        recovery = learned_recoveries[method]
        if (
            recovery is not None
            and recovery >= 0.70
            and best_learned_recovery is not None
            and recovery >= best_learned_recovery - 0.05
        ):
            adequate_methods.append(method)

    if "ridge" in adequate_methods:
        learned_method = "ridge"
        learned_status = "ADEQUATE"
    elif "tiny_mlp" in adequate_methods:
        learned_method = "tiny_mlp"
        learned_status = "ADEQUATE"
    else:
        learned_method = max(
            LEARNED_RESIDUAL_METHODS,
            key=lambda method: (
                learned_recoveries[method]
                if learned_recoveries[method] is not None
                else float("-inf")
            ),
        )
        learned_status = "INADEQUATE"

    deterministic_calibrations = {
        method: calibrate_deterministic_residual(
            validation_examples,
            method,
            frozen_scorer=frozen_scorer,
        )
        for method in DETERMINISTIC_RESIDUAL_METHODS
    }
    deterministic_method = max(
        DETERMINISTIC_RESIDUAL_METHODS,
        key=lambda method: (
            deterministic_calibrations[method]
            .mean_residual_additional_savings,
            -deterministic_calibrations[method]
            .mean_final_solver_ops,
            -deterministic_calibrations[method]
            .mean_attempted_proposals,
            method,
        ),
    )
    deterministic_recovery = _recovery(
        deterministic_calibrations[
            deterministic_method
        ].mean_residual_additional_savings,
        teacher_value,
    )

    selected_learned = learned_calibrations[
        learned_method
    ]
    selection = ResidualModelSelection(
        learned_method=learned_method,
        learned_threshold=(
            selected_learned.threshold
        ),
        learned_validation_recovery=(
            learned_recoveries[learned_method]
        ),
        learned_validation_status=learned_status,
        best_learned_validation_recovery=(
            best_learned_recovery
        ),
        deterministic_method=(
            deterministic_method
        ),
        deterministic_threshold=(
            deterministic_calibrations[
                deterministic_method
            ].threshold
        ),
        deterministic_validation_recovery=(
            deterministic_recovery
        ),
        teacher_validation_additional_savings=(
            teacher_value
        ),
    )
    return (
        selection,
        learned_calibrations,
        deterministic_calibrations,
    )


def final_learned_value_decision(
    *,
    learned_additional_savings: float,
    deterministic_additional_savings: float,
    teacher_additional_savings: float,
    learned_verified_retention: float,
    learned_unsafe_count: int,
    deterministic_recovery: float | None,
) -> dict[str, object]:
    if teacher_additional_savings > 0:
        learned_recovery: float | None = (
            learned_additional_savings
            / teacher_additional_savings
        )
        learned_advantage_fraction: float | None = (
            (
                learned_additional_savings
                - deterministic_additional_savings
            )
            / teacher_additional_savings
        )
    else:
        learned_recovery = None
        learned_advantage_fraction = None

    keep_learned = (
        learned_recovery is not None
        and learned_recovery >= 0.70
        and learned_advantage_fraction is not None
        and learned_advantage_fraction >= 0.10
        and learned_verified_retention == 1.0
        and learned_unsafe_count == 0
    )

    if keep_learned:
        decision = "KEEP_LEARNED_RESIDUAL"
    elif (
        deterministic_recovery is not None
        and deterministic_recovery >= 0.70
    ):
        decision = "KEEP_DETERMINISTIC_RESIDUAL"
    else:
        decision = "HOLD_RESIDUAL_MODELING"

    return {
        "learned_recovery": learned_recovery,
        "learned_advantage_fraction": (
            learned_advantage_fraction
        ),
        "decision": decision,
        "gate_learned_recovery_ge_0_70": (
            learned_recovery is not None
            and learned_recovery >= 0.70
        ),
        "gate_learned_advantage_fraction_ge_0_10": (
            learned_advantage_fraction is not None
            and learned_advantage_fraction >= 0.10
        ),
        "gate_learned_verified_retention_1": (
            learned_verified_retention == 1.0
        ),
        "gate_learned_unsafe_0": (
            learned_unsafe_count == 0
        ),
    }
