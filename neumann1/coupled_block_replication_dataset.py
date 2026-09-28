from __future__ import annotations

from functools import lru_cache

from .coupled_block_dataset import (
    CoupledBlockExample,
    V038_FINAL_EXAMPLES_PER_CELL,
    generate_coupled_block_cell,
    prior_v038_signatures,
    v038_final_examples,
)
from .structural_compression import (
    scale_grid,
)


V039_FINAL_EXAMPLES_PER_CELL = 32


@lru_cache(maxsize=1)
def prior_v039_signatures() -> frozenset[
    tuple[object, ...]
]:
    signatures = set(
        prior_v038_signatures()
    )
    signatures.update(
        example.signature
        for example in v038_final_examples()
    )
    return frozenset(signatures)


@lru_cache(maxsize=1)
def v039_final_examples() -> tuple[
    CoupledBlockExample, ...
]:
    if (
        V039_FINAL_EXAMPLES_PER_CELL
        != V038_FINAL_EXAMPLES_PER_CELL
    ):
        raise AssertionError(
            "v0.0.39 replication changed per-cell sample count"
        )

    forbidden = set(
        prior_v039_signatures()
    )
    output: list[CoupledBlockExample] = []

    for k, n in scale_grid():
        seed = 450_000 + 1000 * k + n
        cell = generate_coupled_block_cell(
            k,
            n,
            count=V039_FINAL_EXAMPLES_PER_CELL,
            split="v039_final",
            seed=seed,
            forbidden_signatures=frozenset(
                forbidden
            ),
        )
        output.extend(cell)
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(output)
