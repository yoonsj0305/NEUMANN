from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean, median
from typing import Iterable

from .learned_compression import (
    AffineCandidate,
    MaterializedReduction,
    ScoredCandidate,
    check_scored_proposals,
    materialize_reduction,
)
from .learned_compression_dataset import LearnedCompressionExample
from .stopping_gauntlet import FrozenV033Scorer, score_candidates
from .structural_compression import (
    ReconstructionOperationCounts,
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


@dataclass(frozen=True)
class CompressionEconomicsObservation:
    method: str
    threshold: float
    core_dimension: int
    apparent_dimension: int
    candidate_count: int
    proposal_count: int
    accepted_count: int
    rejected_count: int
    conflict_rejections: int
    materialization_rejections: int
    successful_tentative_materializations: int
    final_materializations: int
    materialization_attempts: int
    baseline_solver_ops: int
    baseline_verification_ops: int
    baseline_total_arithmetic: int
    final_solver_ops: int
    final_reconstruction_ops: int
    final_verification_ops: int
    final_solver_savings: int
    successful_path_lb_solver_ops: int
    successful_path_lb_reconstruction_ops: int
    successful_path_lb_verification_ops: int
    successful_path_lb_total_arithmetic: int
    successful_path_lb_ratio: float
    final_verified: bool
    unsafe_accepted_reductions: int
    checker_parity: bool


def _full_system_materialization(
    example: LearnedCompressionExample,
) -> MaterializedReduction:
    answer, solver_counts = solve_exact_gauss_jordan(
        example.full_system
    )
    verified, verification_counts = verify_exact_full_system(
        example.full_system,
        answer,
    )
    ground_truth_equivalent = (
        verified
        and all(
            answer[variable] == expected
            for variable, expected in zip(
                example.full_system.variables,
                example.full_system.ground_truth,
            )
        )
    )
    return MaterializedReduction(
        accepted_candidates=(),
        retained_system=example.full_system,
        reconstruction_order=(),
        retained_answer=answer,
        full_answer=answer,
        solver_counts=solver_counts,
        reconstruction_counts=ReconstructionOperationCounts(),
        verification_counts=verification_counts,
        verified=verified,
        ground_truth_equivalent=ground_truth_equivalent,
    )


def _candidate_keys(
    candidates: Iterable[AffineCandidate],
) -> tuple[tuple[int, str], ...]:
    return tuple(candidate.key for candidate in candidates)


def audit_checker_economics(
    example: LearnedCompressionExample,
    method: str,
    threshold: float,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> CompressionEconomicsObservation:
    scored = score_candidates(
        example,
        method,
        frozen_scorer=frozen_scorer,
    )
    proposals = tuple(
        item for item in scored if item.score >= threshold
    )

    baseline_answer, baseline_solver = solve_exact_gauss_jordan(
        example.full_system
    )
    baseline_verified, baseline_verification = (
        verify_exact_full_system(
            example.full_system,
            baseline_answer,
        )
    )
    if not baseline_verified:
        raise AssertionError("baseline full system did not verify")

    accepted: list[AffineCandidate] = []
    rejected: list[AffineCandidate] = []
    conflict_rejections = 0
    materialization_rejections = 0
    successful_tentative = 0
    materialization_attempts = 0

    lb_solver = 0
    lb_reconstruction = 0
    lb_verification = 0

    for scored_candidate in proposals:
        candidate = scored_candidate.candidate

        if any(
            candidate.row_index == item.row_index
            or candidate.target == item.target
            for item in accepted
        ):
            conflict_rejections += 1
            rejected.append(candidate)
            continue

        materialization_attempts += 1
        tentative = tuple(accepted + [candidate])
        materialized = materialize_reduction(
            example,
            tentative,
        )
        if materialized is None:
            materialization_rejections += 1
            rejected.append(candidate)
            continue

        accepted.append(candidate)
        successful_tentative += 1
        lb_solver += materialized.solver_counts.arithmetic_ops
        lb_reconstruction += (
            materialized.reconstruction_counts.arithmetic_ops
        )
        lb_verification += (
            materialized.verification_counts.arithmetic_ops
        )

    if accepted:
        materialization_attempts += 1
        final_materialized = materialize_reduction(
            example,
            tuple(accepted),
        )
        if final_materialized is None:
            raise AssertionError(
                "accepted set failed final materialization"
            )
    else:
        final_materialized = _full_system_materialization(
            example
        )

    final_materializations = 1
    lb_solver += final_materialized.solver_counts.arithmetic_ops
    lb_reconstruction += (
        final_materialized.reconstruction_counts.arithmetic_ops
    )
    lb_verification += (
        final_materialized.verification_counts.arithmetic_ops
    )

    frozen_checker = check_scored_proposals(
        example,
        scored,
        proposal_budget=len(proposals),
    )

    checker_parity = (
        _candidate_keys(accepted)
        == _candidate_keys(frozen_checker.accepted_candidates)
        and _candidate_keys(rejected)
        == _candidate_keys(frozen_checker.rejected_candidates)
        and final_materialized.retained_system
        == frozen_checker.materialized.retained_system
        and final_materialized.full_answer
        == frozen_checker.materialized.full_answer
        and final_materialized.solver_counts.arithmetic_ops
        == frozen_checker.materialized.solver_counts.arithmetic_ops
        and final_materialized.verified
        == frozen_checker.materialized.verified
        and final_materialized.ground_truth_equivalent
        == frozen_checker.materialized.ground_truth_equivalent
    )
    if not checker_parity:
        raise AssertionError(
            "economics audit diverged from frozen v0.0.34 checker"
        )

    baseline_total = (
        baseline_solver.arithmetic_ops
        + baseline_verification.arithmetic_ops
    )
    lb_total = lb_solver + lb_reconstruction + lb_verification
    ratio = lb_total / baseline_total

    final_verified = (
        final_materialized.verified
        and final_materialized.ground_truth_equivalent
    )

    return CompressionEconomicsObservation(
        method=method,
        threshold=float(threshold),
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(scored),
        proposal_count=len(proposals),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        conflict_rejections=conflict_rejections,
        materialization_rejections=materialization_rejections,
        successful_tentative_materializations=(
            successful_tentative
        ),
        final_materializations=final_materializations,
        materialization_attempts=materialization_attempts,
        baseline_solver_ops=baseline_solver.arithmetic_ops,
        baseline_verification_ops=(
            baseline_verification.arithmetic_ops
        ),
        baseline_total_arithmetic=baseline_total,
        final_solver_ops=(
            final_materialized.solver_counts.arithmetic_ops
        ),
        final_reconstruction_ops=(
            final_materialized.reconstruction_counts.arithmetic_ops
        ),
        final_verification_ops=(
            final_materialized.verification_counts.arithmetic_ops
        ),
        final_solver_savings=(
            baseline_solver.arithmetic_ops
            - final_materialized.solver_counts.arithmetic_ops
        ),
        successful_path_lb_solver_ops=lb_solver,
        successful_path_lb_reconstruction_ops=lb_reconstruction,
        successful_path_lb_verification_ops=lb_verification,
        successful_path_lb_total_arithmetic=lb_total,
        successful_path_lb_ratio=ratio,
        final_verified=final_verified,
        unsafe_accepted_reductions=(
            0 if final_verified else len(accepted)
        ),
        checker_parity=checker_parity,
    )


def _p90(values: Iterable[float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("at least one value is required")
    index = max(0, math.ceil(0.9 * len(ordered)) - 1)
    return ordered[index]


def aggregate_economics_observations(
    observations: Iterable[CompressionEconomicsObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one observation is required")

    ratios = [row.successful_path_lb_ratio for row in rows]

    grouped: dict[
        tuple[int, int],
        list[CompressionEconomicsObservation],
    ] = {}
    for row in rows:
        grouped.setdefault(
            (row.core_dimension, row.apparent_dimension),
            [],
        ).append(row)

    cells: list[dict[str, object]] = []
    for (k, n), cell_rows in sorted(grouped.items()):
        cell_ratios = [
            row.successful_path_lb_ratio
            for row in cell_rows
        ]
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(cell_rows),
                "mean_accepted_count": mean(
                    row.accepted_count
                    for row in cell_rows
                ),
                "mean_final_solver_ops": mean(
                    row.final_solver_ops
                    for row in cell_rows
                ),
                "mean_successful_path_lb_total_arithmetic": mean(
                    row.successful_path_lb_total_arithmetic
                    for row in cell_rows
                ),
                "mean_successful_path_lb_ratio": mean(
                    cell_ratios
                ),
                "fraction_lb_ratio_ge_1": mean(
                    1.0
                    if row.successful_path_lb_ratio >= 1.0
                    else 0.0
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
        "checker_parity_rate": mean(
            1.0 if row.checker_parity else 0.0
            for row in rows
        ),
        "mean_candidate_count": mean(
            row.candidate_count
            for row in rows
        ),
        "mean_proposal_count": mean(
            row.proposal_count
            for row in rows
        ),
        "mean_accepted_count": mean(
            row.accepted_count
            for row in rows
        ),
        "mean_rejected_count": mean(
            row.rejected_count
            for row in rows
        ),
        "mean_conflict_rejections": mean(
            row.conflict_rejections
            for row in rows
        ),
        "mean_materialization_rejections": mean(
            row.materialization_rejections
            for row in rows
        ),
        "mean_successful_tentative_materializations": mean(
            row.successful_tentative_materializations
            for row in rows
        ),
        "mean_successful_materializations_including_final": mean(
            row.successful_tentative_materializations
            + row.final_materializations
            for row in rows
        ),
        "mean_materialization_attempts": mean(
            row.materialization_attempts
            for row in rows
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in rows
        ),
        "mean_baseline_verification_ops": mean(
            row.baseline_verification_ops
            for row in rows
        ),
        "mean_baseline_total_arithmetic": mean(
            row.baseline_total_arithmetic
            for row in rows
        ),
        "mean_final_solver_ops": mean(
            row.final_solver_ops
            for row in rows
        ),
        "mean_final_solver_savings": mean(
            row.final_solver_savings
            for row in rows
        ),
        "mean_successful_path_lb_solver_ops": mean(
            row.successful_path_lb_solver_ops
            for row in rows
        ),
        "mean_successful_path_lb_reconstruction_ops": mean(
            row.successful_path_lb_reconstruction_ops
            for row in rows
        ),
        "mean_successful_path_lb_verification_ops": mean(
            row.successful_path_lb_verification_ops
            for row in rows
        ),
        "mean_successful_path_lb_total_arithmetic": mean(
            row.successful_path_lb_total_arithmetic
            for row in rows
        ),
        "mean_successful_path_lb_ratio": mean(ratios),
        "median_successful_path_lb_ratio": median(ratios),
        "p90_successful_path_lb_ratio": _p90(ratios),
        "fraction_lb_ratio_lt_1": mean(
            1.0 if ratio < 1.0 else 0.0
            for ratio in ratios
        ),
        "fraction_lb_ratio_ge_1": mean(
            1.0 if ratio >= 1.0 else 0.0
            for ratio in ratios
        ),
        "cells": cells,
    }
