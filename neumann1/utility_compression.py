from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from statistics import mean
from typing import Iterable

import numpy as np
from scipy.stats import spearmanr
from sklearn.tree import DecisionTreeRegressor

from .learned_compression import (
    AffineCandidate,
    MaterializedReduction,
    ScoredCandidate,
    candidate_features,
    enumerate_affine_candidates,
    materialize_reduction,
)
from .learned_compression_dataset import LearnedCompressionExample
from .stopping_gauntlet import (
    FrozenV033Scorer,
    fit_frozen_v033_scorer,
    score_candidates as score_v034_candidates,
)
from .structural_compression import (
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


UTILITY_TREE_RANDOM_STATE = 35
UTILITY_TREE_MAX_DEPTH = 6
UTILITY_TREE_MIN_SAMPLES_LEAF = 16

UTILITY_METHODS = (
    "utility_tree",
    "reference_mlp",
    "target_leaf",
    "markowitz",
    "sparsity_incidence",
    "oracle_one_step_utility",
)

UTILITY_THRESHOLD_GRID = (
    0.00,
    0.05, 0.10, 0.15, 0.20, 0.25,
    0.30, 0.35, 0.40, 0.45, 0.50,
    0.55, 0.60, 0.65, 0.70, 0.75,
    0.80, 0.85, 0.90, 0.95,
)


@dataclass(frozen=True)
class UtilityTreeFootprint:
    input_feature_dimension: int
    max_depth_limit: int
    min_samples_leaf: int
    fitted_node_count: int
    fitted_max_depth: int
    fitted_leaf_count: int
    fitted_state_sha256: str


@dataclass(frozen=True)
class CheckerCostLowerBound:
    proposed_count: int
    conflict_rejections: int
    materialization_trials: int
    failed_materializations: int
    successful_tentative_solver_ops: int
    successful_tentative_reconstruction_ops: int
    successful_tentative_verification_ops: int


@dataclass(frozen=True)
class UtilityPolicyState:
    accepted_candidates: tuple[AffineCandidate, ...]
    rejected_candidates: tuple[AffineCandidate, ...]
    materialized: MaterializedReduction
    checker_cost_lower_bound: CheckerCostLowerBound


@dataclass(frozen=True)
class UtilityThresholdCalibration:
    method: str
    threshold: float
    mean_solver_savings: float
    mean_method_solver_ops: float
    mean_proposed_count: float
    verified_retention: float
    unsafe_accepted_reductions: int


@dataclass(frozen=True)
class UtilityPolicyObservation:
    method: str
    threshold: float
    core_dimension: int
    apparent_dimension: int
    candidate_count: int
    proposed_count: int
    accepted_count: int
    accepted_reference_count: int
    accepted_nonreference_valid_count: int
    rejected_count: int
    baseline_solver_ops: int
    method_solver_ops: int
    solver_savings: int
    solver_savings_fraction: float
    final_reconstruction_ops: int
    final_verification_ops: int
    final_verified: bool
    unsafe_accepted_reductions: int
    checker_cost_lower_bound: CheckerCostLowerBound
    reference_true_positive_count: int
    reference_count: int


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def _reference_keys(
    example: LearnedCompressionExample,
) -> frozenset[tuple[int, str]]:
    return frozenset(
        (rule.row_index, rule.target)
        for rule in example.oracle_dependencies
    )


def _one_step_utility_with_baseline(
    example: LearnedCompressionExample,
    candidate: AffineCandidate,
    baseline_ops: int,
) -> float:
    reduced = materialize_reduction(
        example,
        (candidate,),
    )
    if reduced is None:
        return 0.0
    savings = max(
        0,
        baseline_ops - reduced.solver_counts.arithmetic_ops,
    )
    if baseline_ops <= 0:
        return 0.0
    return float(savings / baseline_ops)


def one_step_utility(
    example: LearnedCompressionExample,
    candidate: AffineCandidate,
) -> float:
    return _one_step_utility_with_baseline(
        example,
        candidate,
        _baseline_solver_ops(example),
    )


def utility_training_rows(
    examples: Iterable[LearnedCompressionExample],
) -> tuple[
    tuple[tuple[float, ...], ...],
    tuple[float, ...],
]:
    X: list[tuple[float, ...]] = []
    y: list[float] = []

    for example in examples:
        baseline_ops = _baseline_solver_ops(example)
        for candidate in enumerate_affine_candidates(
            example.full_system
        ):
            X.append(
                candidate_features(
                    example.full_system,
                    candidate,
                )
            )
            y.append(
                _one_step_utility_with_baseline(
                    example,
                    candidate,
                    baseline_ops,
                )
            )

    return tuple(X), tuple(y)


def _tree_fingerprint(
    model: DecisionTreeRegressor,
) -> str:
    tree = model.tree_
    digest = hashlib.sha256()
    digest.update(b"NEUMANN-v035-utility-tree\0")
    for array in (
        tree.children_left,
        tree.children_right,
        tree.feature,
        tree.threshold,
        tree.value,
        tree.n_node_samples,
        tree.weighted_n_node_samples,
        tree.impurity,
    ):
        normalized = np.asarray(array)
        digest.update(str(normalized.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(repr(tuple(normalized.shape)).encode("ascii"))
        digest.update(b"\0")
        digest.update(normalized.tobytes(order="C"))
        digest.update(b"\0")
    return digest.hexdigest()


class UtilityTreeScorer:
    def __init__(self) -> None:
        self.model = DecisionTreeRegressor(
            criterion="squared_error",
            max_depth=UTILITY_TREE_MAX_DEPTH,
            min_samples_leaf=UTILITY_TREE_MIN_SAMPLES_LEAF,
            random_state=UTILITY_TREE_RANDOM_STATE,
        )

    def fit(
        self,
        examples: Iterable[LearnedCompressionExample],
    ) -> "UtilityTreeScorer":
        X, y = utility_training_rows(examples)
        if not X:
            raise ValueError("utility training corpus is empty")
        self.model.fit(
            np.asarray(X, dtype=float),
            np.asarray(y, dtype=float),
        )
        return self

    def score(
        self,
        example: LearnedCompressionExample,
    ) -> tuple[ScoredCandidate, ...]:
        candidates = enumerate_affine_candidates(
            example.full_system
        )
        if not candidates:
            return ()

        X = np.asarray(
            [
                candidate_features(
                    example.full_system,
                    candidate,
                )
                for candidate in candidates
            ],
            dtype=float,
        )
        predicted = self.model.predict(X)
        scored = [
            ScoredCandidate(
                candidate=candidate,
                score=max(
                    0.0,
                    min(1.0, float(value)),
                ),
            )
            for candidate, value in zip(
                candidates,
                predicted,
            )
        ]
        scored.sort(
            key=lambda item: (
                -item.score,
                item.candidate.row_index,
                int(item.candidate.target[1:]),
            )
        )
        return tuple(scored)

    def footprint(self) -> UtilityTreeFootprint:
        tree = self.model.tree_
        leaves = int(
            sum(
                1
                for left, right in zip(
                    tree.children_left,
                    tree.children_right,
                )
                if left == right
            )
        )
        return UtilityTreeFootprint(
            input_feature_dimension=int(
                self.model.n_features_in_
            ),
            max_depth_limit=UTILITY_TREE_MAX_DEPTH,
            min_samples_leaf=UTILITY_TREE_MIN_SAMPLES_LEAF,
            fitted_node_count=int(tree.node_count),
            fitted_max_depth=int(tree.max_depth),
            fitted_leaf_count=leaves,
            fitted_state_sha256=_tree_fingerprint(
                self.model
            ),
        )


def fit_utility_tree_once(
    examples: Iterable[LearnedCompressionExample],
) -> UtilityTreeScorer:
    return UtilityTreeScorer().fit(tuple(examples))


def score_utility_method(
    example: LearnedCompressionExample,
    method: str,
    *,
    utility_tree: UtilityTreeScorer,
    frozen_reference_scorer: FrozenV033Scorer,
) -> tuple[ScoredCandidate, ...]:
    if method not in UTILITY_METHODS:
        raise ValueError(f"unknown utility method: {method}")

    if method == "utility_tree":
        return utility_tree.score(example)

    if method == "oracle_one_step_utility":
        baseline_ops = _baseline_solver_ops(example)
        output = [
            ScoredCandidate(
                candidate=candidate,
                score=_one_step_utility_with_baseline(
                    example,
                    candidate,
                    baseline_ops,
                ),
            )
            for candidate in enumerate_affine_candidates(
                example.full_system
            )
        ]
        output.sort(
            key=lambda item: (
                -item.score,
                item.candidate.row_index,
                int(item.candidate.target[1:]),
            )
        )
        return tuple(output)

    v034_method = {
        "reference_mlp": "learned_mlp",
        "target_leaf": "target_leaf",
        "markowitz": "markowitz",
        "sparsity_incidence": "sparsity_incidence",
    }[method]
    return score_v034_candidates(
        example,
        v034_method,
        frozen_scorer=frozen_reference_scorer,
    )


def _materialize_empty(
    example: LearnedCompressionExample,
) -> MaterializedReduction:
    materialized = materialize_reduction(
        example,
        (),
    )
    if materialized is None:
        raise AssertionError(
            "empty reduction failed to materialize"
        )
    return materialized


def _checker_prefix_states(
    example: LearnedCompressionExample,
    scored: tuple[ScoredCandidate, ...],
) -> dict[float, UtilityPolicyState]:
    thresholds = sorted(
        UTILITY_THRESHOLD_GRID,
        reverse=True,
    )
    accepted: list[AffineCandidate] = []
    rejected: list[AffineCandidate] = []
    processed = 0

    conflict_rejections = 0
    materialization_trials = 0
    failed_materializations = 0
    tentative_solver_ops = 0
    tentative_reconstruction_ops = 0
    tentative_verification_ops = 0

    latest_materialized = _materialize_empty(
        example
    )
    states: dict[float, UtilityPolicyState] = {}

    for threshold in thresholds:
        while (
            processed < len(scored)
            and scored[processed].score >= threshold
        ):
            candidate = scored[processed].candidate
            processed += 1

            if any(
                candidate.row_index == item.row_index
                or candidate.target == item.target
                for item in accepted
            ):
                conflict_rejections += 1
                rejected.append(candidate)
                continue

            materialization_trials += 1
            tentative = materialize_reduction(
                example,
                tuple(accepted + [candidate]),
            )
            if tentative is None:
                failed_materializations += 1
                rejected.append(candidate)
                continue

            tentative_solver_ops += (
                tentative.solver_counts.arithmetic_ops
            )
            tentative_reconstruction_ops += (
                tentative.reconstruction_counts.arithmetic_ops
            )
            tentative_verification_ops += (
                tentative.verification_counts.arithmetic_ops
            )
            accepted.append(candidate)
            latest_materialized = tentative

        final_materialized = (
            latest_materialized
            if accepted
            else _materialize_empty(example)
        )
        states[threshold] = UtilityPolicyState(
            accepted_candidates=tuple(accepted),
            rejected_candidates=tuple(rejected),
            materialized=final_materialized,
            checker_cost_lower_bound=CheckerCostLowerBound(
                proposed_count=processed,
                conflict_rejections=conflict_rejections,
                materialization_trials=materialization_trials,
                failed_materializations=failed_materializations,
                successful_tentative_solver_ops=(
                    tentative_solver_ops
                ),
                successful_tentative_reconstruction_ops=(
                    tentative_reconstruction_ops
                ),
                successful_tentative_verification_ops=(
                    tentative_verification_ops
                ),
            ),
        )

    return states


def calibrate_utility_threshold(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    *,
    utility_tree: UtilityTreeScorer,
    frozen_reference_scorer: FrozenV033Scorer,
) -> UtilityThresholdCalibration:
    examples = tuple(examples)
    scored_by_example = tuple(
        (
            example,
            _checker_prefix_states(
                example,
                score_utility_method(
                    example,
                    method,
                    utility_tree=utility_tree,
                    frozen_reference_scorer=(
                        frozen_reference_scorer
                    ),
                ),
            ),
        )
        for example in examples
    )

    candidates: list[UtilityThresholdCalibration] = []

    for threshold in UTILITY_THRESHOLD_GRID:
        solver_savings: list[int] = []
        method_solver_ops: list[int] = []
        proposal_counts: list[int] = []
        verified_flags: list[float] = []
        unsafe = 0

        for example, states in scored_by_example:
            state = states[threshold]
            baseline_ops = _baseline_solver_ops(
                example
            )
            final_ops = (
                state.materialized.solver_counts.arithmetic_ops
            )
            solver_savings.append(
                baseline_ops - final_ops
            )
            method_solver_ops.append(final_ops)
            proposal_counts.append(
                state.checker_cost_lower_bound.proposed_count
            )
            verified = (
                state.materialized.verified
                and state.materialized.ground_truth_equivalent
            )
            verified_flags.append(
                1.0 if verified else 0.0
            )
            if not verified:
                unsafe += len(
                    state.accepted_candidates
                )

        candidates.append(
            UtilityThresholdCalibration(
                method=method,
                threshold=threshold,
                mean_solver_savings=mean(
                    solver_savings
                ),
                mean_method_solver_ops=mean(
                    method_solver_ops
                ),
                mean_proposed_count=mean(
                    proposal_counts
                ),
                verified_retention=mean(
                    verified_flags
                ),
                unsafe_accepted_reductions=unsafe,
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.mean_solver_savings,
            -item.mean_proposed_count,
            item.threshold,
        ),
    )


def observe_utility_policy(
    example: LearnedCompressionExample,
    method: str,
    calibration: UtilityThresholdCalibration,
    *,
    utility_tree: UtilityTreeScorer,
    frozen_reference_scorer: FrozenV033Scorer,
) -> UtilityPolicyObservation:
    scored = score_utility_method(
        example,
        method,
        utility_tree=utility_tree,
        frozen_reference_scorer=frozen_reference_scorer,
    )
    state = _checker_prefix_states(
        example,
        scored,
    )[calibration.threshold]

    baseline_ops = _baseline_solver_ops(example)
    final_ops = (
        state.materialized.solver_counts.arithmetic_ops
    )
    savings = baseline_ops - final_ops
    reference_keys = _reference_keys(example)
    accepted_keys = {
        candidate.key
        for candidate in state.accepted_candidates
    }

    proposed = tuple(
        item
        for item in scored
        if item.score >= calibration.threshold
    )
    proposed_keys = {
        item.candidate.key
        for item in proposed
    }

    verified = (
        state.materialized.verified
        and state.materialized.ground_truth_equivalent
    )

    return UtilityPolicyObservation(
        method=method,
        threshold=calibration.threshold,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(scored),
        proposed_count=len(proposed),
        accepted_count=len(
            state.accepted_candidates
        ),
        accepted_reference_count=len(
            accepted_keys.intersection(reference_keys)
        ),
        accepted_nonreference_valid_count=(
            len(accepted_keys)
            - len(
                accepted_keys.intersection(reference_keys)
            )
        ),
        rejected_count=len(
            state.rejected_candidates
        ),
        baseline_solver_ops=baseline_ops,
        method_solver_ops=final_ops,
        solver_savings=savings,
        solver_savings_fraction=(
            savings / baseline_ops
            if baseline_ops > 0
            else 0.0
        ),
        final_reconstruction_ops=(
            state.materialized
            .reconstruction_counts.arithmetic_ops
        ),
        final_verification_ops=(
            state.materialized
            .verification_counts.arithmetic_ops
        ),
        final_verified=verified,
        unsafe_accepted_reductions=(
            0
            if verified
            else len(
                state.accepted_candidates
            )
        ),
        checker_cost_lower_bound=(
            state.checker_cost_lower_bound
        ),
        reference_true_positive_count=len(
            proposed_keys.intersection(reference_keys)
        ),
        reference_count=len(reference_keys),
    )


def aggregate_utility_observations(
    observations: Iterable[UtilityPolicyObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError(
            "at least one utility observation is required"
        )

    proposed_total = sum(
        row.proposed_count
        for row in rows
    )
    reference_total = sum(
        row.reference_count
        for row in rows
    )
    true_positive_total = sum(
        row.reference_true_positive_count
        for row in rows
    )

    precision = (
        true_positive_total / proposed_total
        if proposed_total
        else 0.0
    )
    recall = (
        true_positive_total / reference_total
        if reference_total
        else 0.0
    )
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    grouped: dict[
        tuple[int, int],
        list[UtilityPolicyObservation],
    ] = {}
    for row in rows:
        grouped.setdefault(
            (row.core_dimension, row.apparent_dimension),
            [],
        ).append(row)

    cells: list[dict[str, object]] = []
    for (k, n), cell_rows in sorted(grouped.items()):
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(cell_rows),
                "mean_solver_savings": mean(
                    row.solver_savings
                    for row in cell_rows
                ),
                "mean_solver_savings_fraction": mean(
                    row.solver_savings_fraction
                    for row in cell_rows
                ),
                "mean_method_solver_ops": mean(
                    row.method_solver_ops
                    for row in cell_rows
                ),
                "mean_accepted_count": mean(
                    row.accepted_count
                    for row in cell_rows
                ),
                "mean_proposed_count": mean(
                    row.proposed_count
                    for row in cell_rows
                ),
                "verified_retention": mean(
                    1.0 if row.final_verified else 0.0
                    for row in cell_rows
                ),
            }
        )

    checker = [
        row.checker_cost_lower_bound
        for row in rows
    ]

    return {
        "method": rows[0].method,
        "threshold": rows[0].threshold,
        "count": len(rows),
        "reference_rule_precision": precision,
        "reference_rule_recall": recall,
        "reference_rule_f1": f1,
        "mean_proposed_count": mean(
            row.proposed_count
            for row in rows
        ),
        "mean_accepted_count": mean(
            row.accepted_count
            for row in rows
        ),
        "mean_accepted_reference_count": mean(
            row.accepted_reference_count
            for row in rows
        ),
        "mean_accepted_nonreference_valid_count": mean(
            row.accepted_nonreference_valid_count
            for row in rows
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in rows
        ),
        "mean_method_solver_ops": mean(
            row.method_solver_ops
            for row in rows
        ),
        "mean_solver_savings": mean(
            row.solver_savings
            for row in rows
        ),
        "mean_solver_savings_fraction": mean(
            row.solver_savings_fraction
            for row in rows
        ),
        "mean_final_reconstruction_ops": mean(
            row.final_reconstruction_ops
            for row in rows
        ),
        "mean_final_verification_ops": mean(
            row.final_verification_ops
            for row in rows
        ),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            row.unsafe_accepted_reductions
            for row in rows
        ),
        "total_rejected_proposals": sum(
            row.rejected_count
            for row in rows
        ),
        "mean_checker_materialization_trials": mean(
            item.materialization_trials
            for item in checker
        ),
        "mean_checker_failed_materializations": mean(
            item.failed_materializations
            for item in checker
        ),
        "mean_checker_successful_tentative_solver_ops": mean(
            item.successful_tentative_solver_ops
            for item in checker
        ),
        "mean_checker_successful_tentative_reconstruction_ops": mean(
            item.successful_tentative_reconstruction_ops
            for item in checker
        ),
        "mean_checker_successful_tentative_verification_ops": mean(
            item.successful_tentative_verification_ops
            for item in checker
        ),
        "cells": cells,
    }


def utility_prediction_metrics(
    examples: Iterable[LearnedCompressionExample],
    utility_tree: UtilityTreeScorer,
) -> dict[str, float | int | None]:
    truth: list[float] = []
    predicted: list[float] = []

    for example in examples:
        baseline_ops = _baseline_solver_ops(example)
        scored = {
            item.candidate.key: item.score
            for item in utility_tree.score(
                example
            )
        }
        for candidate in enumerate_affine_candidates(
            example.full_system
        ):
            truth.append(
                _one_step_utility_with_baseline(
                    example,
                    candidate,
                    baseline_ops,
                )
            )
            predicted.append(
                scored[candidate.key]
            )

    if not truth:
        return {
            "count": 0,
            "mae": None,
            "rmse": None,
            "spearman": None,
        }

    errors = [
        pred - actual
        for pred, actual in zip(
            predicted,
            truth,
        )
    ]
    correlation = spearmanr(
        truth,
        predicted,
    ).statistic

    return {
        "count": len(truth),
        "mae": mean(
            abs(error)
            for error in errors
        ),
        "rmse": math.sqrt(
            mean(
                error * error
                for error in errors
            )
        ),
        "spearman": (
            float(correlation)
            if math.isfinite(float(correlation))
            else None
        ),
    }
