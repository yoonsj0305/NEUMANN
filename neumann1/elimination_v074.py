"""Exact integer sum-product counting and independent transition checking.

Classical variable elimination: no learned component or novelty claim.
"""

from dataclasses import dataclass
from itertools import product
from math import prod
import random
from time import perf_counter, perf_counter_ns

from neumann1.twin_mis_v070 import validate_graph


@dataclass(frozen=True)
class Factor:
    scope: tuple[int, ...]
    table: tuple[int, ...]


@dataclass(frozen=True)
class CountProof:
    order: tuple[int, ...]
    outputs: tuple[Factor, ...]
    count: int


def _guard(deadline):
    if perf_counter() > deadline:
        raise RuntimeError("complete-call deadline exhausted")


def _fill(rows, v):
    neighbors = sorted(rows[v])
    return sum(u not in rows[w] for i, w in enumerate(neighbors)
               for u in neighbors[i + 1:])


def _remove(rows, v):
    neighbors = rows.pop(v)
    for w in neighbors:
        rows[w].discard(v)
        rows[w].update(neighbors - {w})


def greedy_order(graph, method="minfill", seed=0, deadline=float("inf")):
    rows = {v: set(row) for v, row in enumerate(graph)}
    rng = random.Random(seed)
    order = []
    while rows:
        _guard(deadline)
        if method == "mindegree":
            v = min(rows, key=lambda u: (len(rows[u]), _fill(rows, u), u))
        elif method == "minfill":
            v = min(rows, key=lambda u: (_fill(rows, u), len(rows[u]), u))
        elif method == "stochastic":
            fills = {u: _fill(rows, u) for u in rows}
            least = min(fills.values())
            v = rng.choice(sorted(u for u in rows if fills[u] == least))
        else:
            raise ValueError("unknown planner")
        order.append(v)
        _remove(rows, v)
    return tuple(order)


def order_work(graph, order):
    """Static table enumeration proxy, not FLOPs or measured execution cost."""
    if len(order) != len(graph) or set(order) != set(range(len(graph))):
        raise ValueError("invalid elimination permutation")
    rows = {v: set(row) for v, row in enumerate(graph)}
    work, width = 0, 0
    for v in order:
        degree = len(rows[v])
        work += 1 << (degree + 1)
        width = max(width, degree)
        _remove(rows, v)
    return work, width


def plan(graph, method, seed=0, deadline=float("inf")):
    if method in ("minfill", "mindegree"):
        return greedy_order(graph, method, deadline=deadline)
    if method != "best8":
        raise ValueError("unknown planner")
    orders = [greedy_order(graph, "stochastic", seed + i, deadline) for i in range(8)]
    return min(orders, key=lambda order: (*order_work(graph, order), order))


def _initial(graph):
    factors = [Factor((v,), (1, 1)) for v in range(len(graph))]
    factors.extend(Factor((v, u), (1, 1, 1, 0))
                   for v, row in enumerate(graph) for u in row if v < u)
    return factors


def execute(graph, order, deadline=float("inf"), max_scope=18):
    order_work(graph, order)  # Validate before starting.
    factors = _initial(graph)
    outputs = []
    peak_entries = 0
    for v in order:
        _guard(deadline)
        bucket = [factor for factor in factors if v in factor.scope]
        factors = [factor for factor in factors if v not in factor.scope]
        scope = tuple(sorted(set().union(*(set(f.scope) for f in bucket)) - {v}))
        if len(scope) + 1 > max_scope:
            raise RuntimeError("factor-scope budget exhausted")
        positions = {u: i for i, u in enumerate(scope)}
        projections = [tuple(-1 if u == v else positions[u] for u in f.scope)
                       for f in bucket]
        values = []
        for assignment in range(1 << len(scope)):
            if assignment % 256 == 0:
                _guard(deadline)
            total = 0
            for bit in (0, 1):
                value = 1
                for f, projection in zip(bucket, projections):
                    index = 0
                    for i, position in enumerate(projection):
                        index |= (bit if position == -1 else
                                  (assignment >> position) & 1) << i
                    value *= f.table[index]
                total += value
            values.append(total)
        out = Factor(scope, tuple(values))
        outputs.append(out)
        factors.append(out)
        peak_entries = max(peak_entries, sum(len(f.table) for f in factors))
    if any(f.scope for f in factors):
        raise ValueError("non-scalar remainder")
    return CountProof(tuple(order), tuple(outputs), prod(f.table[0] for f in factors)), peak_entries


def check_proof(graph, proof, deadline=float("inf"), max_scope=18):
    """Independent assignment representation and transition implementation.

    Reconstruct original factors here; never trust input factors supplied by
    executor. Does not call _initial, _remove or packed-bit projections.
    """
    validate_graph(graph)
    n = len(graph)
    if (len(proof.order) != n or len(proof.outputs) != n
            or any(type(v) is not int for v in proof.order)
            or set(proof.order) != set(range(n)) or type(proof.count) is not int):
        return False
    active = [((v,), {(0,): 1, (1,): 1}) for v in range(n)]
    active.extend(((v, u), {(0, 0): 1, (0, 1): 1, (1, 0): 1, (1, 1): 0})
                  for v in range(n) for u in graph[v] if v < u)
    for v, output in zip(proof.order, proof.outputs):
        _guard(deadline)
        selected = [(s, t) for s, t in active if v in s]
        active = [(s, t) for s, t in active if v not in s]
        other = tuple(sorted({u for s, _ in selected for u in s if u != v}))
        if (output.scope != other or len(other) + 1 > max_scope
                or len(output.table) != 2 ** len(other)
                or any(type(x) is not int or x < 0 for x in output.table)):
            return False
        verified = {}
        # Reversed Cartesian enumeration corresponds to little-endian tables.
        for index, reverse_bits in enumerate(product((0, 1), repeat=len(other))):
            if index % 256 == 0:
                _guard(deadline)
            bits = tuple(reversed(reverse_bits))
            binding = dict(zip(other, bits))
            expected = 0
            for choice in (0, 1):
                binding[v] = choice
                expected += prod(table[tuple(binding[u] for u in s)] for s, table in selected)
            if output.table[index] != expected:
                return False
            verified[bits] = expected
        active.append((other, verified))
    return all(not s for s, _ in active) and proof.count == prod(t[()] for _, t in active)


def observe(graph, method, seed=0, seconds=10., max_scope=18):
    start = perf_counter_ns()
    deadline = perf_counter() + seconds
    validate_graph(graph)
    order = plan(graph, method, seed, deadline)
    planned = perf_counter_ns()
    proof, peak = execute(graph, order, deadline, max_scope)
    executed = perf_counter_ns()
    verified = check_proof(graph, proof, deadline, max_scope)
    finished = perf_counter_ns()
    work, width = order_work(graph, order)
    return {"verified": verified, "count": proof.count, "order": list(order),
            "total_ms": (finished - start) / 1e6,
            "planning_ms": (planned - start) / 1e6,
            "execution_ms": (executed - planned) / 1e6,
            "verification_ms": (finished - executed) / 1e6,
            "table_assignment_proxy": work, "induced_width": width,
            "retained_proof_entries": sum(len(f.table) for f in proof.outputs),
            "peak_active_table_entries": peak}


def generated_graph(family, n, seed):
    """Local synthetic data; graph construction is outside inference timings."""
    rng = random.Random(seed)
    rows = [set() for _ in range(n)]
    for v in range(n):
        for u in range(v + 1, n):
            if family == "random":
                include = rng.random() < 4 / (n - 1)
            elif family == "bipartite":
                include = (v < n // 2 <= u and rng.random() < 8 / n)
            elif family == "ring_chords":
                include = u == v + 1 or (v == 0 and u == n - 1)
                if not include:
                    include = rng.random() < 2 / (n - 3)
            else:
                raise ValueError("unknown graph family")
            if include:
                rows[v].add(u)
                rows[u].add(v)
    return tuple(tuple(sorted(row)) for row in rows)
