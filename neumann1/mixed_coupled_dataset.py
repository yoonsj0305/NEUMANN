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


MIXED_COUPLED_GENERATOR_VERSION = "v0381_mixed_local_coupled_v1"
V0381_FINAL_EXAMPLES_PER_CELL = 32


@dataclass(frozen=True)
class OracleEasyLeaf:
    row_index: int
    target: str


@dataclass(frozen=True)
class MixedCoupledExample:
    core_dimension: int
    full_system: ExactLinearSystem
    oracle_easy_leaves: tuple[OracleEasyLeaf, ...]
    oracle_blocks: tuple[OracleCoupledBlock, ...]
    split: str
    generator_seed: int
    example_index: int

    @property
    def apparent_dimension(self) -> int:
        return self.full_system.dimension

    @property
    def easy_leaf_count(self) -> int:
        return len(self.oracle_easy_leaves)

    @property
    def block_count(self) -> int:
        return len(self.oracle_blocks)

    @property
    def oracle_elimination_count(self) -> int:
        return (
            self.easy_leaf_count
            + 2 * self.block_count
        )

    @property
    def expected_one_row_candidate_count(self) -> int:
        return (
            self.easy_leaf_count
            + 4 * self.block_count
        )

    @property
    def signature(self) -> tuple[object, ...]:
        return (
            self.full_system.A,
            self.full_system.b,
        )


def mixed_scale_grid() -> tuple[
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
            for coefficient, value in zip(
                row,
                x,
            )
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


def _make_example(
    *,
    k: int,
    n: int,
    rng: random.Random,
    split: str,
    generator_seed: int,
    example_index: int,
    variant: str = "legacy",
) -> MixedCoupledExample:
    if variant not in {"legacy", "coefficient", "overlap", "combined"}:
        raise ValueError(f"unknown mixed-family variant: {variant}")
    if k < 1 or n < k:
        raise ValueError("require 1 <= k <= n")

    d = n - k
    if d % 2 != 0:
        raise ValueError(
            "mixed family requires even n-k"
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
        list(row) + [0] * d
        for row in core_A
    ]
    logical_rhs = [
        int(value)
        for value in core_b
    ]
    logical_solution = list(
        core_solution
    )

    coefficient_values = (-3, -2, 2, 3)

    easy_leaf_count = (
        2
        if d >= 4
        else 0
    )
    block_variable_count = (
        d - easy_leaf_count
    )
    if block_variable_count % 2 != 0:
        raise AssertionError(
            "mixed block variable count must be even"
        )
    block_count = (
        block_variable_count // 2
    )

    leaf_specs: list[
        tuple[int, int]
    ] = []
    block_specs: list[
        tuple[
            tuple[int, int],
            tuple[int, int],
        ]
    ] = []

    next_variable = k
    previous_block_targets: tuple[int, int] | None = None

    for _ in range(easy_leaf_count):
        target_index = next_variable
        next_variable += 1
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
        for core_index in range(k):
            row[core_index] = (
                -coefficients[core_index]
            )
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
        logical_rhs.append(
            int(rhs)
        )
        leaf_specs.append(
            (
                row_index,
                target_index,
            )
        )

    for _ in range(block_count):
        y_index = next_variable
        z_index = y_index + 1
        next_variable += 2

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

        if variant in {"coefficient", "combined"}:
            while True:
                a, b, c, d_coeff = (
                    rng.choice(coefficient_values) for _ in range(4)
                )
                if a * d_coeff != b * c:
                    break
        else:
            a, b, c, d_coeff = 1, 1, 1, -1

        first_row[y_index] = a
        first_row[z_index] = b
        second_row[y_index] = c
        second_row[z_index] = d_coeff

        if variant in {"overlap", "combined"} and previous_block_targets:
            for prior_index in previous_block_targets:
                first_row[prior_index] = 1
                second_row[prior_index] = 1

        first_rhs = sum(
            coefficient * value
            for coefficient, value in zip(first_row, logical_solution)
        )
        second_rhs = sum(
            coefficient * value
            for coefficient, value in zip(second_row, logical_solution)
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
        previous_block_targets = (y_index, z_index)

    if len(logical_rows) != n:
        raise AssertionError(
            "mixed generator did not produce square system"
        )
    if len(logical_solution) != n:
        raise AssertionError(
            "mixed generator solution dimension drift"
        )
    if next_variable != n:
        raise AssertionError(
            "mixed generator variable allocation drift"
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

    oracle_leaves: list[
        OracleEasyLeaf
    ] = []
    for logical_row, logical_target in leaf_specs:
        oracle_leaves.append(
            OracleEasyLeaf(
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

    oracle_leaves.sort(
        key=lambda leaf: (
            leaf.row_index,
            int(
                leaf.target[1:]
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

    return MixedCoupledExample(
        core_dimension=k,
        full_system=ExactLinearSystem(
            variables=variables,
            A=final_A,
            b=final_b,
            ground_truth=(
                observed_solution
            ),
        ),
        oracle_easy_leaves=tuple(
            oracle_leaves
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


def generate_mixed_cell(
    k: int,
    n: int,
    *,
    count: int,
    split: str,
    seed: int,
    forbidden_signatures: frozenset[
        tuple[object, ...]
    ] | None = None,
    variant: str = "legacy",
) -> tuple[MixedCoupledExample, ...]:
    if (k, n) not in mixed_scale_grid() and not (
        split in {"v041_control", "v042_control", "v043_control", "v044_control",
                  "v045_control", "v046_control"}
        and (k, n) == (2, 2)
        and variant == "legacy"
    ):
        raise ValueError(
            f"(k={k}, n={n}) is outside the frozen grid"
        )

    rng = random.Random(seed)
    forbidden = set(
        forbidden_signatures or ()
    )
    seen: set[
        tuple[object, ...]
    ] = set()
    output: list[
        MixedCoupledExample
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
            variant=variant,
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
        for example in v038_final_examples()
    )
    return frozenset(
        signatures
    )


@lru_cache(maxsize=1)
def v0381_final_examples() -> tuple[
    MixedCoupledExample, ...
]:
    forbidden = set(
        prior_v0381_signatures()
    )
    output: list[
        MixedCoupledExample
    ] = []

    for k, n in mixed_scale_grid():
        seed = (
            470_000
            + 1000 * k
            + n
        )
        cell = generate_mixed_cell(
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
        output.extend(
            cell
        )
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(
        output
    )
