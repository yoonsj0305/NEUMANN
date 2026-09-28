from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from statistics import mean
from typing import Iterable

import numpy as np
from sklearn.tree import DecisionTreeRegressor

from .learned_compression import (
    AffineCandidate,
    CheckerResult,
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
from .stopping_gauntlet import FrozenV033Scorer
from .structural_compression import solve_exact_gauss_jordan


RESIDUAL_FEATURE_DIMENSION = 30
TREE_DEPTHS = (2, 3, 4, 6)
TREE_MIN_SAMPLES_LEAF = 16
TREE_RANDOM_STATE = 37

LEARNED_THRESHOLD_GRID = (
    0.0,
    0.001,
    0.0025,
    0.005,
    0.01,
    0.02,
    0.05,
    0.10,
)
DETERMINISTIC_THRESHOLD_GRID = tuple(
    i / 20.0
    for i in range(1, 20)
)
DETERMINISTIC_METHODS = (
    "residual_target_leaf",
    "residual_markowitz",
    "residual_dependency_contrast",
    "residual_structural_combo",
    "residual_random",
)


@dataclass(frozen=True)
class ResidualInitialState:
    example: LearnedCompressionExample
    target_leaf: CheckerResult
    baseline_solver_ops: int

    @property
    def accepted(self) -> tuple[AffineCandidate, ...]:
        return self.target_leaf.accepted_candidates

    @property
    def materialized(self) -> MaterializedReduction:
        return self.target_leaf.materialized


@dataclass(frozen=True)
class ResidualTrainingRow:
    features: tuple[float, ...]
    relative_vor: float


@dataclass(frozen=True)
class ResidualTreeModel:
    regressor: DecisionTreeRegressor
    feature_dimension: int
    requested_max_depth: int
    fitted_depth: int
    fitted_node_count: int
    fitted_leaf_count: int


@dataclass(frozen=True)
class ResidualPolicyCalibration:
    method: str
    threshold: float
    mean_residual_additional_savings: float
    mean_final_solver_ops: float
    mean_proposal_materializations: float


@dataclass(frozen=True)
class ResidualPolicyObservation:
    method: str
    threshold: float | None
    core_dimension: int
    apparent_dimension: int
    baseline_solver_ops: int
    target_leaf_solver_ops: int
    final_solver_ops: int
    target_leaf_accepted_count: int
    residual_accepted_count: int
    residual_additional_solver_savings: int
    total_solver_savings: int
    candidate_score_evaluations: int
    decision_node_comparisons: int
    proposal_materializations: int
    invalid_rejections: int
    nonpositive_rejections: int
    final_verified: bool


def _candidate_key(
    candidate: AffineCandidate,
) -> tuple[int, int]:
    return (
        candidate.row_index,
        int(candidate.target[1:]),
    )


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def prepare_initial_state(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualInitialState:
    return ResidualInitialState(
        example=example,
        target_leaf=target_leaf_checked(
            example,
            frozen_scorer=frozen_scorer,
        ),
        baseline_solver_ops=_baseline_solver_ops(
            example
        ),
    )


def _accepted_row_indices(
    accepted: tuple[AffineCandidate, ...],
) -> set[int]:
    return {
        candidate.row_index
        for candidate in accepted
    }


def _retained_variable_set(
    materialized: MaterializedReduction,
) -> set[str]:
    return set(
        materialized.retained_system.variables
    )


def _remaining_rows(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
) -> tuple[int, ...]:
    removed = _accepted_row_indices(accepted)
    return tuple(
        row_index
        for row_index in range(
            example.full_system.dimension
        )
        if row_index not in removed
    )


def _column_incidence(
    example: LearnedCompressionExample,
    rows: tuple[int, ...],
    name: str,
    *,
    retained_variables: set[str] | None = None,
) -> int:
    if (
        retained_variables is not None
        and name not in retained_variables
    ):
        return 0
    column = example.full_system.variables.index(name)
    return sum(
        1
        for row_index in rows
        if example.full_system.A[
            row_index
        ][column] != 0
    )


def residual_state_features(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    materialized: MaterializedReduction,
    candidate: AffineCandidate,
) -> tuple[float, ...]:
    system = example.full_system
    n = system.dimension
    retained_variables = _retained_variable_set(
        materialized
    )
    retained_dimension = max(
        1,
        materialized.retained_system.dimension,
    )
    rows = _remaining_rows(
        example,
        accepted,
    )

    target_current = _column_incidence(
        example,
        rows,
        candidate.target,
        retained_variables=retained_variables,
    )
    target_original = _column_incidence(
        example,
        tuple(range(n)),
        candidate.target,
    )

    dependency_names = tuple(
        name
        for name, _ in candidate.coefficients
    )
    dependency_current = tuple(
        _column_incidence(
            example,
            rows,
            name,
            retained_variables=retained_variables,
        )
        for name in dependency_names
    )
    dependency_original = tuple(
        _column_incidence(
            example,
            tuple(range(n)),
            name,
        )
        for name in dependency_names
    )

    dep_current_mean = mean(
        dependency_current
    )
    dep_current_max = max(
        dependency_current
    )
    dep_current_min = min(
        dependency_current
    )
    dep_incidence_reduction_mean = mean(
        original - current
        for original, current
        in zip(
            dependency_original,
            dependency_current,
        )
    )

    candidate_row = system.A[
        candidate.row_index
    ]
    row_retained_nnz = sum(
        1
        for variable in retained_variables
        if candidate_row[
            system.variables.index(variable)
        ] != 0
    )

    retained_dependency_count = sum(
        1
        for name in dependency_names
        if name in retained_variables
    )
    dependency_count = len(
        dependency_names
    )

    current_solver_ops = (
        materialized.solver_counts.arithmetic_ops
    )
    static_scale = max(
        1,
        n ** 3,
    )

    state_features = (
        retained_dimension / n,
        len(accepted) / n,
        current_solver_ops / static_scale,
        math.log1p(current_solver_ops)
        / math.log1p(1 + static_scale),
        target_current / retained_dimension,
        row_retained_nnz / retained_dimension,
        dep_current_mean / retained_dimension,
        dep_current_max / retained_dimension,
        dep_current_min / retained_dimension,
        (
            target_current
            - dep_current_mean
        )
        / retained_dimension,
        retained_dependency_count
        / dependency_count,
        (
            dependency_count
            - retained_dependency_count
        )
        / dependency_count,
        (
            target_original
            - target_current
        )
        / n,
        dep_incidence_reduction_mean / n,
    )

    features = (
        candidate_features(
            system,
            candidate,
        )
        + tuple(
            float(value)
            for value in state_features
        )
    )
    if len(features) != RESIDUAL_FEATURE_DIMENSION:
        raise AssertionError(
            "residual feature dimension drift"
        )
    return tuple(
        float(value)
        for value in features
    )


def _feasible_candidates(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
) -> tuple[AffineCandidate, ...]:
    return tuple(
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


def teacher_rows_for_example(
    initial: ResidualInitialState,
) -> tuple[ResidualTrainingRow, ...]:
    example = initial.example
    accepted = list(
        initial.accepted
    )
    current = initial.materialized
    output: list[ResidualTrainingRow] = []

    while True:
        candidates = _feasible_candidates(
            example,
            tuple(accepted),
        )
        if not candidates:
            break

        current_ops = (
            current.solver_counts.arithmetic_ops
        )
        best_candidate = None
        best_materialized = None
        best_gain = 0

        for candidate in candidates:
            features = residual_state_features(
                example,
                tuple(accepted),
                current,
                candidate,
            )
            materialized = materialize_reduction(
                example,
                tuple(
                    accepted
                    + [candidate]
                ),
            )
            if materialized is None:
                continue

            trial_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            gain = (
                current_ops
                - trial_ops
            )
            output.append(
                ResidualTrainingRow(
                    features=features,
                    relative_vor=(
                        gain
                        / max(
                            1,
                            current_ops,
                        )
                    ),
                )
            )

            if (
                gain > best_gain
                or (
                    gain == best_gain
                    and gain > 0
                    and best_candidate is not None
                    and _candidate_key(
                        candidate
                    )
                    < _candidate_key(
                        best_candidate
                    )
                )
            ):
                best_candidate = candidate
                best_materialized = materialized
                best_gain = gain

        if (
            best_candidate is None
            or best_materialized is None
            or best_gain <= 0
        ):
            break

        accepted.append(
            best_candidate
        )
        current = (
            best_materialized
        )

    return tuple(output)


def teacher_training_rows(
    initial_states: Iterable[ResidualInitialState],
) -> tuple[ResidualTrainingRow, ...]:
    output: list[ResidualTrainingRow] = []
    for initial in initial_states:
        output.extend(
            teacher_rows_for_example(
                initial
            )
        )
    return tuple(output)


def fit_residual_tree(
    rows: Iterable[ResidualTrainingRow],
    *,
    max_depth: int,
) -> ResidualTreeModel:
    rows = tuple(rows)
    if not rows:
        raise ValueError(
            "training rows required"
        )
    if max_depth not in TREE_DEPTHS:
        raise ValueError(
            "unregistered tree depth"
        )

    X = np.asarray(
        [
            row.features
            for row in rows
        ],
        dtype=float,
    )
    y = np.asarray(
        [
            row.relative_vor
            for row in rows
        ],
        dtype=float,
    )

    regressor = DecisionTreeRegressor(
        criterion="squared_error",
        splitter="best",
        max_depth=max_depth,
        min_samples_leaf=(
            TREE_MIN_SAMPLES_LEAF
        ),
        random_state=(
            TREE_RANDOM_STATE
        ),
    )
    regressor.fit(X, y)

    return ResidualTreeModel(
        regressor=regressor,
        feature_dimension=int(
            regressor.n_features_in_
        ),
        requested_max_depth=max_depth,
        fitted_depth=int(
            regressor.get_depth()
        ),
        fitted_node_count=int(
            regressor.tree_.node_count
        ),
        fitted_leaf_count=int(
            regressor.get_n_leaves()
        ),
    )


def _current_structural_scores(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    materialized: MaterializedReduction,
    candidate: AffineCandidate,
) -> dict[str, float]:
    retained_variables = (
        _retained_variable_set(
            materialized
        )
    )
    retained_dimension = max(
        1,
        materialized.retained_system.dimension,
    )
    rows = _remaining_rows(
        example,
        accepted,
    )

    target_incidence = _column_incidence(
        example,
        rows,
        candidate.target,
        retained_variables=retained_variables,
    )
    dependency_incidence = tuple(
        _column_incidence(
            example,
            rows,
            name,
            retained_variables=retained_variables,
        )
        for name, _ in candidate.coefficients
    )
    dep_mean = mean(
        dependency_incidence
    )

    row = example.full_system.A[
        candidate.row_index
    ]
    row_nnz = sum(
        1
        for variable in retained_variables
        if row[
            example.full_system.variables.index(
                variable
            )
        ] != 0
    )

    target_leaf = max(
        0.0,
        min(
            1.0,
            1.0
            - target_incidence
            / retained_dimension,
        ),
    )
    markowitz_count = (
        max(
            0,
            row_nnz - 1,
        )
        * max(
            0,
            target_incidence - 1,
        )
    )
    markowitz = (
        1.0
        / (
            1.0
            + markowitz_count
        )
    )
    dependency_contrast = max(
        0.0,
        min(
            1.0,
            0.5
            + 0.5
            * (
                dep_mean
                - target_incidence
            )
            / retained_dimension,
        ),
    )
    structural_combo = (
        0.40 * target_leaf
        + 0.35 * markowitz
        + 0.25 * dependency_contrast
    )

    return {
        "residual_target_leaf": (
            target_leaf
        ),
        "residual_markowitz": (
            markowitz
        ),
        "residual_dependency_contrast": (
            dependency_contrast
        ),
        "residual_structural_combo": (
            structural_combo
        ),
    }


def _random_score(
    example: LearnedCompressionExample,
    accepted: tuple[AffineCandidate, ...],
    candidate: AffineCandidate,
) -> float:
    payload = repr(
        (
            "v037-residual-random",
            example.full_system.A,
            example.full_system.b,
            tuple(
                sorted(
                    (
                        item.row_index,
                        item.target,
                    )
                    for item in accepted
                )
            ),
            candidate.row_index,
            candidate.target,
        )
    ).encode("utf-8")
    digest = hashlib.sha256(
        payload
    ).digest()
    integer = int.from_bytes(
        digest[:8],
        "big",
    )
    return (
        integer
        / float(
            2 ** 64 - 1
        )
    )


def _score_candidates(
    initial: ResidualInitialState,
    accepted: tuple[AffineCandidate, ...],
    materialized: MaterializedReduction,
    *,
    method: str,
    tree_model: ResidualTreeModel | None,
) -> tuple[
    tuple[tuple[AffineCandidate, float], ...],
    int,
]:
    example = initial.example
    candidates = _feasible_candidates(
        example,
        accepted,
    )
    if not candidates:
        return (), 0

    if method == "learned_tree":
        if tree_model is None:
            raise ValueError(
                "learned_tree requires tree_model"
            )
        X = np.asarray(
            [
                residual_state_features(
                    example,
                    accepted,
                    materialized,
                    candidate,
                )
                for candidate in candidates
            ],
            dtype=float,
        )
        scores = (
            tree_model.regressor.predict(
                X
            )
        )
        paths = (
            tree_model.regressor
            .decision_path(X)
        )
        comparisons = int(
            paths.nnz
            - len(candidates)
        )
        items = [
            (
                candidate,
                float(score),
            )
            for candidate, score
            in zip(
                candidates,
                scores,
            )
        ]
    else:
        if (
            method
            not in DETERMINISTIC_METHODS
        ):
            raise ValueError(
                f"unknown residual method: {method}"
            )
        comparisons = 0
        items = []
        for candidate in candidates:
            if method == "residual_random":
                score = _random_score(
                    example,
                    accepted,
                    candidate,
                )
            else:
                score = (
                    _current_structural_scores(
                        example,
                        accepted,
                        materialized,
                        candidate,
                    )[method]
                )
            items.append(
                (
                    candidate,
                    float(score),
                )
            )

    items.sort(
        key=lambda item: (
            -item[1],
            *_candidate_key(
                item[0]
            ),
        )
    )
    return (
        tuple(items),
        comparisons,
    )


def rollout_residual_policy(
    initial: ResidualInitialState,
    *,
    method: str,
    threshold: float,
    tree_model: ResidualTreeModel | None = None,
) -> ResidualPolicyObservation:
    example = initial.example
    accepted = list(
        initial.accepted
    )
    current = initial.materialized
    target_leaf_ops = (
        current.solver_counts.arithmetic_ops
    )

    residual_accepted = 0
    score_evaluations = 0
    decision_comparisons = 0
    proposal_materializations = 0
    invalid_rejections = 0
    nonpositive_rejections = 0

    while True:
        scored, comparisons = (
            _score_candidates(
                initial,
                tuple(accepted),
                current,
                method=method,
                tree_model=tree_model,
            )
        )
        score_evaluations += len(
            scored
        )
        decision_comparisons += (
            comparisons
        )

        eligible = tuple(
            item
            for item in scored
            if item[1] >= threshold
        )
        if not eligible:
            break

        current_ops = (
            current.solver_counts.arithmetic_ops
        )
        accepted_this_step = False

        for candidate, _ in eligible:
            proposal_materializations += 1
            materialized = materialize_reduction(
                example,
                tuple(
                    accepted
                    + [candidate]
                ),
            )
            if materialized is None:
                invalid_rejections += 1
                continue

            trial_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            if trial_ops >= current_ops:
                nonpositive_rejections += 1
                continue

            accepted.append(
                candidate
            )
            current = (
                materialized
            )
            residual_accepted += 1
            accepted_this_step = True
            break

        if not accepted_this_step:
            break

    final_ops = (
        current.solver_counts.arithmetic_ops
    )
    final_verified = (
        current.verified
        and current.ground_truth_equivalent
    )

    return ResidualPolicyObservation(
        method=method,
        threshold=threshold,
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
        ),
        baseline_solver_ops=(
            initial.baseline_solver_ops
        ),
        target_leaf_solver_ops=(
            target_leaf_ops
        ),
        final_solver_ops=final_ops,
        target_leaf_accepted_count=(
            len(initial.accepted)
        ),
        residual_accepted_count=(
            residual_accepted
        ),
        residual_additional_solver_savings=(
            target_leaf_ops
            - final_ops
        ),
        total_solver_savings=(
            initial.baseline_solver_ops
            - final_ops
        ),
        candidate_score_evaluations=(
            score_evaluations
        ),
        decision_node_comparisons=(
            decision_comparisons
        ),
        proposal_materializations=(
            proposal_materializations
        ),
        invalid_rejections=(
            invalid_rejections
        ),
        nonpositive_rejections=(
            nonpositive_rejections
        ),
        final_verified=(
            final_verified
        ),
    )


def rollout_exact_residual_teacher(
    initial: ResidualInitialState,
) -> ResidualPolicyObservation:
    example = initial.example
    accepted = list(
        initial.accepted
    )
    current = initial.materialized
    target_leaf_ops = (
        current.solver_counts.arithmetic_ops
    )

    trials = 0
    invalid = 0
    residual_accepted = 0

    while True:
        candidates = _feasible_candidates(
            example,
            tuple(accepted),
        )
        if not candidates:
            break

        current_ops = (
            current.solver_counts.arithmetic_ops
        )
        best_candidate = None
        best_materialized = None
        best_gain = 0

        for candidate in candidates:
            trials += 1
            materialized = materialize_reduction(
                example,
                tuple(
                    accepted
                    + [candidate]
                ),
            )
            if materialized is None:
                invalid += 1
                continue

            gain = (
                current_ops
                - materialized.solver_counts.arithmetic_ops
            )
            if (
                gain > best_gain
                or (
                    gain == best_gain
                    and gain > 0
                    and best_candidate is not None
                    and _candidate_key(
                        candidate
                    )
                    < _candidate_key(
                        best_candidate
                    )
                )
            ):
                best_candidate = (
                    candidate
                )
                best_materialized = (
                    materialized
                )
                best_gain = gain

        if (
            best_candidate is None
            or best_materialized is None
            or best_gain <= 0
        ):
            break

        accepted.append(
            best_candidate
        )
        current = (
            best_materialized
        )
        residual_accepted += 1

    final_ops = (
        current.solver_counts.arithmetic_ops
    )
    return ResidualPolicyObservation(
        method="exact_residual_teacher",
        threshold=None,
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
        ),
        baseline_solver_ops=(
            initial.baseline_solver_ops
        ),
        target_leaf_solver_ops=(
            target_leaf_ops
        ),
        final_solver_ops=final_ops,
        target_leaf_accepted_count=(
            len(initial.accepted)
        ),
        residual_accepted_count=(
            residual_accepted
        ),
        residual_additional_solver_savings=(
            target_leaf_ops
            - final_ops
        ),
        total_solver_savings=(
            initial.baseline_solver_ops
            - final_ops
        ),
        candidate_score_evaluations=0,
        decision_node_comparisons=0,
        proposal_materializations=trials,
        invalid_rejections=invalid,
        nonpositive_rejections=0,
        final_verified=(
            current.verified
            and current.ground_truth_equivalent
        ),
    )


def aggregate_policy_observations(
    observations: Iterable[ResidualPolicyObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError(
            "at least one observation required"
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
    for (k, n), cell_rows in sorted(
        grouped.items()
    ):
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
                "mean_residual_additional_solver_savings": mean(
                    row.residual_additional_solver_savings
                    for row in cell_rows
                ),
                "positive_residual_gain_rate": mean(
                    1.0
                    if row.residual_additional_solver_savings > 0
                    else 0.0
                    for row in cell_rows
                ),
                "mean_proposal_materializations": mean(
                    row.proposal_materializations
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
            0
            if row.final_verified
            else (
                row.target_leaf_accepted_count
                + row.residual_accepted_count
            )
            for row in rows
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
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
        "mean_total_solver_savings": mean(
            row.total_solver_savings
            for row in rows
        ),
        "mean_residual_additional_solver_savings": mean(
            row.residual_additional_solver_savings
            for row in rows
        ),
        "positive_residual_gain_rate": mean(
            1.0
            if row.residual_additional_solver_savings > 0
            else 0.0
            for row in rows
        ),
        "mean_residual_accepted_count": mean(
            row.residual_accepted_count
            for row in rows
        ),
        "mean_candidate_score_evaluations": mean(
            row.candidate_score_evaluations
            for row in rows
        ),
        "mean_decision_node_comparisons": mean(
            row.decision_node_comparisons
            for row in rows
        ),
        "mean_proposal_materializations": mean(
            row.proposal_materializations
            for row in rows
        ),
        "mean_invalid_rejections": mean(
            row.invalid_rejections
            for row in rows
        ),
        "mean_nonpositive_rejections": mean(
            row.nonpositive_rejections
            for row in rows
        ),
        "cells": cells,
    }


def calibrate_residual_policy(
    initial_states: Iterable[ResidualInitialState],
    *,
    method: str,
    thresholds: tuple[float, ...],
    tree_model: ResidualTreeModel | None = None,
) -> ResidualPolicyCalibration:
    states = tuple(
        initial_states
    )
    candidates: list[
        ResidualPolicyCalibration
    ] = []

    for threshold in thresholds:
        rows = tuple(
            rollout_residual_policy(
                initial,
                method=method,
                threshold=threshold,
                tree_model=tree_model,
            )
            for initial in states
        )
        aggregate = (
            aggregate_policy_observations(
                rows
            )
        )
        candidates.append(
            ResidualPolicyCalibration(
                method=method,
                threshold=threshold,
                mean_residual_additional_savings=float(
                    aggregate[
                        "mean_residual_additional_solver_savings"
                    ]
                ),
                mean_final_solver_ops=float(
                    aggregate[
                        "mean_final_solver_ops"
                    ]
                ),
                mean_proposal_materializations=float(
                    aggregate[
                        "mean_proposal_materializations"
                    ]
                ),
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.mean_residual_additional_savings,
            -item.mean_final_solver_ops,
            -item.mean_proposal_materializations,
            item.threshold,
        ),
    )


def select_smallest_adequate_tree(
    training_rows: Iterable[ResidualTrainingRow],
    calibration_states: Iterable[ResidualInitialState],
) -> tuple[
    ResidualTreeModel,
    ResidualPolicyCalibration,
    tuple[
        tuple[
            ResidualTreeModel,
            ResidualPolicyCalibration,
        ],
        ...,
    ],
]:
    rows = tuple(
        training_rows
    )
    states = tuple(
        calibration_states
    )
    candidates = []

    for depth in TREE_DEPTHS:
        model = fit_residual_tree(
            rows,
            max_depth=depth,
        )
        calibration = (
            calibrate_residual_policy(
                states,
                method="learned_tree",
                thresholds=(
                    LEARNED_THRESHOLD_GRID
                ),
                tree_model=model,
            )
        )
        candidates.append(
            (
                model,
                calibration,
            )
        )

    best_savings = max(
        calibration.mean_residual_additional_savings
        for _, calibration in candidates
    )
    adequacy_floor = (
        0.95
        * best_savings
    )
    adequate = [
        item
        for item in candidates
        if item[1].mean_residual_additional_savings
        >= adequacy_floor
    ]
    selected = min(
        adequate,
        key=lambda item: (
            item[0].requested_max_depth,
            item[0].fitted_node_count,
            item[1].mean_proposal_materializations,
            -item[1].threshold,
        ),
    )
    return (
        selected[0],
        selected[1],
        tuple(candidates),
    )
