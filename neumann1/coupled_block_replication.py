from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .coupled_block import (
    CoupledBlockObservation,
    aggregate_coupled_block,
    observe_coupled_block,
)
from .coupled_block_dataset import (
    CoupledBlockExample,
)
from .learned_compression import (
    enumerate_affine_candidates,
    validate_candidate_against_system,
)
from .stopping_gauntlet import (
    FrozenV033Scorer,
)


@dataclass(frozen=True)
class CandidateVisibilityObservation:
    core_dimension: int
    apparent_dimension: int
    block_count: int
    expected_candidate_count: int
    enumerated_candidate_count: int
    all_candidate_algebra_valid: bool


def observe_candidate_visibility(
    example: CoupledBlockExample,
) -> CandidateVisibilityObservation:
    candidates = enumerate_affine_candidates(
        example.full_system
    )
    algebra_valid = all(
        validate_candidate_against_system(
            example.full_system,
            candidate,
        )[0]
        for candidate in candidates
    )

    expected = (
        0
        if example.block_count == 0
        else 4 * example.block_count
    )

    return CandidateVisibilityObservation(
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        block_count=example.block_count,
        expected_candidate_count=expected,
        enumerated_candidate_count=len(
            candidates
        ),
        all_candidate_algebra_valid=(
            algebra_valid
        ),
    )


def run_replication_observations(
    examples: Iterable[CoupledBlockExample],
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[
    tuple[CoupledBlockObservation, ...],
    tuple[CandidateVisibilityObservation, ...],
]:
    examples = tuple(examples)
    coupled_rows = tuple(
        observe_coupled_block(
            example,
            frozen_scorer=frozen_scorer,
        )
        for example in examples
    )
    visibility_rows = tuple(
        observe_candidate_visibility(
            example
        )
        for example in examples
    )
    return (
        coupled_rows,
        visibility_rows,
    )


def aggregate_replication(
    coupled_rows: Iterable[
        CoupledBlockObservation
    ],
    visibility_rows: Iterable[
        CandidateVisibilityObservation
    ],
) -> dict[str, object]:
    coupled_rows = tuple(
        coupled_rows
    )
    visibility_rows = tuple(
        visibility_rows
    )
    if not coupled_rows:
        raise ValueError(
            "coupled observations are required"
        )
    if len(coupled_rows) != len(
        visibility_rows
    ):
        raise ValueError(
            "replication observation count mismatch"
        )

    base = aggregate_coupled_block(
        coupled_rows
    )

    active_visibility = tuple(
        row
        for row in visibility_rows
        if row.block_count > 0
    )
    if not active_visibility:
        raise ValueError(
            "active visibility observations are required"
        )

    h4a = all(
        row.enumerated_candidate_count
        == row.expected_candidate_count
        for row in active_visibility
    )
    h4b = all(
        row.all_candidate_algebra_valid
        for row in active_visibility
    )

    exact_visibility_rate = mean(
        1.0
        if (
            row.enumerated_candidate_count
            == row.expected_candidate_count
        )
        else 0.0
        for row in active_visibility
    )
    algebra_valid_example_rate = mean(
        1.0
        if row.all_candidate_algebra_valid
        else 0.0
        for row in active_visibility
    )

    h1 = (
        base[
            "mean_oracle_retained_dimension_error"
        ]
        == 0.0
    )
    h2 = (
        base[
            "mean_one_row_elimination_recovery"
        ]
        <= 0.75
    )
    h3 = (
        base[
            "mean_one_row_solver_savings_recovery"
        ]
        <= 0.90
    )
    h5 = (
        base[
            "broad_hard_cell_count"
        ]
        >= 5
    )

    safe = (
        base[
            "one_row_verified_retention"
        ]
        == 1.0
        and base[
            "oracle_verified_retention"
        ]
        == 1.0
        and base[
            "unsafe_one_row_reductions"
        ]
        == 0
        and base[
            "unsafe_block_reductions"
        ]
        == 0
    )

    if not safe:
        status = (
            "INVALID_FAMILY_OR_CHECKER"
        )
    elif all(
        (
            h1,
            h2,
            h3,
            h4a,
            h4b,
            h5,
        )
    ):
        status = (
            "HARDER_FAMILY_VALIDATED"
        )
    else:
        status = (
            "FAMILY_NOT_HARD_ENOUGH"
        )

    return {
        "count": base["count"],
        "active_count": base[
            "active_count"
        ],
        "control_count": base[
            "control_count"
        ],
        "one_row_verified_retention": base[
            "one_row_verified_retention"
        ],
        "oracle_verified_retention": base[
            "oracle_verified_retention"
        ],
        "unsafe_one_row_reductions": base[
            "unsafe_one_row_reductions"
        ],
        "unsafe_block_reductions": base[
            "unsafe_block_reductions"
        ],
        "mean_one_row_elimination_recovery": base[
            "mean_one_row_elimination_recovery"
        ],
        "mean_one_row_solver_savings_recovery": base[
            "mean_one_row_solver_savings_recovery"
        ],
        "descriptive_active_progress_rate": base[
            "active_progress_rate"
        ],
        "mean_oracle_retained_dimension_error": base[
            "mean_oracle_retained_dimension_error"
        ],
        "broad_hard_cell_count": base[
            "broad_hard_cell_count"
        ],
        "candidate_visibility": {
            "active_exact_candidate_count_rate": (
                exact_visibility_rate
            ),
            "active_algebra_valid_example_rate": (
                algebra_valid_example_rate
            ),
            "all_active_candidate_counts_exact": (
                h4a
            ),
            "all_active_candidate_algebra_valid": (
                h4b
            ),
        },
        "harder_family_gates": {
            "H1_oracle_core_exact": h1,
            "H2_one_row_elimination_recovery_le_0_75": h2,
            "H3_one_row_solver_recovery_le_0_90": h3,
            "H4a_candidate_count_exact_100pct": (
                h4a
            ),
            "H4b_candidate_algebra_valid_100pct": (
                h4b
            ),
            "H5_broad_hard_cells_ge_5": h5,
        },
        "family_status": status,
        "cells": base["cells"],
    }
