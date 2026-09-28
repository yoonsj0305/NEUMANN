from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import random

from .learned_compression_dataset import (
    learned_scale_grid,
)
from .structural_compression import (
    ExactLinearSystem,
)


BLOCK_GENERATOR_VERSION = "v038_coupled_block_v1"
BLOCK_FINAL_EXAMPLES_PER_CELL = 32

BASE_UNIMODULAR_BLOCKS = (
    ((2, 3), (3, 5)),
    ((3, 5), (5, 8)),
    ((2, 5), (3, 7)),
    ((5, 8), (8, 13)),
)


@dataclass(frozen=True)
class BlockOracleProposal:
    row_indices: tuple[int, int]
    targets: tuple[str, str]


@dataclass(frozen=True)
class CoupledBlockExample:
    core_dimension: int
    full_system: ExactLinearSystem
    oracle_retained_variables: tuple[str, ...]
    oracle_blocks: tuple[BlockOracleProposal, ...]
    generator_seed: int
    example_index: int

    @property
    def apparent_dimension(self) -> int:
        return self.full_system.dimension

    @property
    def block_count(self) -> int:
        return len(self.oracle_blocks)

    @property
    def signature(self) -> tuple[object, ...]:
        return (
            self.full_system.A,
            self.full_system.b,
        )


def block_scale_grid() -> tuple[tuple[int, int], ...]:
    return learned_scale_grid()


def _det2(
    matrix: tuple[tuple[int, int], tuple[int, int]],
) -> int:
    return (
        matrix[0][0] * matrix[1][1]
        - matrix[0][1] * matrix[1][0]
    )


def _transformed_block(
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int]]:
    matrix = [
        list(row)
        for row in rng.choice(BASE_UNIMODULAR_BLOCKS)
    ]

    if rng.random() < 0.5:
        matrix[0], matrix[1] = matrix[1], matrix[0]
    if rng.random() < 0.5:
        for row in matrix:
            row[0], row[1] = row[1], row[0]

    for row_index in range(2):
        if rng.random() < 0.5:
            matrix[row_index] = [
                -value
                for value in matrix[row_index]
            ]
    for column in range(2):
        if rng.random() < 0.5:
            for row_index in range(2):
                matrix[row_index][column] *= -1

    output = (
        (int(matrix[0][0]), int(matrix[0][1])),
        (int(matrix[1][0]), int(matrix[1][1])),
    )
    if abs(_det2(output)) != 1:
        raise AssertionError(
            "transformed block lost unimodularity"
        )
    if any(
        value != 0 and abs(value) < 2
        for row in output
        for value in row
    ):
        raise AssertionError(
            "unit coefficient entered block matrix"
        )
    return output


def _core_matrix(
    k: int,
    rng: random.Random,
) -> tuple[tuple[int, ...], ...]:
    if k == 2:
        block = _transformed_block(rng)
        return (
            tuple(block[0]),
            tuple(block[1]),
        )
    if k == 4:
        left = _transformed_block(rng)
        right = _transformed_block(rng)
        return (
            (left[0][0], left[0][1], 0, 0),
            (left[1][0], left[1][1], 0, 0),
            (0, 0, right[0][0], right[0][1]),
            (0, 0, right[1][0], right[1][1]),
        )
    raise ValueError(
        f"unsupported core dimension: {k}"
    )


def _matvec(
    A: tuple[tuple[int, ...], ...],
    x: tuple[int, ...],
) -> tuple[int, ...]:
    return tuple(
        sum(
            int(coefficient) * int(value)
            for coefficient, value in zip(
                row,
                x,
            )
        )
        for row in A
    )


def _dependency_row(
    k: int,
    rng: random.Random,
) -> tuple[int, ...]:
    values = (-3, -2, 0, 2, 3)
    for _ in range(100):
        row = tuple(
            rng.choice(values)
            for _ in range(k)
        )
        if any(row):
            return row
    raise RuntimeError(
        "could not generate nonzero block dependency row"
    )


def _make_example(
    *,
    k: int,
    n: int,
    rng: random.Random,
    generator_seed: int,
    example_index: int,
) -> CoupledBlockExample:
    if (n - k) % 2 != 0:
        raise ValueError(
            "coupled block family requires even n-k"
        )

    block_count = (n - k) // 2
    core_A = _core_matrix(k, rng)
    core_values = tuple(
        rng.randint(-3, 3)
        for _ in range(k)
    )
    core_b = _matvec(
        core_A,
        core_values,
    )

    logical_rows: list[list[int]] = []
    logical_rhs: list[int] = []
    logical_values = list(core_values)
    logical_blocks: list[
        tuple[
            tuple[int, int],
            tuple[int, int],
        ]
    ] = []

    for row, rhs in zip(core_A, core_b):
        logical_rows.append(
            list(row) + [0] * (n - k)
        )
        logical_rhs.append(int(rhs))

    for block_index in range(block_count):
        target0 = k + 2 * block_index
        target1 = target0 + 1
        target_values = (
            rng.randint(-3, 3),
            rng.randint(-3, 3),
        )
        logical_values.extend(
            target_values
        )

        U = _transformed_block(rng)
        dependency = (
            _dependency_row(k, rng),
            _dependency_row(k, rng),
        )

        old_rows: list[int] = []
        for local_row in range(2):
            row = [0] * n
            for core_index in range(k):
                row[core_index] = (
                    dependency[local_row][core_index]
                )
            row[target0] = U[local_row][0]
            row[target1] = U[local_row][1]

            rhs = sum(
                row[column] * logical_values[column]
                for column in range(n)
            )
            old_rows.append(
                len(logical_rows)
            )
            logical_rows.append(row)
            logical_rhs.append(int(rhs))

        logical_blocks.append(
            (
                (old_rows[0], old_rows[1]),
                (target0, target1),
            )
        )

    column_permutation = list(range(n))
    rng.shuffle(column_permutation)
    logical_to_observed = {
        logical_index: observed_index
        for observed_index, logical_index in enumerate(
            column_permutation
        )
    }

    variables = tuple(
        f"v{i}"
        for i in range(n)
    )
    observed_rows = [
        tuple(
            row[logical_index]
            for logical_index in column_permutation
        )
        for row in logical_rows
    ]
    observed_values = tuple(
        logical_values[logical_index]
        for logical_index in column_permutation
    )

    row_permutation = list(range(n))
    rng.shuffle(row_permutation)
    old_to_new_row = {
        old_index: new_index
        for new_index, old_index in enumerate(
            row_permutation
        )
    }

    final_A = tuple(
        observed_rows[old_index]
        for old_index in row_permutation
    )
    final_b = tuple(
        logical_rhs[old_index]
        for old_index in row_permutation
    )

    oracle_blocks = []
    for old_rows, logical_targets in logical_blocks:
        observed_rows_pair = tuple(
            sorted(
                old_to_new_row[row_index]
                for row_index in old_rows
            )
        )
        observed_targets = tuple(
            sorted(
                (
                    variables[
                        logical_to_observed[
                            logical_targets[0]
                        ]
                    ],
                    variables[
                        logical_to_observed[
                            logical_targets[1]
                        ]
                    ],
                ),
                key=lambda name: int(name[1:]),
            )
        )
        oracle_blocks.append(
            BlockOracleProposal(
                row_indices=(
                    observed_rows_pair[0],
                    observed_rows_pair[1],
                ),
                targets=(
                    observed_targets[0],
                    observed_targets[1],
                ),
            )
        )

    retained = tuple(
        variables[observed_index]
        for observed_index, logical_index in enumerate(
            column_permutation
        )
        if logical_index < k
    )

    full_system = ExactLinearSystem(
        variables=variables,
        A=final_A,
        b=final_b,
        ground_truth=observed_values,
    )

    for row in final_A:
        for value in row:
            if value != 0 and abs(value) < 2:
                raise AssertionError(
                    "unit coefficient leaked into v0.0.38 family"
                )

    return CoupledBlockExample(
        core_dimension=k,
        full_system=full_system,
        oracle_retained_variables=retained,
        oracle_blocks=tuple(oracle_blocks),
        generator_seed=generator_seed,
        example_index=example_index,
    )


def generate_block_cell(
    k: int,
    n: int,
    *,
    count: int = BLOCK_FINAL_EXAMPLES_PER_CELL,
) -> tuple[CoupledBlockExample, ...]:
    if (k, n) not in block_scale_grid():
        raise ValueError(
            f"(k={k}, n={n}) outside block scale grid"
        )
    if count < 1:
        raise ValueError(
            "count must be >= 1"
        )

    seed = 440_000 + 1000 * k + n
    rng = random.Random(seed)
    seen: set[tuple[object, ...]] = set()
    output: list[CoupledBlockExample] = []

    for index in range(count * 80):
        example = _make_example(
            k=k,
            n=n,
            rng=rng,
            generator_seed=seed,
            example_index=index,
        )
        if example.signature in seen:
            continue
        seen.add(example.signature)
        output.append(example)
        if len(output) == count:
            break

    if len(output) != count:
        raise RuntimeError(
            f"could not generate {count} unique block examples "
            f"for k={k}, n={n}"
        )
    return tuple(output)


@lru_cache(maxsize=1)
def v038_final_examples() -> tuple[
    CoupledBlockExample, ...
]:
    return tuple(
        example
        for k, n in block_scale_grid()
        for example in generate_block_cell(k, n)
    )
