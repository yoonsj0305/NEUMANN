from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .anti_shortcut_v042 import _discover, _key
from .block_discovery import materialize_generic_mixed, route_incidence_one_locals
from .coupled_block import BlockCandidate, derive_block_candidate, validate_block_candidate
from .mixed_coupled_dataset import MixedCoupledExample
from .stopping_gauntlet import FrozenV033Scorer
from .structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


@dataclass(frozen=True)
class IndexedDiscovery:
    candidates: tuple[BlockCandidate, ...]
    row_pair_examinations: int
    posting_edges: int
    posting_updates: int
    derivation_calls: int
    checker_calls: int


@dataclass(frozen=True)
class IndexedExecution:
    local_keys: tuple[tuple[int, str], ...]
    block_keys: tuple[tuple[tuple[int, int], tuple[str, str]], ...]
    answer: dict[str, Fraction]
    retained_dimension: int
    solver_ops: int
    verified: bool
    row_pair_examinations: int
    posting_edges: int
    posting_updates: int
    derivation_calls: int
    checker_calls: int
    materialization_attempts: int
    rejected_materializations: int


def discover_indexed(example: MixedCoupledExample, local_candidates: tuple) -> IndexedDiscovery:
    system = example.full_system
    remaining_rows = set(range(system.dimension)) - {
        candidate.row_index for candidate in local_candidates
    }
    remaining_targets = set(system.variables) - {
        candidate.target for candidate in local_candidates
    }
    postings: dict[str, set[int]] = {}
    row_to_targets: dict[int, set[str]] = {row: set() for row in remaining_rows}
    pair_targets: dict[tuple[int, int], set[str]] = {}
    posting_edges = 0
    posting_updates = 0
    pair_examinations = 0
    derivation_calls = 0
    checker_calls = 0
    chosen: list[BlockCandidate] = []

    for column, name in enumerate(system.variables):
        original_rows = {row for row in range(system.dimension) if system.A[row][column] != 0}
        if name not in remaining_targets or not 2 <= len(original_rows) <= 4:
            continue
        active = original_rows & remaining_rows
        postings[name] = active
        posting_edges += len(active)
        for row in active:
            row_to_targets[row].add(name)
        if len(active) == 2:
            pair_targets.setdefault(tuple(sorted(active)), set()).add(name)

    while len(remaining_rows) > 2 and len(remaining_targets) > 2:
        found: list[BlockCandidate] = []
        for pair, names in sorted(pair_targets.items()):
            pair_examinations += 1
            if len(names) != 2:
                continue
            targets = tuple(sorted(names, key=lambda name: int(name[1:])))
            derivation_calls += 1
            candidate = derive_block_candidate(system, pair, targets)
            if candidate is None:
                continue
            checker_calls += 1
            valid, _ = validate_block_candidate(system, candidate)
            if valid:
                found.append(candidate)
        if not found:
            break

        candidate = min(found, key=_key)
        chosen.append(candidate)
        affected = set().union(*(row_to_targets[row] for row in candidate.row_indices))
        affected.update(name for name in candidate.targets if name in postings)
        for name in affected:
            active = postings[name]
            if len(active) == 2:
                pair = tuple(sorted(active))
                pair_targets[pair].remove(name)
                if not pair_targets[pair]:
                    del pair_targets[pair]
            for row in active:
                row_to_targets[row].discard(name)
            if name in candidate.targets:
                del postings[name]
            else:
                active.difference_update(candidate.row_indices)
                for row in active:
                    row_to_targets[row].add(name)
                if len(active) == 2:
                    pair_targets.setdefault(tuple(sorted(active)), set()).add(name)
            posting_updates += 1
        remaining_rows.difference_update(candidate.row_indices)
        remaining_targets.difference_update(candidate.targets)

    return IndexedDiscovery(tuple(chosen), pair_examinations, posting_edges,
                            posting_updates, derivation_calls, checker_calls)


def execute_peeling(example: MixedCoupledExample, *, frozen_scorer: FrozenV033Scorer,
                    indexed: bool) -> IndexedExecution:
    """Execution path without benchmark-only oracle and baseline solves."""
    local = route_incidence_one_locals(example, frozen_scorer=frozen_scorer)
    discovery = (discover_indexed(example, local) if indexed else
                 _discover(example, "E2_residual_peeling", local))
    blocks = discovery.candidates
    attempts = int(bool(local or blocks))
    materialized = materialize_generic_mixed(example, local, blocks) if attempts else None
    rejected = int(attempts and materialized is None)
    if materialized is None:
        answer, counts = solve_exact_gauss_jordan(example.full_system)
        verified, _ = verify_exact_full_system(example.full_system, answer)
        verified = verified and all(answer[name] == Fraction(value) for name, value in
                                    zip(example.full_system.variables, example.full_system.ground_truth))
        local, blocks = (), ()
        dimension = example.full_system.dimension
        ops = counts.arithmetic_ops
    else:
        answer = materialized.full_answer
        verified = materialized.verified and materialized.ground_truth_equivalent
        dimension = materialized.retained_system.dimension
        ops = materialized.solver_counts.arithmetic_ops
    return IndexedExecution(
        tuple((candidate.row_index, candidate.target) for candidate in local),
        tuple(_key(candidate) for candidate in blocks), answer, dimension, ops,
        verified, discovery.row_pair_examinations,
        discovery.posting_edges if indexed else 0,
        discovery.posting_updates if indexed else 0,
        discovery.derivation_calls, discovery.checker_calls, attempts, rejected,
    )
