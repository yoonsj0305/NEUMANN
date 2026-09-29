"""Classical exact false-twin quotient, with independent optimum checking.

Constructed research audit only; highspy is optional, never a core dependency.
"""

from dataclasses import dataclass
from functools import lru_cache
import random
from time import perf_counter_ns

Graph = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class TwinCertificate:
    groups: tuple[tuple[int, ...], ...]
    quotient: Graph
    weights: tuple[int, ...]


def validate_graph(graph: Graph) -> None:
    n = len(graph)
    for v, neighbors in enumerate(graph):
        if tuple(sorted(set(neighbors))) != neighbors:
            raise ValueError("neighbors must be sorted and unique")
        if any(type(u) is not int or u < 0 or u >= n or u == v
               for u in neighbors):
            raise ValueError("invalid vertex or self edge")
    neighborhoods = [set(row) for row in graph]
    if any(v not in neighborhoods[u] for v, row in enumerate(graph) for u in row):
        raise ValueError("asymmetric graph")


def discover_twins(graph: Graph) -> TwinCertificate:
    groups = {}
    for v, neighbors in enumerate(graph):
        groups.setdefault(neighbors, []).append(v)
    partition = tuple(tuple(group) for group in groups.values())
    owner = {v: i for i, group in enumerate(partition) for v in group}
    quotient = tuple(tuple(sorted({owner[u] for u in graph[group[0]]}))
                     for group in partition)
    return TwinCertificate(partition, quotient, tuple(map(len, partition)))


def check_certificate(graph: Graph, cert: TwinCertificate) -> None:
    """Full-input proof check; do not trust discovery or a hash alone."""
    flat = [v for group in cert.groups for v in group]
    if sorted(flat) != list(range(len(graph))) or any(not g for g in cert.groups):
        raise ValueError("certificate is not a partition")
    if cert.weights != tuple(map(len, cert.groups)):
        raise ValueError("wrong quotient weight")
    if len(cert.quotient) != len(cert.groups):
        raise ValueError("wrong quotient dimension")
    validate_graph(cert.quotient)
    owner = [0] * len(graph)
    for i, group in enumerate(cert.groups):
        for v in group:
            owner[v] = i
    for i, group in enumerate(cert.groups):
        reference = frozenset(graph[group[0]])
        for v in group:
            if frozenset(graph[v]) != reference:
                raise ValueError("unequal original neighborhoods")
            observed = {owner[u] for u in graph[v]}
            if i in observed or observed != set(cert.quotient[i]):
                raise ValueError("wrong quotient edge set")


def independent_optimum(graph: Graph, weights: tuple[int, ...],
                        *, call_limit: int = 2_000_000) -> int:
    """Exact integer DP; separate algorithm from MIP branch-and-cut."""
    if len(weights) != len(graph) or any(w <= 0 for w in weights):
        raise ValueError("positive weights required")
    masks = tuple(sum(1 << u for u in row) for row in graph)
    calls = 0

    @lru_cache(maxsize=None)
    def visit(mask):
        nonlocal calls
        calls += 1
        if calls > call_limit:
            raise RuntimeError("independent optimum call cap reached")
        if mask == 0:
            return 0
        vertices = [v for v in range(len(graph)) if mask & (1 << v)]
        isolated = [v for v in vertices if masks[v] & mask == 0]
        if isolated:
            removed = sum(1 << v for v in isolated)
            return sum(weights[v] for v in isolated) + visit(mask ^ removed)
        pivot = max(vertices, key=lambda v: (masks[v] & mask).bit_count())
        without = mask & ~(1 << pivot)
        return max(visit(without), weights[pivot] + visit(without & ~masks[pivot]))

    return visit((1 << len(graph)) - 1)


def _mip(graph: Graph, weights: tuple[int, ...]):
    import highspy
    import numpy as np
    from scipy.sparse import coo_matrix

    edges = [(v, u) for v, row in enumerate(graph) for u in row if v < u]
    count = len(edges)
    indices = np.asarray(edges, dtype=np.int32).reshape(-1)
    matrix = coo_matrix((np.ones(2 * count),
                         (np.repeat(np.arange(count), 2), indices)),
                        shape=(count, len(graph))).tocsc()
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = len(graph), count
    lp.col_cost_ = [-float(w) for w in weights]
    lp.col_lower_, lp.col_upper_ = [0.] * len(graph), [1.] * len(graph)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * len(graph)
    lp.row_lower_, lp.row_upper_ = [-highspy.kHighsInf] * count, [1.] * count
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.num_col_, lp.a_matrix_.num_row_ = len(graph), count
    lp.a_matrix_.start_ = matrix.indptr.tolist()
    lp.a_matrix_.index_ = matrix.indices.tolist()
    lp.a_matrix_.value_ = matrix.data.tolist()
    solver = highspy.Highs()
    for key, value in (("output_flag", False), ("threads", 1), ("presolve", "on"),
                       ("mip_detect_symmetry", True), ("random_seed", 70),
                       ("mip_rel_gap", 0.), ("mip_abs_gap", 0.), ("time_limit", 5.)):
        if solver.setOptionValue(key, value) != highspy.HighsStatus.kOk:
            raise RuntimeError(f"HiGHS option rejected: {key}")
    if solver.passModel(lp) != highspy.HighsStatus.kOk:
        raise RuntimeError("HiGHS model rejected")
    run_status = solver.run()
    model_status = solver.getModelStatus()
    if model_status != highspy.HighsModelStatus.kOptimal:
        raise RuntimeError("required optimum not reached: "
                           + solver.modelStatusToString(model_status)
                           + f" (run={run_status}, configured_limit=5s)")
    if run_status != highspy.HighsStatus.kOk:
        raise RuntimeError(f"HiGHS solve failed: {run_status}")
    values = solver.getSolution().col_value
    if any(abs(x - round(x)) > 1e-6 or round(x) not in (0, 1) for x in values):
        raise RuntimeError("nonbinary MIP result")
    return tuple(v for v, x in enumerate(values) if round(x) == 1), solver.getInfo().mip_node_count


def observe(graph: Graph, *, compressed: bool) -> dict:
    start = perf_counter_ns()
    validate_graph(graph)
    fallback = False
    cert = None
    if compressed:
        cert = discover_twins(graph)
        try:
            check_certificate(graph, cert)
        except ValueError:
            # Advisory discovery may fail; never execute an unverified quotient.
            cert, fallback = None, True
    planned = perf_counter_ns()
    if cert is None:
        selected, nodes = _mip(graph, (1,) * len(graph))
        solved = perf_counter_ns()
    else:
        reduced, nodes = _mip(cert.quotient, cert.weights)
        solved = perf_counter_ns()
        selected = tuple(v for i in reduced for v in cert.groups[i])
    reconstructed = perf_counter_ns()
    chosen = set(selected)
    if len(chosen) != len(selected) or any(u in chosen for v in chosen for u in graph[v]):
        raise RuntimeError("original graph feasibility failed")
    # The verifier's certificate is independently rediscovered; charge its work
    # for both methods, even when the planner already supplied a certificate.
    verifier_cert = discover_twins(graph)
    check_certificate(graph, verifier_cert)
    optimum = independent_optimum(verifier_cert.quotient, verifier_cert.weights)
    if len(selected) != optimum:
        raise RuntimeError("independent integer optimum check failed")
    finished = perf_counter_ns()
    return {"vertices": len(graph), "edges": sum(map(len, graph)) // 2,
            "retained": len(cert.groups) if cert is not None else len(graph),
            "optimum": optimum, "verified": True, "fallback": fallback,
            "solver_nodes": nodes, "plan_ms": (planned - start) / 1e6,
            "execute_ms": (solved - planned) / 1e6,
            "reconstruct_ms": (reconstructed - solved) / 1e6,
            "verify_ms": (finished - reconstructed) / 1e6,
            "total_ms": (finished - start) / 1e6}


def constructed_graph(k: int, multiplicity: int, index: int) -> Graph:
    seed = 700_000 + 1000 * k + index
    rng = random.Random(seed)
    base_edges = [(v, u) for v in range(k) for u in range(v + 1, k)
                  if rng.random() < .35]
    n = k * multiplicity
    permutation = list(range(n))
    random.Random(seed + 100 * multiplicity).shuffle(permutation)
    adjacency = [set() for _ in range(n)]
    for v, u in base_edges:
        for i in range(multiplicity):
            for j in range(multiplicity):
                a, b = permutation[v * multiplicity + i], permutation[u * multiplicity + j]
                adjacency[a].add(b)
                adjacency[b].add(a)
    return tuple(tuple(sorted(row)) for row in adjacency)
