from __future__ import annotations

from functools import lru_cache

from .compression_utility_dataset import (
    v035_calibration_examples,
    v035_final_examples,
)
from .learned_compression_dataset import (
    LearnedCompressionExample,
    generate_learned_compression_cell,
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)
from .residual_headroom_dataset import (
    v036_final_examples,
)
from .stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


V037_TRAIN_EXAMPLES_PER_CELL = 12
V037_VALIDATION_EXAMPLES_PER_CELL = 6
V037_FINAL_EXAMPLES_PER_CELL = 16


def _signatures(examples) -> set[tuple[object, ...]]:
    return {
        example.signature
        for example in examples
    }


def prior_v037_signatures() -> frozenset[tuple[object, ...]]:
    signatures = _signatures(
        learned_compression_training_examples()
    )
    signatures.update(
        _signatures(
            learned_compression_validation_examples()
        )
    )
    signatures.update(
        _signatures(
            learned_compression_final_examples()
        )
    )
    signatures.update(
        _signatures(v034_calibration_examples())
    )
    signatures.update(
        _signatures(v034_final_examples())
    )
    signatures.update(
        _signatures(v035_calibration_examples())
    )
    signatures.update(
        _signatures(v035_final_examples())
    )
    signatures.update(
        _signatures(v036_final_examples())
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
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(output)


@lru_cache(maxsize=1)
def v037_train_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    return _build_split(
        split="v037_train",
        count_per_cell=V037_TRAIN_EXAMPLES_PER_CELL,
        seed_base=410_000,
        forbidden_signatures=prior_v037_signatures(),
    )


@lru_cache(maxsize=1)
def v037_validation_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = set(prior_v037_signatures())
    forbidden.update(
        _signatures(v037_train_examples())
    )
    return _build_split(
        split="v037_validation",
        count_per_cell=V037_VALIDATION_EXAMPLES_PER_CELL,
        seed_base=420_000,
        forbidden_signatures=frozenset(forbidden),
    )


@lru_cache(maxsize=1)
def v037_final_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = set(prior_v037_signatures())
    forbidden.update(
        _signatures(v037_train_examples())
    )
    forbidden.update(
        _signatures(v037_validation_examples())
    )
    return _build_split(
        split="v037_final",
        count_per_cell=V037_FINAL_EXAMPLES_PER_CELL,
        seed_base=430_000,
        forbidden_signatures=frozenset(forbidden),
    )
