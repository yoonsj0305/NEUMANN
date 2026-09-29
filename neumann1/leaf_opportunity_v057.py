"""Graph-only opportunity screen for degree-at-most-one elimination.

This is deliberately not a solver. A graph peel is only a permissive upper
bound on this narrow candidate family: pivots, fill, numerical stability,
and the cost of discovering/materializing a reduction are not certified.
"""

from __future__ import annotations

from collections import deque

from scipy.sparse import csr_matrix


def peel_upper_bound(matrix: csr_matrix) -> dict[str, int | float]:
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("square matrix required")
    n = matrix.shape[0]
    # Treat a structural edge in either direction as present. The pinned
    # corpus is symmetric, but the routine must not silently use only rows.
    graph = [set() for _ in range(n)]
    for i in range(n):
        for j in matrix.indices[matrix.indptr[i]:matrix.indptr[i + 1]]:
            j = int(j)
            if j != i:
                graph[i].add(j)
                graph[j].add(i)
    initial_leaves = sum(len(neighbors) == 1 for neighbors in graph)
    initial_isolates = sum(len(neighbors) == 0 for neighbors in graph)
    queue = deque(i for i, neighbors in enumerate(graph) if len(neighbors) <= 1)
    removed = set()
    while queue:
        i = queue.popleft()
        if i in removed or len(graph[i]) > 1:
            continue
        removed.add(i)
        for j in tuple(graph[i]):
            graph[j].remove(i)
            if len(graph[j]) <= 1:
                queue.append(j)
        graph[i].clear()
    return {"n": n, "initial_leaves": initial_leaves,
            "initial_isolates": initial_isolates, "peeled_upper_bound": len(removed),
            "fraction_upper_bound": len(removed) / n if n else 0.0}
