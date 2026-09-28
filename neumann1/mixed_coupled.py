from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from statistics import mean
from typing import Iterable

from .coupled_block import (
    BlockCandidate,
    derive_block_candidate,
    validate_block_candidate,
)
from .learned_compression import (
    AffineCandidate,
    enumerate_affine_candidates,
    materialize_reduction,
    validate_candidate_against_system,
)
from .mixed_coupled_dataset import (
    MixedCoupledExample,
)
from .residual_headroom import (
    target_leaf_checked,
)
from .stopping_gauntlet import (
    FrozenV033Scorer,
    score_candidates,
)
from .structural_compression import (
    ExactLinearSystem,
    GaussianOperationCounts,
    ReconstructionOperationCounts,
    VerificationOperationCounts,
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


FROZEN_FIRST_STAGE_THRESHOLD = 0.10
FROZEN_RESIDUAL_METHOD = "markowitz"
FROZEN_RESIDUAL_THRESHOLD = 0.05


@dataclass(frozen=True)
class FrozenOneRowTrace:
    first_stage_accepted: tuple[
        AffineCandidate, ...
    ]
    residual_accepted: tuple[
        AffineCandidate, ...
    ]
    all_accepted: tuple[
        AffineCandidate, ...
    ]
    final_solver_ops: int
    final_verified: bool
    unsafe_accepted_reductions: int
    attempted_residual_proposals: int


@dataclass(frozen=True)
class MixedReferenceMaterialization:
    easy_leaf_candidates: tuple[
        AffineCandidate, ...
    ]
    block_candidates: tuple[
        BlockCandidate, ...
    ]
    retained_system: ExactLinearSystem
    retained_answer: dict[
        str, Fraction
    ]
    full_answer: dict[
        str, Fraction
    ]
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
class MixedCoupledObservation:
    core_dimension: int
    apparent_dimension: int
    easy_leaf_count: int
    block_count: int
    oracle_elimination_count: int
    expected_one_row_candidate_count: int
    enumerated_one_row_candidate_count: int
    candidate_count_exact: bool
    baseline_solver_ops: int
    one_row_first_stage_accepted: int
    one_row_residual_accepted: int
    one_row_total_accepted: int
    one_row_easy_leaf_accepted: int
    easy_leaf_recovery: float | None
    one_row_retained_dimension: int
    oracle_retained_dimension: int
    retained_dimension_gap: int
    one_row_solver_ops: int
    oracle_solver_ops: int
    one_row_solver_savings: int
    oracle_solver_savings: int
    one_row_elimination_recovery: (
        float | None
    )
    one_row_solver_savings_recovery: (
        float | None
    )
    one_row_verified: bool
    oracle_verified: bool
    unsafe_one_row_reductions: int
    unsafe_reference_reductions: int
    oracle_reconstruction_ops: int
    oracle_verification_ops: int


def _target_sort_key(
    name: str,
) -> int:
    return int(
        name[1:]
    )


def oracle_easy_leaf_candidates(
    example: MixedCoupledExample,
) -> tuple[
    AffineCandidate, ...
]:
    candidate_map = {
        candidate.key: candidate
        for candidate
        in enumerate_affine_candidates(
            example.full_system
        )
    }

    output: list[
        AffineCandidate
    ] = []
    for leaf in example.oracle_easy_leaves:
        key = (
            leaf.row_index,
            leaf.target,
        )
        candidate = candidate_map.get(
            key
        )
        if candidate is None:
            raise AssertionError(
                "declared easy leaf is not visible "
                "to the frozen one-row enumerator"
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
    return tuple(
        output
    )


def oracle_block_candidates(
    example: MixedCoupledExample,
) -> tuple[
    BlockCandidate, ...
]:
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
                "declared mixed block is singular"
            )
        output.append(
            candidate
        )

    output.sort(
        key=lambda candidate: (
            candidate.row_indices,
            tuple(
                _target_sort_key(
                    name
                )
                for name
                in candidate.targets
            ),
        )
    )
    return tuple(
        output
    )


def _candidate_pool(
    example: MixedCoupledExample,
    accepted: tuple[
        AffineCandidate, ...
    ],
) -> tuple[
    AffineCandidate, ...
]:
    output = [
        candidate
        for candidate
        in enumerate_affine_candidates(
            example.full_system
        )
        if not any(
            candidate.row_index
            == chosen.row_index
            or candidate.target
            == chosen.target
            for chosen in accepted
        )
    ]
    output.sort(
        key=lambda candidate: (
            candidate.row_index,
            _target_sort_key(
                candidate.target
            ),
        )
    )
    return tuple(
        output
    )


def run_frozen_one_row_pipeline(
    example: MixedCoupledExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> FrozenOneRowTrace:
    initial = target_leaf_checked(
        example,
        frozen_scorer=frozen_scorer,
    )

    accepted = tuple(
        initial.accepted_candidates
    )
    current = initial.materialized

    scored = score_candidates(
        example,
        FROZEN_RESIDUAL_METHOD,
        frozen_scorer=frozen_scorer,
    )
    score_map = {
        item.candidate.key: item.score
        for item in scored
    }

    residual_accepted: list[
        AffineCandidate
    ] = []
    attempts = 0

    while True:
        pool = _candidate_pool(
            example,
            accepted,
        )
        if not pool:
            break

        ranked = sorted(
            (
                (
                    candidate,
                    score_map[
                        candidate.key
                    ],
                )
                for candidate in pool
            ),
            key=lambda item: (
                -item[1],
                item[0].row_index,
                _target_sort_key(
                    item[0].target
                ),
            ),
        )

        state_advanced = False

        for candidate, score in ranked:
            if (
                score
                < FROZEN_RESIDUAL_THRESHOLD
            ):
                break

            attempts += 1
            tentative = materialize_reduction(
                example,
                accepted
                + (candidate,),
            )
            if tentative is None:
                continue

            accepted = (
                accepted
                + (candidate,)
            )
            residual_accepted.append(
                candidate
            )
            current = tentative
            state_advanced = True
            break

        if not state_advanced:
            break

    verified = (
        current.verified
        and current.ground_truth_equivalent
    )

    return FrozenOneRowTrace(
        first_stage_accepted=tuple(
            initial.accepted_candidates
        ),
        residual_accepted=tuple(
            residual_accepted
        ),
        all_accepted=accepted,
        final_solver_ops=(
            current.solver_counts.arithmetic_ops
        ),
        final_verified=verified,
        unsafe_accepted_reductions=(
            0
            if verified
            else len(accepted)
        ),
        attempted_residual_proposals=(
            attempts
        ),
    )


def _apply_affine_rule(
    answer: dict[
        str, Fraction
    ],
    candidate: AffineCandidate,
    counts: ReconstructionOperationCounts,
) -> None:
    total = Fraction(
        candidate.constant
    )

    for index, (
        dependency,
        coefficient,
    ) in enumerate(
        candidate.coefficients
    ):
        if dependency not in answer:
            raise ValueError(
                "missing affine reconstruction dependency"
            )

        product = (
            Fraction(
                coefficient
            )
            * answer[
                dependency
            ]
        )
        counts.multiplications += 1

        if (
            candidate.constant != 0
            or index > 0
        ):
            total += product
            counts.additions += 1
        else:
            total = product

    answer[
        candidate.target
    ] = total


def _apply_fraction_rule(
    answer: dict[
        str, Fraction
    ],
    *,
    target: str,
    constant: Fraction,
    coefficients: tuple[
        tuple[
            str,
            Fraction,
        ],
        ...,
    ],
    counts: ReconstructionOperationCounts,
) -> None:
    total = Fraction(
        constant
    )

    for index, (
        dependency,
        coefficient,
    ) in enumerate(
        coefficients
    ):
        if dependency not in answer:
            raise ValueError(
                "missing block reconstruction dependency"
            )

        product = (
            coefficient
            * answer[
                dependency
            ]
        )
        counts.multiplications += 1

        if (
            constant != 0
            or index > 0
        ):
            total += product
            counts.additions += 1
        else:
            total = product

    answer[
        target
    ] = total


def materialize_mixed_reference(
    example: MixedCoupledExample,
) -> MixedReferenceMaterialization | None:
    system = example.full_system

    leaves = (
        oracle_easy_leaf_candidates(
            example
        )
    )
    blocks = (
        oracle_block_candidates(
            example
        )
    )

    for candidate in leaves:
        ok, _ = (
            validate_candidate_against_system(
                system,
                candidate,
            )
        )
        if not ok:
            return None

    for candidate in blocks:
        ok, _ = (
            validate_block_candidate(
                system,
                candidate,
            )
        )
        if not ok:
            return None

    removed_rows = [
        candidate.row_index
        for candidate in leaves
    ]
    removed_rows.extend(
        row
        for candidate in blocks
        for row in candidate.row_indices
    )

    eliminated_targets = [
        candidate.target
        for candidate in leaves
    ]
    eliminated_targets.extend(
        target
        for candidate in blocks
        for target in candidate.targets
    )

    if len(
        removed_rows
    ) != len(
        set(
            removed_rows
        )
    ):
        return None

    if len(
        eliminated_targets
    ) != len(
        set(
            eliminated_targets
        )
    ):
        return None

    eliminated = set(
        eliminated_targets
    )
    removed = set(
        removed_rows
    )

    retained_variables = tuple(
        variable
        for variable
        in system.variables
        if variable
        not in eliminated
    )
    retained_rows = tuple(
        row
        for row
        in range(
            system.dimension
        )
        if row
        not in removed
    )

    if len(
        retained_variables
    ) != len(
        retained_rows
    ):
        return None
    if not retained_variables:
        return None

    available = set(
        retained_variables
    )

    for candidate in leaves:
        dependencies = {
            name
            for name, _
            in candidate.coefficients
        }
        if not dependencies.issubset(
            available
        ):
            return None

    for candidate in blocks:
        dependencies = {
            name
            for rule
            in candidate.rules
            for name, _
            in rule.coefficients
        }
        if not dependencies.issubset(
            available
        ):
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
                row
            ][
                column
            ]
            for column
            in retained_columns
        )
        for row
        in retained_rows
    )
    retained_b = tuple(
        system.b[
            row
        ]
        for row
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
        variables=retained_variables,
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

    full_answer = dict(
        retained_answer
    )
    reconstruction_counts = (
        ReconstructionOperationCounts()
    )

    try:
        for candidate in leaves:
            _apply_affine_rule(
                full_answer,
                candidate,
                reconstruction_counts,
            )

        for candidate in blocks:
            for rule in candidate.rules:
                _apply_fraction_rule(
                    full_answer,
                    target=rule.target,
                    constant=(
                        rule.constant
                    ),
                    coefficients=(
                        rule.coefficients
                    ),
                    counts=(
                        reconstruction_counts
                    ),
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

    equivalent = (
        verified
        and all(
            full_answer[
                variable
            ]
            == Fraction(
                expected
            )
            for variable, expected
            in zip(
                system.variables,
                system.ground_truth,
            )
        )
    )

    if not equivalent:
        return None

    return MixedReferenceMaterialization(
        easy_leaf_candidates=(
            leaves
        ),
        block_candidates=(
            blocks
        ),
        retained_system=(
            retained_system
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
        verified=(
            verified
        ),
        ground_truth_equivalent=(
            equivalent
        ),
    )


def observe_mixed_coupled(
    example: MixedCoupledExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> MixedCoupledObservation:
    (
        _,
        baseline_counts,
    ) = solve_exact_gauss_jordan(
        example.full_system
    )

    one_row = (
        run_frozen_one_row_pipeline(
            example,
            frozen_scorer=(
                frozen_scorer
            ),
        )
    )

    reference = (
        materialize_mixed_reference(
            example
        )
    )
    if reference is None:
        raise AssertionError(
            "exact mixed reference failed materialization"
        )

    all_candidates = (
        enumerate_affine_candidates(
            example.full_system
        )
    )

    easy_keys = {
        (
            leaf.row_index,
            leaf.target,
        )
        for leaf
        in example.oracle_easy_leaves
    }

    easy_accepted = sum(
        1
        for candidate
        in one_row.all_accepted
        if candidate.key
        in easy_keys
    )

    if (
        example.easy_leaf_count
        > 0
    ):
        easy_recovery: (
            float | None
        ) = (
            easy_accepted
            / example.easy_leaf_count
        )
    else:
        easy_recovery = None

    baseline_ops = (
        baseline_counts.arithmetic_ops
    )
    one_row_ops = (
        one_row.final_solver_ops
    )
    oracle_ops = (
        reference.solver_counts.arithmetic_ops
    )

    one_row_savings = (
        baseline_ops
        - one_row_ops
    )
    oracle_savings = (
        baseline_ops
        - oracle_ops
    )

    total_accepted = len(
        one_row.all_accepted
    )

    if (
        example.oracle_elimination_count
        > 0
    ):
        elimination_recovery: (
            float | None
        ) = (
            total_accepted
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

    reference_verified = (
        reference.verified
        and reference.ground_truth_equivalent
    )

    return MixedCoupledObservation(
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
        ),
        easy_leaf_count=(
            example.easy_leaf_count
        ),
        block_count=(
            example.block_count
        ),
        oracle_elimination_count=(
            example.oracle_elimination_count
        ),
        expected_one_row_candidate_count=(
            example.expected_one_row_candidate_count
        ),
        enumerated_one_row_candidate_count=len(
            all_candidates
        ),
        candidate_count_exact=(
            len(
                all_candidates
            )
            == example.expected_one_row_candidate_count
        ),
        baseline_solver_ops=(
            baseline_ops
        ),
        one_row_first_stage_accepted=len(
            one_row.first_stage_accepted
        ),
        one_row_residual_accepted=len(
            one_row.residual_accepted
        ),
        one_row_total_accepted=(
            total_accepted
        ),
        one_row_easy_leaf_accepted=(
            easy_accepted
        ),
        easy_leaf_recovery=(
            easy_recovery
        ),
        one_row_retained_dimension=(
            example.apparent_dimension
            - total_accepted
        ),
        oracle_retained_dimension=(
            reference.retained_system.dimension
        ),
        retained_dimension_gap=(
            example.apparent_dimension
            - total_accepted
            - example.core_dimension
        ),
        one_row_solver_ops=(
            one_row_ops
        ),
        oracle_solver_ops=(
            oracle_ops
        ),
        one_row_solver_savings=(
            one_row_savings
        ),
        oracle_solver_savings=(
            oracle_savings
        ),
        one_row_elimination_recovery=(
            elimination_recovery
        ),
        one_row_solver_savings_recovery=(
            solver_recovery
        ),
        one_row_verified=(
            one_row.final_verified
        ),
        oracle_verified=(
            reference_verified
        ),
        unsafe_one_row_reductions=(
            one_row.unsafe_accepted_reductions
        ),
        unsafe_reference_reductions=(
            0
            if reference_verified
            else (
                len(
                    reference.easy_leaf_candidates
                )
                + len(
                    reference.block_candidates
                )
            )
        ),
        oracle_reconstruction_ops=(
            reference.reconstruction_counts.arithmetic_ops
        ),
        oracle_verification_ops=(
            reference.verification_counts.arithmetic_ops
        ),
    )


def aggregate_mixed_coupled(
    observations: Iterable[
        MixedCoupledObservation
    ],
) -> dict[str, object]:
    rows = tuple(
        observations
    )
    if not rows:
        raise ValueError(
            "at least one mixed observation is required"
        )

    active = tuple(
        row
        for row in rows
        if row.oracle_elimination_count
        > 0
    )
    controls = tuple(
        row
        for row in rows
        if row.oracle_elimination_count
        == 0
    )
    mixed_active = tuple(
        row
        for row in active
        if row.easy_leaf_count
        > 0
    )

    grouped: dict[
        tuple[int, int],
        list[
            MixedCoupledObservation
        ],
    ] = {}

    for row in rows:
        grouped.setdefault(
            (
                row.core_dimension,
                row.apparent_dimension,
            ),
            [],
        ).append(
            row
        )

    cells: list[
        dict[str, object]
    ] = []
    broad_hard_cells = 0

    for (
        k,
        n,
    ), cell_rows in sorted(
        grouped.items()
    ):
        cell_active = [
            row
            for row in cell_rows
            if row.oracle_elimination_count
            > 0
        ]

        cell: dict[
            str,
            object,
        ] = {
            "core_dimension": k,
            "apparent_dimension": n,
            "count": len(
                cell_rows
            ),
            "mean_easy_leaf_count": mean(
                row.easy_leaf_count
                for row in cell_rows
            ),
            "mean_block_count": mean(
                row.block_count
                for row in cell_rows
            ),
            "candidate_count_exact_rate": mean(
                1.0
                if row.candidate_count_exact
                else 0.0
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

        mixed_cell = [
            row
            for row in cell_rows
            if row.easy_leaf_count
            > 0
        ]
        if mixed_cell:
            cell[
                "mean_easy_leaf_recovery"
            ] = mean(
                float(
                    row.easy_leaf_recovery
                )
                for row in mixed_cell
                if row.easy_leaf_recovery
                is not None
            )

        if cell_active:
            cell_gap = mean(
                row.retained_dimension_gap
                for row in cell_active
            )
            cell_blocks = mean(
                row.block_count
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
        if row.one_row_total_accepted
        > 0
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

    if mixed_active:
        mean_easy_leaf_recovery: (
            float | None
        ) = mean(
            float(
                row.easy_leaf_recovery
            )
            for row in mixed_active
            if row.easy_leaf_recovery
            is not None
        )
    else:
        mean_easy_leaf_recovery = None

    candidate_exact_rate = mean(
        1.0
        if row.candidate_count_exact
        else 0.0
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
    reference_safe = (
        all(
            row.oracle_verified
            for row in rows
        )
        and sum(
            row.unsafe_reference_reductions
            for row in rows
        )
        == 0
    )

    if not (
        one_row_safe
        and reference_safe
    ):
        status = (
            "INVALID_FAMILY_OR_CHECKER"
        )
    elif all(
        (
            h1,
            h2,
            h3,
            h4,
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
        "count": len(
            rows
        ),
        "active_count": len(
            active
        ),
        "mixed_active_count": len(
            mixed_active
        ),
        "control_count": len(
            controls
        ),
        "candidate_count_exact_rate": (
            candidate_exact_rate
        ),
        "mean_easy_leaf_recovery": (
            mean_easy_leaf_recovery
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
        "unsafe_reference_reductions": sum(
            row.unsafe_reference_reductions
            for row in rows
        ),
        "harder_family_gates": {
            "H1_oracle_core_exact": (
                h1
            ),
            "H2_one_row_elimination_recovery_le_0_75": (
                h2
            ),
            "H3_one_row_solver_recovery_le_0_90": (
                h3
            ),
            "H4_one_row_progress_rate_ge_0_75": (
                h4
            ),
            "H5_broad_hard_cells_ge_5": (
                h5
            ),
        },
        "family_status": (
            status
        ),
        "cells": cells,
    }
