from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from statistics import mean
from typing import Iterable

from .coupled_block_dataset import (
    CoupledBlockExample,
)
from .learned_compression import (
    enumerate_affine_candidates,
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
class FractionAffineRule:
    target: str
    constant: Fraction
    coefficients: tuple[
        tuple[str, Fraction], ...
    ]


@dataclass(frozen=True)
class BlockCandidate:
    row_indices: tuple[int, int]
    targets: tuple[str, str]
    rules: tuple[
        FractionAffineRule,
        FractionAffineRule,
    ]

    @property
    def key(
        self,
    ) -> tuple[
        tuple[int, int],
        tuple[str, str],
    ]:
        return (
            self.row_indices,
            self.targets,
        )


@dataclass(frozen=True)
class BlockMaterialization:
    accepted_candidates: tuple[
        BlockCandidate, ...
    ]
    retained_system: ExactLinearSystem
    reconstruction_order: tuple[
        BlockCandidate, ...
    ]
    retained_answer: dict[str, Fraction]
    full_answer: dict[str, Fraction]
    solver_counts: GaussianOperationCounts
    reconstruction_counts: (
        ReconstructionOperationCounts
    )
    verification_counts: (
        VerificationOperationCounts
    )
    verified: bool
    ground_truth_equivalent: bool


@dataclass(frozen=True)
class CoupledBlockObservation:
    core_dimension: int
    apparent_dimension: int
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
    unsafe_block_reductions: int


def _target_sort_key(name: str) -> int:
    return int(name[1:])


def _canonical_rows(
    row_indices: tuple[int, int],
) -> tuple[int, int]:
    if len(set(row_indices)) != 2:
        raise ValueError(
            "block candidate requires two distinct rows"
        )
    return tuple(sorted(row_indices))


def _canonical_targets(
    system: ExactLinearSystem,
    targets: tuple[str, str],
) -> tuple[str, str]:
    if len(set(targets)) != 2:
        raise ValueError(
            "block candidate requires two distinct targets"
        )
    if any(
        target not in system.variables
        for target in targets
    ):
        raise ValueError(
            "block candidate contains unknown target"
        )
    return tuple(
        sorted(
            targets,
            key=_target_sort_key,
        )
    )


def derive_block_candidate(
    system: ExactLinearSystem,
    row_indices: tuple[int, int],
    targets: tuple[str, str],
) -> BlockCandidate | None:
    rows = _canonical_rows(row_indices)
    target_names = _canonical_targets(
        system,
        targets,
    )

    if any(
        row < 0 or row >= system.dimension
        for row in rows
    ):
        return None

    c0 = system.variables.index(
        target_names[0]
    )
    c1 = system.variables.index(
        target_names[1]
    )

    r0 = system.A[rows[0]]
    r1 = system.A[rows[1]]
    b0 = Fraction(
        system.b[rows[0]]
    )
    b1 = Fraction(
        system.b[rows[1]]
    )

    a00 = Fraction(r0[c0])
    a01 = Fraction(r0[c1])
    a10 = Fraction(r1[c0])
    a11 = Fraction(r1[c1])

    determinant = (
        a00 * a11
        - a01 * a10
    )
    if determinant == 0:
        return None

    constant0 = (
        a11 * b0
        - a01 * b1
    ) / determinant
    constant1 = (
        -a10 * b0
        + a00 * b1
    ) / determinant

    coefficients0: list[
        tuple[str, Fraction]
    ] = []
    coefficients1: list[
        tuple[str, Fraction]
    ] = []

    for column, variable in enumerate(
        system.variables
    ):
        if column in (c0, c1):
            continue

        d0 = Fraction(r0[column])
        d1 = Fraction(r1[column])
        if d0 == 0 and d1 == 0:
            continue

        coefficient0 = (
            -a11 * d0
            + a01 * d1
        ) / determinant
        coefficient1 = (
            a10 * d0
            - a00 * d1
        ) / determinant

        if coefficient0 != 0:
            coefficients0.append(
                (
                    variable,
                    coefficient0,
                )
            )
        if coefficient1 != 0:
            coefficients1.append(
                (
                    variable,
                    coefficient1,
                )
            )

    coefficients0.sort(
        key=lambda item: _target_sort_key(
            item[0]
        )
    )
    coefficients1.sort(
        key=lambda item: _target_sort_key(
            item[0]
        )
    )

    rules = (
        FractionAffineRule(
            target=target_names[0],
            constant=constant0,
            coefficients=tuple(
                coefficients0
            ),
        ),
        FractionAffineRule(
            target=target_names[1],
            constant=constant1,
            coefficients=tuple(
                coefficients1
            ),
        ),
    )
    return BlockCandidate(
        row_indices=rows,
        targets=target_names,
        rules=rules,
    )


def validate_block_candidate(
    system: ExactLinearSystem,
    candidate: BlockCandidate,
) -> tuple[bool, str]:
    try:
        expected = derive_block_candidate(
            system,
            candidate.row_indices,
            candidate.targets,
        )
    except ValueError as exc:
        return False, str(exc)

    if expected is None:
        return (
            False,
            "target 2x2 coefficient matrix is singular",
        )
    if expected != candidate:
        return (
            False,
            "block reconstruction algebra mismatch",
        )
    return (
        True,
        "block candidate algebra verified",
    )


def _block_dependencies(
    candidate: BlockCandidate,
) -> frozenset[str]:
    return frozenset(
        name
        for rule in candidate.rules
        for name, _ in rule.coefficients
    )


def _topological_block_order(
    candidates: tuple[BlockCandidate, ...],
    retained_variables: tuple[str, ...],
) -> tuple[BlockCandidate, ...] | None:
    available = set(
        retained_variables
    )
    pending = list(candidates)
    ordered: list[BlockCandidate] = []

    while pending:
        next_pending: list[
            BlockCandidate
        ] = []
        progress = False

        for candidate in pending:
            if _block_dependencies(
                candidate
            ).issubset(available):
                ordered.append(candidate)
                available.update(
                    candidate.targets
                )
                progress = True
            else:
                next_pending.append(
                    candidate
                )

        if not progress:
            return None
        pending = next_pending

    return tuple(ordered)


def _reconstruct_blocks(
    retained_answer: dict[str, Fraction],
    ordered: tuple[BlockCandidate, ...],
) -> tuple[
    dict[str, Fraction],
    ReconstructionOperationCounts,
]:
    answer = dict(
        retained_answer
    )
    counts = ReconstructionOperationCounts()

    for candidate in ordered:
        for rule in candidate.rules:
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
                        "missing block reconstruction dependency"
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

            answer[rule.target] = total

    return answer, counts


def materialize_block_reduction(
    example: CoupledBlockExample,
    candidates: tuple[
        BlockCandidate, ...
    ],
) -> BlockMaterialization | None:
    system = example.full_system

    used_rows = [
        row
        for candidate in candidates
        for row in candidate.row_indices
    ]
    used_targets = [
        target
        for candidate in candidates
        for target in candidate.targets
    ]
    if len(used_rows) != len(
        set(used_rows)
    ):
        return None
    if len(used_targets) != len(
        set(used_targets)
    ):
        return None

    for candidate in candidates:
        ok, _ = validate_block_candidate(
            system,
            candidate,
        )
        if not ok:
            return None

    removed_rows = set(
        used_rows
    )
    eliminated = set(
        used_targets
    )
    retained_variables = tuple(
        variable
        for variable in system.variables
        if variable not in eliminated
    )
    retained_rows = tuple(
        row
        for row in range(
            system.dimension
        )
        if row not in removed_rows
    )

    if len(retained_variables) != len(
        retained_rows
    ):
        return None
    if not retained_variables:
        return None

    ordered = _topological_block_order(
        candidates,
        retained_variables,
    )
    if ordered is None:
        return None

    retained_columns = tuple(
        system.variables.index(
            variable
        )
        for variable in retained_variables
    )
    retained_A = tuple(
        tuple(
            system.A[row][column]
            for column in retained_columns
        )
        for row in retained_rows
    )
    retained_b = tuple(
        system.b[row]
        for row in retained_rows
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
        for variable in retained_variables
    )
    retained_system = ExactLinearSystem(
        variables=retained_variables,
        A=retained_A,
        b=retained_b,
        ground_truth=retained_ground_truth,
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
        ) = _reconstruct_blocks(
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
            full_answer[variable]
            == Fraction(expected)
            for variable, expected
            in zip(
                system.variables,
                system.ground_truth,
            )
        )
    )
    if not ground_truth_equivalent:
        return None

    return BlockMaterialization(
        accepted_candidates=candidates,
        retained_system=retained_system,
        reconstruction_order=ordered,
        retained_answer=retained_answer,
        full_answer=full_answer,
        solver_counts=solver_counts,
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


def oracle_block_candidates(
    example: CoupledBlockExample,
) -> tuple[BlockCandidate, ...]:
    output: list[
        BlockCandidate
    ] = []
    for block in example.oracle_blocks:
        candidate = derive_block_candidate(
            example.full_system,
            block.row_indices,
            block.targets,
        )
        if candidate is None:
            raise AssertionError(
                "generator oracle block is singular"
            )
        output.append(candidate)

    output.sort(
        key=lambda candidate: (
            candidate.row_indices,
            tuple(
                _target_sort_key(name)
                for name in candidate.targets
            ),
        )
    )
    return tuple(output)


def observe_coupled_block(
    example: CoupledBlockExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> CoupledBlockObservation:
    (
        _,
        baseline_counts,
    ) = solve_exact_gauss_jordan(
        example.full_system
    )

    one_row = (
        observe_deterministic_residual_policy(
            example,
            "markowitz",
            0.05,
            frozen_scorer=frozen_scorer,
        )
    )
    one_row_total = (
        one_row.target_leaf_accepted_count
        + one_row.residual_accepted_count
    )

    oracle_candidates = (
        oracle_block_candidates(
            example
        )
    )
    oracle = materialize_block_reduction(
        example,
        oracle_candidates,
    )
    if oracle is None:
        raise AssertionError(
            "oracle block reduction failed materialization"
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
        baseline_ops - oracle_ops
    )
    one_row_savings = (
        baseline_ops - one_row_ops
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

    return CoupledBlockObservation(
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
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
        unsafe_block_reductions=(
            0
            if oracle_verified
            else len(
                oracle_candidates
            )
        ),
    )


def aggregate_coupled_block(
    observations: Iterable[
        CoupledBlockObservation
    ],
) -> dict[str, object]:
    rows = tuple(
        observations
    )
    if not rows:
        raise ValueError(
            "at least one coupled-block observation is required"
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
        list[CoupledBlockObservation],
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
        cell = {
            "core_dimension": k,
            "apparent_dimension": n,
            "count": len(cell_rows),
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
                1.0 if row.one_row_verified else 0.0
                for row in cell_rows
            ),
            "oracle_verified_retention": mean(
                1.0 if row.oracle_verified else 0.0
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
                        for row in cell_active
                        if row.one_row_elimination_recovery
                        is not None
                    ),
                    "mean_one_row_solver_savings_recovery": mean(
                        float(
                            row.one_row_solver_savings_recovery
                        )
                        for row in cell_active
                        if row.one_row_solver_savings_recovery
                        is not None
                    ),
                    "mean_retained_dimension_gap": (
                        cell_gap
                    ),
                    "mean_block_count": (
                        cell_blocks
                    ),
                }
            )
            if (
                cell_gap
                >= 0.5 * cell_blocks
            ):
                broad_hard_cells += 1

        cells.append(cell)

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
    mean_oracle_dimension_error = mean(
        abs(
            row.oracle_retained_dimension
            - row.core_dimension
        )
        for row in active
    )

    h1 = (
        mean_oracle_dimension_error
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
        broad_hard_cells >= 5
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
            row.unsafe_block_reductions
            for row in rows
        )
        == 0
    )

    if not (
        one_row_safe
        and oracle_safe
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
            1.0 if row.one_row_verified else 0.0
            for row in rows
        ),
        "oracle_verified_retention": mean(
            1.0 if row.oracle_verified else 0.0
            for row in rows
        ),
        "unsafe_one_row_reductions": sum(
            row.unsafe_one_row_reductions
            for row in rows
        ),
        "unsafe_block_reductions": sum(
            row.unsafe_block_reductions
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
            mean_oracle_dimension_error
        ),
        "broad_hard_cell_count": (
            broad_hard_cells
        ),
        "harder_family_gates": {
            "H1_oracle_core_exact": h1,
            "H2_one_row_elimination_recovery_le_0_75": h2,
            "H3_one_row_solver_recovery_le_0_90": h3,
            "H4_one_row_progress_rate_ge_0_75": h4,
            "H5_broad_hard_cells_ge_5": h5,
        },
        "family_status": status,
        "cells": cells,
    }
