from __future__ import annotations

from functools import lru_cache

from .anti_shortcut_dataset import ACTIVE_CELLS, ARM_OFFSETS, ARMS, CONTROL_CELLS, FINAL_PER_CELL
from .anti_shortcut_v042_dataset import prior_v042_signatures, v042_final_examples
from .mixed_coupled_dataset import MixedCoupledExample, generate_mixed_cell


@lru_cache(maxsize=1)
def prior_v043_signatures() -> frozenset[tuple[object, ...]]:
    return prior_v042_signatures().union(example.signature for _, example in v042_final_examples())


@lru_cache(maxsize=1)
def v043_final_examples() -> tuple[tuple[str, MixedCoupledExample], ...]:
    forbidden = set(prior_v043_signatures())
    output: list[tuple[str, MixedCoupledExample]] = []
    for arm in ARMS:
        for k, n in ACTIVE_CELLS:
            cell = generate_mixed_cell(
                k, n, count=FINAL_PER_CELL, split="v043_final",
                seed=1_410_000 + 1000*k + n + ARM_OFFSETS[arm],
                forbidden_signatures=frozenset(forbidden), variant=arm,
            )
            output.extend((arm, example) for example in cell)
            forbidden.update(example.signature for example in cell)
    for k, n in CONTROL_CELLS:
        cell = generate_mixed_cell(
            k, n, count=FINAL_PER_CELL, split="v043_control",
            seed=1_710_000 + 1000*k + n,
            forbidden_signatures=frozenset(forbidden), variant="legacy",
        )
        output.extend(("control", example) for example in cell)
        forbidden.update(example.signature for example in cell)
    return tuple(output)


def v043_contract_examples() -> tuple[tuple[str, MixedCoupledExample], ...]:
    return tuple(
        (arm, generate_mixed_cell(
            2, 8, count=1, split="v043_contract",
            seed=1_390_000 + ARM_OFFSETS[arm], variant=arm,
        )[0]) for arm in ARMS
    )
