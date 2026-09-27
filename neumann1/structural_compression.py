from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import json
import math
import random
from statistics import mean
from typing import Iterable


CORE_DIMENSIONS = (2, 4)
APPARENT_DIMENSIONS = (4, 8, 16, 32)
EXAMPLES_PER_CELL = 32
GENERATOR_VERSION = "v032_oracle_linear_v1"


@dataclass(frozen=True)
class ExactLinearSystem:
    variables: tuple[str, ...]
    A: tuple[tuple[int, ...], ...]
    b: tuple[int, ...]
    ground_truth: tuple[int, ...]

    @property
    def dimension(self) -> int:
        return len(self.variables)

    def solver_payload(self) -> dict[str, object]:
        return {
            "variables": list(self.variables),
            "A": [list(row) for row in self.A],
            "b": list(self.b),
        }


@dataclass(frozen=True)
class ReconstructionRule:
    target: str
    coefficients: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class CompressionCertificate:
    original_variables: tuple[str, ...]
    retained_variables: tuple[str, ...]
    eliminated_variables: tuple[str, ...]
    reconstruction_rules: tuple[ReconstructionRule, ...]
    original_A: tuple[tuple[int, ...], ...]
    original_b: tuple[int, ...]
    retained_A: tuple[tuple[int, ...], ...]
    retained_b: tuple[int, ...]
    removed_constraints: tuple[tuple[tuple[int, ...], int], ...]
    dependency_edges: tuple[tuple[str, str], ...]
    exact: bool
    generator_version: str
    generator_seed: int
    example_index: int


@dataclass(frozen=True)
class StructuralCompressionExample:
    apparent_dimension: int
    core_dimension: int
    full_system: ExactLinearSystem
    core_system: ExactLinearSystem
    certificate: CompressionCertificate


@dataclass
class GaussianOperationCounts:
    pivot_tests: int = 0
    row_swaps: int = 0
    divisions: int = 0
    multiplications: int = 0
    subtractions: int = 0

    @property
    def arithmetic_ops(self) -> int:
        return self.divisions + self.multiplications + self.subtractions


@dataclass
class ReconstructionOperationCounts:
    multiplications: int = 0
    additions: int = 0

    @property
    def arithmetic_ops(self) -> int:
        return self.multiplications + self.additions


@dataclass
class VerificationOperationCounts:
    equations: int = 0
    multiplications: int = 0
    additions: int = 0

    @property
    def arithmetic_ops(self) -> int:
        return self.multiplications + self.additions


@dataclass(frozen=True)
class CompressionObservation:
    core_dimension: int
    apparent_dimension: int
    variable_compression_ratio: float
    constraint_compression_ratio: float
    degree_of_freedom_reduction: int
    raw_representation_bytes: int
    compressed_representation_bytes: int
    certificate_bytes: int
    baseline_solver: GaussianOperationCounts
    compressed_solver: GaussianOperationCounts
    reconstruction: ReconstructionOperationCounts
    baseline_verification: VerificationOperationCounts
    compressed_verification: VerificationOperationCounts
    baseline_verified: bool
    compressed_verified: bool
    full_solution_equivalent: bool
    certificate_valid: bool


def scale_grid() -> tuple[tuple[int, int], ...]:
    return tuple(
        (k, n)
        for k in CORE_DIMENSIONS
        for n in APPARENT_DIMENSIONS
        if n >= k
    )


def _canonical_json_bytes(payload: object) -> int:
    return len(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _certificate_payload(
    certificate: CompressionCertificate,
) -> dict[str, object]:
    return asdict(certificate)


def _dense_strictly_diagonally_dominant_matrix(
    k: int,
    rng: random.Random,
) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    off_values = (-2, -1, 1, 2)

    for i in range(k):
        row = [rng.choice(off_values) for _ in range(k)]
        off_sum = sum(
            abs(value)
            for j, value in enumerate(row)
            if j != i
        )
        diagonal = off_sum + rng.randint(1, 3)
        if rng.random() < 0.5:
            diagonal *= -1
        row[i] = diagonal
        rows.append(tuple(row))

    return tuple(rows)


def _matrix_vector_product(
    A: Iterable[Iterable[int]],
    x: Iterable[int],
) -> tuple[int, ...]:
    values = tuple(x)
    return tuple(
        sum(int(c) * int(v) for c, v in zip(row, values))
        for row in A
    )


def _make_example(
    *,
    k: int,
    n: int,
    rng: random.Random,
    generator_seed: int,
    example_index: int,
) -> StructuralCompressionExample:
    if k < 1 or n < k:
        raise ValueError("require 1 <= core dimension <= apparent dimension")

    core_variables = tuple(f"c{i}" for i in range(k))
    eliminated_variables = tuple(
        f"d{i}" for i in range(n - k)
    )
    variables = core_variables + eliminated_variables

    core_A = _dense_strictly_diagonally_dominant_matrix(
        k,
        rng,
    )
    core_solution = tuple(rng.randint(-3, 3) for _ in range(k))
    core_b = _matrix_vector_product(core_A, core_solution)

    full_rows: list[tuple[int, ...]] = []
    full_rhs: list[int] = []
    for row, target in zip(core_A, core_b):
        full_rows.append(
            tuple(row) + (0,) * (n - k)
        )
        full_rhs.append(int(target))

    derived_values: list[int] = []
    rules: list[ReconstructionRule] = []
    edges: list[tuple[str, str]] = []
    coefficient_values = (-2, -1, 1, 2)

    for derived_index, target_name in enumerate(
        eliminated_variables
    ):
        coefficients = tuple(
            (name, rng.choice(coefficient_values))
            for name in core_variables
        )
        derived_value = sum(
            coefficient * value
            for (_, coefficient), value in zip(
                coefficients,
                core_solution,
            )
        )
        derived_values.append(int(derived_value))

        row = [0] * n
        for core_index, (_, coefficient) in enumerate(
            coefficients
        ):
            row[core_index] = -int(coefficient)
            edges.append(
                (core_variables[core_index], target_name)
            )
        row[k + derived_index] = 1
        full_rows.append(tuple(row))
        full_rhs.append(0)
        rules.append(
            ReconstructionRule(
                target=target_name,
                coefficients=coefficients,
            )
        )

    full_solution = core_solution + tuple(derived_values)

    full_system = ExactLinearSystem(
        variables=variables,
        A=tuple(full_rows),
        b=tuple(full_rhs),
        ground_truth=full_solution,
    )
    core_system = ExactLinearSystem(
        variables=core_variables,
        A=core_A,
        b=core_b,
        ground_truth=core_solution,
    )

    removed = tuple(
        (tuple(full_rows[row_index]), int(full_rhs[row_index]))
        for row_index in range(k, n)
    )
    certificate = CompressionCertificate(
        original_variables=variables,
        retained_variables=core_variables,
        eliminated_variables=eliminated_variables,
        reconstruction_rules=tuple(rules),
        original_A=tuple(full_rows),
        original_b=tuple(full_rhs),
        retained_A=core_A,
        retained_b=core_b,
        removed_constraints=removed,
        dependency_edges=tuple(edges),
        exact=True,
        generator_version=GENERATOR_VERSION,
        generator_seed=generator_seed,
        example_index=example_index,
    )
    return StructuralCompressionExample(
        apparent_dimension=n,
        core_dimension=k,
        full_system=full_system,
        core_system=core_system,
        certificate=certificate,
    )


def generate_cell(
    k: int,
    n: int,
    *,
    count: int = EXAMPLES_PER_CELL,
) -> tuple[StructuralCompressionExample, ...]:
    if (k, n) not in scale_grid():
        raise ValueError(
            f"(k={k}, n={n}) is outside the pre-registered grid"
        )
    if count < 1:
        raise ValueError("count must be >= 1")

    seed = 320_000 + 1_000 * k + n
    rng = random.Random(seed)
    seen: set[tuple[object, ...]] = set()
    examples: list[StructuralCompressionExample] = []

    for index in range(count * 50):
        candidate = _make_example(
            k=k,
            n=n,
            rng=rng,
            generator_seed=seed,
            example_index=index,
        )
        signature = (
            candidate.full_system.A,
            candidate.full_system.b,
            candidate.full_system.ground_truth,
        )
        if signature in seen:
            continue
        seen.add(signature)
        examples.append(candidate)
        if len(examples) == count:
            break

    if len(examples) != count:
        raise RuntimeError(
            f"could not generate {count} unique examples "
            f"for k={k}, n={n}"
        )
    return tuple(examples)


def generate_benchmark_corpus() -> tuple[
    StructuralCompressionExample, ...
]:
    return tuple(
        example
        for k, n in scale_grid()
        for example in generate_cell(k, n)
    )


def check_compression_certificate(
    example: StructuralCompressionExample,
) -> tuple[bool, str]:
    certificate = example.certificate
    full = example.full_system
    core = example.core_system

    if not certificate.exact:
        return False, "certificate is not declared exact"
    if certificate.generator_version != GENERATOR_VERSION:
        return False, "unexpected generator version"
    if certificate.original_variables != full.variables:
        return False, "original variable list mismatch"
    if certificate.retained_variables != core.variables:
        return False, "retained variable list mismatch"
    if certificate.original_A != full.A:
        return False, "original matrix mismatch"
    if certificate.original_b != full.b:
        return False, "original right-hand side mismatch"
    if certificate.retained_A != core.A:
        return False, "retained matrix mismatch"
    if certificate.retained_b != core.b:
        return False, "retained right-hand side mismatch"

    expected_eliminated = full.variables[core.dimension :]
    if certificate.eliminated_variables != expected_eliminated:
        return False, "eliminated variable list mismatch"

    if set(certificate.retained_variables).intersection(
        certificate.eliminated_variables
    ):
        return False, "retained and eliminated variables overlap"
    if (
        certificate.retained_variables
        + certificate.eliminated_variables
        != certificate.original_variables
    ):
        return False, "retained/eliminated partition is incomplete"

    expected_removed = tuple(
        (full.A[i], full.b[i])
        for i in range(core.dimension, full.dimension)
    )
    if certificate.removed_constraints != expected_removed:
        return False, "removed constraints mismatch"

    rules_by_target = {
        rule.target: rule
        for rule in certificate.reconstruction_rules
    }
    if set(rules_by_target) != set(
        certificate.eliminated_variables
    ):
        return False, "reconstruction rules are incomplete"

    expected_edges: set[tuple[str, str]] = set()
    available = set(certificate.retained_variables)

    for target_index, target in enumerate(
        certificate.eliminated_variables
    ):
        rule = rules_by_target[target]
        if target in available:
            return False, "duplicate reconstruction target"
        if not rule.coefficients:
            return False, "empty reconstruction rule"

        row_index = core.dimension + target_index
        row = full.A[row_index]
        rhs = full.b[row_index]
        target_column = full.variables.index(target)

        if row[target_column] != 1 or rhs != 0:
            return False, "reconstruction constraint target mismatch"

        coefficient_map = dict(rule.coefficients)
        if len(coefficient_map) != len(rule.coefficients):
            return False, "duplicate dependency in reconstruction rule"

        for dependency, coefficient in rule.coefficients:
            if dependency not in available:
                return False, "reconstruction dependency is not available"
            dep_column = full.variables.index(dependency)
            if row[dep_column] != -coefficient:
                return False, "reconstruction coefficient mismatch"
            expected_edges.add((dependency, target))

        allowed_columns = {
            full.variables.index(dependency)
            for dependency in coefficient_map
        }
        allowed_columns.add(target_column)
        for column, value in enumerate(row):
            if column not in allowed_columns and value != 0:
                return False, "removed constraint contains undeclared dependency"

        available.add(target)

    if set(certificate.dependency_edges) != expected_edges:
        return False, "dependency edge set mismatch"

    return True, "compression certificate verified"


def solve_exact_gauss_jordan(
    system: ExactLinearSystem,
) -> tuple[dict[str, Fraction], GaussianOperationCounts]:
    n = system.dimension
    if len(system.A) != n or len(system.b) != n:
        raise ValueError("exact solver requires a square system")

    matrix = [
        [Fraction(value) for value in row]
        for row in system.A
    ]
    rhs = [Fraction(value) for value in system.b]
    counts = GaussianOperationCounts()

    for column in range(n):
        pivot = None
        for row in range(column, n):
            counts.pivot_tests += 1
            if matrix[row][column] != 0:
                pivot = row
                break
        if pivot is None:
            raise ValueError("singular exact linear system")

        if pivot != column:
            matrix[column], matrix[pivot] = (
                matrix[pivot],
                matrix[column],
            )
            rhs[column], rhs[pivot] = rhs[pivot], rhs[column]
            counts.row_swaps += 1

        pivot_value = matrix[column][column]
        for j in range(column, n):
            matrix[column][j] /= pivot_value
            counts.divisions += 1
        rhs[column] /= pivot_value
        counts.divisions += 1

        for row in range(n):
            if row == column:
                continue
            factor = matrix[row][column]
            if factor == 0:
                continue

            for j in range(column, n):
                matrix[row][j] -= factor * matrix[column][j]
                counts.multiplications += 1
                counts.subtractions += 1
            rhs[row] -= factor * rhs[column]
            counts.multiplications += 1
            counts.subtractions += 1

    answer = {
        name: value
        for name, value in zip(system.variables, rhs)
    }
    return answer, counts


def reconstruct_full_answer(
    core_answer: dict[str, Fraction],
    certificate: CompressionCertificate,
) -> tuple[
    dict[str, Fraction],
    ReconstructionOperationCounts,
]:
    answer = dict(core_answer)
    counts = ReconstructionOperationCounts()

    for rule in certificate.reconstruction_rules:
        total = Fraction(0)
        first = True
        for dependency, coefficient in rule.coefficients:
            if dependency not in answer:
                raise ValueError(
                    f"dependency {dependency} is unavailable "
                    f"for {rule.target}"
                )
            product = Fraction(coefficient) * answer[dependency]
            counts.multiplications += 1
            if first:
                total = product
                first = False
            else:
                total += product
                counts.additions += 1
        answer[rule.target] = total

    return answer, counts


def verify_exact_full_system(
    system: ExactLinearSystem,
    answer: dict[str, Fraction],
) -> tuple[bool, VerificationOperationCounts]:
    counts = VerificationOperationCounts()
    if set(answer) != set(system.variables):
        return False, counts

    for row, target in zip(system.A, system.b):
        counts.equations += 1
        total = Fraction(0)
        first = True
        for coefficient, variable in zip(row, system.variables):
            if coefficient == 0:
                continue
            product = Fraction(coefficient) * answer[variable]
            counts.multiplications += 1
            if first:
                total = product
                first = False
            else:
                total += product
                counts.additions += 1

        if total != Fraction(target):
            return False, counts

    return True, counts


def observe_example(
    example: StructuralCompressionExample,
) -> CompressionObservation:
    certificate_valid, _ = check_compression_certificate(
        example
    )

    baseline_answer, baseline_solver = solve_exact_gauss_jordan(
        example.full_system
    )
    baseline_verified, baseline_verification = (
        verify_exact_full_system(
            example.full_system,
            baseline_answer,
        )
    )

    core_answer, compressed_solver = solve_exact_gauss_jordan(
        example.core_system
    )
    reconstructed_answer, reconstruction = (
        reconstruct_full_answer(
            core_answer,
            example.certificate,
        )
    )
    compressed_verified, compressed_verification = (
        verify_exact_full_system(
            example.full_system,
            reconstructed_answer,
        )
    )

    equivalent = (
        baseline_answer == reconstructed_answer
        and all(
            baseline_answer[name] == Fraction(expected)
            for name, expected in zip(
                example.full_system.variables,
                example.full_system.ground_truth,
            )
        )
    )

    raw_bytes = _canonical_json_bytes(
        example.full_system.solver_payload()
    )
    compressed_bytes = _canonical_json_bytes(
        example.core_system.solver_payload()
    )
    certificate_bytes = _canonical_json_bytes(
        _certificate_payload(example.certificate)
    )

    return CompressionObservation(
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        variable_compression_ratio=(
            example.apparent_dimension / example.core_dimension
        ),
        constraint_compression_ratio=(
            example.apparent_dimension / example.core_dimension
        ),
        degree_of_freedom_reduction=(
            example.apparent_dimension - example.core_dimension
        ),
        raw_representation_bytes=raw_bytes,
        compressed_representation_bytes=compressed_bytes,
        certificate_bytes=certificate_bytes,
        baseline_solver=baseline_solver,
        compressed_solver=compressed_solver,
        reconstruction=reconstruction,
        baseline_verification=baseline_verification,
        compressed_verification=compressed_verification,
        baseline_verified=baseline_verified,
        compressed_verified=compressed_verified,
        full_solution_equivalent=equivalent,
        certificate_valid=certificate_valid,
    )


def _log_log_slope(
    points: tuple[tuple[float, float], ...],
) -> float:
    xs = [math.log(x) for x, _ in points]
    ys = [math.log(y) for _, y in points]
    x_mean = mean(xs)
    y_mean = mean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        raise ValueError("cannot fit slope with zero x variance")
    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(xs, ys)
    )
    return numerator / denominator


def aggregate_observations(
    observations: Iterable[CompressionObservation],
) -> dict[str, object]:
    grouped: dict[
        tuple[int, int],
        list[CompressionObservation],
    ] = {}
    for observation in observations:
        grouped.setdefault(
            (
                observation.core_dimension,
                observation.apparent_dimension,
            ),
            [],
        ).append(observation)

    cells: list[dict[str, object]] = []
    for (k, n) in scale_grid():
        rows = grouped.get((k, n), [])
        if not rows:
            raise ValueError(f"missing observations for k={k}, n={n}")

        cells.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(rows),
                "variable_compression_ratio": mean(
                    row.variable_compression_ratio
                    for row in rows
                ),
                "constraint_compression_ratio": mean(
                    row.constraint_compression_ratio
                    for row in rows
                ),
                "degree_of_freedom_reduction": mean(
                    row.degree_of_freedom_reduction
                    for row in rows
                ),
                "mean_raw_representation_bytes": mean(
                    row.raw_representation_bytes
                    for row in rows
                ),
                "mean_compressed_representation_bytes": mean(
                    row.compressed_representation_bytes
                    for row in rows
                ),
                "mean_certificate_bytes": mean(
                    row.certificate_bytes
                    for row in rows
                ),
                "mean_baseline_solver_arithmetic_ops": mean(
                    row.baseline_solver.arithmetic_ops
                    for row in rows
                ),
                "mean_compressed_solver_arithmetic_ops": mean(
                    row.compressed_solver.arithmetic_ops
                    for row in rows
                ),
                "mean_solver_work_ratio": mean(
                    row.baseline_solver.arithmetic_ops
                    / row.compressed_solver.arithmetic_ops
                    for row in rows
                ),
                "mean_reconstruction_arithmetic_ops": mean(
                    row.reconstruction.arithmetic_ops
                    for row in rows
                ),
                "mean_baseline_verification_arithmetic_ops": mean(
                    row.baseline_verification.arithmetic_ops
                    for row in rows
                ),
                "mean_compressed_verification_arithmetic_ops": mean(
                    row.compressed_verification.arithmetic_ops
                    for row in rows
                ),
                "verified_equivalence_rate": mean(
                    1.0 if row.full_solution_equivalent else 0.0
                    for row in rows
                ),
                "certificate_valid_rate": mean(
                    1.0 if row.certificate_valid else 0.0
                    for row in rows
                ),
            }
        )

    scaling: dict[str, object] = {}
    for k in CORE_DIMENSIONS:
        eligible = [
            cell
            for cell in cells
            if cell["core_dimension"] == k
        ]
        if len(eligible) < 2:
            continue

        baseline_points = tuple(
            (
                float(cell["apparent_dimension"]),
                float(cell["mean_baseline_solver_arithmetic_ops"]),
            )
            for cell in eligible
        )
        compressed_points = tuple(
            (
                float(cell["apparent_dimension"]),
                float(cell["mean_compressed_solver_arithmetic_ops"]),
            )
            for cell in eligible
        )
        scaling[str(k)] = {
            "baseline_solver_log_log_slope": _log_log_slope(
                baseline_points
            ),
            "compressed_solver_log_log_slope": _log_log_slope(
                compressed_points
            ),
        }

    return {
        "cells": cells,
        "scaling": scaling,
    }
