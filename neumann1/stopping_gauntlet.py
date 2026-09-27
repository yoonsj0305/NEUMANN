from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from statistics import mean
from typing import Iterable

from .learned_compression import (
    AffineCandidate,
    LearnedCompressionProposer,
    LearnedCompressorFootprint,
    ScoredCandidate,
    candidate_features,
    check_scored_proposals,
    enumerate_affine_candidates,
    inspect_learned_compressor,
    materialize_reduction,
    oracle_candidates,
)
from .learned_compression_dataset import (
    LearnedCompressionExample,
    learned_compression_training_examples,
)
from .structural_compression import solve_exact_gauss_jordan


METHODS = (
    "learned_mlp",
    "deterministic_random",
    "target_leaf",
    "row_sparsity",
    "sparsity_incidence",
    "dependency_contrast",
    "markowitz",
    "structural_combo",
)

THRESHOLD_GRID = tuple(i / 20.0 for i in range(1, 20))


@dataclass(frozen=True)
class ThresholdCalibration:
    method: str
    threshold: float
    micro_precision: float
    micro_recall: float
    micro_f1: float
    proposed_count: int
    reference_count: int
    true_positive_count: int


@dataclass(frozen=True)
class StoppingObservation:
    method: str
    threshold: float
    core_dimension: int
    apparent_dimension: int
    candidate_count: int
    proposed_count: int
    raw_true_positive_count: int
    raw_reference_count: int
    accepted_count: int
    accepted_reference_count: int
    accepted_nonreference_valid_count: int
    rejected_count: int
    inferred_retained_dimension: int
    retained_dimension_error: int
    baseline_solver_ops: int
    reference_solver_ops: int
    method_solver_ops: int
    baseline_solver_savings: int
    reference_solver_savings: int
    reference_savings_recovery: float | None
    final_verified: bool
    unsafe_accepted_reductions: int
    false_proposals_on_no_compression_control: int
    learned_weighted_sum_proxy: int | None


@dataclass(frozen=True)
class FrozenV033Scorer:
    proposer: LearnedCompressionProposer
    footprint: LearnedCompressorFootprint


def fit_frozen_v033_scorer() -> FrozenV033Scorer:
    proposer = LearnedCompressionProposer().fit(
        learned_compression_training_examples()
    )
    return FrozenV033Scorer(
        proposer=proposer,
        footprint=inspect_learned_compressor(proposer),
    )


def _sort_scored(
    items: Iterable[ScoredCandidate],
) -> tuple[ScoredCandidate, ...]:
    output = list(items)
    output.sort(
        key=lambda item: (
            -item.score,
            item.candidate.row_index,
            int(item.candidate.target[1:]),
        )
    )
    return tuple(output)


def _column_counts(
    example: LearnedCompressionExample,
) -> tuple[int, ...]:
    system = example.full_system
    return tuple(
        sum(
            1
            for row in system.A
            if row[column] != 0
        )
        for column in range(system.dimension)
    )


def _base_structural_scores(
    example: LearnedCompressionExample,
    candidate: AffineCandidate,
) -> dict[str, float]:
    system = example.full_system
    n = float(system.dimension)
    row = system.A[candidate.row_index]
    row_nnz = sum(1 for value in row if value != 0)
    counts = _column_counts(example)
    target_index = system.variables.index(candidate.target)
    target_count = counts[target_index]

    dependency_indices = [
        system.variables.index(name)
        for name, _ in candidate.coefficients
    ]
    dependency_count_mean = mean(
        counts[index]
        for index in dependency_indices
    )

    target_leaf = 1.0 - target_count / n
    row_sparsity = 1.0 - row_nnz / n
    sparsity_incidence = (
        1.0
        - 0.5
        * (
            row_nnz / n
            + target_count / n
        )
    )
    dependency_contrast = max(
        0.0,
        min(
            1.0,
            0.5
            + 0.5
            * (
                dependency_count_mean
                - target_count
            )
            / n,
        ),
    )
    markowitz_count = (
        max(0, row_nnz - 1)
        * max(0, target_count - 1)
    )
    markowitz = 1.0 / (1.0 + markowitz_count)
    structural_combo = (
        0.35 * target_leaf
        + 0.35 * row_sparsity
        + 0.30 * dependency_contrast
    )

    return {
        "target_leaf": target_leaf,
        "row_sparsity": row_sparsity,
        "sparsity_incidence": sparsity_incidence,
        "dependency_contrast": dependency_contrast,
        "markowitz": markowitz,
        "structural_combo": structural_combo,
    }


def _random_score(
    example: LearnedCompressionExample,
    candidate: AffineCandidate,
) -> float:
    payload = (
        "v034-random|"
        + repr(
            (
                example.full_system.A,
                example.full_system.b,
            )
        )
        + f"|{candidate.row_index}|{candidate.target}"
    ).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float(2**64 - 1)


def score_candidates(
    example: LearnedCompressionExample,
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[ScoredCandidate, ...]:
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")

    if method == "learned_mlp":
        return frozen_scorer.proposer.score(example)

    output: list[ScoredCandidate] = []
    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        if method == "deterministic_random":
            score = _random_score(example, candidate)
        else:
            score = _base_structural_scores(
                example,
                candidate,
            )[method]

        if not math.isfinite(score):
            raise ValueError("non-finite scorer output")
        if score < 0.0 or score > 1.0:
            raise ValueError(
                f"score outside [0,1] for {method}: {score}"
            )

        output.append(
            ScoredCandidate(
                candidate=candidate,
                score=float(score),
            )
        )

    return _sort_scored(output)


def _reference_keys(
    example: LearnedCompressionExample,
) -> frozenset[tuple[int, str]]:
    return frozenset(
        (rule.row_index, rule.target)
        for rule in example.oracle_dependencies
    )


def _thresholded(
    scored: tuple[ScoredCandidate, ...],
    threshold: float,
) -> tuple[ScoredCandidate, ...]:
    return tuple(
        item
        for item in scored
        if item.score >= threshold
    )


def _micro_proposal_metrics(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    threshold: float,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[float, float, float, int, int, int]:
    proposed_total = 0
    reference_total = 0
    true_positive_total = 0

    for example in examples:
        reference = _reference_keys(example)
        proposed = {
            item.candidate.key
            for item in _thresholded(
                score_candidates(
                    example,
                    method,
                    frozen_scorer=frozen_scorer,
                ),
                threshold,
            )
        }
        proposed_total += len(proposed)
        reference_total += len(reference)
        true_positive_total += len(
            proposed.intersection(reference)
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
    return (
        precision,
        recall,
        f1,
        proposed_total,
        reference_total,
        true_positive_total,
    )


def calibrate_threshold(
    examples: Iterable[LearnedCompressionExample],
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> ThresholdCalibration:
    examples = tuple(examples)
    candidates: list[ThresholdCalibration] = []

    for threshold in THRESHOLD_GRID:
        (
            precision,
            recall,
            f1,
            proposed_total,
            reference_total,
            true_positive_total,
        ) = _micro_proposal_metrics(
            examples,
            method,
            threshold,
            frozen_scorer=frozen_scorer,
        )
        candidates.append(
            ThresholdCalibration(
                method=method,
                threshold=threshold,
                micro_precision=precision,
                micro_recall=recall,
                micro_f1=f1,
                proposed_count=proposed_total,
                reference_count=reference_total,
                true_positive_count=true_positive_total,
            )
        )

    return max(
        candidates,
        key=lambda item: (
            item.micro_f1,
            item.micro_precision,
            item.threshold,
        ),
    )


def _baseline_solver_ops(
    example: LearnedCompressionExample,
) -> int:
    _, counts = solve_exact_gauss_jordan(
        example.full_system
    )
    return counts.arithmetic_ops


def observe_stopping_method(
    example: LearnedCompressionExample,
    method: str,
    calibration: ThresholdCalibration,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> StoppingObservation:
    scored = score_candidates(
        example,
        method,
        frozen_scorer=frozen_scorer,
    )
    proposals = _thresholded(
        scored,
        calibration.threshold,
    )
    checked = check_scored_proposals(
        example,
        scored,
        proposal_budget=len(proposals),
    )

    reference_keys = _reference_keys(example)
    proposed_keys = {
        item.candidate.key
        for item in proposals
    }
    accepted_keys = {
        candidate.key
        for candidate in checked.accepted_candidates
    }

    reference_materialized = materialize_reduction(
        example,
        oracle_candidates(example),
    )
    if reference_materialized is None:
        raise AssertionError(
            "generator reference reduction failed"
        )

    baseline_ops = _baseline_solver_ops(example)
    reference_ops = (
        reference_materialized.solver_counts.arithmetic_ops
    )
    method_ops = (
        checked.materialized.solver_counts.arithmetic_ops
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
        checked.materialized.verified
        and checked.materialized.ground_truth_equivalent
    )

    inferred_retained = (
        example.apparent_dimension
        - len(checked.accepted_candidates)
    )

    learned_proxy: int | None
    if method == "learned_mlp":
        learned_proxy = (
            len(scored)
            * frozen_scorer.footprint.weighted_sum_terms_per_candidate
        )
    else:
        learned_proxy = None

    return StoppingObservation(
        method=method,
        threshold=calibration.threshold,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        candidate_count=len(scored),
        proposed_count=len(proposals),
        raw_true_positive_count=len(
            proposed_keys.intersection(reference_keys)
        ),
        raw_reference_count=len(reference_keys),
        accepted_count=len(checked.accepted_candidates),
        accepted_reference_count=accepted_reference,
        accepted_nonreference_valid_count=accepted_nonreference,
        rejected_count=len(checked.rejected_candidates),
        inferred_retained_dimension=inferred_retained,
        retained_dimension_error=(
            inferred_retained - example.core_dimension
        ),
        baseline_solver_ops=baseline_ops,
        reference_solver_ops=reference_ops,
        method_solver_ops=method_ops,
        baseline_solver_savings=method_savings,
        reference_solver_savings=reference_savings,
        reference_savings_recovery=recovery,
        final_verified=final_verified,
        unsafe_accepted_reductions=(
            0
            if final_verified
            else len(checked.accepted_candidates)
        ),
        false_proposals_on_no_compression_control=(
            len(proposals)
            if example.apparent_dimension
            == example.core_dimension
            else 0
        ),
        learned_weighted_sum_proxy=learned_proxy,
    )


def aggregate_stopping_observations(
    rows: Iterable[StoppingObservation],
) -> dict[str, object]:
    observations = tuple(rows)
    if not observations:
        raise ValueError("at least one observation is required")

    proposed_total = sum(
        row.proposed_count
        for row in observations
    )
    reference_total = sum(
        row.raw_reference_count
        for row in observations
    )
    true_positive_total = sum(
        row.raw_true_positive_count
        for row in observations
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

    savings_rows = [
        row
        for row in observations
        if row.reference_savings_recovery is not None
    ]

    learned_proxy_rows = [
        row.learned_weighted_sum_proxy
        for row in observations
        if row.learned_weighted_sum_proxy is not None
    ]

    grouped: dict[
        tuple[int, int],
        list[StoppingObservation],
    ] = {}
    for row in observations:
        grouped.setdefault(
            (row.core_dimension, row.apparent_dimension),
            [],
        ).append(row)

    cells: list[dict[str, object]] = []
    for (k, n), cell_rows in sorted(grouped.items()):
        cell_savings = [
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
                "mean_inferred_retained_dimension": mean(
                    row.inferred_retained_dimension
                    for row in cell_rows
                ),
                "mean_abs_retained_dimension_error": mean(
                    abs(row.retained_dimension_error)
                    for row in cell_rows
                ),
                "mean_method_solver_ops": mean(
                    row.method_solver_ops
                    for row in cell_rows
                ),
                "mean_reference_savings_recovery": (
                    mean(float(value) for value in cell_savings)
                    if cell_savings
                    else None
                ),
                "verified_retention": mean(
                    1.0 if row.final_verified else 0.0
                    for row in cell_rows
                ),
            }
        )

    return {
        "method": observations[0].method,
        "threshold": observations[0].threshold,
        "count": len(observations),
        "raw_proposal_micro_precision": precision,
        "raw_proposal_micro_recall": recall,
        "raw_proposal_micro_f1": f1,
        "proposed_count": proposed_total,
        "reference_count": reference_total,
        "true_positive_count": true_positive_total,
        "false_proposals_on_no_compression_controls": sum(
            row.false_proposals_on_no_compression_control
            for row in observations
        ),
        "examples_with_any_accepted_compression": sum(
            1
            for row in observations
            if row.accepted_count > 0
        ),
        "mean_accepted_eliminations": mean(
            row.accepted_count
            for row in observations
        ),
        "mean_accepted_reference_eliminations": mean(
            row.accepted_reference_count
            for row in observations
        ),
        "mean_accepted_nonreference_valid_eliminations": mean(
            row.accepted_nonreference_valid_count
            for row in observations
        ),
        "total_fail_closed_rejections": sum(
            row.rejected_count
            for row in observations
        ),
        "unsafe_accepted_reduction_count": sum(
            row.unsafe_accepted_reductions
            for row in observations
        ),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in observations
        ),
        "mean_inferred_retained_dimension": mean(
            row.inferred_retained_dimension
            for row in observations
        ),
        "mean_abs_retained_dimension_error": mean(
            abs(row.retained_dimension_error)
            for row in observations
        ),
        "mean_signed_retained_dimension_error": mean(
            row.retained_dimension_error
            for row in observations
        ),
        "exact_retained_dimension_match_rate": mean(
            1.0 if row.retained_dimension_error == 0 else 0.0
            for row in observations
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in observations
        ),
        "mean_reference_solver_ops": mean(
            row.reference_solver_ops
            for row in observations
        ),
        "mean_method_solver_ops": mean(
            row.method_solver_ops
            for row in observations
        ),
        "mean_solver_savings_vs_baseline": mean(
            row.baseline_solver_savings
            for row in observations
        ),
        "mean_reference_savings_recovery": (
            mean(
                float(row.reference_savings_recovery)
                for row in savings_rows
            )
            if savings_rows
            else None
        ),
        "mean_learned_weighted_sum_proxy": (
            mean(
                int(value)
                for value in learned_proxy_rows
            )
            if learned_proxy_rows
            else None
        ),
        "cells": cells,
    }
