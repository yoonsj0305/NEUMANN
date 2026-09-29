from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from random import Random

from .adversarial_v044_dataset import add_high_degree_targets
from .cached_cost_v046_dataset import prior_v046_signatures, v046_final_examples
from .mixed_coupled_dataset import MixedCoupledExample, generate_mixed_cell
from .structural_compression import ExactLinearSystem


@dataclass(frozen=True)
class CostGateItem:
    arm: str
    example: MixedCoupledExample


def dense_example(seed: int, index: int, *, split: str) -> MixedCoupledExample:
    rng = Random(seed + index)
    k, n = 12, 16
    rows = [[0] * n for _ in range(n)]
    for i in range(k):
        for j in range(k):
            if i != j:
                rows[i][j] = rng.choice((-3, -2, 2, 3))
        rows[i][i] = sum(abs(value) for value in rows[i]) + rng.randint(2, 5)
    for i in range(k, n):
        for j in range(k):
            rows[i][j] = rng.choice((-3, -2, 2, 3))
        for j in range(k, n):
            if i != j:
                rows[i][j] = rng.choice((-3, -2, 2, 3))
        rows[i][i] = sum(abs(rows[i][j]) for j in range(k, n) if i != j) + rng.randint(2, 5)
    solution = [rng.randint(-6, 6) for _ in range(n)]
    row_order, col_order = list(range(n)), list(range(n))
    rng.shuffle(row_order)
    rng.shuffle(col_order)
    signs = [rng.choice((-1, 1)) for _ in range(n)]
    matrix = tuple(tuple(signs[i] * rows[row][col] for col in col_order)
                   for i, row in enumerate(row_order))
    truth = tuple(solution[col] for col in col_order)
    rhs = tuple(sum(a * x for a, x in zip(row, truth)) for row in matrix)
    system = ExactLinearSystem(tuple(f"v{i}" for i in range(n)), matrix, rhs, truth)
    return MixedCoupledExample(k, system, (), (), split, seed, index)


def control_example(seed: int, index: int, *, split: str) -> MixedCoupledExample:
    rng = Random(seed + index)
    n = 16
    rows = []
    for i in range(n):
        row = [rng.choice((-3, -2, 2, 3)) for _ in range(n)]
        row[i] = sum(abs(row[j]) for j in range(n) if j != i) + rng.randint(2, 5)
        rows.append(tuple(row))
    truth = tuple(rng.randint(-6, 6) for _ in range(n))
    matrix = tuple(rows)
    rhs = tuple(sum(a * x for a, x in zip(row, truth)) for row in matrix)
    system = ExactLinearSystem(tuple(f"v{i}" for i in range(n)), matrix, rhs, truth)
    return MixedCoupledExample(n, system, (), (), split, seed, index)


@lru_cache(maxsize=1)
def final_examples() -> tuple[CostGateItem, ...]:
    forbidden = set(prior_v046_signatures())
    forbidden.update(item.example.signature for item in v046_final_examples())
    output: list[CostGateItem] = []

    def add(arm: str, example: MixedCoupledExample) -> None:
        if example.signature in forbidden:
            raise AssertionError("v0.0.48 duplicate or prior signature")
        forbidden.add(example.signature)
        output.append(CostGateItem(arm, example))

    for k in (2, 4):
        for base in generate_mixed_cell(k, 16, count=24, split="v048_high_source",
                                        seed=3_480_000 + 1000 * k + 16,
                                        variant="coefficient"):
            add("high_degree", add_high_degree_targets(base).example)
    for index in range(48):
        add("dense", dense_example(3_490_000, index, split="v048_dense"))
    for index in range(32):
        add("control", control_example(3_500_016, index, split="v048_control"))
    return tuple(output)


def contract_examples() -> tuple[CostGateItem, ...]:
    return (CostGateItem("high_degree", add_high_degree_targets(generate_mixed_cell(
                2, 16, count=1, split="v048_contract", seed=3_470_000,
                variant="coefficient")[0]).example),
            CostGateItem("dense", dense_example(3_471_000, 0, split="v048_contract")),
            CostGateItem("control", control_example(
                3_472_000, 0, split="v048_contract")))
