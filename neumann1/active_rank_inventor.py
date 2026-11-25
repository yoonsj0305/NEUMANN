"""Active low-rank relation invention from black-box source queries.

A third, nonassociative representation family: construct a rational row/column
coordinate system using exact source queries and a bounded adaptive rank search.
No supplied task formula, row factors, basis columns, or target outputs.

Sparsity is an inductive hypothesis, NOT a source-proven universal law.
When trusted rank-bound premise holds and observed basis reaches that bound,
cross-factorization is mathematically exact on the declared finite domain.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from random import Random
from typing import Hashable, Callable

from .monoid_operator_inventor import EvidenceInsufficient
from .active_law_inventor import BudgetExhausted


def _rank(rows):
    if not rows:
        return 0
    a = [list(map(Fraction, row)) for row in rows]
    cols = len(a[0])
    pivot = 0
    for col in range(cols):
        k = next((i for i in range(pivot, len(a)) if a[i][col]), None)
        if k is None:
            continue
        a[pivot], a[k] = a[k], a[pivot]
        d = a[pivot][col]
        a[pivot] = [z / d for z in a[pivot]]
        for i in range(pivot + 1, len(a)):
            t = a[i][col]
            if t:
                a[i] = [x - t * y for x, y in zip(a[i], a[pivot])]
        pivot += 1
        if pivot == len(a):
            break
    return pivot


def _inverse(square):
    n = len(square)
    a = [[Fraction(v) for v in row] +
         [Fraction(i == j) for j in range(n)]
         for i, row in enumerate(square)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if a[i][j]), None)
        if pivot is None:
            raise EvidenceInsufficient("rank-deficient coordinate basis")
        a[j], a[pivot] = a[pivot], a[j]
        scale = a[j][j]
        a[j] = [v / scale for v in a[j]]
        for i in range(n):
            if i == j:
                continue
            factor = a[i][j]
            if factor:
                a[i] = [x - factor * y for x, y in zip(a[i], a[j])]
    return tuple(tuple(row[n:]) for row in a)


@dataclass(frozen=True)
class InventedRankOperator:
    rows: tuple[Hashable, ...]
    columns: tuple[Hashable, ...]
    pivot_rows: tuple[Hashable, ...]
    pivot_columns: tuple[Hashable, ...]
    row_coordinates: dict[Hashable, tuple[Fraction, ...]]
    pivot_vectors: dict[Hashable, tuple[Fraction, ...]]
    source_facts: tuple[tuple[Hashable, Hashable, Fraction], ...]
    repairs: int
    source_checks: int
    rank_upper_bound: int | None
    conditional_on_rank_bound: bool
    verified_exhaustively: bool

    @property
    def rank(self):
        return len(self.pivot_rows)

    def apply(self, a, b, *, require_exhaustive=False):
        if require_exhaustive and not self.verified_exhaustively:
            raise EvidenceInsufficient(
                "unconditional guarantee unavailable from sparse source")
        if a not in self.row_coordinates or b not in self.columns:
            raise EvidenceInsufficient("query outside declared domain")
        j = self.columns.index(b)
        weights = self.row_coordinates[a]
        return sum((w * self.pivot_vectors[p][j]
                    for w, p in zip(weights, self.pivot_rows)), Fraction(0))


def invent_rank_operator(rows, columns, ask: Callable, *, query_budget,
                         seed=0, patience=6, validation=16,
                         max_rank=12, rank_upper_bound=None):
    """Induce new coordinate operators; probe counterexamples and repair IR.

    The oracle is a source-time capability only. Output is provisional except
    when every cell was queried, or when a TRUSTED outside premise gives an
    exact upper rank bound matching the independently observed lower bound.
    Even a trusted bound is not proved by this source oracle.
    """
    rows = tuple(rows)
    columns = tuple(columns)
    if not rows or not columns or (len(set(rows)) != len(rows)
                                  or len(set(columns)) != len(columns)):
        raise EvidenceInsufficient("nonempty unique source domain required")
    if query_budget < 0 or patience < 1 or validation < 0 or max_rank < 1:
        raise ValueError("invalid source budget or bounds")
    if rank_upper_bound is not None and not 0 <= rank_upper_bound <= max_rank:
        raise ValueError("invalid external rank upper bound")

    row_set, col_set = set(rows), set(columns)
    facts = {}

    def query(a, b):
        if a not in row_set or b not in col_set:
            raise EvidenceInsufficient("query outside declared domain")
        if (a, b) not in facts:
            if len(facts) == query_budget:
                raise BudgetExhausted("source query budget exhausted")
            answer = ask(a, b)
            if isinstance(answer, bool) or not isinstance(answer, (int, Fraction)):
                raise EvidenceInsufficient("exact rational source output required")
            facts[a, b] = Fraction(answer)
        return facts[a, b]

    rng = Random(seed)
    discovery_order = list(rows)
    rng.shuffle(discovery_order)
    basis, basis_vectors = [], {}
    no_growth = checks = repairs = 0
    for a in discovery_order:
        vector = tuple(query(a, b) for b in columns)
        checks += 1
        if _rank([basis_vectors[x] for x in basis] + [vector]) > len(basis):
            basis.append(a)
            basis_vectors[a] = vector
            no_growth = 0
            if len(basis) >= max_rank:
                break
        else:
            no_growth += 1
        if (basis and no_growth >= patience and
                (rank_upper_bound is None or len(basis) >= rank_upper_bound)):
            break
    if not basis:
        raise EvidenceInsufficient(
            "rank-zero extrapolation unsupported without full-table evidence")

    def build():
        r = len(basis)
        pivot_indices = []
        for j in range(len(columns)):
            trial = pivot_indices + [j]
            if _rank([[basis_vectors[a][k] for k in trial]
                      for a in basis]) > len(pivot_indices):
                pivot_indices.append(j)
                if len(pivot_indices) == r:
                    break
        if len(pivot_indices) != r:
            raise EvidenceInsufficient("pivot coordinates unavailable")
        cross = [[basis_vectors[a][j] for j in pivot_indices]
                 for a in basis]
        inverse = _inverse(cross)
        coords = {}
        for a in rows:
            anchors = tuple(query(a, columns[j]) for j in pivot_indices)
            coords[a] = tuple(
                sum((anchors[k] * inverse[k][j] for k in range(r)), Fraction(0))
                for j in range(r))
        return InventedRankOperator(
            rows, columns, tuple(basis),
            tuple(columns[j] for j in pivot_indices),
            coords, dict(basis_vectors), (), repairs, checks,
            rank_upper_bound, False, False)

    # Reconstruct the representation after counterexamples, rather than
    # permanently rejecting a family when the first rank guess was too small.
    while True:
        model = build()
        mismatch = next(((a, b) for (a, b), value in facts.items()
                         if model.apply(a, b) != value), None)
        if mismatch is None:
            sample_rows = list(rows)
            rng.shuffle(sample_rows)
            source_counts = {a: sum((a, b) in facts for b in columns)
                             for a in rows}
            sample_rows.sort(key=lambda a: source_counts[a])
            probes = []
            # Cover distinct underobserved rows before revisiting any row.
            for a in sample_rows:
                options = [b for b in columns if (a, b) not in facts]
                if options:
                    probes.append((a, rng.choice(options)))
                if len(probes) >= validation:
                    break
            if len(probes) < validation:
                extras = [(a, b) for a in rows for b in columns
                          if (a, b) not in facts and (a, b) not in probes]
                rng.shuffle(extras)
                probes += extras[:validation - len(probes)]
            for a, b in probes:
                predicted = model.apply(a, b)
                actual = query(a, b)
                checks += 1
                if predicted != actual:
                    mismatch = (a, b)
                    break
        if mismatch is None:
            break
        if len(basis) >= max_rank:
            raise EvidenceInsufficient("representation complexity exceeds rank cap")
        row = mismatch[0]
        if row in basis:
            raise EvidenceInsufficient("basis row contradicts source evidence")
        full_row = tuple(query(row, b) for b in columns)
        if _rank([basis_vectors[x] for x in basis] + [full_row]) <= len(basis):
            raise EvidenceInsufficient("no exact low-rank repair")
        basis.append(row)
        basis_vectors[row] = full_row
        repairs += 1

    observed = tuple((a, b, v) for (a, b), v in facts.items())
    full = len(observed) == len(rows) * len(columns)
    conditional = (rank_upper_bound is not None
                   and len(basis) == rank_upper_bound)
    return InventedRankOperator(
        rows, columns, tuple(basis), model.pivot_columns,
        model.row_coordinates, dict(basis_vectors), observed,
        repairs, checks, rank_upper_bound, conditional, full)
