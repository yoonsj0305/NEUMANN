from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from random import Random


Matrix = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class BoundaryAnalysis:
    rank: int
    pairs: tuple[tuple[int, int], ...]
    overlapping_pairs: bool


def exact_rank(matrix: Matrix) -> int:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("expected a square matrix")
    work = [[Fraction(value) for value in row] for row in matrix]
    rank = 0
    for column in range(n):
        pivot = next((row for row in range(rank, n) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        scale = work[rank][column]
        for row in range(rank + 1, n):
            if work[row][column]:
                factor = work[row][column] / scale
                for col in range(column, n):
                    work[row][col] -= factor * work[rank][col]
        rank += 1
    return rank


def analyze(matrix: Matrix) -> BoundaryAnalysis:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("expected a square matrix")
    supports: dict[tuple[int, int], list[int]] = {}
    for col in range(n):
        rows = tuple(row for row in range(n) if matrix[row][col])
        if len(rows) == 2:
            supports.setdefault(rows, []).append(col)
    eligible = []
    for rows, columns in sorted(supports.items()):
        if len(columns) != 2:
            continue
        (r0, r1), (c0, c1) = rows, columns
        if matrix[r0][c0] * matrix[r1][c1] != matrix[r0][c1] * matrix[r1][c0]:
            eligible.append(rows)
    overlap = any(set(left) & set(right)
                  for i, left in enumerate(eligible) for right in eligible[i + 1:])
    return BoundaryAnalysis(exact_rank(matrix), tuple(eligible), overlap)


def _pivot(rng: Random) -> tuple[int, int, int, int]:
    while True:
        a, b, c, d = (rng.choice((-5, -4, -3, -2, -1, 1, 2, 3, 4, 5))
                      for _ in range(4))
        if a * d != b * c:
            return a, b, c, d


def matrix_for(arm: str, seed: int) -> Matrix:
    rng = Random(seed)
    a, b, c, d = _pivot(rng)
    e, f, g, h = _pivot(rng)
    if arm == "overlap":
        return ((a, b, 0, 0), (c, d, e, f), (0, 0, g, h), (0, 0, 0, 0))
    if arm == "repair":
        return ((a, b, 0, 0), (c, d, e, f), (0, 0, g, h), (0, 0, 0, 1))
    if arm == "disjoint":
        return ((a, b, 0, 0), (c, d, 0, 0), (0, 0, e, f), (0, 0, g, h))
    raise ValueError(f"unknown arm: {arm}")
