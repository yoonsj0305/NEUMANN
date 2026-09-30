from dataclasses import replace
from itertools import combinations

import pytest

from neumann1.elimination_v074 import (check_proof, execute, generated_graph,
                                      greedy_order, observe, order_work, plan)


def brute_count(graph):
    return sum(all(not (bits & (1 << v) and bits & (1 << u))
                   for v, row in enumerate(graph) for u in row if v < u)
               for bits in range(1 << len(graph)))


def test_exact_all_small_graphs_and_orders():
    edges = list(combinations(range(4), 2))
    for mask in range(1 << len(edges)):
        rows = [set() for _ in range(4)]
        for i, (u, v) in enumerate(edges):
            if mask & (1 << i):
                rows[u].add(v)
                rows[v].add(u)
        graph = tuple(tuple(sorted(row)) for row in rows)
        expected = brute_count(graph)
        for order in (tuple(range(4)), (3, 1, 0, 2), plan(graph, "best8", 7)):
            proof, _ = execute(graph, order)
            assert proof.count == expected
            assert check_proof(graph, proof)


def test_empty_isolated_and_disconnected():
    for graph in ((), ((),), ((), (), ()), ((1,), (0,), (3,), (2,))):
        proof, _ = execute(graph, tuple(range(len(graph))))
        assert proof.count == brute_count(graph)
        assert check_proof(graph, proof)


def test_independent_checker_rejects_corruption():
    graph = generated_graph("random", 8, 740)
    proof, _ = execute(graph, greedy_order(graph))
    assert not check_proof(graph, replace(proof, count=proof.count + 1))
    assert not check_proof(graph, replace(proof, order=(0,) * 8))
    for i, output in enumerate(proof.outputs):
        changed = replace(output, table=(output.table[0] + 1, *output.table[1:]))
        outputs = (*proof.outputs[:i], changed, *proof.outputs[i + 1:])
        assert not check_proof(graph, replace(proof, outputs=outputs))
    assert not check_proof(graph, replace(proof, outputs=proof.outputs[:-1]))


def test_budget_and_invalid_inputs_fail_closed():
    graph = ((1, 2), (0, 2), (0, 1))
    with pytest.raises(ValueError):
        execute(graph, (0, 0, 2))
    with pytest.raises(RuntimeError):
        observe(graph, "minfill", seconds=-1)
    with pytest.raises(RuntimeError):
        observe(graph, "minfill", max_scope=2)
    with pytest.raises(ValueError):
        observe(((1,), ()), "minfill")


def test_fixed_generators_planners_and_proxy():
    for family in ("random", "bipartite", "ring_chords"):
        graph = generated_graph(family, 10, 74)
        assert graph == generated_graph(family, 10, 74)
        for method in ("minfill", "mindegree", "best8"):
            result = observe(graph, method, 74)
            assert result["verified"] and result["count"] == brute_count(graph)
            assert result["total_ms"] == pytest.approx(sum(result[k] for k in
                   ("planning_ms", "execution_ms", "verification_ms")))
        candidates = [greedy_order(graph, "stochastic", 74 + i) for i in range(8)]
        assert order_work(graph, plan(graph, "best8", 74)) == min(order_work(graph, o)
                                                                for o in candidates)


def test_summary_has_no_failure_speed_ratios_or_oracle_speedup_claim():
    from benchmark_v074 import METHODS, corpus, summarize

    rows = []
    for name, *_ in corpus():
        for method in METHODS:
            for repeat in range(3):
                cost = 2. if method == "best8" else 1.
                rows.append({"graph": name, "method": method, "repeat": repeat,
                             "verified": True, "count": 7, "total_ms": cost,
                             "planning_ms": cost - .5, "execution_ms": .25,
                             "verification_ms": .25, "table_assignment_proxy": 50,
                             "induced_width": 3, "retained_proof_entries": 20,
                             "peak_active_table_entries": 12})
    _, summary, verdict = summarize(rows)
    assert summary["zero_planning_diagnostic"]["passes_cost_screen"]
    assert not summary["charged"]["passes_cost_screen"]
    assert verdict == "ZERO_COST_PLANNER_HEADROOM_ONLY_REQUIRES_NEW_LEARNED_GATE"
    rows[0] = {**rows[0], "verified": False}
    cells, summary, verdict = summarize(rows)
    assert verdict == "CAPABILITY_UNREACHED"
    assert summary["charged"]["geometric_mean_ratio"] is None
    assert cells[0]["best8_reference_ratio"] is None
    assert cells[0]["zero_planning_reference_ratio"] is None
