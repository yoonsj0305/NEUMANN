from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import combinations


Graph = tuple[tuple[int, ...], ...]
Matrix = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class OrderedSolve:
    answer: tuple[Fraction, ...]
    arithmetic_ops: int
    fill_edges: int


def graph_from_matrix(matrix: Matrix) -> Graph:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("expected square matrix")
    if any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(n)):
        raise ValueError("expected symmetric matrix")
    return tuple(tuple(j for j in range(n) if j != i and matrix[i][j]) for i in range(n))


def _initial_state(graph: Graph) -> tuple[tuple[int, tuple[int, ...]], ...]:
    return tuple((i, tuple(sorted(neighbors))) for i, neighbors in enumerate(graph))


def _step(state: tuple[tuple[int, tuple[int, ...]], ...], pivot: int):
    graph = {v: set(neighbors) for v, neighbors in state}
    neighbors = graph[pivot]
    fill = sum(j not in graph[i] for i, j in combinations(sorted(neighbors), 2))
    for i in neighbors:
        graph[i].discard(pivot)
        graph[i].update(neighbors - {i})
    del graph[pivot]
    next_state = tuple((v, tuple(sorted(graph[v]))) for v in sorted(graph))
    degree = len(neighbors)
    return next_state, degree * degree + 6 * degree + 1, fill


def greedy_order(graph: Graph, *, rule: str) -> tuple[int, ...]:
    if rule not in {"min_degree", "min_fill"}:
        raise ValueError("unknown ordering rule")
    state = _initial_state(graph)
    order = []
    while state:
        options = []
        for v, neighbors in state:
            _, _, fill = _step(state, v)
            key = (len(neighbors), fill, v) if rule == "min_degree" else (fill, len(neighbors), v)
            options.append((key, v))
        pivot = min(options)[1]
        order.append(pivot)
        state, _, _ = _step(state, pivot)
    return tuple(order)


def optimal_symbolic_order(graph: Graph) -> tuple[tuple[int, ...], int, int]:
    @lru_cache(maxsize=None)
    def best(state: tuple[tuple[int, tuple[int, ...]], ...]) -> tuple[int, tuple[int, ...]]:
        if not state:
            return 0, ()
        choices = []
        for pivot, _ in state:
            rest, step_cost, _ = _step(state, pivot)
            remaining_cost, remaining_order = best(rest)
            choices.append((step_cost + remaining_cost, (pivot,) + remaining_order))
        return min(choices)

    cost, order = best(_initial_state(graph))
    return order, cost, best.cache_info().misses


def solve_in_order(matrix: Matrix, rhs: tuple[int, ...], order: tuple[int, ...]) -> OrderedSolve:
    n = len(matrix)
    graph = graph_from_matrix(matrix)
    if len(rhs) != n or tuple(sorted(order)) != tuple(range(n)):
        raise ValueError("invalid rhs or elimination order")
    work = [[Fraction(value) for value in row] for row in matrix]
    b = [Fraction(value) for value in rhs]
    state = _initial_state(graph)
    rules = []
    ops = fills = 0
    for pivot in order:
        if work[pivot][pivot] <= 0:
            raise ValueError("nonpositive pivot; SPD precondition failed")
        neighbors = dict(state)[pivot]
        rules.append((pivot, work[pivot][pivot], b[pivot],
                      tuple((j, work[pivot][j]) for j in neighbors)))
        factors = {i: work[i][pivot] / work[pivot][pivot] for i in neighbors}
        for i in neighbors:
            b[i] -= factors[i] * b[pivot]
        for i, j in combinations(neighbors, 2):
            work[i][j] -= factors[i] * work[pivot][j]
            work[j][i] = work[i][j]
        for i in neighbors:
            work[i][i] -= factors[i] * work[pivot][i]
        state, cost, fill = _step(state, pivot)
        ops += cost
        fills += fill
    answer = [Fraction(0) for _ in range(n)]
    for pivot, diagonal, value, coefficients in reversed(rules):
        answer[pivot] = (value - sum(coefficient * answer[j]
                                     for j, coefficient in coefficients)) / diagonal
    if any(sum(Fraction(a) * x for a, x in zip(row, answer)) != value
           for row, value in zip(matrix, rhs)):
        raise AssertionError("original equations not verified")
    return OrderedSolve(tuple(answer), ops, fills)
