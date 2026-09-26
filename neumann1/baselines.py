from __future__ import annotations
from itertools import permutations
from typing import Dict, List, Tuple, Any
from .types import CostLedger


def exhaustive_assignment(left: List[str], rights: List[str], edges: Dict[str, List[str]], ledger: CostLedger) -> Dict[str, Any]:
    for perm in permutations(rights, len(left)):
        ok = True
        for u, v in zip(left, perm):
            ledger.solver_steps += 1
            if v not in edges.get(u, []):
                ok = False
                break
        if ok:
            return {"matched": len(left), "assignment": dict(zip(left, perm)), "perfect": True}
    return {"matched": 0, "assignment": {}, "perfect": False}


def enumerate_simple_paths(graph: Dict[str, List[Tuple[str, float]]], source: str, target: str, ledger: CostLedger):
    best_path = None
    best_cost = float("inf")

    def dfs(node: str, visited: set[str], path: list[str], cost: float):
        nonlocal best_path, best_cost
        ledger.solver_steps += 1
        if node == target:
            if cost < best_cost:
                best_cost = cost
                best_path = path[:]
            return
        for nxt, w in graph[node]:
            ledger.solver_steps += 1
            if nxt in visited:
                continue
            visited.add(nxt)
            path.append(nxt)
            dfs(nxt, visited, path, cost + w)
            path.pop()
            visited.remove(nxt)

    dfs(source, {source}, [source], 0.0)
    return {"distance": None if best_path is None else best_cost, "path": best_path}
