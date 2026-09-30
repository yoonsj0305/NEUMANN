from __future__ import annotations

import gc
from functools import lru_cache
import weakref

import pytest

from benchmark_v073 import load_graphs
from neumann1 import proof_mis_v071, twin_mis_v070
from neumann1.proof_mis_v071 import DPProof
from neumann1.twin_mis_v070 import constructed_graph, discover_twins


def _legacy_independent_with_stats(graph, weights, *, call_limit=2_000_000):
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
        return max(
            visit(without),
            weights[pivot] + visit(without & ~masks[pivot]),
        )

    value = visit((1 << len(graph)) - 1)
    return value, visit.cache_info().currsize


def _legacy_proof(graph, weights, *, state_limit=2_000_000, time_limit_s=5.0):
    neighbors = proof_mis_v071._neighbors(graph)
    memo = {}
    deadline = proof_mis_v071.perf_counter_ns() + int(time_limit_s * 1e9)

    def visit(mask):
        if mask in memo:
            return memo[mask]
        if len(memo) >= state_limit:
            raise RuntimeError("proof DP state cap reached")
        if len(memo) % 1024 == 0 and proof_mis_v071.perf_counter_ns() >= deadline:
            raise RuntimeError("proof DP execution time cap reached")
        if not mask:
            value = 0
        else:
            weight, without, with_pivot = proof_mis_v071._transition(
                mask, neighbors, weights
            )
            if with_pivot == -1:
                value = weight + visit(without)
            else:
                value = max(visit(without), weight + visit(with_pivot))
        memo[mask] = value
        return value

    visit((1 << len(graph)) - 1)
    return DPProof(tuple(sorted(memo.items())))


def _equivalence_graphs():
    classics = load_graphs()
    return (
        ((1,), (0,), ()),
        constructed_graph(6, 3, 7, seed_base=750_000),
        classics["karate"],
        classics["florentine"],
    )


def test_v075_independent_optimum_answer_and_state_count_match_legacy():
    for graph in _equivalence_graphs():
        cert = discover_twins(graph)
        for target, weights in (
            (graph, (1,) * len(graph)),
            (cert.quotient, cert.weights),
        ):
            legacy = _legacy_independent_with_stats(target, weights)
            current = twin_mis_v070._independent_optimum_with_stats(
                target, weights
            )
            assert current == legacy


def test_v075_proof_record_matches_legacy_exactly():
    for graph in _equivalence_graphs():
        cert = discover_twins(graph)
        for target, weights in (
            (graph, (1,) * len(graph)),
            (cert.quotient, cert.weights),
        ):
            assert proof_mis_v071.solve_with_proof(
                target, weights
            ) == _legacy_proof(target, weights)


def _capture_independent_memo(monkeypatch):
    refs = []
    real = twin_mis_v070._independent_visit

    def spy(mask, masks, weights, memo, calls, call_limit):
        if not refs:
            refs.append(weakref.ref(memo))
        return real(mask, masks, weights, memo, calls, call_limit)

    monkeypatch.setattr(twin_mis_v070, "_independent_visit", spy)
    return refs


def _capture_proof_memo(monkeypatch):
    refs = []
    real = proof_mis_v071._proof_visit

    def spy(mask, neighbors, weights, memo, state_limit, deadline):
        if not refs:
            refs.append(weakref.ref(memo))
        return real(mask, neighbors, weights, memo, state_limit, deadline)

    monkeypatch.setattr(proof_mis_v071, "_proof_visit", spy)
    return refs


def test_v075_per_call_state_freed_without_gc_on_normal_exit(monkeypatch):
    graph = constructed_graph(6, 3, 9, seed_base=751_000)
    enabled = gc.isenabled()
    gc.disable()
    try:
        independent_refs = _capture_independent_memo(monkeypatch)
        twin_mis_v070.independent_optimum(graph, (1,) * len(graph))
        assert independent_refs and independent_refs[0]() is None

        proof_refs = _capture_proof_memo(monkeypatch)
        proof_mis_v071.solve_with_proof(graph, (1,) * len(graph))
        assert proof_refs and proof_refs[0]() is None
    finally:
        if enabled:
            gc.enable()


def test_v075_per_call_state_freed_without_gc_on_budget_exit(monkeypatch):
    graph = constructed_graph(6, 3, 11, seed_base=752_000)
    enabled = gc.isenabled()
    gc.disable()
    try:
        independent_refs = _capture_independent_memo(monkeypatch)
        try:
            twin_mis_v070.independent_optimum(
                graph, (1,) * len(graph), call_limit=1
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected independent optimum budget failure")
        assert independent_refs and independent_refs[0]() is None

        proof_refs = _capture_proof_memo(monkeypatch)
        try:
            proof_mis_v071.solve_with_proof(
                graph, (1,) * len(graph), state_limit=1
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected proof DP budget failure")
        assert proof_refs and proof_refs[0]() is None
    finally:
        if enabled:
            gc.enable()


def test_v075_public_budget_and_verification_contracts_still_hold():
    graph = constructed_graph(6, 3, 13, seed_base=753_000)
    proof = proof_mis_v071.solve_with_proof(graph, (1,) * len(graph))
    assert proof_mis_v071.check_proof(graph, (1,) * len(graph), proof) >= 0

    with pytest.raises(RuntimeError, match="call cap"):
        twin_mis_v070.independent_optimum(
            graph, (1,) * len(graph), call_limit=1
        )

    with pytest.raises(RuntimeError, match="state cap"):
        proof_mis_v071.solve_with_proof(
            graph, (1,) * len(graph), state_limit=1
        )
