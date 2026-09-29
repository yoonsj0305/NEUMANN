from __future__ import annotations

from dataclasses import dataclass
from random import Random

from .sparse_order_v050 import Graph, Matrix


@dataclass(frozen=True)
class SparseOrderExample:
    degree: int
    graph: Graph
    matrix: Matrix
    rhs: tuple[int, ...]
    truth: tuple[int, ...]
    seed: int


def make_example(degree: int, seed: int) -> SparseOrderExample:
    if degree not in (3, 4):
        raise ValueError("degree must be 3 or 4")
    rng = Random(seed)
    n = 12
    edges = {tuple(sorted((i, (i+1) % n))) for i in range(n)}
    for _ in range(degree - 2):
        for attempt in range(10000):
            vertices = list(range(n))
            rng.shuffle(vertices)
            proposed = {tuple(sorted(vertices[i:i+2])) for i in range(0, n, 2)}
            if proposed.isdisjoint(edges):
                edges.update(proposed)
                break
        else:
            raise AssertionError("could not find disjoint matching")
    neighbors = [set() for _ in range(n)]
    for i, j in edges:
        neighbors[i].add(j)
        neighbors[j].add(i)
    graph = tuple(tuple(sorted(items)) for items in neighbors)
    matrix = tuple(tuple((degree+1 if i == j else -1 if j in neighbors[i] else 0)
                         for j in range(n)) for i in range(n))
    truth = tuple(rng.randint(-3, 3) for _ in range(n))
    rhs = tuple(sum(a*x for a, x in zip(row, truth)) for row in matrix)
    return SparseOrderExample(degree, graph, matrix, rhs, truth, seed)


def contract_examples() -> tuple[SparseOrderExample, ...]:
    return make_example(3, 3_700_000), make_example(4, 3_700_001)


def final_examples() -> tuple[SparseOrderExample, ...]:
    return tuple(make_example(degree, 3_710_000 + 1000*degree + i)
                 for degree in (3, 4) for i in range(24))
