from __future__ import annotations
from typing import Any, Dict, List, Tuple
from .types import IRKind, Representation, CostLedger


class BipartiteMatchingSolver:
    name = "augmenting_path_matching"

    def supports(self, representation: Representation) -> bool:
        return representation.kind == IRKind.BIPARTITE_MATCHING

    def solve(self, representation: Representation, ledger: CostLedger) -> Dict[str, Any]:
        left: List[str] = list(representation.payload["left"])
        edges: Dict[str, List[str]] = representation.payload["edges"]
        right_match: Dict[str, str] = {}

        def augment(u: str, seen: set[str]) -> bool:
            for v in edges.get(u, []):
                ledger.solver_steps += 1
                if v in seen:
                    continue
                seen.add(v)
                if v not in right_match or augment(right_match[v], seen):
                    right_match[v] = u
                    return True
            return False

        matched = 0
        for u in left:
            if augment(u, set()):
                matched += 1

        assignment = {u: v for v, u in right_match.items()}
        return {"matched": matched, "assignment": assignment, "perfect": matched == len(left)}


class ShortestPathSolver:
    name = "dijkstra"

    def supports(self, representation: Representation) -> bool:
        return representation.kind == IRKind.SHORTEST_PATH

    def solve(self, representation: Representation, ledger: CostLedger) -> Dict[str, Any]:
        graph: Dict[str, List[Tuple[str, float]]] = representation.payload["graph"]
        source = representation.payload["source"]
        target = representation.payload["target"]
        dist = {node: float("inf") for node in graph}
        prev: Dict[str, str] = {}
        dist[source] = 0.0
        unvisited = set(graph)

        while unvisited:
            u = min(unvisited, key=lambda n: dist[n])
            ledger.solver_steps += len(unvisited)
            unvisited.remove(u)
            if u == target or dist[u] == float("inf"):
                break
            for v, w in graph[u]:
                ledger.solver_steps += 1
                alt = dist[u] + w
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u

        if dist[target] == float("inf"):
            return {"distance": None, "path": None}

        path = [target]
        while path[-1] != source:
            path.append(prev[path[-1]])
        path.reverse()
        return {"distance": dist[target], "path": path}


class LinearSystemSolver:
    name = "gaussian_elimination"

    def supports(self, representation: Representation) -> bool:
        return representation.kind == IRKind.LINEAR_SYSTEM

    def solve(self, representation: Representation, ledger: CostLedger) -> Dict[str, float]:
        a = [list(map(float, row)) for row in representation.payload["A"]]
        b = list(map(float, representation.payload["b"]))
        names = representation.payload.get("variables") or [f"x{i}" for i in range(len(b))]
        n = len(b)

        for i in range(n):
            pivot = max(range(i, n), key=lambda r: abs(a[r][i]))
            ledger.solver_steps += n - i
            if abs(a[pivot][i]) < 1e-12:
                raise ValueError("Singular linear system")
            a[i], a[pivot] = a[pivot], a[i]
            b[i], b[pivot] = b[pivot], b[i]
            p = a[i][i]
            for j in range(i, n):
                a[i][j] /= p
                ledger.solver_steps += 1
            b[i] /= p
            for r in range(n):
                if r == i:
                    continue
                f = a[r][i]
                if abs(f) < 1e-15:
                    continue
                for j in range(i, n):
                    a[r][j] -= f * a[i][j]
                    ledger.solver_steps += 1
                b[r] -= f * b[i]

        return dict(zip(names, b))
