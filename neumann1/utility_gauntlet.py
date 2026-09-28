from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean
from typing import Iterable

from .frozen_v033_checkpoint import FrozenV033CheckpointProposer
from .frozen_v035_checkpoints import (
    FrozenV035ReferenceClassifier,
    FrozenV035UtilityRegressor,
)
from .learned_compression import (
    AffineCandidate,
    MaterializedReduction,
    ScoredCandidate,
    enumerate_affine_candidates,
    materialize_reduction,
    oracle_candidates,
)
from .learned_compression_dataset import LearnedCompressionExample
from .stopping_gauntlet import (
    fit_frozen_v033_scorer,
    score_candidates as score_v034_candidates,
)
from .structural_compression import solve_exact_gauss_jordan
from .utility_training import certified_one_step_solver_utility


V035_METHODS = (
    "matched_reference",
    "matched_utility",
    "historical_reference",
    "target_leaf",
    "markowitz",
    "sparsity_incidence",
    "deterministic_random",
    "oracle_one_step_utility",
)

V035_DEPLOYABLE_METHODS = tuple(
    method
    for method in V035_METHODS
    if method != "oracle_one_step_utility"
)

V035_THRESHOLD_GRID = tuple(
    i / 20.0
    for i in range(20)
)


@dataclass(frozen=True)
class UtilityScorerBundle:
    matched_reference: FrozenV035ReferenceClassifier
    matched_utility: FrozenV035UtilityRegressor
    historical_reference: FrozenV033CheckpointProposer


@dataclass(frozen=True)
class PrefixReductionState:
    proposed_count: int
    accepted_candidates: tuple[AffineCandidate, ...]
    rejected_count: int
    materialized: MaterializedReduction


@dataclass(frozen=True)
class UtilityThresholdCalibration:
    method: str
    threshold: float
    mean_solver_savings: float
    proposed_count: int


@dataclass(frozen=True)
class UtilityPolicyObservation:
    method: str
    threshold: float
    core_dimension: int
    apparent_dimension: int
    candidate_count: int
    proposed_count: int
    rejected_count: int
    accepted_count: int
    accepted_reference_count: int
    accepted_nonreference_valid_count: int
    raw_true_positive_count: int
    raw_reference_count: int
    baseline_solver_ops: int
    reference_solver_ops: int
    method_solver_ops: int
    solver_savings_vs_baseline: int
    reference_solver_savings: int
    reference_savings_recovery: float | None
    inferred_retained_dimension: int
    retained_dimension_error: int
    reconstruction_ops: int
    verification_ops: int
    final_verified: bool
    unsafe_accepted_reductions: int


def make_v035_scorers() -> UtilityScorerBundle:
    historical = fit_frozen_v033_scorer()
    return UtilityScorerBundle(
        matched_reference=FrozenV035ReferenceClassifier(),
        matched_utility=FrozenV035UtilityRegressor(),
        historical_reference=historical.proposer,
    )


def _sorted(
    rows: Iterable[ScoredCandidate],
) -> tuple[ScoredCandidate, ...]:
    output = list(rows)
    output.sort(
        key=lambda item: (
            -item.score,
            item.candidate.row_index,
            int(item.candidate.target[1:]),
        )
    )
    return tuple(output)


def exact_one_step_utility_scores(
    example: LearnedCompressionExample,
) -> tuple[ScoredCandidate, ...]:
    _, baseline_counts = solve_exact_gauss_jordan(
        example.full_system
    )
    baseline_ops = baseline_counts.arithmetic_ops

    return _sorted(
        ScoredCandidate(
            candidate=candidate,
            score=certified_one_step_solver_utility(
                example,
                candidate,
                baseline_solver_ops=baseline_ops,
            ),
        )
        for candidate in enumerate_affine_candidates(
            example.full_system
        )
    )


def score_v035_candidates(
    example: LearnedCompressionExample,
    method: str,
    *,
    scorers: UtilityScorerBundle,
) -> tuple[ScoredCandidate, ...]:
    if method == "matched_reference":
        return scorers.matched_reference.score(example)
    if method == "matched_utility":
        return scorers.matched_utility.score(example)
    if method == "historical_reference":
        return scorers.historical_reference.score(example)
    if method in {
        "target_leaf",
        "markowitz",
        "sparsity_incidence",
        "deterministic_random",
    }:
        return score_v034_candidates(
            example,
            method,
            frozen_scorer=fit_frozen_v033_scorer(),
        )
    if method == "oracle_one_step_utility":
        return exact_one_step_utility_scores(example)
    raise ValueError(f"unknown v0.0.35 method: {method}")


def _full_materialization(
    example: LearnedCompressionExample,
) -> MaterializedReduction:
    return materialize_reduction(
        example,
        (),
    ) or _raise_full_materialization()


def _raise_full_materialization():
    raise AssertionError("empty reduction failed to materialize")


def build_prefix_trace(
    example: LearnedCompressionExample,
    scored: tuple[ScoredCandidate, ...],
) -> tuple[PrefixReductionState, ...]:
    current = _full_materialization(example)
    accepted: list[AffineCandidate] = []
    rejected_count = 0
    trace = [
        PrefixReductionState(
            proposed_count=0,
            accepted_candidates=(),
            rejected_count=0,
            materialized=current,
        )
    ]

    for index, scored_candidate in enumerate(
        scored,
        start=1,
    ):
        candidate = scored_candidate.candidate

        if any(
            candidate.row_index == item.row_index
            or candidate.target == item.target
            for item in accepted
        ):
            rejected_count += 1
        else:
            tentative = tuple(accepted + [candidate])
            materialized = materialize_reduction(
                example,
                tentative,
            )
            if materialized is None:
                rejected_count += 1
            else:
                accepted.append(candidate)
                current = materialized

        trace.append(
            PrefixReductionState(
                proposed_count=index,
                accepted_candidates=tuple(accepted),
                rejected_count=rejected_count,
                materialized=current,
            )
        )

    return tuple(trace)


def _prefix_count(
    scored: tuple[ScoredCandidate, ...],
    threshold: float,
) -> int:
    return sum(
        1
        for item in scored
        if item.score >= threshold
    )


def _reference_keys(
    example: LearnedCompressionExample,
) -> frozenset[tuple[int, str]]:
    return frozenset(
        (rule.row_index, rule.target)
        for rule in example.oracle_dependencies
    )


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def _reference_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    reduction = materialize_reduction(
        example,
        oracle_candidates(example),
    )
    if reduction is None:
        raise AssertionError(
            "generator reference reduction failed materialization"
        )
    return reduction.solver_counts.arithmetic_ops


def calibrate_utility_threshold(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    *,
    scorers: UtilityScorerBundle,
) -> UtilityThresholdCalibration:
    examples = tuple(examples)

    prepared = []
    for example in examples:
        scored = score_v035_candidates(
            example,
            method,
            scorers=scorers,
        )
        trace = build_prefix_trace(example, scored)
        baseline_ops = _baseline_solver_ops(example)
        prepared.append(
            (scored, trace, baseline_ops)
        )

    candidates: list[UtilityThresholdCalibration] = []
    for threshold in V035_THRESHOLD_GRID:
        savings = []
        proposed_total = 0

        for scored, trace, baseline_ops in prepared:
            proposed = _prefix_count(
                scored,
                threshold,
            )
            state = trace[proposed]
            proposed_total += proposed
            savings.append(
                baseline_ops
                - state.materialized.solver_counts.arithmetic_ops
            )

        candidates.append(
            UtilityThresholdCalibration(
                method=method,
                threshold=threshold,
                mean_solver_savings=mean(savings),
                proposed_count=proposed_total,
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.mean_solver_savings,
            -item.proposed_count,
            item.threshold,
        ),
    )


def observe_utility_policy(
    example: LearnedCompressionExample,
    method: str,
    calibration: UtilityThresholdCalibration,
    *,
    scorers: UtilityScorerBundle,
) -> UtilityPolicyObservation:
    scored = score_v035_candidates(
        example,
        method,
        scorers=scorers,
    )
    proposed_count = _prefix_count(
        scored,
        calibration.threshold,
    )
    trace = build_prefix_trace(
        example,
        scored,
    )
    state = trace[proposed_count]

    reference_keys = _reference_keys(example)
    proposed_keys = {
        item.candidate.key
        for item in scored[:proposed_count]
    }
    accepted_keys = {
        candidate.key
        for candidate in state.accepted_candidates
    }

    baseline_ops = _baseline_solver_ops(example)
    reference_ops = _reference_solver_ops(example)
    method_ops = (
        state.materialized.solver_counts.arithmetic_ops
    )
    reference_savings = baseline_ops - reference_ops
    method_savings = baseline_ops - method_ops

    if reference_savings > 0:
        recovery: float | None = (
            method_savings / reference_savings
        )
    else:
        recovery = None

    accepted_reference = len(
        accepted_keys.intersection(reference_keys)
    )
    accepted_nonreference = (
        len(accepted_keys) - accepted_reference
    )

    final_verified = (
        state.materialized.verified
        and state.materialized.ground_truth_equivalent
    )
    inferred_retained = (
        example.apparent_dimension
        - len(state.accepted_candidates)
    )

    return UtilityPolicyObservation(
        method=method,
        threshold=calibration.threshold,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(scored),
        proposed_count=proposed_count,
        rejected_count=state.rejected_count,
        accepted_count=len(state.accepted_candidates),
        accepted_reference_count=accepted_reference,
        accepted_nonreference_valid_count=accepted_nonreference,
        raw_true_positive_count=len(
            proposed_keys.intersection(reference_keys)
        ),
        raw_reference_count=len(reference_keys),
        baseline_solver_ops=baseline_ops,
        reference_solver_ops=reference_ops,
        method_solver_ops=method_ops,
        solver_savings_vs_baseline=method_savings,
        reference_solver_savings=reference_savings,
        reference_savings_recovery=recovery,
        inferred_retained_dimension=inferred_retained,
        retained_dimension_error=(
            inferred_retained
            - example.core_dimension
        ),
        reconstruction_ops=(
            state.materialized.reconstruction_counts.arithmetic_ops
        ),
        verification_ops=(
            state.materialized.verification_counts.arithmetic_ops
        ),
        final_verified=final_verified,
        unsafe_accepted_reductions=(
            0
            if final_verified
            else len(state.accepted_candidates)
        ),
    )


def _pearson(
    xs: list[float],
    ys: list[float],
) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    x_var = sum(
        (value - x_mean) ** 2
        for value in xs
    )
    y_var = sum(
        (value - y_mean) ** 2
        for value in ys
    )
    if x_var == 0.0 or y_var == 0.0:
        return None
    covariance = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(xs, ys)
    )
    return covariance / math.sqrt(x_var * y_var)


def utility_regressor_diagnostics(
    examples: Iterable[LearnedCompressionExample],
    *,
    scorers: UtilityScorerBundle,
) -> dict[str, float | int | None]:
    predicted: list[float] = []
    actual: list[float] = []

    for example in examples:
        predicted_rows = scorers.matched_utility.score(example)
        actual_rows = exact_one_step_utility_scores(example)

        predicted_by_key = {
            item.candidate.key: item.score
            for item in predicted_rows
        }
        actual_by_key = {
            item.candidate.key: item.score
            for item in actual_rows
        }
        if set(predicted_by_key) != set(actual_by_key):
            raise AssertionError(
                "utility diagnostic candidate universe drift"
            )

        for key in sorted(
            predicted_by_key,
            key=lambda item: (
                item[0],
                int(item[1][1:]),
            ),
        ):
            predicted.append(
                float(predicted_by_key[key])
            )
            actual.append(
                float(actual_by_key[key])
            )

    errors = [
        prediction - target
        for prediction, target in zip(
            predicted,
            actual,
        )
    ]
    return {
        "candidate_count": len(errors),
        "mae": mean(abs(error) for error in errors),
        "mse": mean(error * error for error in errors),
        "pearson_correlation": _pearson(
            predicted,
            actual,
        ),
        "mean_predicted_utility": mean(predicted),
        "mean_true_utility": mean(actual),
    }


def aggregate_utility_observations(
    observations: Iterable[UtilityPolicyObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one observation is required")

    proposed_total = sum(
        row.proposed_count
        for row in rows
    )
    reference_total = sum(
        row.raw_reference_count
        for row in rows
    )
    true_positive_total = sum(
        row.raw_true_positive_count
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
        2.0 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    recovery_rows = [
        row.reference_savings_recovery
        for row in rows
        if row.reference_savings_recovery is not None
    ]

    grouped: dict[
        tuple[int, int],
        list[UtilityPolicyObservation],
    ] = {}
    for row in rows:
        grouped.setdefault(
            (
                row.core_dimension,
                row.apparent_dimension,
            ),
            [],
        ).append(row)

    cells: list[dict[str, object]] = []
    for (k, n), cell_rows in sorted(
        grouped.items()
    ):
        cell_recovery = [
            row.reference_savings_recovery
            for row in cell_rows
            if row.reference_savings_recovery is not None
        ]
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(cell_rows),
                "mean_proposed_count": mean(
                    row.proposed_count
                    for row in cell_rows
                ),
                "mean_accepted_count": mean(
                    row.accepted_count
                    for row in cell_rows
                ),
                "mean_solver_ops": mean(
                    row.method_solver_ops
                    for row in cell_rows
                ),
                "mean_solver_savings": mean(
                    row.solver_savings_vs_baseline
                    for row in cell_rows
                ),
                "mean_reference_savings_recovery": (
                    mean(
                        float(value)
                        for value in cell_recovery
                    )
                    if cell_recovery
                    else None
                ),
                "mean_abs_retained_dimension_error": mean(
                    abs(row.retained_dimension_error)
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
        "proposal_precision": precision,
        "proposal_recall": recall,
        "proposal_f1": f1,
        "mean_proposed_candidates": mean(
            row.proposed_count
            for row in rows
        ),
        "mean_accepted_eliminations": mean(
            row.accepted_count
            for row in rows
        ),
        "mean_accepted_reference_eliminations": mean(
            row.accepted_reference_count
            for row in rows
        ),
        "mean_accepted_nonreference_valid_eliminations": mean(
            row.accepted_nonreference_valid_count
            for row in rows
        ),
        "mean_rejected_proposals": mean(
            row.rejected_count
            for row in rows
        ),
        "total_fail_closed_rejections": sum(
            row.rejected_count
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
        "mean_inferred_retained_dimension": mean(
            row.inferred_retained_dimension
            for row in rows
        ),
        "mean_abs_retained_dimension_error": mean(
            abs(row.retained_dimension_error)
            for row in rows
        ),
        "exact_retained_dimension_match_rate": mean(
            1.0 if row.retained_dimension_error == 0 else 0.0
            for row in rows
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in rows
        ),
        "mean_reference_solver_ops": mean(
            row.reference_solver_ops
            for row in rows
        ),
        "mean_method_solver_ops": mean(
            row.method_solver_ops
            for row in rows
        ),
        "mean_solver_savings_vs_baseline": mean(
            row.solver_savings_vs_baseline
            for row in rows
        ),
        "mean_reference_savings_recovery": (
            mean(
                float(value)
                for value in recovery_rows
            )
            if recovery_rows
            else None
        ),
        "mean_reconstruction_ops": mean(
            row.reconstruction_ops
            for row in rows
        ),
        "mean_verification_ops": mean(
            row.verification_ops
            for row in rows
        ),
        "cells": cells,
    }
