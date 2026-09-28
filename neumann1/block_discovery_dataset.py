from __future__ import annotations

from functools import lru_cache

from .mixed_coupled_dataset import (
    MixedCoupledExample,
    V0381_FINAL_EXAMPLES_PER_CELL,
    generate_mixed_cell,
    mixed_scale_grid,
    prior_v0381_signatures,
    v0381_final_examples,
)


V040_FINAL_EXAMPLES_PER_CELL = 32


@lru_cache(maxsize=1)
def prior_v040_signatures() -> frozenset[
    tuple[object, ...]
]:
    signatures = set(
        prior_v0381_signatures()
    )
    signatures.update(
        example.signature
        for example in v0381_final_examples()
    )
    return frozenset(signatures)


@lru_cache(maxsize=1)
def v040_final_examples() -> tuple[
    MixedCoupledExample, ...
]:
    forbidden = set(
        prior_v040_signatures()
    )
    output: list[
        MixedCoupledExample
    ] = []

    for k, n in mixed_scale_grid():
        seed = (
            500_000
            + 1000 * k
            + n
        )
        cell = generate_mixed_cell(
            k,
            n,
            count=(
                V040_FINAL_EXAMPLES_PER_CELL
            ),
            split="v040_final",
            seed=seed,
            forbidden_signatures=(
                frozenset(
                    forbidden
                )
            ),
        )
        output.extend(cell)
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(output)


def v040_contract_examples() -> tuple[
    MixedCoupledExample, ...
]:
    """
    Small non-final fixtures for correctness tests.

    These seeds are intentionally outside the final audit seeds.
    """
    output: list[
        MixedCoupledExample
    ] = []
    forbidden = set(
        prior_v040_signatures()
    )

    for k, n in (
        (2, 8),
        (4, 8),
        (2, 16),
    ):
        cell = generate_mixed_cell(
            k,
            n,
            count=1,
            split="v040_contract",
            seed=(
                490_000
                + 1000 * k
                + n
            ),
            forbidden_signatures=(
                frozenset(
                    forbidden
                )
            ),
        )
        output.extend(cell)
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(output)
