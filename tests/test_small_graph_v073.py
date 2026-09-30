from dataclasses import replace

import pytest

from benchmark_v073 import load_graphs, summarize
from neumann1 import proof_mis_v071
from neumann1.proof_mis_v071 import observe_dp
from neumann1.twin_mis_v070 import discover_twins


def test_frozen_graph_counts_and_real_route_exactness():
    expected = {"karate": (34, 78), "davis": (32, 89),
                "florentine": (15, 20), "lesmis": (77, 254)}
    graphs = load_graphs()
    for name, graph in graphs.items():
        assert (len(graph), sum(map(len, graph)) // 2) == expected[name]
        direct = observe_dp(graph, compressed=False)
        routed = observe_dp(graph, compressed=False, routed=True)
        assert direct["verified"] and routed["verified"]
        assert direct["optimum"] == routed["optimum"]
        assert routed["retained"] == len(discover_twins(graph).groups)


def test_bad_routing_certificate_falls_back_to_direct(monkeypatch):
    graph = ((2,), (2,), (0, 1))
    real = discover_twins(graph)
    monkeypatch.setattr(proof_mis_v071, "discover_twins",
                        lambda _: replace(real, weights=(1, 1)))
    result = observe_dp(graph, compressed=False, routed=True)
    assert result["verified"] and result["fallback"]
    assert result["routed_to"] == "direct" and result["optimum"] == 2
    with pytest.raises(ValueError):
        observe_dp(graph, compressed=True)


def test_capability_failure_censors_ratios():
    graphs = load_graphs()
    rows = []
    for name in graphs:
        for repeat in range(5):
            for method in ("direct", "quotient", "routed"):
                verified = not (name == "lesmis" and method == "direct")
                rows.append({"graph": name, "method": method, "repeat": repeat,
                             "verified": verified,
                             **({"total_ms": 10., "optimum": 5, "proof_bytes": 10,
                                 "proof_states": 2} if verified else
                                {"total_ms": 5000.})})
    cells, decision, agree = summarize(rows, graphs)
    assert decision == "CAPABILITY_UNREACHED" and agree
    lesmis = next(c for c in cells if c["graph"] == "lesmis")
    assert lesmis["routed_direct_ratio"] is None
    assert lesmis["routed_best_ratio"] is None
