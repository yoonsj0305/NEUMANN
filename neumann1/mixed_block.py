from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from statistics import mean
from typing import Iterable

from .coupled_block import (
    BlockCandidate,
    FractionAffineRule,
    derive_block_candidate,
    validate_block_candidate,
)
from .learned_compression import (
    AffineCandidate,
    enumerate_affine_candidates,
    validate_candidate_against_system,
)
from .mixed_block_dataset import (
    MixedBlockExample,
)
from .residual_learning import (
    observe_deterministic_residual_policy,
)
from .stopping_gauntlet import (
    FrozenV033Scorer,
)
from .structural_compression import (
    ExactLinearSystem,
    GaussianOperationCounts,
    ReconstructionOperationCounts,
    VerificationOperationCounts,
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


@dataclass(frozen=True)
class MixedMaterialization:
    easy_candidates: tuple[
        AffineCandidate, ...
    ]
    block_candidates: tuple[
        BlockCandidate, ...
    ]
    retained_system: ExactLinearSystem
    reconstruction_order: tuple[
        FractionAffineRule, ...
    ]
    retained_answer: dict[
        str, Fraction
    ]
    full_answer: dict[
        str, Fraction
    ]
    solver_counts: (
        GaussianOperationCounts
    )
    reconstruction_counts: (
        ReconstructionOperationCounts
    )
    verification_counts: (
        VerificationOperationCounts
    )
    verified: bool
    ground_truth_equivalent: bool


@dataclass(frozen=True)
class MixedFamilyObservation:
    core_dimension: int
    apparent_dimension: int
    easy_oracle_count: int
    oracle_block_count: int
    oracle_elimination_count: int
    one_row_candidate_count: int
    one_row_first_stage_accepted: int
    one_row_residual_accepted: int
    one_row_total_accepted: int
    one_row_retained_dimension: int
    oracle_retained_dimension: int
    retained_dimension_gap: int
    baseline_solver_ops: int
    one_row_solver_ops: int
    oracle_solver_ops: int
    oracle_solver_savings: int
    one_row_solver_savings: int
    one_row_elimination_recovery: (
        float | None
    )
    one_row_solver_savings_recovery: (
        float | None
    )
    oracle_reconstruction_ops: int
    oracle_verification_ops: int
    one_row_verified: bool
    oracle_verified: bool
    unsafe_one_row_reductions: int
    unsafe_mixed_oracle_reductions: int
    easy_candidates_visible: bool
    expected_coupled_candidates_visible: bool


def _target_sort_key(
    name: str,
) -> int:
    return int(name[1:])


def oracle_easy_candidates(
    example: MixedBlockExample,
) -> tuple[
    AffineCandidate, ...
]:
    candidate_map = {
        candidate.key: candidate
        for candidate in enumerate_affine_candidates(
            example.full_system
        )
    }

    output: list[
        AffineCandidate
    ] = []
    for rule in (
        example.oracle_easy_rules
    ):
        candidate = candidate_map.get(
            (
                rule.row_index,
                rule.target,
            )
        )
        if candidate is None:
            raise AssertionError(
                "declared easy rule is not an affine candidate"
            )
        ok, _ = (
            validate_candidate_against_system(
                example.full_system,
                candidate,
            )
        )
        if not ok:
            raise AssertionError(
                "declared easy rule failed exact affine validation"
            )
        output.append(
            candidate
        )

    output.sort(
        key=lambda candidate: (
            candidate.row_index,
            _target_sort_key(
                candidate.target
            ),
        )
    )
    return tuple(output)


def oracle_block_candidates(
    example: MixedBlockExample,
) -> tuple[
    BlockCandidate, ...
]:
    output: list[
        BlockCandidate
    ] = []

    for block in (
        example.oracle_blocks
    ):
        candidate = derive_block_candidate(
            example.full_system,
            block.row_indices,
            block.targets,
        )
        if candidate is None:
            raise AssertionError(
                "declared mixed block is singular"
            )
        ok, _ = validate_block_candidate(
            example.full_system,
            candidate,
        )
        if not ok:
            raise AssertionError(
                "declared mixed block failed exact validation"
            )
        output.append(
            candidate
        )

    output.sort(
        key=lambda candidate: (
            candidate.row_indices,
            tuple(
                _target_sort_key(
                    target
                )
                for target
                in candidate.targets
            ),
        )
    )
    return tuple(output)


def _easy_rule(
    candidate: AffineCandidate,
) -> FractionAffineRule:
    return FractionAffineRule(
        target=candidate.target,
        constant=Fraction(
            candidate.constant
        ),
        coefficients=tuple(
            (
                dependency,
                Fraction(coefficient),
            )
            for dependency, coefficient
            in candidate.coefficients
        ),
    )


def _topological_rule_order(
    rules: tuple[
        FractionAffineRule, ...
    ],
    retained_variables: tuple[
        str, ...
    ],
) -> tuple[
    FractionAffineRule, ...
] | None:
    available = set(
        retained_variables
    )
    pending = list(rules)
    ordered: list[
        FractionAffineRule
    ] = []

    while pending:
        next_pending: list[
            FractionAffineRule
        ] = []
        progress = False

        for rule in pending:
            dependencies = {
                name
                for name, _
                in rule.coefficients
            }
            if dependencies.issubset(
                available
            ):
                ordered.append(
                    rule
                )
                available.add(
                    rule.target
                )
                progress = True
            else:
                next_pending.append(
                    rule
                )

        if not progress:
            return None
        pending = next_pending

    return tuple(
        ordered
    )


def _reconstruct_rules(
    retained_answer: dict[
        str, Fraction
    ],
    ordered: tuple[
        FractionAffineRule, ...
    ],
) -> tuple[
    dict[str, Fraction],
    ReconstructionOperationCounts,
]:
    answer = dict(
        retained_answer
    )
    counts = (
        ReconstructionOperationCounts()
    )

    for rule in ordered:
        total = Fraction(
            rule.constant
        )
        for index, (
            dependency,
            coefficient,
        ) in enumerate(
            rule.coefficients
        ):
            if dependency not in answer:
                raise ValueError(
                    "missing mixed reconstruction dependency"
                )

            product = (
                coefficient
                * answer[dependency]
            )
            counts.multiplications += 1

            if (
                rule.constant != 0
                or index > 0
            ):
                total += product
                counts.additions += 1
            else:
                total = product

        answer[
            rule.target
        ] = total

    return answer, counts


def materialize_mixed_reduction(
    example: MixedBlockExample,
    easy_candidates: tuple[
        AffineCandidate, ...
    ],
    block_candidates: tuple[
        BlockCandidate, ...
    ],
) -> MixedMaterialization | None:
    system = example.full_system

    easy_rows = [
        candidate.row_index
        for candidate
        in easy_candidates
    ]
    easy_targets = [
        candidate.target
        for candidate
        in easy_candidates
    ]
    block_rows = [
        row
        for candidate
        in block_candidates
        for row
        in candidate.row_indices
    ]
    block_targets = [
        target
        for candidate
        in block_candidates
        for target
        in candidate.targets
    ]

    all_rows = (
        easy_rows
        + block_rows
    )
    all_targets = (
        easy_targets
        + block_targets
    )

    if len(all_rows) != len(
        set(all_rows)
    ):
        return None
    if len(all_targets) != len(
        set(all_targets)
    ):
        return None

    for candidate in (
        easy_candidates
    ):
        ok, _ = (
            validate_candidate_against_system(
                system,
                candidate,
            )
        )
        if not ok:
            return None

    for candidate in (
        block_candidates
    ):
        ok, _ = (
            validate_block_candidate(
                system,
                candidate,
            )
        )
        if not ok:
            return None

    removed_rows = set(
        all_rows
    )
    eliminated = set(
        all_targets
    )

    retained_variables = tuple(
        variable
        for variable
        in system.variables
        if variable
        not in eliminated
    )
    retained_rows = tuple(
        row_index
        for row_index
        in range(
            system.dimension
        )
        if row_index
        not in removed_rows
    )

    if len(retained_variables) != len(
        retained_rows
    ):
        return None
    if not retained_variables:
        return None

    all_rules = tuple(
        [_easy_rule(candidate)
         for candidate
         in easy_candidates]
        + [
            rule
            for candidate
            in block_candidates
            for rule
            in candidate.rules
        ]
    )

    ordered = _topological_rule_order(
        all_rules,
        retained_variables,
    )
    if ordered is None:
        return None

    retained_columns = tuple(
        system.variables.index(
            variable
        )
        for variable
        in retained_variables
    )
    retained_A = tuple(
        tuple(
            system.A[
                row_index
            ][column]
            for column
            in retained_columns
        )
        for row_index
        in retained_rows
    )
    retained_b = tuple(
        system.b[
            row_index
        ]
        for row_index
        in retained_rows
    )

    ground_truth_map = dict(
        zip(
            system.variables,
            system.ground_truth,
        )
    )
    retained_ground_truth = tuple(
        ground_truth_map[
            variable
        ]
        for variable
        in retained_variables
    )

    retained_system = ExactLinearSystem(
        variables=(
            retained_variables
        ),
        A=retained_A,
        b=retained_b,
        ground_truth=(
            retained_ground_truth
        ),
    )

    try:
        (
            retained_answer,
            solver_counts,
        ) = solve_exact_gauss_jordan(
            retained_system
        )
    except ValueError:
        return None

    try:
        (
            full_answer,
            reconstruction_counts,
        ) = _reconstruct_rules(
            retained_answer,
            ordered,
        )
    except ValueError:
        return None

    (
        verified,
        verification_counts,
    ) = verify_exact_full_system(
        system,
        full_answer,
    )

    ground_truth_equivalent = (
        verified
        and all(
            full_answer[
                variable
            ]
            == Fraction(expected)
            for variable, expected
            in zip(
                system.variables,
                system.ground_truth,
            )
        )
    )
    if not (
        ground_truth_equivalent
    ):
        return None

    return MixedMaterialization(
        easy_candidates=(
            easy_candidates
        ),
        block_candidates=(
            block_candidates
        ),
        retained_system=(
            retained_system
        ),
        reconstruction_order=(
            ordered
        ),
        retained_answer=(
            retained_answer
        ),
        full_answer=(
            full_answer
        ),
        solver_counts=(
            solver_counts
        ),
        reconstruction_counts=(
            reconstruction_counts
        ),
        verification_counts=(
            verification_counts
        ),
        verified=verified,
        ground_truth_equivalent=(
            ground_truth_equivalent
        ),
    )


def mixed_oracle_materialization(
    example: MixedBlockExample,
) -> MixedMaterialization:
    easy = oracle_easy_candidates(
        example
    )
    blocks = oracle_block_candidates(
        example
    )
    materialized = (
        materialize_mixed_reduction(
            example,
            easy,
            blocks,
        )
    )
    if materialized is None:
        raise AssertionError(
            "mixed oracle reduction failed materialization"
        )
    return materialized


def _column_counts(
    system: ExactLinearSystem,
) -> tuple[int, ...]:
    return tuple(
        sum(
            1
            for row in system.A
            if row[column] != 0
        )
        for column
        in range(
            system.dimension
        )
    )


def _visibility_checks(
    example: MixedBlockExample,
) -> tuple[
    bool, bool
]:
    candidates = (
        enumerate_affine_candidates(
            example.full_system
        )
    )
    candidate_keys = {
        candidate.key
        for candidate
        in candidates
    }

    easy_visible = all(
        (
            rule.row_index,
            rule.target,
        )
        in candidate_keys
        for rule
        in example.oracle_easy_rules
    )

    counts = _column_counts(
        example.full_system
    )
    easy_incidence_one = all(
        counts[
            example.full_system.variables.index(
                rule.target
            )
        ]
        == 1
        for rule
        in example.oracle_easy_rules
    )

    expected_coupled = (
        4 * example.block_count
    )
    block_row_set = {
        row
        for block
        in example.oracle_blocks
        for row
        in block.row_indices
    }
    coupled_candidate_count = sum(
        1
        for candidate
        in candidates
        if candidate.row_index
        in block_row_set
    )
    coupled_visible = (
        coupled_candidate_count
        >= expected_coupled
    )

    return (
        easy_visible
        and easy_incidence_one,
        coupled_visible,
    )


def observe_mixed_family(
    example: MixedBlockExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> MixedFamilyObservation:
    _, baseline_counts = (
        solve_exact_gauss_jordan(
            example.full_system
        )
    )

    one_row = (
        observe_deterministic_residual_policy(
            example,
            "markowitz",
            0.05,
            frozen_scorer=(
                frozen_scorer
            ),
        )
    )
    one_row_total = (
        one_row.target_leaf_accepted_count
        + one_row.residual_accepted_count
    )

    oracle = (
        mixed_oracle_materialization(
            example
        )
    )

    baseline_ops = (
        baseline_counts.arithmetic_ops
    )
    one_row_ops = (
        one_row.final_solver_ops
    )
    oracle_ops = (
        oracle.solver_counts.arithmetic_ops
    )

    oracle_savings = (
        baseline_ops
        - oracle_ops
    )
    one_row_savings = (
        baseline_ops
        - one_row_ops
    )

    if (
        example.oracle_elimination_count
        > 0
    ):
        elimination_recovery: (
            float | None
        ) = (
            one_row_total
            / example.oracle_elimination_count
        )
    else:
        elimination_recovery = None

    if oracle_savings > 0:
        solver_recovery: (
            float | None
        ) = (
            one_row_savings
            / oracle_savings
        )
    else:
        solver_recovery = None

    oracle_verified = (
        oracle.verified
        and oracle.ground_truth_equivalent
    )

    (
        easy_visible,
        coupled_visible,
    ) = _visibility_checks(
        example
    )

    return MixedFamilyObservation(
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
        ),
        easy_oracle_count=(
            example.easy_leaf_count
        ),
        oracle_block_count=(
            example.block_count
        ),
        oracle_elimination_count=(
            example.oracle_elimination_count
        ),
        one_row_candidate_count=len(
            enumerate_affine_candidates(
                example.full_system
            )
        ),
        one_row_first_stage_accepted=(
            one_row.target_leaf_accepted_count
        ),
        one_row_residual_accepted=(
            one_row.residual_accepted_count
        ),
        one_row_total_accepted=(
            one_row_total
        ),
        one_row_retained_dimension=(
            example.apparent_dimension
            - one_row_total
        ),
        oracle_retained_dimension=(
            oracle.retained_system.dimension
        ),
        retained_dimension_gap=(
            example.apparent_dimension
            - one_row_total
            - example.core_dimension
        ),
        baseline_solver_ops=(
            baseline_ops
        ),
        one_row_solver_ops=(
            one_row_ops
        ),
        oracle_solver_ops=(
            oracle_ops
        ),
        oracle_solver_savings=(
            oracle_savings
        ),
        one_row_solver_savings=(
            one_row_savings
        ),
        one_row_elimination_recovery=(
            elimination_recovery
        ),
        one_row_solver_savings_recovery=(
            solver_recovery
        ),
        oracle_reconstruction_ops=(
            oracle.reconstruction_counts.arithmetic_ops
        ),
        oracle_verification_ops=(
            oracle.verification_counts.arithmetic_ops
        ),
        one_row_verified=(
            one_row.final_verified
        ),
        oracle_verified=(
            oracle_verified
        ),
        unsafe_one_row_reductions=(
            one_row.unsafe_accepted_reductions
        ),
        unsafe_mixed_oracle_reductions=(
            0
            if oracle_verified
            else example.oracle_elimination_count
        ),
        easy_candidates_visible=(
            easy_visible
        ),
        expected_coupled_candidates_visible=(
            coupled_visible
        ),
    )


def aggregate_mixed_family(
    observations: Iterable[
        MixedFamilyObservation
    ],
) -> dict[str, object]:
    rows = tuple(
        observations
    )
    if not rows:
        raise ValueError(
            "at least one mixed-family observation is required"
        )

    active = tuple(
        row
        for row in rows
        if row.oracle_elimination_count > 0
    )
    controls = tuple(
        row
        for row in rows
        if row.oracle_elimination_count == 0
    )

    grouped: dict[
        tuple[int, int],
        list[MixedFamilyObservation],
    ] = {}
    for row in rows:
        grouped.setdefault(
            (
                row.core_dimension,
                row.apparent_dimension,
            ),
            [],
        ).append(row)

    cells: list[
        dict[str, object]
    ] = []
    broad_hard_cells = 0

    for (k, n), cell_rows in sorted(
        grouped.items()
    ):
        cell_active = [
            row
            for row in cell_rows
            if row.oracle_elimination_count > 0
        ]

        cell: dict[
            str, object
        ] = {
            "core_dimension": k,
            "apparent_dimension": n,
            "count": len(cell_rows),
            "mean_easy_oracle_count": mean(
                row.easy_oracle_count
                for row in cell_rows
            ),
            "mean_block_count": mean(
                row.oracle_block_count
                for row in cell_rows
            ),
            "mean_one_row_candidate_count": mean(
                row.one_row_candidate_count
                for row in cell_rows
            ),
            "mean_one_row_total_accepted": mean(
                row.one_row_total_accepted
                for row in cell_rows
            ),
            "mean_one_row_retained_dimension": mean(
                row.one_row_retained_dimension
                for row in cell_rows
            ),
            "mean_oracle_retained_dimension": mean(
                row.oracle_retained_dimension
                for row in cell_rows
            ),
            "mean_one_row_solver_ops": mean(
                row.one_row_solver_ops
                for row in cell_rows
            ),
            "mean_oracle_solver_ops": mean(
                row.oracle_solver_ops
                for row in cell_rows
            ),
            "one_row_verified_retention": mean(
                1.0
                if row.one_row_verified
                else 0.0
                for row in cell_rows
            ),
            "oracle_verified_retention": mean(
                1.0
                if row.oracle_verified
                else 0.0
                for row in cell_rows
            ),
        }

        if cell_active:
            cell_gap = mean(
                row.retained_dimension_gap
                for row in cell_active
            )
            cell_blocks = mean(
                row.oracle_block_count
                for row in cell_active
            )
            cell.update(
                {
                    "mean_one_row_elimination_recovery": mean(
                        float(
                            row.one_row_elimination_recovery
                        )
                        for row
                        in cell_active
                        if row.one_row_elimination_recovery
                        is not None
                    ),
                    "mean_one_row_solver_savings_recovery": mean(
                        float(
                            row.one_row_solver_savings_recovery
                        )
                        for row
                        in cell_active
                        if row.one_row_solver_savings_recovery
                        is not None
                    ),
                    "mean_retained_dimension_gap": (
                        cell_gap
                    ),
                }
            )

            if (
                cell_gap
                >= 0.5
                * cell_blocks
            ):
                broad_hard_cells += 1

        cells.append(
            cell
        )

    mean_elimination_recovery = mean(
        float(
            row.one_row_elimination_recovery
        )
        for row in active
        if row.one_row_elimination_recovery
        is not None
    )
    mean_solver_recovery = mean(
        float(
            row.one_row_solver_savings_recovery
        )
        for row in active
        if row.one_row_solver_savings_recovery
        is not None
    )
    progress_rate = mean(
        1.0
        if row.one_row_total_accepted > 0
        else 0.0
        for row in active
    )
    oracle_dimension_error = mean(
        abs(
            row.oracle_retained_dimension
            - row.core_dimension
        )
        for row in active
    )

    h1 = (
        oracle_dimension_error
        == 0.0
    )
    h2 = (
        mean_elimination_recovery
        <= 0.75
    )
    h3 = (
        mean_solver_recovery
        <= 0.90
    )
    h4 = (
        progress_rate
        >= 0.75
    )
    h5 = (
        broad_hard_cells
        >= 5
    )

    one_row_safe = (
        all(
            row.one_row_verified
            for row in rows
        )
        and sum(
            row.unsafe_one_row_reductions
            for row in rows
        )
        == 0
    )
    oracle_safe = (
        all(
            row.oracle_verified
            for row in rows
        )
        and sum(
            row.unsafe_mixed_oracle_reductions
            for row in rows
        )
        == 0
    )

    visibility_ok = all(
        (
            row.oracle_elimination_count == 0
            or (
                row.expected_coupled_candidates_visible
                and (
                    row.easy_oracle_count == 0
                    or row.easy_candidates_visible
                )
            )
        )
        for row in rows
    )

    if not (
        one_row_safe
        and oracle_safe
        and visibility_ok
    ):
        status = (
            "INVALID_FAMILY_OR_CHECKER"
        )
    elif all(
        (h1, h2, h3, h4, h5)
    ):
        status = (
            "HARDER_FAMILY_VALIDATED"
        )
    else:
        status = (
            "FAMILY_NOT_HARD_ENOUGH"
        )

    return {
        "count": len(rows),
        "active_count": len(active),
        "control_count": len(controls),
        "one_row_verified_retention": mean(
            1.0
            if row.one_row_verified
            else 0.0
            for row in rows
        ),
        "oracle_verified_retention": mean(
            1.0
            if row.oracle_verified
            else 0.0
            for row in rows
        ),
        "unsafe_one_row_reductions": sum(
            row.unsafe_one_row_reductions
            for row in rows
        ),
        "unsafe_mixed_oracle_reductions": sum(
            row.unsafe_mixed_oracle_reductions
            for row in rows
        ),
        "mean_one_row_elimination_recovery": (
            mean_elimination_recovery
        ),
        "mean_one_row_solver_savings_recovery": (
            mean_solver_recovery
        ),
        "active_progress_rate": (
            progress_rate
        ),
        "mean_oracle_retained_dimension_error": (
            oracle_dimension_error
        ),
        "broad_hard_cell_count": (
            broad_hard_cells
        ),
        "motif_visibility_contract": (
            visibility_ok
        ),
        "harder_family_gates": {
            "H1_oracle_core_exact": h1,
            "H2_one_row_elimination_recovery_le_0_75": h2,
            "H3_one_row_solver_recovery_le_0_90": h3,
            "H4_one_row_progress_rate_ge_0_75": h4,
            "H5_broad_hard_cells_ge_5": h5,
        },
        "family_status": (
            status
        ),
        "cells": cells,
    }
