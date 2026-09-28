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
from .stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


UTILITY_TRAIN_EXAMPLES_PER_CELL = 64
UTILITY_CALIBRATION_EXAMPLES_PER_CELL = 24
UTILITY_FINAL_EXAMPLES_PER_CELL = 32


def _prior_signatures() -> frozenset[tuple[object, ...]]:
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
    signatures.update(
        example.signature
        for example in v034_calibration_examples()
    )
    signatures.update(
        example.signature
        for example in v034_final_examples()
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
def utility_training_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    return _build_split(
        split="v035_utility_train",
        count_per_cell=UTILITY_TRAIN_EXAMPLES_PER_CELL,
        seed_base=380_000,
        forbidden_signatures=_prior_signatures(),
    )


@lru_cache(maxsize=1)
def utility_calibration_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = set(_prior_signatures())
    forbidden.update(
        example.signature
        for example in utility_training_examples()
    )
    return _build_split(
        split="v035_utility_calibration",
        count_per_cell=UTILITY_CALIBRATION_EXAMPLES_PER_CELL,
        seed_base=390_000,
        forbidden_signatures=frozenset(forbidden),
    )


@lru_cache(maxsize=1)
def utility_final_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = set(_prior_signatures())
    forbidden.update(
        example.signature
        for example in utility_training_examples()
    )
    forbidden.update(
        example.signature
        for example in utility_calibration_examples()
    )
    return _build_split(
        split="v035_utility_final",
        count_per_cell=UTILITY_FINAL_EXAMPLES_PER_CELL,
        seed_base=400_000,
        forbidden_signatures=frozenset(forbidden),
    )
