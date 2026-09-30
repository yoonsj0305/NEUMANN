"""v0.0.75 frozen DP lifetime-equivalence audit.

This benchmark keeps the pre-change recursive implementations locally so the
cycle-free refactor can be measured on identical inputs in one process.
"""

from __future__ import annotations

import argparse
import gc
from functools import lru_cache
import json
import math
from pathlib import Path
import platform
from statistics import median
from time import perf_counter_ns

from neumann1 import proof_mis_v071, twin_mis_v070
from neumann1.proof_mis_v071 import DPProof
from neumann1.twin_mis_v070 import (
    check_certificate,
    constructed_graph,
    discover_twins,
)


K_VALUES = (4, 5, 6, 7, 8)
INDICES = (0, 1, 2, 3, 4)
MULTIPLICITY = 3
SEED_BASE = 755_000
REPEATS = 5
VARIANTS = ("legacy", "cycle_free")
SOLVERS = ("independent", "proof")
TARGETS = ("direct", "quotient")
NO_REGRESSION_CAP = 1.20


def corpus():
    for k in K_VALUES:
        for index in INDICES:
            graph = constructed_graph(
                k,
                MULTIPLICITY,
                index,
                seed_base=SEED_BASE,
            )
            cert = discover_twins(graph)
            check_certificate(graph, cert)
            yield {
                "name": f"k{k}_i{index}",
                "k": k,
                "index": index,
                "graph": graph,
                "quotient": cert.quotient,
                "quotient_weights": cert.weights,
            }


def _legacy_independent(graph, weights, *, call_limit=2_000_000):
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
    deadline = perf_counter_ns() + int(time_limit_s * 1e9)

    def visit(mask):
        if mask in memo:
            return memo[mask]
        if len(memo) >= state_limit:
            raise RuntimeError("proof DP state cap reached")
        if len(memo) % 1024 == 0 and perf_counter_ns() >= deadline:
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


def _current_independent(graph, weights):
    return twin_mis_v070._independent_optimum_with_stats(graph, weights)


def _current_proof(graph, weights):
    return proof_mis_v071.solve_with_proof(graph, weights)


def _reference_pair(graph, weights, solver):
    if solver == "independent":
        legacy = _legacy_independent(graph, weights)
        current = _current_independent(graph, weights)
        if current != legacy:
            raise RuntimeError("independent answer/state mismatch")
        return legacy, current, None

    if solver == "proof":
        legacy = _legacy_proof(graph, weights)
        current = _current_proof(graph, weights)
        if current != legacy:
            raise RuntimeError("proof record mismatch")
        verify_start = perf_counter_ns()
        legacy_value = proof_mis_v071.check_proof(graph, weights, legacy)
        current_value = proof_mis_v071.check_proof(graph, weights, current)
        verify_ms = (perf_counter_ns() - verify_start) / 1e6
        if legacy_value != current_value:
            raise RuntimeError("proof verification mismatch")
        return legacy, current, verify_ms

    raise ValueError("unknown solver")


def _call(graph, weights, solver, variant):
    if solver == "independent":
        return (
            _legacy_independent(graph, weights)
            if variant == "legacy"
            else _current_independent(graph, weights)
        )
    if solver == "proof":
        return (
            _legacy_proof(graph, weights)
            if variant == "legacy"
            else _current_proof(graph, weights)
        )
    raise ValueError("unknown solver")


def _timed_lifecycle(graph, weights, solver, variant, expected):
    # Standardize the pre-call heap. GC remains enabled during the call.
    gc.collect()
    start = perf_counter_ns()
    result = _call(graph, weights, solver, variant)
    if result != expected:
        raise RuntimeError("timed result diverged from frozen reference")
    del result
    # Charge complete cleanup because the experiment is about per-call lifetime.
    gc.collect()
    return (perf_counter_ns() - start) / 1e6


def _target(case, target):
    if target == "direct":
        graph = case["graph"]
        return graph, (1,) * len(graph)
    if target == "quotient":
        return case["quotient"], case["quotient_weights"]
    raise ValueError("unknown target")


def _geometric_mean(values):
    return math.exp(sum(math.log(value) for value in values) / len(values))


def summarize(cells):
    groups = {}
    for solver in SOLVERS:
        for target in TARGETS:
            subset = [
                cell
                for cell in cells
                if cell["solver"] == solver and cell["target"] == target
            ]
            ratios = [cell["cycle_free_legacy_ratio"] for cell in subset]
            groups[f"{solver}_{target}"] = {
                "cases": len(subset),
                "geometric_mean_ratio": _geometric_mean(ratios),
                "max_cell_ratio": max(ratios),
                "passes_geometric_mean_cap": _geometric_mean(ratios) <= NO_REGRESSION_CAP,
                "passes_every_cell_cap": max(ratios) <= NO_REGRESSION_CAP,
            }

    all_groups_pass = all(
        group["passes_geometric_mean_cap"] and group["passes_every_cell_cap"]
        for group in groups.values()
    )
    decision = (
        "LIFETIME_FIX_VALIDATED"
        if all_groups_pass
        else "LIFETIME_FIX_CORRECT_BUT_PERF_REGRESSION"
    )
    return {
        "groups": groups,
        "all_groups_pass": all_groups_pass,
        "decision": decision,
    }


def run():
    if not gc.isenabled():
        raise RuntimeError("v0.0.75 timing requires cyclic GC enabled")

    rows = []
    cells = []

    for case in corpus():
        for target in TARGETS:
            graph, weights = _target(case, target)
            for solver in SOLVERS:
                legacy_ref, current_ref, verify_ms = _reference_pair(
                    graph, weights, solver
                )
                references = {
                    "legacy": legacy_ref,
                    "cycle_free": current_ref,
                }

                # Untimed warmup per implementation.
                for variant in VARIANTS:
                    warm = _call(graph, weights, solver, variant)
                    if warm != references[variant]:
                        raise RuntimeError("warmup result mismatch")
                    del warm
                    gc.collect()

                timings = {variant: [] for variant in VARIANTS}
                for repeat in range(REPEATS):
                    order = VARIANTS[repeat % 2:] + VARIANTS[:repeat % 2]
                    for variant in order:
                        elapsed = _timed_lifecycle(
                            graph,
                            weights,
                            solver,
                            variant,
                            references[variant],
                        )
                        timings[variant].append(elapsed)
                        rows.append(
                            {
                                "case": case["name"],
                                "k": case["k"],
                                "index": case["index"],
                                "target": target,
                                "solver": solver,
                                "variant": variant,
                                "repeat": repeat,
                                "lifecycle_ms": elapsed,
                            }
                        )

                legacy_median = median(timings["legacy"])
                current_median = median(timings["cycle_free"])
                cells.append(
                    {
                        "case": case["name"],
                        "k": case["k"],
                        "index": case["index"],
                        "vertices": len(graph),
                        "target": target,
                        "solver": solver,
                        "answer": (
                            legacy_ref[0]
                            if solver == "independent"
                            else legacy_ref.states[-1][1]
                        ),
                        "states": (
                            legacy_ref[1]
                            if solver == "independent"
                            else len(legacy_ref.states)
                        ),
                        "reference_verify_ms": verify_ms,
                        "legacy_median_lifecycle_ms": legacy_median,
                        "cycle_free_median_lifecycle_ms": current_median,
                        "cycle_free_legacy_ratio": current_median / legacy_median,
                        "passes_1_20_cap": current_median / legacy_median <= NO_REGRESSION_CAP,
                    }
                )

    summary = summarize(cells)
    return {
        "experiment": "v0.0.75 proof-DP lifetime hygiene audit",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "gc_enabled": gc.isenabled(),
        },
        "corpus": {
            "cases": 25,
            "k_values": list(K_VALUES),
            "indices": list(INDICES),
            "multiplicity": MULTIPLICITY,
            "seed_base": SEED_BASE,
            "repeats": REPEATS,
        },
        "no_regression_cap": NO_REGRESSION_CAP,
        "summary": summary,
        "cells": cells,
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(
        json.dumps(
            {
                "decision": result["summary"]["decision"],
                "groups": result["summary"]["groups"],
            },
            indent=2,
        )
    )
