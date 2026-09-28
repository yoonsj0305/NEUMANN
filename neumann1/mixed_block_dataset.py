from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import random

from .coupled_block_dataset import (
    OracleCoupledBlock,
    prior_v038_signatures,
    v038_final_examples,
)
from .structural_compression import (
    ExactLinearSystem,
    scale_grid,
)


MIXED_BLOCK_GENERATOR_VERSION = "v0381_mixed_local_coupled_v1"
V0381_FINAL_EXAMPLES_PER_CELL = 32


@dataclass(frozen=True)
class OracleEasyRule:
    row_index: int
    target: str


@dataclass(frozen=True)
class MixedBlockExample:
    core_dimension: int
    full_system: ExactLinearSystem
    oracle_easy_rules: tuple[OracleEasyRule, ...]
    oracle_blocks: tuple[OracleCoupledBlock, ...]
    split: str
    generator_seed: int
    example_index: int

    @property
    def apparent_dimension(self) -> int:
        return self.full_system.dimension

    @property
    def derived_count(self) -> int:
        return self.apparent_dimension - self.core_dimension

    @property
    def easy_leaf_count(self) -> int:
        return len(self.oracle_easy_rules)

    @property
    def block_count(self) -> int:
        return len(self.oracle_blocks)

    @property
    def oracle_elimination_count(self) -> int:
        return self.easy_leaf_count + 2 * self.block_count

    @property
    def signature(self) -> tuple[object, ...]:
        return (
            self.full_system.A,
            self.full_system.b,
        )


def mixed_block_scale_grid() -> tuple[
    tuple[int, int], ...
]:
    return scale_grid()


def _matrix_vector_product(
    A: tuple[tuple[int, ...], ...],
    x: tuple[int, ...],
) -> tuple[int, ...]:
    return tuple(
        sum(
            int(coefficient) * int(value)
            for coefficient, value in zip(row, x)
        )
        for row in A
    )


def _dense_no_unit_diagonally_dominant_matrix(
    k: int,
    rng: random.Random,
) -> tuple[tuple[int, ...], ...]:
    off_values = (-3, -2, 2, 3)
    rows: list[tuple[int, ...]] = []

    for i in range(k):
        row = [
            rng.choice(off_values)
            for _ in range(k)
        ]
        off_sum = sum(
            abs(value)
            for j, value in enumerate(row)
            if j != i
        )
        diagonal = off_sum + rng.randint(2, 4)
        if rng.random() < 0.5:
            diagonal *= -1
        row[i] = diagonal

        if any(abs(value) == 1 for value in row):
            raise AssertionError(
                "mixed-family core unexpectedly contains unit coefficient"
            )
        rows.append(tuple(row))

    return tuple(rows)


def _motif_counts(
    derived_count: int,
) -> tuple[int, int]:
    if derived_count < 0:
        raise ValueError(
            "derived_count must be non-negative"
        )
    if derived_count == 0:
        return 0, 0
    if derived_count == 2:
        return 0, 1
    if derived_count < 4 or derived_count % 2 != 0:
        raise ValueError(
            "mixed family expects derived_count in {0,2} or even >=4"
        )

    easy_count = 2
    block_count = (
        derived_count - easy_count
    ) // 2
    return easy_count, block_count


def _make_example(
    *,
    k: int,
    n: int,
    rng: random.Random,
    split: str,
    generator_seed: int,
    example_index: int,
) -> MixedBlockExample:
    if k < 1 or n < k:
        raise ValueError(
            "require 1 <= k <= n"
        )

    derived_count = n - k
    easy_count, block_count = (
        _motif_counts(
            derived_count
        )
    )

    core_A = (
        _dense_no_unit_diagonally_dominant_matrix(
            k,
            rng,
        )
    )
    core_solution = tuple(
        rng.randint(-3, 3)
        for _ in range(k)
    )
    core_b = _matrix_vector_product(
        core_A,
        core_solution,
    )

    logical_rows: list[list[int]] = [
        list(row) + [0] * derived_count
        for row in core_A
    ]
    logical_rhs: list[int] = [
        int(value)
        for value in core_b
    ]
    logical_solution = list(
        core_solution
    )

    easy_specs: list[
        tuple[int, int]
    ] = []
    block_specs: list[
        tuple[
            tuple[int, int],
            tuple[int, int],
        ]
    ] = []

    coefficient_values = (-3, -2, 2, 3)

    # Easy leaves occupy the first derived slots.
    for easy_index in range(
        easy_count
    ):
        target_index = k + easy_index
        target_value = rng.randint(-6, 6)
        logical_solution.append(
            target_value
        )

        coefficients = tuple(
            rng.choice(
                coefficient_values
            )
            for _ in range(k)
        )

        row = [0] * n
        for core_index, coefficient in enumerate(
            coefficients
        ):
            row[core_index] = -coefficient
        row[target_index] = 1

        rhs = (
            target_value
            - sum(
                coefficient * value
                for coefficient, value in zip(
                    coefficients,
                    core_solution,
                )
            )
        )
        row_index = len(
            logical_rows
        )
        logical_rows.append(row)
        logical_rhs.append(int(rhs))
        easy_specs.append(
            (
                row_index,
                target_index,
            )
        )

    # Coupled variables occupy every remaining derived slot.
    coupled_start = k + easy_count

    for block_index in range(
        block_count
    ):
        y_index = (
            coupled_start
            + 2 * block_index
        )
        z_index = y_index + 1

        y_value = rng.randint(-6, 6)
        z_value = rng.randint(-6, 6)
        logical_solution.extend(
            [y_value, z_value]
        )

        first_coefficients = tuple(
            rng.choice(
                coefficient_values
            )
            for _ in range(k)
        )
        second_coefficients = tuple(
            rng.choice(
                coefficient_values
            )
            for _ in range(k)
        )

        first_row = [0] * n
        second_row = [0] * n

        for core_index in range(k):
            first_row[core_index] = (
                -first_coefficients[
                    core_index
                ]
            )
            second_row[core_index] = (
                -second_coefficients[
                    core_index
                ]
            )

        first_row[y_index] = 1
        first_row[z_index] = 1
        second_row[y_index] = 1
        second_row[z_index] = -1

        first_rhs = (
            y_value
            + z_value
            - sum(
                coefficient * value
                for coefficient, value in zip(
                    first_coefficients,
                    core_solution,
                )
            )
        )
        second_rhs = (
            y_value
            - z_value
            - sum(
                coefficient * value
                for coefficient, value in zip(
                    second_coefficients,
                    core_solution,
                )
            )
        )

        first_row_index = len(
            logical_rows
        )
        logical_rows.append(
            first_row
        )
        logical_rhs.append(
            int(first_rhs)
        )

        second_row_index = len(
            logical_rows
        )
        logical_rows.append(
            second_row
        )
        logical_rhs.append(
            int(second_rhs)
        )

        block_specs.append(
            (
                (
                    first_row_index,
                    second_row_index,
                ),
                (
                    y_index,
                    z_index,
                ),
            )
        )

    if len(logical_rows) != n:
        raise AssertionError(
            "mixed generator did not produce a square system"
        )
    if len(logical_solution) != n:
        raise AssertionError(
            "mixed generator solution dimension drift"
        )

    column_permutation = list(
        range(n)
    )
    rng.shuffle(
        column_permutation
    )
    logical_to_observed_column = {
        logical_index: observed_index
        for observed_index, logical_index
        in enumerate(
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
            for logical_index
            in column_permutation
        )
        for row in logical_rows
    ]
    observed_solution = tuple(
        logical_solution[
            logical_index
        ]
        for logical_index
        in column_permutation
    )

    row_permutation = list(
        range(n)
    )
    rng.shuffle(
        row_permutation
    )
    logical_to_observed_row = {
        logical_index: observed_index
        for observed_index, logical_index
        in enumerate(
            row_permutation
        )
    }

    final_A = tuple(
        observed_rows[
            logical_index
        ]
        for logical_index
        in row_permutation
    )
    final_b = tuple(
        logical_rhs[
            logical_index
        ]
        for logical_index
        in row_permutation
    )

    oracle_easy_rules: list[
        OracleEasyRule
    ] = []
    for logical_row, logical_target in easy_specs:
        oracle_easy_rules.append(
            OracleEasyRule(
                row_index=(
                    logical_to_observed_row[
                        logical_row
                    ]
                ),
                target=variables[
                    logical_to_observed_column[
                        logical_target
                    ]
                ],
            )
        )

    oracle_easy_rules.sort(
        key=lambda rule: (
            rule.row_index,
            int(rule.target[1:]),
        )
    )

    oracle_blocks: list[
        OracleCoupledBlock
    ] = []
    for (
        logical_rows_pair,
        logical_targets,
    ) in block_specs:
        observed_rows_pair = tuple(
            sorted(
                logical_to_observed_row[
                    index
                ]
                for index
                in logical_rows_pair
            )
        )
        observed_targets = tuple(
            sorted(
                (
                    variables[
                        logical_to_observed_column[
                            index
                        ]
                    ]
                    for index
                    in logical_targets
                ),
                key=lambda name: int(
                    name[1:]
                ),
            )
        )
        oracle_blocks.append(
            OracleCoupledBlock(
                row_indices=(
                    observed_rows_pair
                ),
                targets=(
                    observed_targets
                ),
            )
        )

    oracle_blocks.sort(
        key=lambda block: (
            block.row_indices,
            tuple(
                int(name[1:])
                for name
                in block.targets
            ),
        )
    )

    example = MixedBlockExample(
        core_dimension=k,
        full_system=ExactLinearSystem(
            variables=variables,
            A=final_A,
            b=final_b,
            ground_truth=(
                observed_solution
            ),
        ),
        oracle_easy_rules=tuple(
            oracle_easy_rules
        ),
        oracle_blocks=tuple(
            oracle_blocks
        ),
        split=split,
        generator_seed=(
            generator_seed
        ),
        example_index=(
            example_index
        ),
    )

    if (
        example.oracle_elimination_count
        != derived_count
    ):
        raise AssertionError(
            "mixed oracle elimination count drift"
        )

    return example


def generate_mixed_block_cell(
    k: int,
    n: int,
    *,
    count: int,
    split: str,
    seed: int,
    forbidden_signatures: frozenset[
        tuple[object, ...]
    ] | None = None,
) -> tuple[
    MixedBlockExample, ...
]:
    if (k, n) not in (
        mixed_block_scale_grid()
    ):
        raise ValueError(
            f"(k={k}, n={n}) is outside the frozen grid"
        )
    if count < 1:
        raise ValueError(
            "count must be >= 1"
        )

    rng = random.Random(seed)
    forbidden = set(
        forbidden_signatures or ()
    )
    seen: set[
        tuple[object, ...]
    ] = set()
    output: list[
        MixedBlockExample
    ] = []

    for index in range(
        count * 100
    ):
        example = _make_example(
            k=k,
            n=n,
            rng=rng,
            split=split,
            generator_seed=seed,
            example_index=index,
        )
        if (
            example.signature in forbidden
            or example.signature in seen
        ):
            continue

        seen.add(
            example.signature
        )
        output.append(
            example
        )

        if len(output) == count:
            break

    if len(output) != count:
        raise RuntimeError(
            f"could not generate {count} unique mixed examples "
            f"for k={k}, n={n}"
        )

    return tuple(output)


@lru_cache(maxsize=1)
def prior_v0381_signatures() -> frozenset[
    tuple[object, ...]
]:
    signatures = set(
        prior_v038_signatures()
    )
    signatures.update(
        example.signature
        for example
        in v038_final_examples()
    )
    return frozenset(
        signatures
    )


@lru_cache(maxsize=1)
def v0381_final_examples() -> tuple[
    MixedBlockExample, ...
]:
    forbidden = set(
        prior_v0381_signatures()
    )
    output: list[
        MixedBlockExample
    ] = []

    for k, n in (
        mixed_block_scale_grid()
    ):
        seed = (
            450_000
            + 1000 * k
            + n
        )
        cell = (
            generate_mixed_block_cell(
                k,
                n,
                count=(
                    V0381_FINAL_EXAMPLES_PER_CELL
                ),
                split="v0381_final",
                seed=seed,
                forbidden_signatures=(
                    frozenset(
                        forbidden
                    )
                ),
            )
        )
        output.extend(cell)
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(output)
