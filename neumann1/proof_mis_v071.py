"""Proof-carrying exact MIS DP, compared with the existing MIP path.

Classical algorithm on constructed graphs; no neural component or novelty claim.
"""

from dataclasses import dataclass
import json
from time import perf_counter_ns

from neumann1.twin_mis_v070 import (
    Graph, check_certificate, discover_twins, validate_graph,
)


@dataclass(frozen=True)
class DPProof:
    # Ascending masks make every dependency precede its parent.
    states: tuple[tuple[int, int], ...]


def _neighbors(graph: Graph) -> tuple[int, ...]:
    return tuple(sum(1 << u for u in row) for row in graph)


def _transition(mask: int, neighbors: tuple[int, ...],
                weights: tuple[int, ...]) -> tuple[int, int, int]:
    """Return (forced weight, exclude child, include child); -1 means forced."""
    vertices = [v for v in range(len(weights)) if mask & (1 << v)]
    isolated = [v for v in vertices if not (neighbors[v] & mask)]
    if isolated:
        removed = sum(1 << v for v in isolated)
        return sum(weights[v] for v in isolated), mask ^ removed, -1
    pivot = max(vertices, key=lambda v: (neighbors[v] & mask).bit_count())
    without = mask & ~(1 << pivot)
    return weights[pivot], without, without & ~neighbors[pivot]


def solve_with_proof(graph: Graph, weights: tuple[int, ...],
                     *, state_limit: int = 2_000_000,
                     time_limit_s: float = 5.) -> DPProof:
    if len(graph) != len(weights) or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("positive integer weight per vertex required")
    neighbors = _neighbors(graph)
    memo: dict[int, int] = {}
    deadline = perf_counter_ns() + int(time_limit_s * 1e9)

    def visit(mask: int) -> int:
        if mask in memo:
            return memo[mask]
        if len(memo) >= state_limit:
            raise RuntimeError("proof DP state cap reached")
        if len(memo) % 1024 == 0 and perf_counter_ns() >= deadline:
            raise RuntimeError("proof DP execution time cap reached")
        if not mask:
            value = 0
        else:
            weight, without, with_pivot = _transition(mask, neighbors, weights)
            if with_pivot == -1:
                value = weight + visit(without)
            else:
                value = max(visit(without), weight + visit(with_pivot))
        memo[mask] = value
        return value

    visit((1 << len(graph)) - 1)
    return DPProof(tuple(sorted(memo.items())))


def check_proof(graph: Graph, weights: tuple[int, ...], proof: DPProof) -> int:
    """Check the supplied Bellman DAG without recursively solving missing states."""
    validate_graph(graph)
    if len(graph) != len(weights) or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("positive integer weight per vertex required")
    checked: dict[int, int] = {}
    full = (1 << len(graph)) - 1
    for mask, value in proof.states:
        if (type(mask) is not int or mask < 0 or mask > full or mask in checked
                or (checked and mask <= next(reversed(checked)))
                or type(value) is not int or value < 0):
            raise ValueError("invalid proof state")
        if mask == 0:
            expected = 0
        else:
            # Deliberately use sets and the original adjacency, not the
            # executor's bitset transition helper: reduce common-mode bugs.
            live = {v for v in range(len(graph)) if mask & (1 << v)}
            isolated = {v for v in live if not live.intersection(graph[v])}
            if isolated:
                child = mask - sum(1 << v for v in isolated)
                if child not in checked:
                    raise ValueError("missing forced Bellman child")
                expected = sum(weights[v] for v in isolated) + checked[child]
            else:
                pivot = max(sorted(live), key=lambda v: len(live.intersection(graph[v])))
                excluded = mask - (1 << pivot)
                included = excluded - sum(1 << u for u in graph[pivot] if u in live)
                if excluded not in checked or included not in checked:
                    raise ValueError("missing branch Bellman child")
                expected = max(checked[excluded], weights[pivot] + checked[included])
        if value != expected:
            raise ValueError("incorrect Bellman equality")
        checked[mask] = value
    if full not in checked:
        raise ValueError("missing root")
    return checked[full]


def recover_set(graph: Graph, weights: tuple[int, ...], proof: DPProof) -> tuple[int, ...]:
    """Only call after check_proof, which guarantees complete Bellman closure."""
    table = dict(proof.states)
    neighbors = _neighbors(graph)
    mask = (1 << len(graph)) - 1
    chosen = []
    while mask:
        vertices = [v for v in range(len(graph)) if mask & (1 << v)]
        isolated = [v for v in vertices if not (neighbors[v] & mask)]
        if isolated:
            chosen.extend(isolated)
            mask &= ~sum(1 << v for v in isolated)
            continue
        pivot = max(vertices, key=lambda v: (neighbors[v] & mask).bit_count())
        without = mask & ~(1 << pivot)
        with_pivot = without & ~neighbors[pivot]
        if weights[pivot] + table[with_pivot] > table[without]:
            chosen.append(pivot)
            mask = with_pivot
        else:
            mask = without
    return tuple(sorted(chosen))


def observe_dp(graph: Graph, *, compressed: bool, routed: bool = False) -> dict:
    if compressed and routed:
        raise ValueError("select compressed or routed, not both")
    start = perf_counter_ns()
    validate_graph(graph)
    cert = None
    fallback = False
    if compressed or routed:
        candidate = discover_twins(graph)
        if compressed or len(candidate.groups) < len(graph):
            try:
                check_certificate(graph, candidate)
            except ValueError:
                if not routed:
                    raise
                fallback = True
            else:
                cert = candidate
    planned = perf_counter_ns()
    target = cert.quotient if cert is not None else graph
    weights = cert.weights if cert is not None else (1,) * len(graph)
    proof = solve_with_proof(target, weights)
    solved = perf_counter_ns()
    optimum = check_proof(target, weights, proof)
    proof_checked = perf_counter_ns()
    reduced = recover_set(target, weights, proof)
    selected = (tuple(v for i in reduced for v in cert.groups[i])
                if cert is not None else reduced)
    reconstructed = perf_counter_ns()
    chosen = set(selected)
    if (len(chosen) != len(selected)
            or any(u in chosen for v in chosen for u in graph[v])
            or len(selected) != optimum):
        raise RuntimeError("original graph solution failed proof/feasibility check")
    # Independently recheck full-input equivalence at the output boundary.
    if cert is not None:
        check_certificate(graph, cert)
    proof_bytes = len(json.dumps(proof.states, separators=(",", ":")))
    finished = perf_counter_ns()
    return {"vertices": len(graph), "edges": sum(map(len, graph)) // 2,
            "retained": len(target), "optimum": optimum, "verified": True,
            "routed_to": ("quotient" if cert is not None else "direct"),
            "fallback": fallback,
            "proof_states": len(proof.states), "proof_bytes": proof_bytes,
            "plan_ms": (planned - start) / 1e6,
            "execute_ms": (solved - planned) / 1e6,
            "reconstruct_ms": (reconstructed - proof_checked) / 1e6,
            "verify_ms": (proof_checked - solved + finished - reconstructed) / 1e6,
            "total_ms": (finished - start) / 1e6}
