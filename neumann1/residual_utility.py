from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .learned_compression import (
    AffineCandidate,
    CheckerResult,
    check_scored_proposals,
    enumerate_affine_candidates,
    materialize_reduction,
)
from .learned_compression_dataset import (
    LearnedCompressionExample,
)
from .stopping_gauntlet import (
    FrozenV033Scorer,
    score_candidates,
)
from .structural_compression import (
    solve_exact_gauss_jordan,
)


FROZEN_TARGET_LEAF_THRESHOLD = 0.10


@dataclass(frozen=True)
class ResidualUtilityObservation:
    core_dimension: int
    apparent_dimension: int
    candidate_count: int
    cheap_proposed_count: int
    cheap_accepted_count: int
    cheap_rejected_count: int
    residual_accepted_count: int
    baseline_solver_ops: int
    cheap_solver_ops: int
    residual_solver_ops: int
    cheap_solver_savings: int
    residual_additional_savings: int
    residual_trial_materializations: int
    residual_successful_trial_materializations: int
    residual_invalid_trial_materializations: int
    residual_successful_trial_solver_ops: int
    residual_positive_gain_sum: int
    residual_positive_gain_count: int
    stopped_without_positive_gain: bool
    cheap_verified: bool
    final_verified: bool


def _target_index(candidate: AffineCandidate) -> int:
    return int(candidate.target[1:])


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def certified_target_leaf_state(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> CheckerResult:
    scored = score_candidates(
        example,
        "target_leaf",
        frozen_scorer=frozen_scorer,
    )
    proposal_count = sum(
        1
        for item in scored
        if item.score >= FROZEN_TARGET_LEAF_THRESHOLD
    )
    return check_scored_proposals(
        example,
        scored,
        proposal_budget=proposal_count,
    )


def observe_cheap_first_residual_utility(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualUtilityObservation:
    candidates = enumerate_affine_candidates(
        example.full_system
    )
    baseline_ops = _baseline_solver_ops(example)

    cheap = certified_target_leaf_state(
        example,
        frozen_scorer=frozen_scorer,
    )
    accepted = list(cheap.accepted_candidates)
    current_materialized = cheap.materialized
    cheap_ops = (
        current_materialized.solver_counts.arithmetic_ops
    )
    current_ops = cheap_ops

    trials = 0
    successful = 0
    invalid = 0
    successful_solver_ops = 0
    selected_gains: list[int] = []
    residual_accepted = 0
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

        best_candidate: AffineCandidate | None = None
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
        residual_accepted += 1
        selected_gains.append(best_gain)

    cheap_verified = (
        cheap.materialized.verified
        and cheap.materialized.ground_truth_equivalent
    )
    final_verified = (
        current_materialized.verified
        and current_materialized.ground_truth_equivalent
    )

    return ResidualUtilityObservation(
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(candidates),
        cheap_proposed_count=len(
            cheap.proposed_candidates
        ),
        cheap_accepted_count=len(
            cheap.accepted_candidates
        ),
        cheap_rejected_count=len(
            cheap.rejected_candidates
        ),
        residual_accepted_count=residual_accepted,
        baseline_solver_ops=baseline_ops,
        cheap_solver_ops=cheap_ops,
        residual_solver_ops=current_ops,
        cheap_solver_savings=baseline_ops - cheap_ops,
        residual_additional_savings=(
            cheap_ops - current_ops
        ),
        residual_trial_materializations=trials,
        residual_successful_trial_materializations=successful,
        residual_invalid_trial_materializations=invalid,
        residual_successful_trial_solver_ops=(
            successful_solver_ops
        ),
        residual_positive_gain_sum=sum(
            selected_gains
        ),
        residual_positive_gain_count=len(
            selected_gains
        ),
        stopped_without_positive_gain=(
            stopped_without_positive_gain
        ),
        cheap_verified=cheap_verified,
        final_verified=final_verified,
    )


def aggregate_residual_observations(
    observations: Iterable[ResidualUtilityObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError(
            "at least one observation is required"
        )

    grouped: dict[
        tuple[int, int],
        list[ResidualUtilityObservation],
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
        mean_cheap_ops = mean(
            row.cheap_solver_ops
            for row in cell_rows
        )
        mean_residual_gain = mean(
            row.residual_additional_savings
            for row in cell_rows
        )
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(cell_rows),
                "mean_cheap_solver_ops": mean_cheap_ops,
                "mean_residual_solver_ops": mean(
                    row.residual_solver_ops
                    for row in cell_rows
                ),
                "mean_residual_additional_savings": (
                    mean_residual_gain
                ),
                "residual_remaining_work_reduction": (
                    mean_residual_gain / mean_cheap_ops
                    if mean_cheap_ops > 0
                    else 0.0
                ),
                "mean_residual_trial_materializations": mean(
                    row.residual_trial_materializations
                    for row in cell_rows
                ),
                "mean_residual_successful_trial_solver_ops": mean(
                    row.residual_successful_trial_solver_ops
                    for row in cell_rows
                ),
                "mean_final_retained_dimension": mean(
                    row.apparent_dimension
                    - row.cheap_accepted_count
                    - row.residual_accepted_count
                    for row in cell_rows
                ),
                "verified_retention": mean(
                    1.0 if row.final_verified else 0.0
                    for row in cell_rows
                ),
            }
        )

    mean_cheap_ops = mean(
        row.cheap_solver_ops
        for row in rows
    )
    mean_residual_gain = mean(
        row.residual_additional_savings
        for row in rows
    )

    return {
        "count": len(rows),
        "frozen_target_leaf_threshold": (
            FROZEN_TARGET_LEAF_THRESHOLD
        ),
        "verified_retention_cheap": mean(
            1.0 if row.cheap_verified else 0.0
            for row in rows
        ),
        "verified_retention_residual": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            0
            if row.final_verified
            else (
                row.cheap_accepted_count
                + row.residual_accepted_count
            )
            for row in rows
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in rows
        ),
        "mean_cheap_solver_ops": mean_cheap_ops,
        "mean_residual_solver_ops": mean(
            row.residual_solver_ops
            for row in rows
        ),
        "mean_cheap_solver_savings": mean(
            row.cheap_solver_savings
            for row in rows
        ),
        "mean_residual_additional_savings": (
            mean_residual_gain
        ),
        "residual_remaining_work_reduction": (
            mean_residual_gain / mean_cheap_ops
            if mean_cheap_ops > 0
            else 0.0
        ),
        "mean_cheap_proposed_count": mean(
            row.cheap_proposed_count
            for row in rows
        ),
        "mean_cheap_accepted_count": mean(
            row.cheap_accepted_count
            for row in rows
        ),
        "mean_cheap_rejected_count": mean(
            row.cheap_rejected_count
            for row in rows
        ),
        "mean_residual_accepted_count": mean(
            row.residual_accepted_count
            for row in rows
        ),
        "mean_residual_trial_materializations": mean(
            row.residual_trial_materializations
            for row in rows
        ),
        "mean_residual_successful_trial_materializations": mean(
            row.residual_successful_trial_materializations
            for row in rows
        ),
        "mean_residual_invalid_trial_materializations": mean(
            row.residual_invalid_trial_materializations
            for row in rows
        ),
        "mean_residual_successful_trial_solver_ops": mean(
            row.residual_successful_trial_solver_ops
            for row in rows
        ),
        "mean_final_retained_dimension": mean(
            row.apparent_dimension
            - row.cheap_accepted_count
            - row.residual_accepted_count
            for row in rows
        ),
        "stopped_without_positive_gain_count": sum(
            1
            for row in rows
            if row.stopped_without_positive_gain
        ),
        "cells": cells,
    }
