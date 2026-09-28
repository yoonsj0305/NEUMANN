from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
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
from .mixed_coupled import (
    FROZEN_FIRST_STAGE_THRESHOLD,
    FROZEN_RESIDUAL_METHOD,
    FROZEN_RESIDUAL_THRESHOLD,
    MixedReferenceMaterialization,
    _apply_affine_rule,
    _apply_fraction_rule,
    materialize_mixed_reference,
    run_frozen_one_row_pipeline,
)
from .mixed_coupled_dataset import (
    MixedCoupledExample,
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


DISCOVERY_METHODS = (
    "D0_frozen_local_only",
    "D1_local_first_exact_overlap",
    "D2_incidence_exact_overlap",
    "D3_incidence_sparse_unit_pair",
    "D4_incidence_component_graph",
)


@dataclass(frozen=True)
class DiscoveryResult:
    block_candidates: tuple[
        BlockCandidate, ...
    ]
    row_pair_examinations: int
    graph_edges_examined: int


@dataclass(frozen=True)
class GenericMixedMaterialization:
    local_candidates: tuple[
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
class DiscoveryObservation:
    method: str
    core_dimension: int
    apparent_dimension: int
    oracle_elimination_count: int
    oracle_block_count: int
    baseline_solver_ops: int
    oracle_solver_ops: int
    final_solver_ops: int
    accepted_local_count: int
    accepted_block_count: int
    total_eliminated_variables: int
    retained_dimension: int
    solver_savings: int
    oracle_solver_savings: int
    solver_savings_recovery: float | None
    elimination_recovery: float | None
    discovered_block_candidate_count: int
    row_pair_examinations: int
    graph_edges_examined: int
    block_true_positive_count: int
    block_predicted_count: int
    block_reference_count: int
    easy_leaf_true_positive_count: int
    easy_leaf_predicted_count: int
    easy_leaf_reference_count: int
    coupled_target_consumed_locally: int
    final_verified: bool
    unsafe_accepted_reductions: int


def _target_index(
    name: str,
) -> int:
    return int(name[1:])


def _candidate_key(
    candidate: AffineCandidate,
) -> tuple[int, str]:
    return (
        candidate.row_index,
        candidate.target,
    )


def _block_key(
    candidate: BlockCandidate,
) -> tuple[
    tuple[int, int],
    tuple[str, str],
]:
    return (
        tuple(
            sorted(
                candidate.row_indices
            )
        ),
        tuple(
            sorted(
                candidate.targets,
                key=_target_index,
            )
        ),
    )


def target_incidence(
    system: ExactLinearSystem,
) -> dict[str, int]:
    output: dict[str, int] = {}
    for column, variable in enumerate(
        system.variables
    ):
        output[variable] = sum(
            1
            for row in system.A
            if row[column] != 0
        )
    return output


def candidate_targets_by_row(
    example: MixedCoupledExample,
    *,
    unavailable_rows: frozenset[int] = frozenset(),
    unavailable_targets: frozenset[str] = frozenset(),
) -> dict[int, frozenset[str]]:
    grouped: dict[
        int,
        set[str],
    ] = {}

    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        if (
            candidate.row_index
            in unavailable_rows
            or candidate.target
            in unavailable_targets
        ):
            continue
        grouped.setdefault(
            candidate.row_index,
            set(),
        ).add(
            candidate.target
        )

    return {
        row: frozenset(
            targets
        )
        for row, targets
        in grouped.items()
    }


def _topological_reconstruction_order(
    local_candidates: tuple[
        AffineCandidate, ...
    ],
    block_candidates: tuple[
        BlockCandidate, ...
    ],
    retained_variables: tuple[str, ...],
) -> tuple[
    tuple[
        str,
        AffineCandidate | BlockCandidate,
    ],
    ...,
] | None:
    pending: list[
        tuple[
            str,
            AffineCandidate | BlockCandidate,
            frozenset[str],
            frozenset[str],
        ]
    ] = []

    for candidate in local_candidates:
        pending.append(
            (
                "local",
                candidate,
                frozenset(
                    {
                        candidate.target
                    }
                ),
                frozenset(
                    name
                    for name, _
                    in candidate.coefficients
                ),
            )
        )

    for candidate in block_candidates:
        pending.append(
            (
                "block",
                candidate,
                frozenset(
                    candidate.targets
                ),
                frozenset(
                    name
                    for rule
                    in candidate.rules
                    for name, _
                    in rule.coefficients
                ),
            )
        )

    available = set(
        retained_variables
    )
    ordered: list[
        tuple[
            str,
            AffineCandidate | BlockCandidate,
        ]
    ] = []

    while pending:
        next_pending = []
        progress = False

        for (
            kind,
            candidate,
            targets,
            dependencies,
        ) in pending:
            if dependencies.issubset(
                available
            ):
                ordered.append(
                    (
                        kind,
                        candidate,
                    )
                )
                available.update(
                    targets
                )
                progress = True
            else:
                next_pending.append(
                    (
                        kind,
                        candidate,
                        targets,
                        dependencies,
                    )
                )

        if not progress:
            return None

        pending = next_pending

    return tuple(
        ordered
    )


def materialize_generic_mixed(
    example: MixedCoupledExample,
    local_candidates: tuple[
        AffineCandidate, ...
    ],
    block_candidates: tuple[
        BlockCandidate, ...
    ],
) -> GenericMixedMaterialization | None:
    system = example.full_system

    for candidate in local_candidates:
        ok, _ = (
            validate_candidate_against_system(
                system,
                candidate,
            )
        )
        if not ok:
            return None

    for candidate in block_candidates:
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
        for candidate
        in local_candidates
    ]
    removed_rows.extend(
        row
        for candidate
        in block_candidates
        for row
        in candidate.row_indices
    )

    eliminated_targets = [
        candidate.target
        for candidate
        in local_candidates
    ]
    eliminated_targets.extend(
        target
        for candidate
        in block_candidates
        for target
        in candidate.targets
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

    removed = set(
        removed_rows
    )
    eliminated = set(
        eliminated_targets
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

    reconstruction_order = (
        _topological_reconstruction_order(
            local_candidates,
            block_candidates,
            retained_variables,
        )
    )
    if reconstruction_order is None:
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
        for kind, candidate in reconstruction_order:
            if kind == "local":
                if not isinstance(
                    candidate,
                    AffineCandidate,
                ):
                    raise AssertionError(
                        "local reconstruction type drift"
                    )
                _apply_affine_rule(
                    full_answer,
                    candidate,
                    reconstruction_counts,
                )
            else:
                if not isinstance(
                    candidate,
                    BlockCandidate,
                ):
                    raise AssertionError(
                        "block reconstruction type drift"
                    )
                for rule in candidate.rules:
                    _apply_fraction_rule(
                        full_answer,
                        target=rule.target,
                        constant=rule.constant,
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

    return GenericMixedMaterialization(
        local_candidates=(
            local_candidates
        ),
        block_candidates=(
            block_candidates
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


def route_incidence_one_locals(
    example: MixedCoupledExample,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> tuple[
    AffineCandidate, ...
]:
    incidence = target_incidence(
        example.full_system
    )

    scored = score_candidates(
        example,
        "target_leaf",
        frozen_scorer=frozen_scorer,
    )

    accepted: tuple[
        AffineCandidate, ...
    ] = ()

    for item in scored:
        candidate = (
            item.candidate
        )

        if (
            item.score
            < FROZEN_FIRST_STAGE_THRESHOLD
        ):
            continue

        if (
            incidence[
                candidate.target
            ]
            != 1
        ):
            continue

        if any(
            candidate.row_index
            == chosen.row_index
            or candidate.target
            == chosen.target
            for chosen in accepted
        ):
            continue

        tentative = (
            materialize_reduction(
                example,
                accepted
                + (candidate,),
            )
        )
        if tentative is None:
            continue

        accepted = (
            accepted
            + (candidate,)
        )

    return accepted


def _available_rows_targets(
    example: MixedCoupledExample,
    local_candidates: tuple[
        AffineCandidate, ...
    ],
) -> tuple[
    frozenset[int],
    frozenset[str],
]:
    unavailable_rows = frozenset(
        candidate.row_index
        for candidate
        in local_candidates
    )
    unavailable_targets = frozenset(
        candidate.target
        for candidate
        in local_candidates
    )
    return (
        unavailable_rows,
        unavailable_targets,
    )


def discover_exact_candidate_overlap(
    example: MixedCoupledExample,
    local_candidates: tuple[
        AffineCandidate, ...
    ],
) -> DiscoveryResult:
    (
        unavailable_rows,
        unavailable_targets,
    ) = _available_rows_targets(
        example,
        local_candidates,
    )

    grouped = candidate_targets_by_row(
        example,
        unavailable_rows=(
            unavailable_rows
        ),
        unavailable_targets=(
            unavailable_targets
        ),
    )

    rows = [
        row
        for row
        in range(
            example.apparent_dimension
        )
        if row
        not in unavailable_rows
    ]

    found: dict[
        tuple[
            tuple[int, int],
            tuple[str, str],
        ],
        BlockCandidate,
    ] = {}
    examinations = 0

    for row_a, row_b in combinations(
        rows,
        2,
    ):
        examinations += 1

        shared = (
            grouped.get(
                row_a,
                frozenset(),
            )
            .intersection(
                grouped.get(
                    row_b,
                    frozenset(),
                )
            )
        )

        if len(shared) != 2:
            continue

        targets = tuple(
            sorted(
                shared,
                key=_target_index,
            )
        )
        candidate = derive_block_candidate(
            example.full_system,
            (
                row_a,
                row_b,
            ),
            targets,
        )
        if candidate is None:
            continue

        ok, _ = (
            validate_block_candidate(
                example.full_system,
                candidate,
            )
        )
        if not ok:
            continue

        found[
            _block_key(
                candidate
            )
        ] = candidate

    return DiscoveryResult(
        block_candidates=tuple(
            found[key]
            for key in sorted(
                found
            )
        ),
        row_pair_examinations=(
            examinations
        ),
        graph_edges_examined=0,
    )


def discover_sparse_unit_pair(
    example: MixedCoupledExample,
    local_candidates: tuple[
        AffineCandidate, ...
    ],
) -> DiscoveryResult:
    (
        unavailable_rows,
        unavailable_targets,
    ) = _available_rows_targets(
        example,
        local_candidates,
    )

    incidence = target_incidence(
        example.full_system
    )
    variables = (
        example.full_system.variables
    )
    rows = [
        row
        for row
        in range(
            example.apparent_dimension
        )
        if row
        not in unavailable_rows
    ]

    found: dict[
        tuple[
            tuple[int, int],
            tuple[str, str],
        ],
        BlockCandidate,
    ] = {}
    examinations = 0

    for row_a, row_b in combinations(
        rows,
        2,
    ):
        examinations += 1

        shared: list[str] = []
        for column, variable in enumerate(
            variables
        ):
            if variable in unavailable_targets:
                continue

            if (
                abs(
                    example.full_system.A[
                        row_a
                    ][
                        column
                    ]
                )
                == 1
                and abs(
                    example.full_system.A[
                        row_b
                    ][
                        column
                    ]
                )
                == 1
                and incidence[
                    variable
                ]
                == 2
            ):
                shared.append(
                    variable
                )

        if len(shared) != 2:
            continue

        targets = tuple(
            sorted(
                shared,
                key=_target_index,
            )
        )
        candidate = derive_block_candidate(
            example.full_system,
            (
                row_a,
                row_b,
            ),
            targets,
        )
        if candidate is None:
            continue

        ok, _ = (
            validate_block_candidate(
                example.full_system,
                candidate,
            )
        )
        if not ok:
            continue

        found[
            _block_key(
                candidate
            )
        ] = candidate

    return DiscoveryResult(
        block_candidates=tuple(
            found[key]
            for key in sorted(
                found
            )
        ),
        row_pair_examinations=(
            examinations
        ),
        graph_edges_examined=0,
    )


def discover_component_graph(
    example: MixedCoupledExample,
    local_candidates: tuple[
        AffineCandidate, ...
    ],
) -> DiscoveryResult:
    (
        unavailable_rows,
        unavailable_targets,
    ) = _available_rows_targets(
        example,
        local_candidates,
    )

    adjacency: dict[
        tuple[str, object],
        set[
            tuple[str, object]
        ],
    ] = {}
    edge_count = 0

    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        if (
            candidate.row_index
            in unavailable_rows
            or candidate.target
            in unavailable_targets
        ):
            continue

        row_node = (
            "row",
            candidate.row_index,
        )
        target_node = (
            "target",
            candidate.target,
        )
        adjacency.setdefault(
            row_node,
            set(),
        ).add(
            target_node
        )
        adjacency.setdefault(
            target_node,
            set(),
        ).add(
            row_node
        )
        edge_count += 1

    visited: set[
        tuple[str, object]
    ] = set()
    found: dict[
        tuple[
            tuple[int, int],
            tuple[str, str],
        ],
        BlockCandidate,
    ] = {}

    for node in sorted(
        adjacency,
        key=lambda item: (
            item[0],
            str(
                item[1]
            ),
        ),
    ):
        if node in visited:
            continue

        stack = [
            node
        ]
        component: set[
            tuple[str, object]
        ] = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(
                current
            )
            component.add(
                current
            )
            stack.extend(
                neighbor
                for neighbor
                in adjacency.get(
                    current,
                    set(),
                )
                if neighbor
                not in visited
            )

        row_nodes = sorted(
            int(
                item[1]
            )
            for item
            in component
            if item[0]
            == "row"
        )
        target_nodes = sorted(
            (
                str(
                    item[1]
                )
                for item
                in component
                if item[0]
                == "target"
            ),
            key=_target_index,
        )

        if (
            len(
                row_nodes
            )
            != 2
            or len(
                target_nodes
            )
            != 2
        ):
            continue

        candidate = derive_block_candidate(
            example.full_system,
            (
                row_nodes[0],
                row_nodes[1],
            ),
            (
                target_nodes[0],
                target_nodes[1],
            ),
        )
        if candidate is None:
            continue

        ok, _ = (
            validate_block_candidate(
                example.full_system,
                candidate,
            )
        )
        if not ok:
            continue

        found[
            _block_key(
                candidate
            )
        ] = candidate

    return DiscoveryResult(
        block_candidates=tuple(
            found[key]
            for key in sorted(
                found
            )
        ),
        row_pair_examinations=0,
        graph_edges_examined=(
            edge_count
        ),
    )


def select_nonconflicting_blocks(
    local_candidates: tuple[
        AffineCandidate, ...
    ],
    discovered: tuple[
        BlockCandidate, ...
    ],
) -> tuple[
    BlockCandidate, ...
]:
    used_rows = {
        candidate.row_index
        for candidate
        in local_candidates
    }
    used_targets = {
        candidate.target
        for candidate
        in local_candidates
    }
    accepted: list[
        BlockCandidate
    ] = []

    for candidate in sorted(
        discovered,
        key=_block_key,
    ):
        if any(
            row
            in used_rows
            for row
            in candidate.row_indices
        ):
            continue

        if any(
            target
            in used_targets
            for target
            in candidate.targets
        ):
            continue

        accepted.append(
            candidate
        )
        used_rows.update(
            candidate.row_indices
        )
        used_targets.update(
            candidate.targets
        )

    return tuple(
        accepted
    )


def _oracle_block_keys(
    example: MixedCoupledExample,
) -> set[
    tuple[
        tuple[int, int],
        tuple[str, str],
    ]
]:
    return {
        (
            tuple(
                sorted(
                    block.row_indices
                )
            ),
            tuple(
                sorted(
                    block.targets,
                    key=_target_index,
                )
            ),
        )
        for block
        in example.oracle_blocks
    }


def _oracle_easy_keys(
    example: MixedCoupledExample,
) -> set[
    tuple[int, str]
]:
    return {
        (
            leaf.row_index,
            leaf.target,
        )
        for leaf
        in example.oracle_easy_leaves
    }


def _oracle_coupled_targets(
    example: MixedCoupledExample,
) -> set[str]:
    return {
        target
        for block
        in example.oracle_blocks
        for target
        in block.targets
    }


def _discovery_for_method(
    example: MixedCoupledExample,
    method: str,
    local_candidates: tuple[
        AffineCandidate, ...
    ],
) -> DiscoveryResult:
    if method in {
        "D1_local_first_exact_overlap",
        "D2_incidence_exact_overlap",
    }:
        return (
            discover_exact_candidate_overlap(
                example,
                local_candidates,
            )
        )

    if method == (
        "D3_incidence_sparse_unit_pair"
    ):
        return (
            discover_sparse_unit_pair(
                example,
                local_candidates,
            )
        )

    if method == (
        "D4_incidence_component_graph"
    ):
        return (
            discover_component_graph(
                example,
                local_candidates,
            )
        )

    raise ValueError(
        f"unknown discovery method: {method}"
    )


def observe_discovery_method(
    example: MixedCoupledExample,
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> DiscoveryObservation:
    if method not in DISCOVERY_METHODS:
        raise ValueError(
            f"unknown method: {method}"
        )

    (
        _,
        baseline_counts,
    ) = solve_exact_gauss_jordan(
        example.full_system
    )
    baseline_ops = (
        baseline_counts.arithmetic_ops
    )

    reference: (
        MixedReferenceMaterialization
        | None
    ) = materialize_mixed_reference(
        example
    )
    if reference is None:
        raise AssertionError(
            "mixed oracle failed"
        )

    oracle_ops = (
        reference.solver_counts.arithmetic_ops
    )
    oracle_savings = (
        baseline_ops
        - oracle_ops
    )

    if method == "D0_frozen_local_only":
        trace = run_frozen_one_row_pipeline(
            example,
            frozen_scorer=frozen_scorer,
        )
        local_candidates = (
            trace.all_accepted
        )
        accepted_blocks: tuple[
            BlockCandidate, ...
        ] = ()
        discovery = DiscoveryResult(
            block_candidates=(),
            row_pair_examinations=0,
            graph_edges_examined=0,
        )
        final_ops = (
            trace.final_solver_ops
        )
        final_verified = (
            trace.final_verified
        )
        unsafe = (
            trace.unsafe_accepted_reductions
        )
    else:
        if method == (
            "D1_local_first_exact_overlap"
        ):
            trace = (
                run_frozen_one_row_pipeline(
                    example,
                    frozen_scorer=(
                        frozen_scorer
                    ),
                )
            )
            local_candidates = (
                trace.all_accepted
            )
        else:
            local_candidates = (
                route_incidence_one_locals(
                    example,
                    frozen_scorer=(
                        frozen_scorer
                    ),
                )
            )

        discovery = (
            _discovery_for_method(
                example,
                method,
                local_candidates,
            )
        )
        accepted_blocks = (
            select_nonconflicting_blocks(
                local_candidates,
                discovery.block_candidates,
            )
        )
        materialized = (
            materialize_generic_mixed(
                example,
                local_candidates,
                accepted_blocks,
            )
        )

        if materialized is None:
            final_ops = (
                baseline_ops
            )
            final_verified = False
            unsafe = (
                len(
                    local_candidates
                )
                + 2
                * len(
                    accepted_blocks
                )
            )
        else:
            final_ops = (
                materialized.solver_counts.arithmetic_ops
            )
            final_verified = (
                materialized.verified
                and materialized.ground_truth_equivalent
            )
            unsafe = (
                0
                if final_verified
                else (
                    len(
                        local_candidates
                    )
                    + 2
                    * len(
                        accepted_blocks
                    )
                )
            )

    eliminated = (
        len(
            local_candidates
        )
        + 2
        * len(
            accepted_blocks
        )
    )
    retained_dimension = (
        example.apparent_dimension
        - eliminated
    )
    solver_savings = (
        baseline_ops
        - final_ops
    )

    if oracle_savings > 0:
        solver_recovery: (
            float | None
        ) = (
            solver_savings
            / oracle_savings
        )
    else:
        solver_recovery = None

    if (
        example.oracle_elimination_count
        > 0
    ):
        elimination_recovery: (
            float | None
        ) = (
            eliminated
            / example.oracle_elimination_count
        )
    else:
        elimination_recovery = None

    oracle_block_keys = (
        _oracle_block_keys(
            example
        )
    )
    predicted_block_keys = {
        _block_key(
            candidate
        )
        for candidate
        in accepted_blocks
    }

    oracle_easy_keys = (
        _oracle_easy_keys(
            example
        )
    )
    predicted_local_keys = {
        _candidate_key(
            candidate
        )
        for candidate
        in local_candidates
    }

    coupled_targets = (
        _oracle_coupled_targets(
            example
        )
    )

    return DiscoveryObservation(
        method=method,
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
        ),
        oracle_elimination_count=(
            example.oracle_elimination_count
        ),
        oracle_block_count=(
            example.block_count
        ),
        baseline_solver_ops=(
            baseline_ops
        ),
        oracle_solver_ops=(
            oracle_ops
        ),
        final_solver_ops=(
            final_ops
        ),
        accepted_local_count=len(
            local_candidates
        ),
        accepted_block_count=len(
            accepted_blocks
        ),
        total_eliminated_variables=(
            eliminated
        ),
        retained_dimension=(
            retained_dimension
        ),
        solver_savings=(
            solver_savings
        ),
        oracle_solver_savings=(
            oracle_savings
        ),
        solver_savings_recovery=(
            solver_recovery
        ),
        elimination_recovery=(
            elimination_recovery
        ),
        discovered_block_candidate_count=len(
            discovery.block_candidates
        ),
        row_pair_examinations=(
            discovery.row_pair_examinations
        ),
        graph_edges_examined=(
            discovery.graph_edges_examined
        ),
        block_true_positive_count=len(
            predicted_block_keys
            .intersection(
                oracle_block_keys
            )
        ),
        block_predicted_count=len(
            predicted_block_keys
        ),
        block_reference_count=len(
            oracle_block_keys
        ),
        easy_leaf_true_positive_count=len(
            predicted_local_keys
            .intersection(
                oracle_easy_keys
            )
        ),
        easy_leaf_predicted_count=len(
            predicted_local_keys
        ),
        easy_leaf_reference_count=len(
            oracle_easy_keys
        ),
        coupled_target_consumed_locally=sum(
            1
            for candidate
            in local_candidates
            if candidate.target
            in coupled_targets
        ),
        final_verified=(
            final_verified
        ),
        unsafe_accepted_reductions=(
            unsafe
        ),
    )


def aggregate_discovery_method(
    observations: Iterable[
        DiscoveryObservation
    ],
) -> dict[str, object]:
    rows = tuple(
        observations
    )
    if not rows:
        raise ValueError(
            "at least one discovery observation is required"
        )

    active = tuple(
        row
        for row in rows
        if row.oracle_elimination_count
        > 0
    )

    block_tp = sum(
        row.block_true_positive_count
        for row in rows
    )
    block_pred = sum(
        row.block_predicted_count
        for row in rows
    )
    block_ref = sum(
        row.block_reference_count
        for row in rows
    )

    block_precision = (
        block_tp / block_pred
        if block_pred
        else (
            1.0
            if block_ref == 0
            else 0.0
        )
    )
    block_recall = (
        block_tp / block_ref
        if block_ref
        else 1.0
    )
    block_f1 = (
        2
        * block_precision
        * block_recall
        / (
            block_precision
            + block_recall
        )
        if (
            block_precision
            + block_recall
        )
        > 0
        else 0.0
    )

    leaf_tp = sum(
        row.easy_leaf_true_positive_count
        for row in rows
    )
    leaf_pred = sum(
        row.easy_leaf_predicted_count
        for row in rows
    )
    leaf_ref = sum(
        row.easy_leaf_reference_count
        for row in rows
    )

    leaf_precision = (
        leaf_tp / leaf_pred
        if leaf_pred
        else (
            1.0
            if leaf_ref == 0
            else 0.0
        )
    )
    leaf_recall = (
        leaf_tp / leaf_ref
        if leaf_ref
        else 1.0
    )

    grouped: dict[
        tuple[int, int],
        list[
            DiscoveryObservation
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

    cells = []
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
        cell = {
            "core_dimension": k,
            "apparent_dimension": n,
            "count": len(
                cell_rows
            ),
            "mean_final_solver_ops": mean(
                row.final_solver_ops
                for row in cell_rows
            ),
            "mean_retained_dimension": mean(
                row.retained_dimension
                for row in cell_rows
            ),
            "verified_retention": mean(
                1.0
                if row.final_verified
                else 0.0
                for row in cell_rows
            ),
        }
        if cell_active:
            cell.update(
                {
                    "mean_solver_savings_recovery": mean(
                        float(
                            row.solver_savings_recovery
                        )
                        for row in cell_active
                        if row.solver_savings_recovery
                        is not None
                    ),
                    "mean_elimination_recovery": mean(
                        float(
                            row.elimination_recovery
                        )
                        for row in cell_active
                        if row.elimination_recovery
                        is not None
                    ),
                }
            )
        cells.append(
            cell
        )

    return {
        "method": rows[0].method,
        "count": len(
            rows
        ),
        "active_count": len(
            active
        ),
        "verified_retention": mean(
            1.0
            if row.final_verified
            else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            row.unsafe_accepted_reductions
            for row in rows
        ),
        "mean_final_solver_ops": mean(
            row.final_solver_ops
            for row in rows
        ),
        "mean_retained_dimension": mean(
            row.retained_dimension
            for row in rows
        ),
        "mean_solver_savings_recovery": mean(
            float(
                row.solver_savings_recovery
            )
            for row in active
            if row.solver_savings_recovery
            is not None
        ),
        "mean_elimination_recovery": mean(
            float(
                row.elimination_recovery
            )
            for row in active
            if row.elimination_recovery
            is not None
        ),
        "mean_accepted_local_count": mean(
            row.accepted_local_count
            for row in rows
        ),
        "mean_accepted_block_count": mean(
            row.accepted_block_count
            for row in rows
        ),
        "mean_discovered_block_candidate_count": mean(
            row.discovered_block_candidate_count
            for row in rows
        ),
        "mean_row_pair_examinations": mean(
            row.row_pair_examinations
            for row in rows
        ),
        "mean_graph_edges_examined": mean(
            row.graph_edges_examined
            for row in rows
        ),
        "block_precision": (
            block_precision
        ),
        "block_recall": (
            block_recall
        ),
        "block_f1": (
            block_f1
        ),
        "easy_leaf_routing_precision": (
            leaf_precision
        ),
        "easy_leaf_routing_recall": (
            leaf_recall
        ),
        "mean_coupled_target_consumed_locally": mean(
            row.coupled_target_consumed_locally
            for row in rows
        ),
        "cells": cells,
    }


def select_best_deterministic(
    aggregates: dict[
        str,
        dict[str, object],
    ],
) -> tuple[
    str,
    dict[str, object],
]:
    order = {
        "D2_incidence_exact_overlap": 0,
        "D3_incidence_sparse_unit_pair": 1,
        "D4_incidence_component_graph": 2,
        "D1_local_first_exact_overlap": 3,
    }

    methods = tuple(
        order
    )

    best = max(
        methods,
        key=lambda method: (
            float(
                aggregates[
                    method
                ][
                    "mean_solver_savings_recovery"
                ]
            ),
            -float(
                aggregates[
                    method
                ][
                    "mean_final_solver_ops"
                ]
            ),
            -float(
                aggregates[
                    method
                ][
                    "mean_discovered_block_candidate_count"
                ]
            ),
            -float(
                aggregates[
                    method
                ][
                    "mean_row_pair_examinations"
                ]
            ),
            -order[
                method
            ],
        ),
    )
    return (
        best,
        aggregates[
            best
        ],
    )


def deterministic_discovery_decision(
    aggregate: dict[
        str,
        object,
    ],
) -> dict[str, object]:
    recovery = float(
        aggregate[
            "mean_solver_savings_recovery"
        ]
    )
    elimination = float(
        aggregate[
            "mean_elimination_recovery"
        ]
    )
    recall = float(
        aggregate[
            "block_recall"
        ]
    )
    safe = (
        float(
            aggregate[
                "verified_retention"
            ]
        )
        == 1.0
        and int(
            aggregate[
                "unsafe_accepted_reduction_count"
            ]
        )
        == 0
    )

    keep = (
        recovery >= 0.95
        and elimination >= 0.95
        and recall >= 0.95
        and safe
    )

    if keep:
        decision = (
            "KEEP_DETERMINISTIC_DISCOVERY"
        )
    elif (
        safe
        and (
            recovery >= 0.70
            or recall >= 0.70
        )
        and (
            recovery < 0.95
            or recall < 0.95
        )
    ):
        decision = (
            "LEARNED_DISCOVERY_HEADROOM"
        )
    else:
        decision = (
            "REDESIGN_DISCOVERY_REPRESENTATION"
        )

    return {
        "decision": decision,
        "gate_solver_recovery_ge_0_95": (
            recovery >= 0.95
        ),
        "gate_elimination_recovery_ge_0_95": (
            elimination >= 0.95
        ),
        "gate_block_recall_ge_0_95": (
            recall >= 0.95
        ),
        "gate_verified_retention_1": (
            float(
                aggregate[
                    "verified_retention"
                ]
            )
            == 1.0
        ),
        "gate_unsafe_0": (
            int(
                aggregate[
                    "unsafe_accepted_reduction_count"
                ]
            )
            == 0
        ),
    }
