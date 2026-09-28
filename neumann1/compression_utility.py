from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .learned_compression import (
    AffineCandidate,
    ScoredCandidate,
    check_scored_proposals,
    enumerate_affine_candidates,
    materialize_reduction,
)
from .learned_compression_dataset import (
    LearnedCompressionExample,
)
from .stopping_gauntlet import (
    METHODS,
    THRESHOLD_GRID,
    FrozenV033Scorer,
    ThresholdCalibration,
    aggregate_stopping_observations,
    observe_stopping_method,
    score_candidates,
)
from .structural_compression import (
    solve_exact_gauss_jordan,
)


@dataclass(frozen=True)
class UtilityThresholdCalibration:
    method: str
    threshold: float
    mean_solver_savings: float
    mean_solver_ops: float
    mean_proposed_count: float


@dataclass(frozen=True)
class UtilityOracleObservation:
    method: str
    core_dimension: int
    apparent_dimension: int
    candidate_count: int
    proposed_count: int
    accepted_count: int
    rejected_count: int
    baseline_solver_ops: int
    method_solver_ops: int
    solver_savings: int
    trial_materializations: int
    successful_trial_materializations: int
    invalid_trial_materializations: int
    successful_trial_solver_ops: int
    positive_marginal_gain_sum: int
    positive_marginal_gain_count: int
    stopped_without_positive_gain: bool
    final_verified: bool


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def _target_index(candidate: AffineCandidate) -> int:
    return int(candidate.target[1:])


def _proposal_prefix_curve(
    example: LearnedCompressionExample,
    scored: tuple[ScoredCandidate, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    baseline_ops = _baseline_solver_ops(example)
    solver_ops = [baseline_ops]
    accepted_counts = [0]
    accepted: list[AffineCandidate] = []
    current_ops = baseline_ops

    for item in scored:
        candidate = item.candidate
        if any(
            candidate.row_index == chosen.row_index
            or candidate.target == chosen.target
            for chosen in accepted
        ):
            solver_ops.append(current_ops)
            accepted_counts.append(len(accepted))
            continue

        tentative = tuple(accepted + [candidate])
        materialized = materialize_reduction(
            example,
            tentative,
        )
        if materialized is not None:
            accepted.append(candidate)
            current_ops = (
                materialized.solver_counts.arithmetic_ops
            )

        solver_ops.append(current_ops)
        accepted_counts.append(len(accepted))

    return tuple(solver_ops), tuple(accepted_counts)


def calibrate_utility_threshold(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> UtilityThresholdCalibration:
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")

    rows = []
    for example in tuple(examples):
        scored = score_candidates(
            example,
            method,
            frozen_scorer=frozen_scorer,
        )
        curve, _ = _proposal_prefix_curve(
            example,
            scored,
        )
        rows.append(
            (
                scored,
                curve,
                curve[0],
            )
        )

    candidates: list[UtilityThresholdCalibration] = []
    for threshold in THRESHOLD_GRID:
        final_ops: list[int] = []
        savings: list[int] = []
        proposals: list[int] = []

        for scored, curve, baseline_ops in rows:
            prefix = sum(
                1
                for item in scored
                if item.score >= threshold
            )
            method_ops = curve[prefix]
            final_ops.append(method_ops)
            savings.append(
                baseline_ops - method_ops
            )
            proposals.append(prefix)

        candidates.append(
            UtilityThresholdCalibration(
                method=method,
                threshold=threshold,
                mean_solver_savings=mean(savings),
                mean_solver_ops=mean(final_ops),
                mean_proposed_count=mean(proposals),
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.mean_solver_savings,
            -item.mean_solver_ops,
            -item.mean_proposed_count,
            item.threshold,
        ),
    )


def observe_utility_calibrated_method(
    example: LearnedCompressionExample,
    calibration: UtilityThresholdCalibration,
    *,
    frozen_scorer: FrozenV033Scorer,
):
    compatibility = ThresholdCalibration(
        method=calibration.method,
        threshold=calibration.threshold,
        micro_precision=0.0,
        micro_recall=0.0,
        micro_f1=0.0,
        proposed_count=0,
        reference_count=0,
        true_positive_count=0,
    )
    return observe_stopping_method(
        example,
        calibration.method,
        compatibility,
        frozen_scorer=frozen_scorer,
    )


def _isolated_utility_scored(
    example: LearnedCompressionExample,
) -> tuple[
    tuple[ScoredCandidate, ...],
    int,
    int,
    int,
]:
    baseline_ops = _baseline_solver_ops(example)
    output: list[ScoredCandidate] = []
    trials = 0
    successful = 0
    successful_solver_ops = 0

    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        trials += 1
        materialized = materialize_reduction(
            example,
            (candidate,),
        )
        if materialized is None:
            gain = -1.0
        else:
            successful += 1
            trial_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            successful_solver_ops += trial_ops
            gain = float(
                baseline_ops - trial_ops
            )

        output.append(
            ScoredCandidate(
                candidate=candidate,
                score=gain,
            )
        )

    output.sort(
        key=lambda item: (
            -item.score,
            item.candidate.row_index,
            _target_index(item.candidate),
        )
    )
    return (
        tuple(output),
        trials,
        successful,
        successful_solver_ops,
    )


def observe_static_isolated_utility(
    example: LearnedCompressionExample,
) -> UtilityOracleObservation:
    (
        scored,
        trials,
        successful,
        successful_solver_ops,
    ) = _isolated_utility_scored(example)

    positive_count = sum(
        1
        for item in scored
        if item.score > 0.0
    )
    checked = check_scored_proposals(
        example,
        scored,
        proposal_budget=positive_count,
    )

    baseline_ops = _baseline_solver_ops(example)
    method_ops = (
        checked.materialized.solver_counts.arithmetic_ops
    )
    final_verified = (
        checked.materialized.verified
        and checked.materialized.ground_truth_equivalent
    )

    selected_gains = [
        int(item.score)
        for item in checked.proposed_candidates
        if item.score > 0.0
    ]

    return UtilityOracleObservation(
        method="static_isolated_utility",
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(scored),
        proposed_count=positive_count,
        accepted_count=len(
            checked.accepted_candidates
        ),
        rejected_count=len(
            checked.rejected_candidates
        ),
        baseline_solver_ops=baseline_ops,
        method_solver_ops=method_ops,
        solver_savings=baseline_ops - method_ops,
        trial_materializations=trials,
        successful_trial_materializations=successful,
        invalid_trial_materializations=(
            trials - successful
        ),
        successful_trial_solver_ops=(
            successful_solver_ops
        ),
        positive_marginal_gain_sum=sum(
            selected_gains
        ),
        positive_marginal_gain_count=len(
            selected_gains
        ),
        stopped_without_positive_gain=True,
        final_verified=final_verified,
    )


def observe_dynamic_greedy_utility(
    example: LearnedCompressionExample,
) -> UtilityOracleObservation:
    candidates = enumerate_affine_candidates(
        example.full_system
    )
    baseline_ops = _baseline_solver_ops(example)
    current_ops = baseline_ops
    accepted: list[AffineCandidate] = []
    current_materialized = None

    trials = 0
    successful = 0
    invalid = 0
    successful_solver_ops = 0
    selected_gains: list[int] = []
    stopped_without_positive_gain = False

    while True:
        feasible_pool = [
            candidate
            for candidate in candidates
            if not any(
                candidate.row_index == chosen.row_index
                or candidate.target == chosen.target
                for chosen in accepted
            )
        ]
        if not feasible_pool:
            break

        best_candidate = None
        best_materialized = None
        best_gain = 0

        for candidate in feasible_pool:
            trials += 1
            materialized = materialize_reduction(
                example,
                tuple(accepted + [candidate]),
            )
            if materialized is None:
                invalid += 1
                continue

            successful += 1
            trial_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            successful_solver_ops += trial_ops
            gain = current_ops - trial_ops

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

        if (
            best_candidate is None
            or best_materialized is None
            or best_gain <= 0
        ):
            stopped_without_positive_gain = True
            break

        accepted.append(best_candidate)
        current_materialized = best_materialized
        current_ops = (
            best_materialized.solver_counts.arithmetic_ops
        )
        selected_gains.append(best_gain)

    if current_materialized is None:
        checked = check_scored_proposals(
            example,
            (),
            proposal_budget=0,
        )
        current_materialized = checked.materialized

    final_verified = (
        current_materialized.verified
        and current_materialized.ground_truth_equivalent
    )

    return UtilityOracleObservation(
        method="dynamic_greedy_utility",
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(candidates),
        proposed_count=len(accepted),
        accepted_count=len(accepted),
        rejected_count=0,
        baseline_solver_ops=baseline_ops,
        method_solver_ops=current_ops,
        solver_savings=baseline_ops - current_ops,
        trial_materializations=trials,
        successful_trial_materializations=successful,
        invalid_trial_materializations=invalid,
        successful_trial_solver_ops=(
            successful_solver_ops
        ),
        positive_marginal_gain_sum=sum(
            selected_gains
        ),
        positive_marginal_gain_count=len(
            selected_gains
        ),
        stopped_without_positive_gain=(
            stopped_without_positive_gain
        ),
        final_verified=final_verified,
    )


def aggregate_utility_oracle_observations(
    observations: Iterable[UtilityOracleObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError(
            "at least one observation is required"
        )

    grouped: dict[
        tuple[int, int],
        list[UtilityOracleObservation],
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
                "mean_solver_ops": mean(
                    row.method_solver_ops
                    for row in cell_rows
                ),
                "mean_solver_savings_vs_baseline": mean(
                    row.solver_savings
                    for row in cell_rows
                ),
                "mean_accepted_eliminations": mean(
                    row.accepted_count
                    for row in cell_rows
                ),
                "mean_trial_materializations": mean(
                    row.trial_materializations
                    for row in cell_rows
                ),
                "verified_retention": mean(
                    1.0 if row.final_verified else 0.0
                    for row in cell_rows
                ),
            }
        )

    gain_count = sum(
        row.positive_marginal_gain_count
        for row in rows
    )
    gain_sum = sum(
        row.positive_marginal_gain_sum
        for row in rows
    )

    return {
        "method": rows[0].method,
        "count": len(rows),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            0 if row.final_verified else row.accepted_count
            for row in rows
        ),
        "mean_candidate_count": mean(
            row.candidate_count
            for row in rows
        ),
        "mean_proposed_count": mean(
            row.proposed_count
            for row in rows
        ),
        "mean_accepted_eliminations": mean(
            row.accepted_count
            for row in rows
        ),
        "mean_rejected_count": mean(
            row.rejected_count
            for row in rows
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in rows
        ),
        "mean_solver_ops": mean(
            row.method_solver_ops
            for row in rows
        ),
        "mean_solver_savings_vs_baseline": mean(
            row.solver_savings
            for row in rows
        ),
        "mean_retained_dimension": mean(
            row.apparent_dimension - row.accepted_count
            for row in rows
        ),
        "mean_trial_materializations": mean(
            row.trial_materializations
            for row in rows
        ),
        "mean_successful_trial_materializations": mean(
            row.successful_trial_materializations
            for row in rows
        ),
        "mean_invalid_trial_materializations": mean(
            row.invalid_trial_materializations
            for row in rows
        ),
        "mean_successful_trial_solver_ops": mean(
            row.successful_trial_solver_ops
            for row in rows
        ),
        "mean_positive_marginal_gain_selected": (
            gain_sum / gain_count
            if gain_count
            else 0.0
        ),
        "stopped_without_positive_gain_count": sum(
            1
            for row in rows
            if row.stopped_without_positive_gain
        ),
        "cells": cells,
    }


def aggregate_utility_calibrated_methods(
    observations,
) -> dict[str, object]:
    return aggregate_stopping_observations(
        observations
    )
