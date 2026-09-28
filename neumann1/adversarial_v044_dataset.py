from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
import random

from .anti_shortcut_dataset import CONTROL_CELLS
from .indexed_peeling_v043_dataset import prior_v043_signatures, v043_final_examples
from .mixed_coupled_dataset import MixedCoupledExample, generate_mixed_cell
from .structural_compression import ExactLinearSystem


HIGH_CELLS = ((2, 16), (2, 32), (4, 16), (4, 32))
ALTERNATIVE_CELLS = ((2, 6), (4, 8))


@dataclass(frozen=True)
class AlternativeWitness:
    row_pair: tuple[int, int]
    target_pairs: tuple[tuple[str, str], tuple[str, str]]


@dataclass(frozen=True)
class AdversarialExample:
    arm: str
    example: MixedCoupledExample
    high_targets: tuple[str, str] | None = None
    witness: AlternativeWitness | None = None


def add_high_degree_targets(example: MixedCoupledExample) -> AdversarialExample:
    if len(example.oracle_blocks) < 3:
        raise ValueError("high-degree intervention requires three disjoint blocks")
    target = example.oracle_blocks[-1].targets
    donors = example.oracle_blocks[:2]
    system = example.full_system
    matrix = [list(row) for row in system.A]
    for donor in donors:
        for row_index in donor.row_indices:
            for name, coefficient in zip(target, (2, -3)):
                column = system.variables.index(name)
                if matrix[row_index][column] != 0:
                    raise AssertionError("high-degree donor already contains selected target")
                matrix[row_index][column] = coefficient
    rhs = tuple(sum(a * x for a, x in zip(row, system.ground_truth)) for row in matrix)
    altered = replace(example, full_system=replace(
        system, A=tuple(tuple(row) for row in matrix), b=rhs,
    ), split="v044_high_degree")
    degrees = tuple(sum(row[system.variables.index(name)] != 0 for row in matrix)
                    for name in target)
    if degrees != (6, 6):
        raise AssertionError(f"unexpected intervention incidence: {degrees}")
    return AdversarialExample("high_degree", altered, target)


def make_alternative_example(k: int, rng: random.Random, seed: int,
                             index: int) -> AdversarialExample:
    if k not in (2, 4):
        raise ValueError("alternative certificate family requires k in {2,4}")
    n = k + 4
    core = [[0] * n for _ in range(k)]
    for i in range(k):
        for j in range(k):
            core[i][j] = (8*k + rng.randint(0, 5)) if i == j else rng.choice((-3, -2, 2, 3))
    coupled = ((13, 2, 2, 3), (3, 14, 3, 2),
               (2, 3, 15, 2), (3, 2, 2, 16))
    matrix = core + [
        [rng.choice((-3, -2, 2, 3)) for _ in range(k)] + list(row)
        for row in coupled
    ]
    solution = tuple(rng.randint(-6, 6) for _ in range(n))
    rows = list(range(n))
    columns = list(range(n))
    rng.shuffle(rows)
    rng.shuffle(columns)
    signs = [rng.choice((-1, 1)) for _ in range(n)]
    observed_A = tuple(tuple(signs[i] * matrix[row][column] for column in columns)
                       for i, row in enumerate(rows))
    observed_solution = tuple(solution[column] for column in columns)
    observed_b = tuple(sum(a * x for a, x in zip(row, observed_solution))
                       for row in observed_A)
    variables = tuple(f"v{i}" for i in range(n))
    row_pair = tuple(sorted((rows.index(k), rows.index(k+1))))
    target_pairs = tuple(tuple(sorted((variables[columns.index(k+a)],
                                       variables[columns.index(k+b)]),
                                      key=lambda name: int(name[1:])))
                         for a, b in ((0, 1), (2, 3)))
    system = ExactLinearSystem(variables, observed_A, observed_b, observed_solution)
    example = MixedCoupledExample(k, system, (), (), "v044_alternatives", seed, index)
    return AdversarialExample("alternatives", example,
                              witness=AlternativeWitness(row_pair, target_pairs))


@lru_cache(maxsize=1)
def prior_v044_signatures() -> frozenset[tuple[object, ...]]:
    return prior_v043_signatures().union(example.signature for _, example in v043_final_examples())


@lru_cache(maxsize=1)
def v044_final_examples() -> tuple[AdversarialExample, ...]:
    forbidden = set(prior_v044_signatures())
    output: list[AdversarialExample] = []

    def add(item: AdversarialExample) -> None:
        signature = item.example.signature
        if signature in forbidden:
            raise AssertionError("duplicate or previously audited final signature")
        forbidden.add(signature)
        output.append(item)

    for k, n in HIGH_CELLS:
        for base in generate_mixed_cell(k, n, count=24, split="v044_source",
                                        seed=1_810_000+1000*k+n, variant="coefficient"):
            add(add_high_degree_targets(base))
    for k, n in ALTERNATIVE_CELLS:
        seed = 1_910_000+1000*k+n
        rng = random.Random(seed)
        for index in range(48):
            add(make_alternative_example(k, rng, seed, index))
    for k, n in CONTROL_CELLS:
        for example in generate_mixed_cell(k, n, count=16, split="v044_control",
                                           seed=2_010_000+1000*k+n):
            add(AdversarialExample("control", example))
    return tuple(output)


def v044_contract_examples() -> tuple[AdversarialExample, AdversarialExample]:
    base = generate_mixed_cell(2, 16, count=1, split="v044_contract",
                               seed=1_790_000, variant="coefficient")[0]
    return (add_high_degree_targets(base),
            make_alternative_example(2, random.Random(1_795_000), 1_795_000, 0))
