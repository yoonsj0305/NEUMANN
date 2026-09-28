from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

from .adversarial_v044 import exact_schur_witness
from .anti_shortcut_v042 import _key
from .block_discovery import materialize_generic_mixed, route_incidence_one_locals
from .coupled_block import BlockCandidate, derive_block_candidate, validate_block_candidate
from .mixed_coupled_dataset import MixedCoupledExample
from .stopping_gauntlet import FrozenV033Scorer
from .structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


@dataclass(frozen=True)
class V045Discovery:
    candidates: tuple[BlockCandidate, ...]
    pair_examinations: int
    posting_edges: int
    posting_updates: int
    derivations: int
    checkers: int


@dataclass(frozen=True)
class V045Execution:
    local_keys: tuple[tuple[int, str], ...]
    block_keys: tuple[tuple[tuple[int, int], tuple[str, str]], ...]
    answer: dict[str, Fraction]
    retained_dimension: int
    solver_ops: int
    verified: bool
    mode: str
    pair_examinations: int
    posting_edges: int
    posting_updates: int
    derivations: int
    checkers: int
    schur_construction_ops: int
    materialization_attempts: int
    rejected_materializations: int


def discover_incidence_six(example: MixedCoupledExample, local: tuple) -> V045Discovery:
    system = example.full_system
    remaining_rows = set(range(system.dimension)) - {item.row_index for item in local}
    remaining_targets = set(system.variables) - {item.target for item in local}
    postings: dict[str, set[int]] = {}
    row_to_targets: dict[int, set[str]] = {row: set() for row in remaining_rows}
    pair_targets: dict[tuple[int, int], set[str]] = {}
    edges = updates = examined = derivations = checkers = 0
    chosen: list[BlockCandidate] = []
    for col, name in enumerate(system.variables):
        original = {row for row in range(system.dimension) if system.A[row][col] != 0}
        if name not in remaining_targets or not 2 <= len(original) <= 6:
            continue
        active = original & remaining_rows
        postings[name] = active
        edges += len(active)
        for row in active:
            row_to_targets[row].add(name)
        if len(active) == 2:
            pair_targets.setdefault(tuple(sorted(active)), set()).add(name)

    while len(remaining_rows) > 2 and len(remaining_targets) > 2:
        valid_candidates: list[BlockCandidate] = []
        for pair, names in sorted(pair_targets.items()):
            examined += 1
            if len(names) != 2:
                continue
            targets = tuple(sorted(names, key=lambda name: int(name[1:])))
            derivations += 1
            candidate = derive_block_candidate(system, pair, targets)
            if candidate is None:
                continue
            checkers += 1
            if validate_block_candidate(system, candidate)[0]:
                valid_candidates.append(candidate)
        if not valid_candidates:
            break
        candidate = min(valid_candidates, key=_key)
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
            updates += 1
        remaining_rows.difference_update(candidate.row_indices)
        remaining_targets.difference_update(candidate.targets)
    return V045Discovery(tuple(chosen), examined, edges, updates, derivations, checkers)


def execute_v045(example: MixedCoupledExample, *, frozen_scorer: FrozenV033Scorer) -> V045Execution:
    system = example.full_system
    local = route_incidence_one_locals(example, frozen_scorer=frozen_scorer)
    discovery = discover_incidence_six(example, local)
    blocks = discovery.candidates
    pair_examinations = discovery.pair_examinations
    derivations = discovery.derivations
    checkers = discovery.checkers
    construction = attempts = rejected = 0
    materialized = None
    dense_answer = None
    dense_dimension = dense_ops = None
    mode = "full"

    if local or blocks:
        attempts = 1
        materialized = materialize_generic_mixed(example, local, blocks)
        if materialized is None:
            rejected = 1
        else:
            mode = "sparse"
    elif system.dimension in (6, 8):
        incidence = {name: sum(row[col] != 0 for row in system.A)
                     for col, name in enumerate(system.variables)}
        for row_pair in combinations(range(system.dimension), 2):
            pair_examinations += 1
            shared = [name for col, name in enumerate(system.variables)
                      if incidence[name] == 4 and all(system.A[row][col] != 0
                                                       for row in row_pair)]
            if len(shared) != 4:
                continue
            for targets in combinations(sorted(shared, key=lambda name: int(name[1:])), 2):
                derivations += 1
                candidate = derive_block_candidate(system, row_pair, targets)
                if candidate is None:
                    continue
                checkers += 1
                if not validate_block_candidate(system, candidate)[0]:
                    continue
                blocks = (candidate,)
                attempts = 1
                # The independent exact witness derives and checks the rule once more.
                derivations += 1
                checkers += 1
                witness = exact_schur_witness(system, row_pair, targets)
                if witness is None or not witness.verified:
                    rejected = 1
                else:
                    dense_answer = witness.answer
                    dense_dimension = witness.retained_dimension
                    dense_ops = witness.retained_solver_ops
                    construction = witness.construction_ops
                    mode = "schur"
                break
            break

    if materialized is not None:
        answer = materialized.full_answer
        verified = materialized.verified and materialized.ground_truth_equivalent
        dimension = materialized.retained_system.dimension
        solver_ops = materialized.solver_counts.arithmetic_ops
    elif dense_answer is not None:
        answer = dense_answer
        verified = True
        dimension = dense_dimension
        solver_ops = dense_ops
    else:
        answer, counts = solve_exact_gauss_jordan(system)
        verified, _ = verify_exact_full_system(system, answer)
        verified = verified and all(answer[name] == Fraction(value)
                                    for name, value in zip(system.variables, system.ground_truth))
        dimension = system.dimension
        solver_ops = counts.arithmetic_ops
        local, blocks = (), ()
        mode = "full"

    return V045Execution(
        tuple((item.row_index, item.target) for item in local),
        tuple(_key(item) for item in blocks), answer, dimension, solver_ops,
        verified, mode, pair_examinations, discovery.posting_edges,
        discovery.posting_updates, derivations, checkers, construction,
        attempts, rejected,
    )
