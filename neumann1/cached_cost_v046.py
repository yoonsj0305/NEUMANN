from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from heapq import heappop, heappush

from .anti_shortcut_v042 import _key
from .block_discovery import materialize_generic_mixed, route_incidence_one_locals
from .coupled_block import BlockCandidate, derive_block_candidate, validate_block_candidate
from .mixed_coupled_dataset import MixedCoupledExample
from .stopping_gauntlet import FrozenV033Scorer
from .structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


@dataclass(frozen=True)
class CachedDiscovery:
    candidates: tuple[BlockCandidate, ...]
    pair_examinations: int
    stale_heap_pops: int
    posting_edges: int
    posting_updates: int
    derivations: int
    checkers: int


@dataclass(frozen=True)
class CachedExecution:
    local_keys: tuple[tuple[int, str], ...]
    block_keys: tuple[tuple[tuple[int, int], tuple[str, str]], ...]
    answer: dict[str, Fraction]
    retained_dimension: int
    solver_ops: int
    verified: bool
    pair_examinations: int
    stale_heap_pops: int
    posting_edges: int
    posting_updates: int
    derivations: int
    checkers: int
    materialization_attempts: int
    rejected_materializations: int


def discover_cached_six(example: MixedCoupledExample, local: tuple) -> CachedDiscovery:
    system = example.full_system
    remaining_rows = set(range(system.dimension)) - {item.row_index for item in local}
    remaining_targets = set(system.variables) - {item.target for item in local}
    postings: dict[str, set[int]] = {}
    row_to_targets: dict[int, set[str]] = {row: set() for row in remaining_rows}
    pair_targets: dict[tuple[int, int], set[str]] = {}
    cache: dict[tuple[int, int], tuple[tuple[str, str], BlockCandidate | None]] = {}
    heap: list[tuple[tuple[int, int], tuple[str, str], BlockCandidate]] = []
    edges = updates = examinations = stale = derivations = checkers = 0
    chosen: list[BlockCandidate] = []

    def consider(pair: tuple[int, int]) -> None:
        nonlocal examinations, derivations, checkers
        names = pair_targets.get(pair, set())
        if len(names) != 2:
            return
        examinations += 1
        targets = tuple(sorted(names, key=lambda name: int(name[1:])))
        derivations += 1
        candidate = derive_block_candidate(system, pair, targets)
        if candidate is not None:
            checkers += 1
            if not validate_block_candidate(system, candidate)[0]:
                candidate = None
        cache[pair] = (targets, candidate)
        if candidate is not None:
            heappush(heap, (pair, targets, candidate))

    for column, name in enumerate(system.variables):
        original = {row for row in range(system.dimension) if system.A[row][column] != 0}
        if name not in remaining_targets or not 2 <= len(original) <= 6:
            continue
        active = original & remaining_rows
        postings[name] = active
        edges += len(active)
        for row in active:
            row_to_targets[row].add(name)
        if len(active) == 2:
            pair_targets.setdefault(tuple(sorted(active)), set()).add(name)
    if len(remaining_rows) > 2 and len(remaining_targets) > 2:
        for pair in sorted(pair_targets):
            consider(pair)

    while len(remaining_rows) > 2 and len(remaining_targets) > 2:
        candidate = None
        while heap:
            pair, targets, proposed = heappop(heap)
            current = cache.get(pair)
            if (current != (targets, proposed)
                or not set(pair).issubset(remaining_rows)
                or not set(targets).issubset(remaining_targets)):
                stale += 1
                continue
            candidate = proposed
            break
        if candidate is None:
            break
        chosen.append(candidate)
        affected = set().union(*(row_to_targets[row] for row in candidate.row_indices))
        affected.update(name for name in candidate.targets if name in postings)
        touched: set[tuple[int, int]] = set()
        for name in affected:
            active = postings[name]
            if len(active) == 2:
                pair = tuple(sorted(active))
                touched.add(pair)
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
                    pair = tuple(sorted(active))
                    touched.add(pair)
                    pair_targets.setdefault(pair, set()).add(name)
            updates += 1
        remaining_rows.difference_update(candidate.row_indices)
        remaining_targets.difference_update(candidate.targets)
        for pair in touched:
            cache.pop(pair, None)
        if len(remaining_rows) > 2 and len(remaining_targets) > 2:
            for pair in sorted(touched):
                consider(pair)
    return CachedDiscovery(tuple(chosen), examinations+stale, stale, edges,
                           updates, derivations, checkers)


def execute_v046(example: MixedCoupledExample, *, frozen_scorer: FrozenV033Scorer) -> CachedExecution:
    system = example.full_system
    local = route_incidence_one_locals(example, frozen_scorer=frozen_scorer)
    discovery = discover_cached_six(example, local)
    blocks = discovery.candidates
    attempts = int(bool(local or blocks))
    materialized = materialize_generic_mixed(example, local, blocks) if attempts else None
    rejected = int(attempts and materialized is None)
    if materialized is None:
        answer, counts = solve_exact_gauss_jordan(system)
        verified, _ = verify_exact_full_system(system, answer)
        verified = verified and all(answer[name] == Fraction(value)
                                    for name, value in zip(system.variables, system.ground_truth))
        dimension = system.dimension
        ops = counts.arithmetic_ops
        local, blocks = (), ()
    else:
        answer = materialized.full_answer
        verified = materialized.verified and materialized.ground_truth_equivalent
        dimension = materialized.retained_system.dimension
        ops = materialized.solver_counts.arithmetic_ops
    return CachedExecution(
        tuple((item.row_index, item.target) for item in local),
        tuple(_key(item) for item in blocks), answer, dimension, ops,
        verified, discovery.pair_examinations, discovery.stale_heap_pops,
        discovery.posting_edges, discovery.posting_updates,
        discovery.derivations, discovery.checkers, attempts, rejected,
    )
