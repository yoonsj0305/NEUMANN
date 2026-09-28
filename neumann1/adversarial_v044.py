from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .coupled_block import derive_block_candidate, validate_block_candidate
from .structural_compression import ExactLinearSystem, solve_exact_gauss_jordan, verify_exact_full_system


@dataclass(frozen=True)
class SchurWitness:
    answer: dict[str, Fraction]
    retained_dimension: int
    retained_solver_ops: int
    construction_ops: int
    verified: bool


def exact_schur_witness(system: ExactLinearSystem, row_pair: tuple[int, int],
                        target_pair: tuple[str, str]) -> SchurWitness | None:
    """Reference substitution for one candidate, independent of F1 discovery."""
    candidate = derive_block_candidate(system, row_pair, target_pair)
    if candidate is None or not validate_block_candidate(system, candidate)[0]:
        return None
    remaining_rows = tuple(row for row in range(system.dimension)
                           if row not in candidate.row_indices)
    remaining_names = tuple(name for name in system.variables
                            if name not in candidate.targets)
    if not remaining_names or len(remaining_rows) != len(remaining_names):
        return None
    rule_by_target = {rule.target: rule for rule in candidate.rules}
    rules = tuple(rule_by_target[name] for name in candidate.targets)
    columns = {name: system.variables.index(name) for name in system.variables}
    matrix: list[tuple[Fraction, ...]] = []
    rhs: list[Fraction] = []
    construction_ops = 0
    for row in remaining_rows:
        new_row = []
        for name in remaining_names:
            value = Fraction(system.A[row][columns[name]])
            for rule in rules:
                coefficient = system.A[row][columns[rule.target]]
                dependency = dict(rule.coefficients).get(name, Fraction(0))
                if coefficient != 0 and dependency != 0:
                    value += coefficient * dependency
                    construction_ops += 2
            new_row.append(value)
        value = Fraction(system.b[row])
        for rule in rules:
            coefficient = system.A[row][columns[rule.target]]
            if coefficient != 0 and rule.constant != 0:
                value -= coefficient * rule.constant
                construction_ops += 2
        matrix.append(tuple(new_row))
        rhs.append(value)
    reduced = ExactLinearSystem(
        remaining_names, tuple(matrix), tuple(rhs),
        tuple(system.ground_truth[columns[name]] for name in remaining_names),
    )
    retained_answer, counts = solve_exact_gauss_jordan(reduced)
    full_answer = dict(retained_answer)
    for rule in rules:
        full_answer[rule.target] = rule.constant + sum(
            (coefficient * retained_answer[name] for name, coefficient in rule.coefficients),
            Fraction(0),
        )
    verified, _ = verify_exact_full_system(system, full_answer)
    verified = verified and all(full_answer[name] == Fraction(expected)
                                for name, expected in zip(system.variables, system.ground_truth))
    return SchurWitness(full_answer, len(remaining_names),
                        counts.arithmetic_ops, construction_ops, verified)
