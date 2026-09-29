from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

from .adversarial_v044_dataset import add_high_degree_targets
from .cached_cost_v046_dataset import v046_final_examples
from .cost_gate_v048 import prechoice_features
from .cost_gate_v048_dataset import final_examples as v048_final_examples
from .mixed_coupled_dataset import MixedCoupledExample, generate_mixed_cell
from .cached_cost_v046_dataset import prior_v046_signatures


@dataclass(frozen=True)
class MatchedPair:
    recoverable: MixedCoupledExample
    retained_support: MixedCoupledExample
    targets: tuple[str, str]


def relocate_support(base: MixedCoupledExample) -> MatchedPair:
    positive = add_high_degree_targets(base)
    system = positive.example.full_system
    targets = positive.high_targets
    donor = base.oracle_blocks[1].row_indices
    core_rows = [row for row in range(system.dimension)
                 if row not in {leaf.row_index for leaf in base.oracle_easy_leaves}
                 and row not in {r for block in base.oracle_blocks for r in block.row_indices}]
    if len(core_rows) < 2:
        raise ValueError("need two retained core rows")
    matrix = [list(row) for row in system.A]
    for name, coefficient in zip(targets, (2, -3)):
        col = system.variables.index(name)
        for row in donor:
            if matrix[row][col] != coefficient:
                raise AssertionError("unexpected donor coefficient")
            matrix[row][col] = 0
        for row in core_rows[:2]:
            if matrix[row][col] != 0:
                raise AssertionError("core target already present")
            matrix[row][col] = coefficient
    new_matrix = tuple(tuple(row) for row in matrix)
    rhs = tuple(sum(a * x for a, x in zip(row, system.ground_truth))
                for row in new_matrix)
    negative = replace(positive.example, full_system=replace(system, A=new_matrix, b=rhs),
                       split="v049_retained_support")
    if prechoice_features(positive.example) != prechoice_features(negative):
        raise AssertionError("cheap features differ")
    return MatchedPair(positive.example, negative, targets)


@lru_cache(maxsize=1)
def final_pairs() -> tuple[MatchedPair, ...]:
    forbidden = set(prior_v046_signatures())
    forbidden.update(item.example.signature for item in v046_final_examples())
    forbidden.update(item.example.signature for item in v048_final_examples())
    output = []
    for k in (2, 4):
        for n in (16, 32):
            for base in generate_mixed_cell(k, n, count=24, split="v049_source",
                                            seed=3_620_000 + 1000*k + n,
                                            variant="coefficient"):
                pair = relocate_support(base)
                for example in (pair.recoverable, pair.retained_support):
                    if example.signature in forbidden:
                        raise AssertionError("v0.0.49 duplicate or prior signature")
                    forbidden.add(example.signature)
                output.append(pair)
    return tuple(output)


def contract_pair() -> MatchedPair:
    base = generate_mixed_cell(2, 16, count=1, split="v049_contract",
                               seed=3_610_000, variant="coefficient")[0]
    return relocate_support(base)
