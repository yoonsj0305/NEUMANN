from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import random

from .adversarial_v044_dataset import (
    AdversarialExample, ALTERNATIVE_CELLS, HIGH_CELLS,
    add_high_degree_targets, make_alternative_example,
    prior_v044_signatures, v044_final_examples,
)
from .anti_shortcut_dataset import CONTROL_CELLS
from .mixed_coupled_dataset import generate_mixed_cell


@lru_cache(maxsize=1)
def prior_v045_signatures() -> frozenset[tuple[object, ...]]:
    return prior_v044_signatures().union(item.example.signature for item in v044_final_examples())


@lru_cache(maxsize=1)
def v045_final_examples() -> tuple[AdversarialExample, ...]:
    forbidden = set(prior_v045_signatures())
    output: list[AdversarialExample] = []

    def add(item: AdversarialExample) -> None:
        if item.example.signature in forbidden:
            raise AssertionError("v0.0.45 signature reused")
        forbidden.add(item.example.signature)
        output.append(item)

    for k, n in HIGH_CELLS:
        bases = generate_mixed_cell(k, n, count=24, split="v045_source",
                                    seed=2_110_000+1000*k+n, variant="coefficient")
        for base in bases:
            item = add_high_degree_targets(base)
            add(replace(item, example=replace(item.example, split="v045_high_degree")))
    for k, n in ALTERNATIVE_CELLS:
        seed = 2_210_000+1000*k+n
        rng = random.Random(seed)
        for index in range(48):
            item = make_alternative_example(k, rng, seed, index)
            add(replace(item, example=replace(item.example, split="v045_alternatives")))
    for k, n in CONTROL_CELLS:
        for example in generate_mixed_cell(k, n, count=16, split="v045_control",
                                           seed=2_310_000+1000*k+n):
            add(AdversarialExample("control", example))
    return tuple(output)


def v045_contract_examples() -> tuple[AdversarialExample, AdversarialExample]:
    base = generate_mixed_cell(2, 16, count=1, split="v045_contract",
                               seed=2_090_000, variant="coefficient")[0]
    return (add_high_degree_targets(base),
            make_alternative_example(2, random.Random(2_095_000), 2_095_000, 0))
