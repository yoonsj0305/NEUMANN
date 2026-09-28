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
from .stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


V036_FINAL_EXAMPLES_PER_CELL = 32


def _signatures(examples) -> set[tuple[object, ...]]:
    return {
        example.signature
        for example in examples
    }


def prior_v036_signatures() -> frozenset[tuple[object, ...]]:
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
    return frozenset(signatures)


@lru_cache(maxsize=1)
def v036_final_examples() -> tuple[
    LearnedCompressionExample, ...
]:
    forbidden = set(prior_v036_signatures())
    output: list[LearnedCompressionExample] = []

    for k, n in learned_scale_grid():
        seed = 400_000 + 1000 * k + n
        cell = generate_learned_compression_cell(
            k,
            n,
            count=V036_FINAL_EXAMPLES_PER_CELL,
            split="v036_final",
            seed=seed,
            forbidden_signatures=frozenset(forbidden),
        )
        output.extend(cell)
        forbidden.update(
            example.signature
            for example in cell
        )

    return tuple(output)
