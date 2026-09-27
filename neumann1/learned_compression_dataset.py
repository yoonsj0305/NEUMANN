from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import random
from typing import Iterable

from .structural_compression import (
    APPARENT_DIMENSIONS,
    CORE_DIMENSIONS,
    ExactLinearSystem,
)


LEARNED_COMPRESSION_GENERATOR_VERSION = "v033_affine_permuted_v1"
TRAIN_EXAMPLES_PER_CELL = 96
VALIDATION_EXAMPLES_PER_CELL = 24
FINAL_EXAMPLES_PER_CELL = 32


@dataclass(frozen=True)
class AffineDependency:
    row_index: int
    target: str
    constant: int
    coefficients: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class LearnedCompressionExample:
    core_dimension: int
    full_system: ExactLinearSystem
    oracle_retained_variables: tuple[str, ...]
    oracle_dependencies: tuple[AffineDependency, ...]
    split: str
    generator_seed: int
    example_index: int

    @property
    def apparent_dimension(self) -> int:
        return self.full_system.dimension

    @property
    def oracle_elimination_count(self) -> int:
        return self.apparent_dimension - self.core_dimension

    @property
    def signature(self) -> tuple[object, ...]:
        return (
            self.full_system.A,
            self.full_system.b,
        )


def learned_scale_grid() -> tuple[tuple[int, int], ...]:
    return tuple(
        (k, n)
        for k in CORE_DIMENSIONS
        for n in APPARENT_DIMENSIONS
        if n >= k
    )


def _dense_strictly_diagonally_dominant_matrix(
    k: int,
    rng: random.Random,
) -> tuple[tuple[int, ...], ...]:
    off_values = (-2, -1, 1, 2)
    rows: list[tuple[int, ...]] = []

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


def _choose_dependency_rule(
    target_index: int,
    values: list[int],
    rng: random.Random,
) -> tuple[int, tuple[tuple[int, int], ...], int]:
    pool = list(range(target_index))
    max_dependencies = min(3, len(pool))

    for _ in range(500):
        dependency_count = rng.randint(1, max_dependencies)
        dependencies = sorted(
            rng.sample(pool, dependency_count)
        )
        coefficients = tuple(
            (dependency, rng.choice((-2, -1, 1, 2)))
            for dependency in dependencies
        )
        constant = rng.randint(-4, 4)
        value = constant + sum(
            coefficient * values[dependency]
            for dependency, coefficient in coefficients
        )
        if abs(value) <= 500:
            return constant, coefficients, int(value)

    raise RuntimeError("could not generate bounded affine dependency")


def _make_example(
    *,
    k: int,
    n: int,
    rng: random.Random,
    split: str,
    generator_seed: int,
    example_index: int,
) -> LearnedCompressionExample:
    if k < 1 or n < k:
        raise ValueError("require 1 <= k <= n")

    core_A = _dense_strictly_diagonally_dominant_matrix(k, rng)
    core_solution = tuple(rng.randint(-3, 3) for _ in range(k))
    core_b = _matrix_vector_product(core_A, core_solution)

    logical_rows: list[list[int]] = []
    logical_rhs: list[int] = []
    row_target: dict[int, int] = {}
    semantic_rules: dict[
        int,
        tuple[int, tuple[tuple[int, int], ...]],
    ] = {}

    for row, rhs in zip(core_A, core_b):
        logical_rows.append(
            list(row) + [0] * (n - k)
        )
        logical_rhs.append(int(rhs))

    values = list(core_solution)

    for target_index in range(k, n):
        constant, dependencies, value = _choose_dependency_rule(
            target_index,
            values,
            rng,
        )
        values.append(value)

        row = [0] * n
        sign = rng.choice((-1, 1))
        row[target_index] = sign
        for dependency, coefficient in dependencies:
            row[dependency] = -sign * coefficient

        rhs = sign * constant
        row_index = len(logical_rows)
        logical_rows.append(row)
        logical_rhs.append(rhs)
        row_target[row_index] = target_index
        semantic_rules[target_index] = (
            constant,
            dependencies,
        )

    column_permutation = list(range(n))
    rng.shuffle(column_permutation)
    logical_to_observed = {
        logical_index: observed_index
        for observed_index, logical_index in enumerate(
            column_permutation
        )
    }

    variables = tuple(f"v{i}" for i in range(n))
    observed_rows = [
        tuple(row[logical_index] for logical_index in column_permutation)
        for row in logical_rows
    ]
    observed_solution = tuple(
        values[logical_index]
        for logical_index in column_permutation
    )

    row_permutation = list(range(n))
    rng.shuffle(row_permutation)
    old_to_new_row = {
        old_index: new_index
        for new_index, old_index in enumerate(row_permutation)
    }
    final_A = tuple(
        observed_rows[old_index]
        for old_index in row_permutation
    )
    final_b = tuple(
        logical_rhs[old_index]
        for old_index in row_permutation
    )

    retained = tuple(
        variables[observed_index]
        for observed_index, logical_index in enumerate(
            column_permutation
        )
        if logical_index < k
    )

    oracle_dependencies: list[AffineDependency] = []
    for target_index in range(k, n):
        old_row = next(
            row_index
            for row_index, logical_target in row_target.items()
            if logical_target == target_index
        )
        constant, dependencies = semantic_rules[target_index]
        target_name = variables[
            logical_to_observed[target_index]
        ]
        observed_coefficients = tuple(
            sorted(
                (
                    (
                        variables[
                            logical_to_observed[dependency]
                        ],
                        coefficient,
                    )
                    for dependency, coefficient in dependencies
                ),
                key=lambda item: int(item[0][1:]),
            )
        )
        oracle_dependencies.append(
            AffineDependency(
                row_index=old_to_new_row[old_row],
                target=target_name,
                constant=constant,
                coefficients=observed_coefficients,
            )
        )

    oracle_dependencies.sort(
        key=lambda rule: int(rule.target[1:])
    )

    return LearnedCompressionExample(
        core_dimension=k,
        full_system=ExactLinearSystem(
            variables=variables,
            A=final_A,
            b=final_b,
            ground_truth=observed_solution,
        ),
        oracle_retained_variables=retained,
        oracle_dependencies=tuple(oracle_dependencies),
        split=split,
        generator_seed=generator_seed,
        example_index=example_index,
    )


def generate_learned_compression_cell(
    k: int,
    n: int,
    *,
    count: int,
    split: str,
    seed: int,
    forbidden_signatures: frozenset[tuple[object, ...]] | None = None,
) -> tuple[LearnedCompressionExample, ...]:
    if (k, n) not in learned_scale_grid():
        raise ValueError(
            f"(k={k}, n={n}) is outside the pre-registered grid"
        )
    if count < 1:
        raise ValueError("count must be >= 1")

    rng = random.Random(seed)
    forbidden = set(forbidden_signatures or ())
    seen: set[tuple[object, ...]] = set()
    output: list[LearnedCompressionExample] = []

    for index in range(count * 100):
        candidate = _make_example(
            k=k,
            n=n,
            rng=rng,
            split=split,
            generator_seed=seed,
            example_index=index,
        )
        signature = candidate.signature
        if signature in forbidden or signature in seen:
            continue
        seen.add(signature)
        output.append(candidate)
        if len(output) == count:
            break

    if len(output) != count:
        raise RuntimeError(
            f"could not generate {count} examples for k={k}, n={n}"
        )

    return tuple(output)


def _split_corpus(
    *,
    split: str,
    count_per_cell: int,
    seed_base: int,
    forbidden_signatures: frozenset[tuple[object, ...]] | None = None,
) -> tuple[LearnedCompressionExample, ...]:
    forbidden = set(forbidden_signatures or ())
    output: list[LearnedCompressionExample] = []

    for k, n in learned_scale_grid():
        seed = seed_base + 1000 * k + n
        cell = generate_learned_compression_cell(
            k,
            n,
            count=count_per_cell,
            split=split,
            seed=seed,
            forbidden_signatures=frozenset(forbidden),
        )
        output.extend(cell)
        forbidden.update(example.signature for example in cell)

    return tuple(output)


@lru_cache(maxsize=1)
def learned_compression_training_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    return _split_corpus(
        split="train",
        count_per_cell=TRAIN_EXAMPLES_PER_CELL,
        seed_base=330_000,
    )


@lru_cache(maxsize=1)
def learned_compression_validation_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    training_signatures = frozenset(
        example.signature
        for example in learned_compression_training_examples()
    )
    return _split_corpus(
        split="validation",
        count_per_cell=VALIDATION_EXAMPLES_PER_CELL,
        seed_base=340_000,
        forbidden_signatures=training_signatures,
    )


@lru_cache(maxsize=1)
def learned_compression_final_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = {
        example.signature
        for example in learned_compression_training_examples()
    }
    forbidden.update(
        example.signature
        for example in learned_compression_validation_examples()
    )
    return _split_corpus(
        split="final",
        count_per_cell=FINAL_EXAMPLES_PER_CELL,
        seed_base=350_000,
        forbidden_signatures=frozenset(forbidden),
    )
