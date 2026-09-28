from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .block_compression import (
    materialize_block_reduction,
    oracle_block_candidates,
    validate_block_candidate,
)
from .block_compression_dataset import (
    CoupledBlockExample,
)
from .learned_compression import (
    enumerate_affine_candidates,
)
from .structural_compression import (
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


@dataclass(frozen=True)
class BlockCompressionObservation:
    core_dimension: int
    apparent_dimension: int
    expected_block_count: int
    scalar_candidate_count: int
    oracle_block_proposal_count: int
    individually_validated_block_count: int
    accepted_block_count: int
    retained_dimension: int
    baseline_solver_ops: int
    scalar_solver_ops: int
    oracle_solver_ops: int
    oracle_solver_savings: int
    oracle_solver_savings_fraction: float
    reconstruction_ops: int
    verification_ops: int
    certificate_integer_scalars: int
    certificate_bytes: int
    all_nonzero_coefficients_abs_ge_2: bool
    baseline_verified: bool
    final_verified: bool
    ground_truth_equivalent: bool
    unsafe_accepted_reductions: int


def observe_block_compression(
    example: CoupledBlockExample,
) -> BlockCompressionObservation:
    system = example.full_system

    baseline_answer, baseline_counts = (
        solve_exact_gauss_jordan(system)
    )
    baseline_verified, _ = (
        verify_exact_full_system(
            system,
            baseline_answer,
        )
    )
    baseline_ops = (
        baseline_counts.arithmetic_ops
    )

    scalar_candidates = (
        enumerate_affine_candidates(system)
    )

    oracle_candidates = (
        oracle_block_candidates(example)
    )
    individually_validated = sum(
        1
        for candidate in oracle_candidates
        if validate_block_candidate(
            system,
            candidate,
        )[0]
    )

    materialized = (
        materialize_block_reduction(
            example,
            oracle_candidates,
        )
    )

    coefficient_invariant = all(
        value == 0 or abs(value) >= 2
        for row in system.A
        for value in row
    )

    if materialized is None:
        accepted_count = 0
        retained_dimension = (
            system.dimension
        )
        oracle_ops = baseline_ops
        reconstruction_ops = 0
        verification_ops = 0
        certificate_integer_scalars = 0
        certificate_bytes = 0
        final_verified = False
        equivalent = False
    else:
        accepted_count = len(
            materialized.accepted_blocks
        )
        retained_dimension = (
            materialized.retained_system.dimension
        )
        oracle_ops = (
            materialized.solver_counts.arithmetic_ops
        )
        reconstruction_ops = (
            materialized.reconstruction_counts.arithmetic_ops
        )
        verification_ops = (
            materialized.verification_counts.arithmetic_ops
        )
        certificate_integer_scalars = (
            materialized.certificate_integer_scalars
        )
        certificate_bytes = (
            materialized.certificate_bytes
        )
        final_verified = (
            materialized.verified
        )
        equivalent = (
            materialized.ground_truth_equivalent
        )

    savings = baseline_ops - oracle_ops
    savings_fraction = (
        savings / baseline_ops
        if baseline_ops > 0
        else 0.0
    )

    unsafe = (
        0
        if final_verified and equivalent
        else accepted_count
    )

    return BlockCompressionObservation(
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        expected_block_count=(
            (example.apparent_dimension
             - example.core_dimension)
            // 2
        ),
        scalar_candidate_count=len(
            scalar_candidates
        ),
        oracle_block_proposal_count=len(
            oracle_candidates
        ),
        individually_validated_block_count=(
            individually_validated
        ),
        accepted_block_count=(
            accepted_count
        ),
        retained_dimension=retained_dimension,
        baseline_solver_ops=baseline_ops,
        scalar_solver_ops=baseline_ops,
        oracle_solver_ops=oracle_ops,
        oracle_solver_savings=savings,
        oracle_solver_savings_fraction=(
            savings_fraction
        ),
        reconstruction_ops=(
            reconstruction_ops
        ),
        verification_ops=verification_ops,
        certificate_integer_scalars=(
            certificate_integer_scalars
        ),
        certificate_bytes=(
            certificate_bytes
        ),
        all_nonzero_coefficients_abs_ge_2=(
            coefficient_invariant
        ),
        baseline_verified=(
            baseline_verified
        ),
        final_verified=final_verified,
        ground_truth_equivalent=equivalent,
        unsafe_accepted_reductions=unsafe,
    )


def _slope(
    points: Iterable[tuple[float, float]],
) -> float:
    points = tuple(points)
    if len(points) < 2:
        return 0.0

    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    x_mean = mean(xs)
    y_mean = mean(ys)

    denominator = sum(
        (x - x_mean) ** 2
        for x in xs
    )
    if denominator == 0:
        return 0.0

    numerator = sum(
        (x - x_mean)
        * (y - y_mean)
        for x, y in points
    )
    return numerator / denominator


def aggregate_block_compression(
    observations: Iterable[
        BlockCompressionObservation
    ],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError(
            "at least one block observation is required"
        )

    grouped: dict[
        tuple[int, int],
        list[BlockCompressionObservation],
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
                "mean_baseline_solver_ops": mean(
                    row.baseline_solver_ops
                    for row in cell_rows
                ),
                "mean_scalar_solver_ops": mean(
                    row.scalar_solver_ops
                    for row in cell_rows
                ),
                "mean_oracle_solver_ops": mean(
                    row.oracle_solver_ops
                    for row in cell_rows
                ),
                "mean_oracle_solver_savings": mean(
                    row.oracle_solver_savings
                    for row in cell_rows
                ),
                "mean_oracle_solver_savings_fraction": mean(
                    row.oracle_solver_savings_fraction
                    for row in cell_rows
                ),
                "mean_reconstruction_ops": mean(
                    row.reconstruction_ops
                    for row in cell_rows
                ),
                "mean_verification_ops": mean(
                    row.verification_ops
                    for row in cell_rows
                ),
                "mean_certificate_bytes": mean(
                    row.certificate_bytes
                    for row in cell_rows
                ),
                "mean_retained_dimension": mean(
                    row.retained_dimension
                    for row in cell_rows
                ),
                "scalar_candidate_count_total": sum(
                    row.scalar_candidate_count
                    for row in cell_rows
                ),
                "verified_retention": mean(
                    1.0
                    if row.final_verified
                    and row.ground_truth_equivalent
                    else 0.0
                    for row in cell_rows
                ),
            }
        )

    scaling = {}
    for k in sorted(
        {
            row.core_dimension
            for row in rows
        }
    ):
        k_cells = [
            cell
            for cell in cells
            if cell["core_dimension"] == k
        ]
        scaling[str(k)] = {
            "baseline_solver_ops_slope": _slope(
                (
                    float(
                        cell["apparent_dimension"]
                    ),
                    float(
                        cell[
                            "mean_baseline_solver_ops"
                        ]
                    ),
                )
                for cell in k_cells
            ),
            "scalar_solver_ops_slope": _slope(
                (
                    float(
                        cell["apparent_dimension"]
                    ),
                    float(
                        cell[
                            "mean_scalar_solver_ops"
                        ]
                    ),
                )
                for cell in k_cells
            ),
            "block_oracle_solver_ops_slope": _slope(
                (
                    float(
                        cell["apparent_dimension"]
                    ),
                    float(
                        cell[
                            "mean_oracle_solver_ops"
                        ]
                    ),
                )
                for cell in k_cells
            ),
        }

    scalar_zero = all(
        row.scalar_candidate_count == 0
        for row in rows
    )
    verified = all(
        row.final_verified
        and row.ground_truth_equivalent
        for row in rows
    )
    unsafe_zero = all(
        row.unsafe_accepted_reductions == 0
        for row in rows
    )
    retained_exact = all(
        row.retained_dimension
        == row.core_dimension
        for row in rows
    )
    coefficient_invariant = all(
        row.all_nonzero_coefficients_abs_ge_2
        for row in rows
    )
    proposal_count_exact = all(
        row.oracle_block_proposal_count
        == row.expected_block_count
        and row.individually_validated_block_count
        == row.expected_block_count
        and row.accepted_block_count
        == row.expected_block_count
        for row in rows
    )

    positive_compression_cells = all(
        cell["mean_oracle_solver_savings"] > 0
        for cell in cells
        if cell["apparent_dimension"]
        > cell["core_dimension"]
    )

    n32_cells = [
        cell
        for cell in cells
        if cell["apparent_dimension"] == 32
    ]
    n32_fraction_gate = (
        len(n32_cells) == 2
        and all(
            cell[
                "mean_oracle_solver_savings_fraction"
            ]
            >= 0.80
            for cell in n32_cells
        )
    )

    safety_exactness = (
        coefficient_invariant
        and scalar_zero
        and verified
        and unsafe_zero
        and retained_exact
        and proposal_count_exact
    )

    if not safety_exactness:
        decision = "REJECT_BLOCK_OPERATOR"
    elif (
        positive_compression_cells
        and n32_fraction_gate
    ):
        decision = "PROCEED_BLOCK_DISCOVERY"
    else:
        decision = "HOLD_BLOCK_DISCOVERY"

    return {
        "count": len(rows),
        "cells": cells,
        "scaling": scaling,
        "all_nonzero_coefficients_abs_ge_2": (
            coefficient_invariant
        ),
        "scalar_candidate_count_zero_everywhere": (
            scalar_zero
        ),
        "oracle_block_count_exact_everywhere": (
            proposal_count_exact
        ),
        "verified_retention": mean(
            1.0
            if row.final_verified
            and row.ground_truth_equivalent
            else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            row.unsafe_accepted_reductions
            for row in rows
        ),
        "retained_dimension_exact_everywhere": (
            retained_exact
        ),
        "positive_savings_all_compression_cells": (
            positive_compression_cells
        ),
        "n32_savings_fraction_ge_0_80_both_k": (
            n32_fraction_gate
        ),
        "mean_baseline_solver_ops": mean(
            row.baseline_solver_ops
            for row in rows
        ),
        "mean_oracle_solver_ops": mean(
            row.oracle_solver_ops
            for row in rows
        ),
        "mean_oracle_solver_savings": mean(
            row.oracle_solver_savings
            for row in rows
        ),
        "mean_reconstruction_ops": mean(
            row.reconstruction_ops
            for row in rows
        ),
        "mean_verification_ops": mean(
            row.verification_ops
            for row in rows
        ),
        "mean_certificate_bytes": mean(
            row.certificate_bytes
            for row in rows
        ),
        "continuation_decision": decision,
    }
