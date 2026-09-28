from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .compression_utility import (
    UtilityOracleObservation,
    observe_dynamic_greedy_utility,
)
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
class ResidualHeadroomObservation:
    core_dimension: int
    apparent_dimension: int
    baseline_solver_ops: int
    target_leaf_proposed_count: int
    target_leaf_accepted_count: int
    target_leaf_rejected_count: int
    target_leaf_solver_ops: int
    target_leaf_solver_savings: int
    full_dynamic_solver_ops: int
    full_dynamic_solver_savings: int
    full_dynamic_trial_materializations: int
    full_dynamic_successful_trial_solver_ops: int
    residual_added_count: int
    residual_solver_ops: int
    residual_additional_solver_savings: int
    residual_total_solver_savings: int
    residual_trial_materializations: int
    residual_successful_trial_materializations: int
    residual_invalid_trial_materializations: int
    residual_successful_trial_solver_ops: int
    full_dynamic_headroom_over_target_leaf: int
    residual_headroom_recovery: float | None
    residual_positive_gain: bool
    residual_selected_gain_sum: int
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


def target_leaf_checked(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> CheckerResult:
    scored = score_candidates(
        example,
        "target_leaf",
        frozen_scorer=frozen_scorer,
    )
    budget = sum(
        1
        for item in scored
        if item.score >= FROZEN_TARGET_LEAF_THRESHOLD
    )
    return check_scored_proposals(
        example,
        scored,
        proposal_budget=budget,
    )


def _dynamic_residual_from_initial(
    example: LearnedCompressionExample,
    initial: CheckerResult,
) -> tuple[
    tuple[AffineCandidate, ...],
    object,
    int,
    int,
    int,
    int,
    tuple[int, ...],
]:
    candidates = enumerate_affine_candidates(
        example.full_system
    )
    accepted = list(initial.accepted_candidates)
    current_materialized = initial.materialized
    current_ops = (
        current_materialized.solver_counts.arithmetic_ops
    )

    trials = 0
    successful = 0
    invalid = 0
    successful_solver_ops = 0
    selected_gains: list[int] = []

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
            break

        accepted.append(best_candidate)
        current_materialized = best_materialized
        current_ops = (
            best_materialized.solver_counts.arithmetic_ops
        )
        selected_gains.append(best_gain)

    return (
        tuple(accepted),
        current_materialized,
        trials,
        successful,
        invalid,
        successful_solver_ops,
        tuple(selected_gains),
    )


def observe_residual_headroom(
    example: LearnedCompressionExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ResidualHeadroomObservation:
    baseline_ops = _baseline_solver_ops(example)

    target_leaf = target_leaf_checked(
        example,
        frozen_scorer=frozen_scorer,
    )
    target_leaf_ops = (
        target_leaf.materialized.solver_counts.arithmetic_ops
    )

    full_dynamic: UtilityOracleObservation = (
        observe_dynamic_greedy_utility(example)
    )

    (
        residual_accepted,
        residual_materialized,
        residual_trials,
        residual_successful,
        residual_invalid,
        residual_successful_solver_ops,
        residual_gains,
    ) = _dynamic_residual_from_initial(
        example,
        target_leaf,
    )

    residual_ops = (
        residual_materialized.solver_counts.arithmetic_ops
    )
    residual_additional = (
        target_leaf_ops - residual_ops
    )
    full_headroom = (
        target_leaf_ops - full_dynamic.method_solver_ops
    )

    if full_headroom > 0:
        recovery: float | None = (
            residual_additional / full_headroom
        )
    else:
        recovery = None

    final_verified = (
        target_leaf.materialized.verified
        and target_leaf.materialized.ground_truth_equivalent
        and full_dynamic.final_verified
        and residual_materialized.verified
        and residual_materialized.ground_truth_equivalent
    )

    return ResidualHeadroomObservation(
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        baseline_solver_ops=baseline_ops,
        target_leaf_proposed_count=len(
            target_leaf.proposed_candidates
        ),
        target_leaf_accepted_count=len(
            target_leaf.accepted_candidates
        ),
        target_leaf_rejected_count=len(
            target_leaf.rejected_candidates
        ),
        target_leaf_solver_ops=target_leaf_ops,
        target_leaf_solver_savings=(
            baseline_ops - target_leaf_ops
        ),
        full_dynamic_solver_ops=(
            full_dynamic.method_solver_ops
        ),
        full_dynamic_solver_savings=(
            full_dynamic.solver_savings
        ),
        full_dynamic_trial_materializations=(
            full_dynamic.trial_materializations
        ),
        full_dynamic_successful_trial_solver_ops=(
            full_dynamic.successful_trial_solver_ops
        ),
        residual_added_count=(
            len(residual_accepted)
            - len(target_leaf.accepted_candidates)
        ),
        residual_solver_ops=residual_ops,
        residual_additional_solver_savings=(
            residual_additional
        ),
        residual_total_solver_savings=(
            baseline_ops - residual_ops
        ),
        residual_trial_materializations=(
            residual_trials
        ),
        residual_successful_trial_materializations=(
            residual_successful
        ),
        residual_invalid_trial_materializations=(
            residual_invalid
        ),
        residual_successful_trial_solver_ops=(
            residual_successful_solver_ops
        ),
        full_dynamic_headroom_over_target_leaf=(
            full_headroom
        ),
        residual_headroom_recovery=recovery,
        residual_positive_gain=(
            residual_additional > 0
        ),
        residual_selected_gain_sum=sum(
            residual_gains
        ),
        final_verified=final_verified,
    )


def aggregate_residual_headroom(
    observations: Iterable[ResidualHeadroomObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError(
            "at least one observation is required"
        )

    mean_full_headroom = mean(
        row.full_dynamic_headroom_over_target_leaf
        for row in rows
    )
    mean_residual_headroom = mean(
        row.residual_additional_solver_savings
        for row in rows
    )
    if mean_full_headroom > 0:
        aggregate_recovery: float | None = (
            mean_residual_headroom
            / mean_full_headroom
        )
    else:
        aggregate_recovery = None

    mean_full_trials = mean(
        row.full_dynamic_trial_materializations
        for row in rows
    )
    mean_residual_trials = mean(
        row.residual_trial_materializations
        for row in rows
    )
    if mean_full_trials > 0:
        teacher_materialization_reduction = (
            1.0
            - mean_residual_trials / mean_full_trials
        )
    else:
        teacher_materialization_reduction = 0.0

    positive_rate = mean(
        1.0 if row.residual_positive_gain else 0.0
        for row in rows
    )

    grouped: dict[
        tuple[int, int],
        list[ResidualHeadroomObservation],
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
    for (k, n), cell_rows in sorted(grouped.items()):
        cell_full_headroom = mean(
            row.full_dynamic_headroom_over_target_leaf
            for row in cell_rows
        )
        cell_residual = mean(
            row.residual_additional_solver_savings
            for row in cell_rows
        )
        cell_recovery = (
            cell_residual / cell_full_headroom
            if cell_full_headroom > 0
            else None
        )
        cell_full_trials = mean(
            row.full_dynamic_trial_materializations
            for row in cell_rows
        )
        cell_residual_trials = mean(
            row.residual_trial_materializations
            for row in cell_rows
        )
        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(cell_rows),
                "mean_target_leaf_solver_ops": mean(
                    row.target_leaf_solver_ops
                    for row in cell_rows
                ),
                "mean_full_dynamic_solver_ops": mean(
                    row.full_dynamic_solver_ops
                    for row in cell_rows
                ),
                "mean_residual_solver_ops": mean(
                    row.residual_solver_ops
                    for row in cell_rows
                ),
                "mean_full_dynamic_headroom": (
                    cell_full_headroom
                ),
                "mean_residual_additional_savings": (
                    cell_residual
                ),
                "residual_headroom_recovery": (
                    cell_recovery
                ),
                "positive_residual_rate": mean(
                    1.0 if row.residual_positive_gain else 0.0
                    for row in cell_rows
                ),
                "mean_full_dynamic_trials": (
                    cell_full_trials
                ),
                "mean_residual_trials": (
                    cell_residual_trials
                ),
                "teacher_materialization_reduction": (
                    1.0
                    - cell_residual_trials / cell_full_trials
                    if cell_full_trials > 0
                    else 0.0
                ),
                "verified_retention": mean(
                    1.0 if row.final_verified else 0.0
                    for row in cell_rows
                ),
            }
        )

    gate_recovery = (
        aggregate_recovery is not None
        and aggregate_recovery >= 0.50
    )
    gate_positive_rate = (
        positive_rate >= 0.25
    )
    gate_teacher_reduction = (
        teacher_materialization_reduction >= 0.50
    )
    pass_count = sum(
        [
            gate_recovery,
            gate_positive_rate,
            gate_teacher_reduction,
        ]
    )
    if pass_count == 3:
        decision = "PROCEED_LEARNED_RESIDUAL"
    elif pass_count >= 1:
        decision = "HOLD_SCALE_ROUTER"
    else:
        decision = "DELETE_LEARNED_RESIDUAL"

    return {
        "count": len(rows),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            0 if row.final_verified else (
                row.target_leaf_accepted_count
                + row.residual_added_count
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
        "mean_full_dynamic_solver_ops": mean(
            row.full_dynamic_solver_ops
            for row in rows
        ),
        "mean_residual_solver_ops": mean(
            row.residual_solver_ops
            for row in rows
        ),
        "mean_target_leaf_solver_savings": mean(
            row.target_leaf_solver_savings
            for row in rows
        ),
        "mean_full_dynamic_solver_savings": mean(
            row.full_dynamic_solver_savings
            for row in rows
        ),
        "mean_residual_total_solver_savings": mean(
            row.residual_total_solver_savings
            for row in rows
        ),
        "mean_full_dynamic_headroom": (
            mean_full_headroom
        ),
        "mean_residual_additional_savings": (
            mean_residual_headroom
        ),
        "residual_headroom_recovery": (
            aggregate_recovery
        ),
        "positive_residual_rate": positive_rate,
        "mean_target_leaf_accepted_count": mean(
            row.target_leaf_accepted_count
            for row in rows
        ),
        "mean_residual_added_count": mean(
            row.residual_added_count
            for row in rows
        ),
        "mean_full_dynamic_trials": (
            mean_full_trials
        ),
        "mean_residual_trials": (
            mean_residual_trials
        ),
        "teacher_materialization_reduction": (
            teacher_materialization_reduction
        ),
        "mean_full_dynamic_successful_trial_solver_ops": mean(
            row.full_dynamic_successful_trial_solver_ops
            for row in rows
        ),
        "mean_residual_successful_trial_solver_ops": mean(
            row.residual_successful_trial_solver_ops
            for row in rows
        ),
        "gate_residual_headroom_recovery_ge_0_50": (
            gate_recovery
        ),
        "gate_positive_residual_rate_ge_0_25": (
            gate_positive_rate
        ),
        "gate_teacher_materialization_reduction_ge_0_50": (
            gate_teacher_reduction
        ),
        "continuation_gate_pass_count": pass_count,
        "continuation_decision": decision,
        "cells": cells,
    }
