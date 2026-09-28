from __future__ import annotations

from functools import lru_cache

from .learned_compression_dataset import (
    LearnedCompressionExample,
    generate_learned_compression_cell,
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)


V034_CALIBRATION_EXAMPLES_PER_CELL = 24
V034_FINAL_EXAMPLES_PER_CELL = 32


def _v033_signatures() -> frozenset[tuple[object, ...]]:
    signatures = {
        example.signature
        for example in learned_compression_training_examples()
    }
    signatures.update(
        example.signature
        for example in learned_compression_validation_examples()
    )
    signatures.update(
        example.signature
        for example in learned_compression_final_examples()
    )
    return frozenset(signatures)


def _build_split(
    *,
    split: str,
    count_per_cell: int,
    seed_base: int,
    forbidden_signatures: frozenset[tuple[object, ...]],
) -> tuple[LearnedCompressionExample, ...]:
    forbidden = set(forbidden_signatures)
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
def v034_calibration_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    return _build_split(
        split="v034_calibration",
        count_per_cell=V034_CALIBRATION_EXAMPLES_PER_CELL,
        seed_base=360_000,
        forbidden_signatures=_v033_signatures(),
    )


@lru_cache(maxsize=1)
def v034_final_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = set(_v033_signatures())
    forbidden.update(
        example.signature
        for example in v034_calibration_examples()
    )
    return _build_split(
        split="v034_final",
        count_per_cell=V034_FINAL_EXAMPLES_PER_CELL,
        seed_base=370_000,
        forbidden_signatures=frozenset(forbidden),
    )
