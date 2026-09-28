from __future__ import annotations

from functools import lru_cache

from .block_discovery_dataset import prior_v040_signatures, v040_final_examples
from .mixed_coupled_dataset import MixedCoupledExample, generate_mixed_cell


ARMS = ("coefficient", "overlap", "combined")
ACTIVE_CELLS = ((2, 16), (2, 32), (4, 16), (4, 32))
CONTROL_CELLS = ((2, 2), (4, 4))
FINAL_PER_CELL = 16
ARM_OFFSETS = {"coefficient": 0, "overlap": 100_000,
               "combined": 200_000}


@lru_cache(maxsize=1)
def prior_v041_signatures() -> frozenset[tuple[object, ...]]:
    return prior_v040_signatures().union(
        example.signature for example in v040_final_examples()
    )


@lru_cache(maxsize=1)
def v041_final_examples() -> tuple[tuple[str, MixedCoupledExample], ...]:
    forbidden = set(prior_v041_signatures())
    output: list[tuple[str, MixedCoupledExample]] = []
    for arm in ARMS:
        for k, n in ACTIVE_CELLS:
            cell = generate_mixed_cell(
                k, n, count=FINAL_PER_CELL, split="v041_final",
                seed=610_000 + 1000 * k + n + ARM_OFFSETS[arm],
                forbidden_signatures=frozenset(forbidden), variant=arm,
            )
            output.extend((arm, example) for example in cell)
            forbidden.update(example.signature for example in cell)

    for k, n in CONTROL_CELLS:
        cell = generate_mixed_cell(
            k, n, count=FINAL_PER_CELL, split="v041_control",
            seed=910_000 + 1000 * k + n,
            forbidden_signatures=frozenset(forbidden), variant="legacy",
        )
        output.extend(("control", example) for example in cell)
        forbidden.update(example.signature for example in cell)
    return tuple(output)


def v041_contract_examples() -> tuple[tuple[str, MixedCoupledExample], ...]:
    return tuple(
        (arm, generate_mixed_cell(
            2, 8, count=1, split="v041_contract",
            seed=600_000 + ARM_OFFSETS[arm], variant=arm,
        )[0])
        for arm in ARMS
    )
