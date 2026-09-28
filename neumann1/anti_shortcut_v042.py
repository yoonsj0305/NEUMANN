from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

from .block_discovery import (
    materialize_generic_mixed, route_incidence_one_locals, target_incidence,
)
from .coupled_block import BlockCandidate, derive_block_candidate, validate_block_candidate
from .mixed_coupled import materialize_mixed_reference
from .mixed_coupled_dataset import MixedCoupledExample
from .stopping_gauntlet import FrozenV033Scorer
from .structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


E_METHODS = ("E1_static_nonunit", "E2_residual_peeling")


@dataclass(frozen=True)
class PeelingDiscovery:
    candidates: tuple[BlockCandidate, ...]
    row_pair_examinations: int
    derivation_calls: int
    checker_calls: int


@dataclass(frozen=True)
class PeelingObservation:
    method: str
    core_dimension: int
    apparent_dimension: int
    oracle_elimination_count: int
    baseline_solver_ops: int
    oracle_solver_ops: int
    final_solver_ops: int
    accepted_local_count: int
    accepted_block_count: int
    block_true_positive_count: int
    block_reference_count: int
    block_predicted_count: int
    row_pair_examinations: int
    derivation_calls: int
    checker_calls: int
    final_materialization_attempts: int
    rejected_joint_materializations: int
    verified: bool
    unsafe_accepted_reductions: int

    @property
    def elimination_recovery(self) -> float | None:
        if self.oracle_elimination_count == 0:
            return None
        return (self.accepted_local_count + 2*self.accepted_block_count
                ) / self.oracle_elimination_count

    @property
    def solver_savings_recovery(self) -> float | None:
        savings = self.baseline_solver_ops - self.oracle_solver_ops
        if savings <= 0:
            return None
        return (self.baseline_solver_ops - self.final_solver_ops) / savings


def _key(candidate: BlockCandidate) -> tuple[tuple[int, int], tuple[str, str]]:
    return candidate.row_indices, candidate.targets


def _discover(example: MixedCoupledExample, method: str,
              local_candidates: tuple) -> PeelingDiscovery:
    if method not in E_METHODS:
        raise ValueError(f"unknown method: {method}")
    system = example.full_system
    incidence = target_incidence(system)
    remaining_rows = set(range(system.dimension)) - {
        candidate.row_index for candidate in local_candidates
    }
    remaining_targets = set(system.variables) - {
        candidate.target for candidate in local_candidates
    }
    chosen: list[BlockCandidate] = []
    pair_examinations = 0
    derivation_calls = 0
    checker_calls = 0

    while True:
        residual_incidence = {
            name: sum(system.A[row][column] != 0 for row in remaining_rows)
            for column, name in enumerate(system.variables)
        }
        found: list[BlockCandidate] = []
        for row_a, row_b in combinations(sorted(remaining_rows), 2):
            pair_examinations += 1
            targets = [name for column, name in enumerate(system.variables)
                       if name in remaining_targets
                       and system.A[row_a][column] != 0
                       and system.A[row_b][column] != 0
                       and (incidence[name] == 2 if method == "E1_static_nonunit"
                            else 2 <= incidence[name] <= 4
                            and residual_incidence[name] == 2)]
            if len(targets) != 2:
                continue
            targets.sort(key=lambda name: int(name[1:]))
            derivation_calls += 1
            candidate = derive_block_candidate(
                system, (row_a, row_b), (targets[0], targets[1]),
            )
            if candidate is None:
                continue
            checker_calls += 1
            valid, _ = validate_block_candidate(system, candidate)
            if valid:
                found.append(candidate)

        if not found:
            break
        chosen_candidate = min(found, key=_key)
        chosen.append(chosen_candidate)
        remaining_rows.difference_update(chosen_candidate.row_indices)
        remaining_targets.difference_update(chosen_candidate.targets)
        if method == "E1_static_nonunit":
            # Static candidates have global incidence two, but conflict
            # selection still requires revisiting the remaining row set.
            continue

    return PeelingDiscovery(tuple(chosen), pair_examinations,
                            derivation_calls, checker_calls)


def observe_peeling_method(example: MixedCoupledExample, method: str,
                           *, frozen_scorer: FrozenV033Scorer) -> PeelingObservation:
    if method not in E_METHODS:
        raise ValueError(f"unknown method: {method}")
    full_answer, full_counts = solve_exact_gauss_jordan(example.full_system)
    reference = materialize_mixed_reference(example)
    if reference is None or not reference.verified:
        raise AssertionError("exact oracle failed")
    local = route_incidence_one_locals(example, frozen_scorer=frozen_scorer)
    discovery = _discover(example, method, local)
    materialized = materialize_generic_mixed(
        example, local, discovery.candidates,
    )
    if materialized is None:
        # Fail closed: rejected proposals cannot contribute savings.
        verified, _ = verify_exact_full_system(example.full_system, full_answer)
        verified = verified and all(
            full_answer[name] == Fraction(expected)
            for name, expected in zip(example.full_system.variables,
                                      example.full_system.ground_truth)
        )
        accepted_local, accepted_blocks = (), ()
        final_ops = full_counts.arithmetic_ops
        rejected = 1
    else:
        accepted_local, accepted_blocks = local, discovery.candidates
        final_ops = materialized.solver_counts.arithmetic_ops
        verified = materialized.verified and materialized.ground_truth_equivalent
        rejected = 0

    oracle_keys = {(block.row_indices, block.targets)
                   for block in example.oracle_blocks}
    predicted_keys = {_key(candidate) for candidate in accepted_blocks}
    return PeelingObservation(
        method=method,
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        oracle_elimination_count=example.oracle_elimination_count,
        baseline_solver_ops=full_counts.arithmetic_ops,
        oracle_solver_ops=reference.solver_counts.arithmetic_ops,
        final_solver_ops=final_ops,
        accepted_local_count=len(accepted_local),
        accepted_block_count=len(accepted_blocks),
        block_true_positive_count=len(oracle_keys & predicted_keys),
        block_reference_count=len(oracle_keys),
        block_predicted_count=len(predicted_keys),
        row_pair_examinations=discovery.row_pair_examinations,
        derivation_calls=discovery.derivation_calls,
        checker_calls=discovery.checker_calls,
        final_materialization_attempts=1,
        rejected_joint_materializations=rejected,
        verified=verified,
        unsafe_accepted_reductions=0 if verified else (
            len(accepted_local) + 2*len(accepted_blocks)),
    )
