"""Bounded, graph-only ordering audit for pinned PACE minimum-fill instances.

The structural proxy deliberately remains separate from numeric solve time.
No PACE contest-optimum or learned-model claim is made by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from random import Random


Graph = tuple[int, ...]  # Vertex-indexed bitsets, labels mapped in sorted order.


@dataclass(frozen=True)
class OrderingCost:
    arithmetic_ops: int
    fill_edges: int


def parse_pace_graph(content: str) -> Graph:
    edges: set[tuple[int, int]] = set()
    vertices: set[int] = set()
    for line in content.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError("PACE edge line must have two vertices")
        a, b = (int(part) for part in parts)
        if a < 0 or b < 0 or a == b:
            raise ValueError("invalid PACE edge")
        edge = (min(a, b), max(a, b))
        if edge in edges:
            raise ValueError("duplicate PACE edge")
        edges.add(edge)
        vertices.update(edge)
    if not vertices:
        raise ValueError("empty PACE graph")
    labels = sorted(vertices)
    index = {label: i for i, label in enumerate(labels)}
    adjacency = [0] * len(labels)
    for a, b in edges:
        i, j = index[a], index[b]
        adjacency[i] |= 1 << j
        adjacency[j] |= 1 << i
    return tuple(adjacency)


def selected_public(root: Path) -> list[tuple[str, Graph, str]]:
    """All public instances with 2 <= n <= 128, no outcome-based selection."""
    entries = []
    for path in sorted((root / "public").glob("*.graph")):
        raw = path.read_bytes()
        graph = parse_pace_graph(raw.decode("utf-8"))
        if 2 <= len(graph) <= 128:
            entries.append((path.name, graph, sha256(raw).hexdigest()))
    return entries


def _vertices(mask: int):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask -= bit


def _score(adjacency: list[int], vertex: int) -> tuple[int, int]:
    neighbors = adjacency[vertex]
    degree = neighbors.bit_count()
    existing_twice = sum((adjacency[u] & neighbors).bit_count()
                         for u in _vertices(neighbors))
    fill = degree * (degree - 1) // 2 - existing_twice // 2
    return degree, fill


def _eliminate(adjacency: list[int], pivot: int) -> OrderingCost:
    neighbors = adjacency[pivot]
    degree, fill = _score(adjacency, pivot)
    for u in _vertices(neighbors):
        adjacency[u] = (adjacency[u] | neighbors) & ~(1 << u | 1 << pivot)
    adjacency[pivot] = 0
    return OrderingCost(degree * degree + 6 * degree + 1, fill)


def order_cost(graph: Graph, order: tuple[int, ...]) -> OrderingCost:
    if sorted(order) != list(range(len(graph))):
        raise ValueError("not a permutation of graph vertices")
    adjacency = list(graph)
    ops = fill = 0
    for pivot in order:
        step = _eliminate(adjacency, pivot)
        ops += step.arithmetic_ops
        fill += step.fill_edges
    return OrderingCost(ops, fill)


def greedy_order(graph: Graph, rule: str, *, seed: int | None = None) -> tuple[int, ...]:
    if rule not in {"min_degree", "min_fill"}:
        raise ValueError("unknown greedy rule")
    rng = Random(seed) if seed is not None else None
    adjacency = list(graph)
    active = set(range(len(graph)))
    order = []
    while active:
        choices = []
        for v in sorted(active):
            degree, fill = _score(adjacency, v)
            key = (degree, fill, v) if rule == "min_degree" else (fill, degree, v)
            choices.append((key, v))
        choices.sort()
        if rng is None:
            pivot = choices[0][1]
        else:
            # Fixed, bounded stochastic departures from greedy; the final
            # selected order still pays for all 16 proposal searches.
            pivot = choices[rng.choices(range(min(3, len(choices))),
                                        weights=(6, 3, 1)[:min(3, len(choices))])[0]][1]
        order.append(pivot)
        _eliminate(adjacency, pivot)
        active.remove(pivot)
    return tuple(order)


def bounded_proposals(graph: Graph, name: str) -> tuple[tuple[int, ...], ...]:
    """Sixteen reproducible min-fill restarts, independent of Python hash seed."""
    orders = []
    for restart in range(16):
        digest = sha256(f"PACE-v051/{name}/{restart}".encode()).digest()
        orders.append(greedy_order(graph, "min_fill", seed=int.from_bytes(digest[:8], "big")))
    return tuple(orders)


def reference_cost(graph: Graph, order: tuple[int, ...]) -> OrderingCost:
    """Independent set-based elimination checks the bitset counter."""
    if sorted(order) != list(range(len(graph))):
        raise ValueError("invalid order")
    state = [{j for j in range(len(graph)) if row & (1 << j)} for row in graph]
    ops = fill = 0
    for pivot in order:
        neighbors = sorted(state[pivot])
        degree = len(neighbors)
        ops += degree * degree + 6 * degree + 1
        for i, u in enumerate(neighbors):
            for v in neighbors[i + 1:]:
                if v not in state[u]:
                    fill += 1
                state[u].add(v)
                state[v].add(u)
            state[u].remove(pivot)
        state[pivot].clear()
    return OrderingCost(ops, fill)
