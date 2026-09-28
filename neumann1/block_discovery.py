from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from statistics import mean
from typing import Iterable

from .coupled_block import (
    derive_block_candidate,
    validate_block_candidate,
)
from .coupled_block_dataset import (
    OracleCoupledBlock,
)
from .learned_compression import (
    AffineCandidate,
    enumerate_affine_candidates,
)
from .mixed_coupled import (
    materialize_mixed_reference,
    run_frozen_one_row_pipeline,
)
from .mixed_coupled_dataset import (
    MixedCoupledExample,
    OracleEasyLeaf,
)
from .stopping_gauntlet import (
    FrozenV033Scorer,
)
from .structural_compression import (
    ExactLinearSystem,
    solve_exact_gauss_jordan,
)


DISCOVERY_METHOD_ORDER = (
    "incidence_signature",
    "row_pair_shared_target",
    "exact_visible_pair",
)


@dataclass(frozen=True)
class DiscoveryWork:
    candidate_entries_scanned: int = 0
    target_signatures_built: int = 0
    two_row_signature_groups_inspected: int = 0
    row_pairs_compared: int = 0
    shared_target_intersections: int = 0
    shared_target_pairs_enumerated: int = 0
    block_derivations_attempted: int = 0

    @property
    def proxy_total(self) -> int:
        return (
            self.candidate_entries_scanned
            + self.target_signatures_built
            + self.two_row_signature_groups_inspected
            + self.row_pairs_compared
            + self.shared_target_intersections
            + self.shared_target_pairs_enumerated
            + self.block_derivations_attempted
        )


@dataclass(frozen=True)
class DiscoveryPlan:
    method: str
    easy_leaves: tuple[
        OracleEasyLeaf, ...
    ]
    blocks: tuple[
        OracleCoupledBlock, ...
    ]
    unresolved_candidate_count: int
    work: DiscoveryWork


@dataclass(frozen=True)
class DiscoveryObservation:
    method: str
    core_dimension: int
    apparent_dimension: int
    baseline_solver_ops: int
    oracle_solver_ops: int
    oracle_solver_savings: int
    local_only_solver_ops: int
    local_only_solver_savings: int
    discovered_solver_ops: int
    discovered_solver_savings: int
    solver_savings_recovery: float | None
    local_only_solver_savings_recovery: float | None
    discovered_retained_dimension: int
    retained_dimension_error: int
    oracle_easy_leaf_count: int
    discovered_easy_leaf_count: int
    true_positive_easy_leaves: int
    oracle_block_count: int
    discovered_block_count: int
    true_positive_blocks: int
    unresolved_candidate_count: int
    verified: bool
    unsafe_accepted_reductions: int
    work: DiscoveryWork


def _target_sort_key(
    name: str,
) -> int:
    return int(name[1:])


def _candidate_maps(
    system: ExactLinearSystem,
) -> tuple[
    tuple[AffineCandidate, ...],
    dict[str, tuple[int, ...]],
    dict[int, frozenset[str]],
    dict[tuple[int, str], AffineCandidate],
]:
    candidates = enumerate_affine_candidates(
        system
    )

    rows_by_target_mutable: dict[
        str,
        set[int],
    ] = {}
    targets_by_row_mutable: dict[
        int,
        set[str],
    ] = {}
    candidate_map: dict[
        tuple[int, str],
        AffineCandidate,
    ] = {}

    for candidate in candidates:
        rows_by_target_mutable.setdefault(
            candidate.target,
            set(),
        ).add(
            candidate.row_index
        )
        targets_by_row_mutable.setdefault(
            candidate.row_index,
            set(),
        ).add(
            candidate.target
        )
        candidate_map[
            candidate.key
        ] = candidate

    rows_by_target = {
        target: tuple(
            sorted(rows)
        )
        for target, rows
        in rows_by_target_mutable.items()
    }
    targets_by_row = {
        row: frozenset(
            targets
        )
        for row, targets
        in targets_by_row_mutable.items()
    }

    return (
        candidates,
        rows_by_target,
        targets_by_row,
        candidate_map,
    )


def _leaf_identities(
    rows_by_target: dict[
        str,
        tuple[int, ...],
    ],
) -> tuple[
    OracleEasyLeaf, ...
]:
    output = [
        OracleEasyLeaf(
            row_index=rows[0],
            target=target,
        )
        for target, rows
        in rows_by_target.items()
        if len(rows) == 1
    ]
    output.sort(
        key=lambda leaf: (
            leaf.row_index,
            _target_sort_key(
                leaf.target
            ),
        )
    )
    return tuple(output)


def _block_key(
    block: OracleCoupledBlock,
) -> tuple[
    tuple[int, int],
    tuple[str, str],
]:
    return (
        tuple(
            sorted(
                block.row_indices
            )
        ),
        tuple(
            sorted(
                block.targets,
                key=_target_sort_key,
            )
        ),
    )


def _canonical_block_identity(
    rows: tuple[int, int],
    targets: tuple[str, str],
) -> OracleCoupledBlock:
    return OracleCoupledBlock(
        row_indices=tuple(
            sorted(rows)
        ),
        targets=tuple(
            sorted(
                targets,
                key=_target_sort_key,
            )
        ),
    )


def _validate_block_identity(
    system: ExactLinearSystem,
    block: OracleCoupledBlock,
) -> bool:
    candidate = derive_block_candidate(
        system,
        block.row_indices,
        block.targets,
    )
    if candidate is None:
        return False

    ok, _ = validate_block_candidate(
        system,
        candidate,
    )
    return ok


def discover_incidence_signature(
    system: ExactLinearSystem,
) -> DiscoveryPlan:
    (
        candidates,
        rows_by_target,
        _,
        _,
    ) = _candidate_maps(system)

    leaves = _leaf_identities(
        rows_by_target
    )

    targets_by_signature: dict[
        tuple[int, ...],
        list[str],
    ] = {}
    for target, rows in rows_by_target.items():
        if len(rows) == 2:
            targets_by_signature.setdefault(
                rows,
                [],
            ).append(
                target
            )

    blocks: list[
        OracleCoupledBlock
    ] = []
    derivations = 0
    grouped_targets: set[str] = set()

    for rows, targets in sorted(
        targets_by_signature.items()
    ):
        targets = sorted(
            targets,
            key=_target_sort_key,
        )
        if len(targets) != 2:
            continue

        block = _canonical_block_identity(
            (
                rows[0],
                rows[1],
            ),
            (
                targets[0],
                targets[1],
            ),
        )
        derivations += 1
        if _validate_block_identity(
            system,
            block,
        ):
            blocks.append(
                block
            )
            grouped_targets.update(
                targets
            )

    leaf_targets = {
        leaf.target
        for leaf in leaves
    }
    resolved_candidate_count = sum(
        1
        for candidate in candidates
        if (
            candidate.target in leaf_targets
            or candidate.target
            in grouped_targets
        )
    )

    return DiscoveryPlan(
        method="incidence_signature",
        easy_leaves=leaves,
        blocks=tuple(blocks),
        unresolved_candidate_count=(
            len(candidates)
            - resolved_candidate_count
        ),
        work=DiscoveryWork(
            candidate_entries_scanned=(
                len(candidates)
            ),
            target_signatures_built=(
                len(rows_by_target)
            ),
            two_row_signature_groups_inspected=(
                len(
                    targets_by_signature
                )
            ),
            block_derivations_attempted=(
                derivations
            ),
        ),
    )


def discover_row_pair_shared_target(
    system: ExactLinearSystem,
) -> DiscoveryPlan:
    (
        candidates,
        rows_by_target,
        targets_by_row,
        _,
    ) = _candidate_maps(system)

    leaves = _leaf_identities(
        rows_by_target
    )

    proposed: list[
        OracleCoupledBlock
    ] = []
    row_pairs = 0
    intersections = 0
    derivations = 0

    for first in range(
        system.dimension
    ):
        first_targets = targets_by_row.get(
            first,
            frozenset(),
        )
        for second in range(
            first + 1,
            system.dimension,
        ):
            row_pairs += 1
            intersections += 1
            shared = sorted(
                first_targets.intersection(
                    targets_by_row.get(
                        second,
                        frozenset(),
                    )
                ),
                key=_target_sort_key,
            )
            if len(shared) != 2:
                continue

            block = _canonical_block_identity(
                (
                    first,
                    second,
                ),
                (
                    shared[0],
                    shared[1],
                ),
            )
            derivations += 1
            if _validate_block_identity(
                system,
                block,
            ):
                proposed.append(
                    block
                )

    proposed.sort(
        key=_block_key
    )

    blocks: list[
        OracleCoupledBlock
    ] = []
    used_rows: set[int] = set()
    used_targets: set[str] = set()

    for block in proposed:
        if any(
            row in used_rows
            for row in block.row_indices
        ):
            continue
        if any(
            target in used_targets
            for target in block.targets
        ):
            continue
        blocks.append(
            block
        )
        used_rows.update(
            block.row_indices
        )
        used_targets.update(
            block.targets
        )

    resolved_targets = {
        leaf.target
        for leaf in leaves
    }
    resolved_targets.update(
        target
        for block in blocks
        for target in block.targets
    )
    resolved_candidate_count = sum(
        1
        for candidate in candidates
        if candidate.target
        in resolved_targets
    )

    return DiscoveryPlan(
        method="row_pair_shared_target",
        easy_leaves=leaves,
        blocks=tuple(blocks),
        unresolved_candidate_count=(
            len(candidates)
            - resolved_candidate_count
        ),
        work=DiscoveryWork(
            candidate_entries_scanned=(
                len(candidates)
            ),
            target_signatures_built=(
                len(rows_by_target)
            ),
            row_pairs_compared=(
                row_pairs
            ),
            shared_target_intersections=(
                intersections
            ),
            block_derivations_attempted=(
                derivations
            ),
        ),
    )


def discover_exact_visible_pair(
    system: ExactLinearSystem,
) -> DiscoveryPlan:
    (
        candidates,
        rows_by_target,
        targets_by_row,
        _,
    ) = _candidate_maps(system)

    leaves = _leaf_identities(
        rows_by_target
    )

    proposed: list[
        OracleCoupledBlock
    ] = []
    row_pairs = 0
    intersections = 0
    target_pairs = 0
    derivations = 0

    for first in range(
        system.dimension
    ):
        first_targets = targets_by_row.get(
            first,
            frozenset(),
        )
        for second in range(
            first + 1,
            system.dimension,
        ):
            row_pairs += 1
            intersections += 1
            shared = sorted(
                first_targets.intersection(
                    targets_by_row.get(
                        second,
                        frozenset(),
                    )
                ),
                key=_target_sort_key,
            )

            for targets in combinations(
                shared,
                2,
            ):
                target_pairs += 1
                block = _canonical_block_identity(
                    (
                        first,
                        second,
                    ),
                    (
                        targets[0],
                        targets[1],
                    ),
                )
                derivations += 1
                if _validate_block_identity(
                    system,
                    block,
                ):
                    proposed.append(
                        block
                    )

    unique: dict[
        tuple[
            tuple[int, int],
            tuple[str, str],
        ],
        OracleCoupledBlock,
    ] = {
        _block_key(block): block
        for block in proposed
    }

    blocks: list[
        OracleCoupledBlock
    ] = []
    used_rows: set[int] = set()
    used_targets: set[str] = set()

    for key in sorted(
        unique
    ):
        block = unique[key]
        if any(
            row in used_rows
            for row in block.row_indices
        ):
            continue
        if any(
            target in used_targets
            for target in block.targets
        ):
            continue

        blocks.append(
            block
        )
        used_rows.update(
            block.row_indices
        )
        used_targets.update(
            block.targets
        )

    resolved_targets = {
        leaf.target
        for leaf in leaves
    }
    resolved_targets.update(
        target
        for block in blocks
        for target in block.targets
    )
    resolved_candidate_count = sum(
        1
        for candidate in candidates
        if candidate.target
        in resolved_targets
    )

    return DiscoveryPlan(
        method="exact_visible_pair",
        easy_leaves=leaves,
        blocks=tuple(blocks),
        unresolved_candidate_count=(
            len(candidates)
            - resolved_candidate_count
        ),
        work=DiscoveryWork(
            candidate_entries_scanned=(
                len(candidates)
            ),
            target_signatures_built=(
                len(rows_by_target)
            ),
            row_pairs_compared=(
                row_pairs
            ),
            shared_target_intersections=(
                intersections
            ),
            shared_target_pairs_enumerated=(
                target_pairs
            ),
            block_derivations_attempted=(
                derivations
            ),
        ),
    )


def discover(
    system: ExactLinearSystem,
    method: str,
) -> DiscoveryPlan:
    if method == "incidence_signature":
        return discover_incidence_signature(
            system
        )
    if method == "row_pair_shared_target":
        return discover_row_pair_shared_target(
            system
        )
    if method == "exact_visible_pair":
        return discover_exact_visible_pair(
            system
        )

    raise ValueError(
        f"unknown discovery method: {method}"
    )


def _leaf_key(
    leaf: OracleEasyLeaf,
) -> tuple[int, str]:
    return (
        leaf.row_index,
        leaf.target,
    )


def _execute_plan(
    example: MixedCoupledExample,
    plan: DiscoveryPlan,
):
    shadow = replace(
        example,
        oracle_easy_leaves=(
            plan.easy_leaves
        ),
        oracle_blocks=(
            plan.blocks
        ),
    )
    return materialize_mixed_reference(
        shadow
    )


def observe_discovery(
    example: MixedCoupledExample,
    method: str,
    *,
    frozen_scorer: FrozenV033Scorer,
) -> DiscoveryObservation:
    (
        _,
        baseline_counts,
    ) = solve_exact_gauss_jordan(
        example.full_system
    )
    baseline_ops = (
        baseline_counts.arithmetic_ops
    )

    oracle = materialize_mixed_reference(
        example
    )
    if oracle is None:
        raise AssertionError(
            "oracle mixed reference failed"
        )

    local = run_frozen_one_row_pipeline(
        example,
        frozen_scorer=frozen_scorer,
    )

    plan = discover(
        example.full_system,
        method,
    )
    discovered = _execute_plan(
        example,
        plan,
    )

    oracle_ops = (
        oracle.solver_counts.arithmetic_ops
    )
    oracle_savings = (
        baseline_ops - oracle_ops
    )
    local_savings = (
        baseline_ops
        - local.final_solver_ops
    )

    oracle_leaf_keys = {
        _leaf_key(leaf)
        for leaf in example.oracle_easy_leaves
    }
    discovered_leaf_keys = {
        _leaf_key(leaf)
        for leaf in plan.easy_leaves
    }

    oracle_block_keys = {
        _block_key(block)
        for block in example.oracle_blocks
    }
    discovered_block_keys = {
        _block_key(block)
        for block in plan.blocks
    }

    if discovered is None:
        discovered_ops = baseline_ops
        discovered_savings = 0
        retained_dimension = (
            example.apparent_dimension
        )
        verified = False
        unsafe = (
            len(plan.easy_leaves)
            + len(plan.blocks)
        )
    else:
        discovered_ops = (
            discovered.solver_counts.arithmetic_ops
        )
        discovered_savings = (
            baseline_ops
            - discovered_ops
        )
        retained_dimension = (
            discovered.retained_system.dimension
        )
        verified = (
            discovered.verified
            and discovered.ground_truth_equivalent
        )
        unsafe = (
            0
            if verified
            else (
                len(plan.easy_leaves)
                + len(plan.blocks)
            )
        )

    if oracle_savings > 0:
        recovery: float | None = (
            discovered_savings
            / oracle_savings
        )
        local_recovery: float | None = (
            local_savings
            / oracle_savings
        )
    else:
        recovery = None
        local_recovery = None

    return DiscoveryObservation(
        method=method,
        core_dimension=(
            example.core_dimension
        ),
        apparent_dimension=(
            example.apparent_dimension
        ),
        baseline_solver_ops=(
            baseline_ops
        ),
        oracle_solver_ops=(
            oracle_ops
        ),
        oracle_solver_savings=(
            oracle_savings
        ),
        local_only_solver_ops=(
            local.final_solver_ops
        ),
        local_only_solver_savings=(
            local_savings
        ),
        discovered_solver_ops=(
            discovered_ops
        ),
        discovered_solver_savings=(
            discovered_savings
        ),
        solver_savings_recovery=(
            recovery
        ),
        local_only_solver_savings_recovery=(
            local_recovery
        ),
        discovered_retained_dimension=(
            retained_dimension
        ),
        retained_dimension_error=abs(
            retained_dimension
            - example.core_dimension
        ),
        oracle_easy_leaf_count=len(
            oracle_leaf_keys
        ),
        discovered_easy_leaf_count=len(
            discovered_leaf_keys
        ),
        true_positive_easy_leaves=len(
            oracle_leaf_keys.intersection(
                discovered_leaf_keys
            )
        ),
        oracle_block_count=len(
            oracle_block_keys
        ),
        discovered_block_count=len(
            discovered_block_keys
        ),
        true_positive_blocks=len(
            oracle_block_keys.intersection(
                discovered_block_keys
            )
        ),
        unresolved_candidate_count=(
            plan.unresolved_candidate_count
        ),
        verified=(
            verified
        ),
        unsafe_accepted_reductions=(
            unsafe
        ),
        work=(
            plan.work
        ),
    )


def _safe_ratio(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 1.0
    return (
        numerator
        / denominator
    )


def aggregate_discovery(
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
        if row.oracle_solver_savings > 0
    )

    oracle_leaf_count = sum(
        row.oracle_easy_leaf_count
        for row in rows
    )
    discovered_leaf_count = sum(
        row.discovered_easy_leaf_count
        for row in rows
    )
    true_leaf_count = sum(
        row.true_positive_easy_leaves
        for row in rows
    )

    oracle_block_count = sum(
        row.oracle_block_count
        for row in rows
    )
    discovered_block_count = sum(
        row.discovered_block_count
        for row in rows
    )
    true_block_count = sum(
        row.true_positive_blocks
        for row in rows
    )

    easy_leaf_recall = _safe_ratio(
        true_leaf_count,
        oracle_leaf_count,
    )
    easy_leaf_precision = _safe_ratio(
        true_leaf_count,
        discovered_leaf_count,
    )
    block_recall = _safe_ratio(
        true_block_count,
        oracle_block_count,
    )
    block_precision = _safe_ratio(
        true_block_count,
        discovered_block_count,
    )

    mean_active_recovery = mean(
        float(
            row.solver_savings_recovery
        )
        for row in active
        if row.solver_savings_recovery
        is not None
    )
    mean_local_recovery = mean(
        float(
            row.local_only_solver_savings_recovery
        )
        for row in active
        if row.local_only_solver_savings_recovery
        is not None
    )
    mean_dimension_error = mean(
        row.retained_dimension_error
        for row in active
    )

    verified_retention = mean(
        1.0
        if row.verified
        else 0.0
        for row in rows
    )
    unsafe = sum(
        row.unsafe_accepted_reductions
        for row in rows
    )

    adequate = (
        verified_retention == 1.0
        and unsafe == 0
        and mean_dimension_error == 0.0
        and mean_active_recovery >= 0.98
        and easy_leaf_recall >= 0.98
        and block_recall >= 0.98
    )

    return {
        "method": rows[0].method,
        "count": len(rows),
        "active_count": len(active),
        "verified_retention": (
            verified_retention
        ),
        "unsafe_accepted_reductions": (
            unsafe
        ),
        "mean_active_solver_savings_recovery": (
            mean_active_recovery
        ),
        "mean_local_only_solver_savings_recovery": (
            mean_local_recovery
        ),
        "mean_active_retained_dimension_error": (
            mean_dimension_error
        ),
        "easy_leaf_precision": (
            easy_leaf_precision
        ),
        "easy_leaf_recall": (
            easy_leaf_recall
        ),
        "block_precision": (
            block_precision
        ),
        "block_recall": (
            block_recall
        ),
        "mean_unresolved_candidate_count": mean(
            row.unresolved_candidate_count
            for row in rows
        ),
        "mean_discovery_work": {
            "candidate_entries_scanned": mean(
                row.work.candidate_entries_scanned
                for row in rows
            ),
            "target_signatures_built": mean(
                row.work.target_signatures_built
                for row in rows
            ),
            "two_row_signature_groups_inspected": mean(
                row.work.two_row_signature_groups_inspected
                for row in rows
            ),
            "row_pairs_compared": mean(
                row.work.row_pairs_compared
                for row in rows
            ),
            "shared_target_intersections": mean(
                row.work.shared_target_intersections
                for row in rows
            ),
            "shared_target_pairs_enumerated": mean(
                row.work.shared_target_pairs_enumerated
                for row in rows
            ),
            "block_derivations_attempted": mean(
                row.work.block_derivations_attempted
                for row in rows
            ),
            "proxy_total": mean(
                row.work.proxy_total
                for row in rows
            ),
        },
        "adequate": adequate,
    }


def select_discovery_method(
    aggregates: dict[
        str,
        dict[str, object],
    ],
) -> dict[str, object]:
    selected: str | None = None

    for method in DISCOVERY_METHOD_ORDER:
        if bool(
            aggregates[
                method
            ][
                "adequate"
            ]
        ):
            selected = method
            break

    best_method = max(
        DISCOVERY_METHOD_ORDER,
        key=lambda method: float(
            aggregates[
                method
            ][
                "mean_active_solver_savings_recovery"
            ]
        ),
    )
    best_recovery = float(
        aggregates[
            best_method
        ][
            "mean_active_solver_savings_recovery"
        ]
    )

    all_safe = all(
        aggregate[
            "verified_retention"
        ]
        == 1.0
        and aggregate[
            "unsafe_accepted_reductions"
        ]
        == 0
        for aggregate in aggregates.values()
    )

    if selected is not None:
        decision = (
            "DELETE_LEARNED_BLOCK_SCORER"
        )
    elif (
        all_safe
        and best_recovery >= 0.75
    ):
        decision = (
            "AUTHORIZE_SMALLEST_LEARNED_BLOCK_SCORER"
        )
    else:
        decision = (
            "REDESIGN_DISCOVERY_REPRESENTATION"
        )

    return {
        "selected_method": selected,
        "best_deterministic_method": (
            best_method
        ),
        "best_deterministic_recovery": (
            best_recovery
        ),
        "all_deterministic_methods_safe": (
            all_safe
        ),
        "decision": decision,
    }
