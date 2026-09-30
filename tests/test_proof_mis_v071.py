from dataclasses import replace
import itertools

import pytest

from benchmark_v071 import summarize
from neumann1.proof_mis_v071 import (
    check_proof, observe_dp, recover_set, solve_with_proof,
)
from neumann1.twin_mis_v070 import constructed_graph, discover_twins


def _graphs(n):
    edges = list(itertools.combinations(range(n), 2))
    for choices in itertools.product((False, True), repeat=len(edges)):
        adjacency = [set() for _ in range(n)]
        for (a, b), exists in zip(edges, choices):
            if exists:
                adjacency[a].add(b)
                adjacency[b].add(a)
        yield tuple(tuple(sorted(row)) for row in adjacency)


def _brute(graph, weights):
    return max(sum(weights[v] for v in range(len(graph)) if mask & (1 << v))
               for mask in range(1 << len(graph))
               if all(not(mask & (1 << v) and mask & (1 << u))
                      for v, row in enumerate(graph) for u in row))


def test_exhaustive_graphs_and_weighted_quotients():
    for n in range(6):
        for graph in _graphs(n):
            cert = discover_twins(graph)
            for target, weights in ((graph, (1,) * n), (cert.quotient, cert.weights)):
                proof = solve_with_proof(target, weights)
                optimum = check_proof(target, weights, proof)
                chosen = recover_set(target, weights, proof)
                assert optimum == _brute(target, weights)
                assert sum(weights[i] for i in chosen) == optimum
                assert all(u not in chosen for v in chosen for u in target[v])


def test_forged_bellman_proofs_rejected():
    graph = ((1,), (0,), ())
    proof = solve_with_proof(graph, (1, 1, 1))
    assert check_proof(graph, (1, 1, 1), proof) == 2
    with pytest.raises(ValueError):
        check_proof(graph, (1, 1, 1), replace(proof, states=proof.states[:-1]))
    with pytest.raises(ValueError):
        check_proof(graph, (1, 1, 1), replace(proof, states=proof.states[1:]))
    with pytest.raises(ValueError):
        check_proof(graph, (1, 1, 1), replace(proof,
                                            states=proof.states[:-1] + ((7, 3),)))
    with pytest.raises(ValueError):
        check_proof(graph, (1, 1, 1), replace(proof,
                                            states=proof.states + (proof.states[-1],)))
    interior = list(proof.states)
    interior[1] = (interior[1][0], interior[1][1] + 1)
    with pytest.raises(ValueError):
        check_proof(graph, (1, 1, 1), replace(proof, states=tuple(interior)))
    with pytest.raises(ValueError):
        check_proof(graph, (1, 2, 1), proof)


def test_budget_and_full_path():
    graph = constructed_graph(6, 3, 7, seed_base=710_000)
    with pytest.raises(RuntimeError):
        solve_with_proof(graph, (1,) * len(graph), state_limit=1)
    direct = observe_dp(graph, compressed=False)
    compressed = observe_dp(graph, compressed=True)
    assert direct["verified"] and compressed["verified"]
    assert direct["optimum"] == compressed["optimum"]
    assert compressed["retained"] <= 6


def test_censored_runs_cannot_create_speedup():
    rows = []
    for k in (16, 32):
        for m in (1, 4, 8):
            for i in range(3):
                for repeat in range(3):
                    for method in ("direct_dp", "quotient_dp", "quotient_mip"):
                        verified = not (k == 32 and m == 8 and method == "direct_dp")
                        rows.append({"k": k, "multiplicity": m, "index": i,
                                     "repeat": repeat, "method": method,
                                     "verified": verified, "total_ms": 10. if verified else 5000.,
                                     **({"optimum": 3, "proof_bytes": 5,
                                         "proof_states": 2} if verified else {})})
    cells, verdict, agree, mip_pass, compression_pass = summarize(rows)
    hard = next(c for c in cells if c["k"] == 32 and c["multiplicity"] == 8)
    assert hard["compression_ratio"] is None
    assert verdict == "DIRECT_CAPABILITY_UNREACHED"
    assert agree and not mip_pass and not compression_pass
