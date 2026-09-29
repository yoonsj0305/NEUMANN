from dataclasses import replace
import itertools

import pytest
from benchmark_v070 import verified_ratio

from neumann1.twin_mis_v070 import (
    check_certificate, constructed_graph, discover_twins,
    independent_optimum, observe, validate_graph,
)


def brute(graph):
    return max(sum(bits) for bits in itertools.product((0, 1), repeat=len(graph))
               if all(not (bits[v] and bits[u]) for v, row in enumerate(graph) for u in row))


def test_exhaustive_small_graph_equivalence_and_dp():
    n = 4
    edges = list(itertools.combinations(range(n), 2))
    for bits in itertools.product((0, 1), repeat=len(edges)):
        adj = [set() for _ in range(n)]
        for (v, u), exists in zip(edges, bits):
            if exists:
                adj[v].add(u); adj[u].add(v)
        graph = tuple(tuple(sorted(row)) for row in adj)
        cert = discover_twins(graph)
        check_certificate(graph, cert)
        assert independent_optimum(cert.quotient, cert.weights) == brute(graph)


def test_forged_weights_and_partition_rejected():
    graph = ((2,), (2,), (0, 1))
    cert = discover_twins(graph)
    with pytest.raises(ValueError):
        check_certificate(graph, replace(cert, weights=(1, 1)))
    with pytest.raises(ValueError):
        check_certificate(graph, replace(cert, groups=((0, 2), (1,))))
    with pytest.raises(ValueError):
        check_certificate(graph, replace(cert, quotient=((), ())))


def test_edge_perturbation_breaks_false_twin_witness():
    graph = ((2,), (2,), (0, 1), ())
    cert = discover_twins(graph)
    perturbed = ((2, 3), (2,), (0, 1), (0,))
    with pytest.raises(ValueError):
        check_certificate(perturbed, cert)
    validate_graph(perturbed)


def test_original_edge_check_and_independent_optimum_smoke():
    pytest.importorskip("highspy")
    graph = constructed_graph(6, 3, 7)
    direct, quotient = observe(graph, compressed=False), observe(graph, compressed=True)
    assert direct["verified"] and quotient["verified"]
    assert direct["optimum"] == quotient["optimum"] == brute(constructed_graph(6, 1, 7)) * 3
    assert quotient["retained"] <= 6


def test_invalid_graph_and_dp_budget_fail_closed():
    with pytest.raises(ValueError):
        validate_graph(((1,), ()))
    with pytest.raises(RuntimeError):
        independent_optimum(((1,), (0,)), (1, 1), call_limit=1)


def test_timeout_does_not_create_a_fake_speed_ratio():
    methods = {"direct": {"verified_calls": 8, "median_total_ms": 5000.},
               "quotient": {"verified_calls": 9, "median_total_ms": 10.}}
    assert verified_ratio(methods) is None
    methods["direct"]["verified_calls"] = 9
    assert verified_ratio(methods) == .002
