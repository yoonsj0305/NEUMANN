"""Small non-planted graph audit: direct, always-quotient, and cheap route."""

import argparse
import json
import os
from pathlib import Path
import platform
from statistics import median
from time import perf_counter_ns

from neumann1.proof_mis_v071 import observe_dp
from neumann1.twin_mis_v070 import discover_twins, validate_graph


CORPUS = Path(__file__).parent / "docs/experiments/data/v073_classic_graphs.json"
METHODS = ("direct", "quotient", "routed")


def load_graphs():
    data = json.loads(CORPUS.read_text())
    if data["source_commit"] != "92f497e2eb8192d1ce9205595f512294e4a9b696":
        raise ValueError("unfrozen graph source")
    graphs = {}
    for name, item in data["graphs"].items():
        n = item["vertices"]
        adjacency = [set() for _ in range(n)]
        for v, u in item["edges"]:
            if type(v) is not int or type(u) is not int or v == u or not (0 <= v < u < n):
                raise ValueError("bad edge archive")
            if u in adjacency[v]:
                raise ValueError("duplicate edge archive")
            adjacency[v].add(u)
            adjacency[u].add(v)
        graph = tuple(tuple(sorted(row)) for row in adjacency)
        validate_graph(graph)
        graphs[name] = graph
    if set(graphs) != {"karate", "davis", "florentine", "lesmis"}:
        raise ValueError("incomplete frozen corpus")
    return graphs


def _observe(graph, method):
    return observe_dp(graph, compressed=method == "quotient", routed=method == "routed")


def summarize(rows, graphs):
    cells = []
    for name, graph in graphs.items():
        count = len(discover_twins(graph).groups)
        methods = {}
        for method in METHODS:
            subset = [r for r in rows if r["graph"] == name and r["method"] == method]
            if len(subset) != 5:
                raise ValueError("incomplete timed archive")
            complete = all(r["verified"] for r in subset)
            methods[method] = {
                "verified_calls": sum(r["verified"] for r in subset),
                "median_total_ms": median(r["total_ms"] for r in subset) if complete else None,
                "median_proof_bytes": median(r["proof_bytes"] for r in subset) if complete else None,
                "median_proof_states": median(r["proof_states"] for r in subset) if complete else None,
            }
        ratio = (methods["routed"]["median_total_ms"] / methods["direct"]["median_total_ms"]
                 if methods["routed"]["verified_calls"] == 5
                 and methods["direct"]["verified_calls"] == 5 else None)
        relative_best = (methods["routed"]["median_total_ms"] /
                         min(methods[m]["median_total_ms"] for m in ("direct", "quotient"))
                         if all(methods[m]["verified_calls"] == 5 for m in METHODS) else None)
        cells.append({"graph": name, "vertices": len(graph),
                      "edges": sum(map(len, graph)) // 2,
                      "retained": count, "methods": methods,
                      "routed_direct_ratio": ratio,
                      "routed_best_ratio": relative_best})
    complete = all(c["methods"][m]["verified_calls"] == 5 for c in cells for m in METHODS)
    agree = all(len({r["optimum"] for r in rows if r["verified"] and r["graph"] == c["graph"]}) == 1
                for c in cells)
    if not complete or not agree:
        decision = "CAPABILITY_UNREACHED"
    elif (all(c["routed_direct_ratio"] <= 1.2 for c in cells
              if c["retained"] == c["vertices"])
          and all(c["routed_best_ratio"] <= 1.2 for c in cells
                  if c["retained"] < c["vertices"])
          and any(c["routed_direct_ratio"] <= .8 for c in cells
                  if c["retained"] < c["vertices"])):
        decision = "SMALL_GRAPH_ROUTING_OPPORTUNITY"
    else:
        decision = "NO_SMALL_GRAPH_ROUTING_ADVANTAGE"
    return cells, decision, agree


def run():
    graphs = load_graphs()
    rows = []
    for name, graph in graphs.items():
        for method in METHODS:
            try:
                _observe(graph, method)
            except RuntimeError:
                pass
        for repeat in range(5):
            for method in METHODS[repeat % 3:] + METHODS[:repeat % 3]:
                start = perf_counter_ns()
                try:
                    result = _observe(graph, method)
                except RuntimeError as exc:
                    result = {"verified": False, "error": str(exc),
                              "total_ms": (perf_counter_ns() - start) / 1e6}
                rows.append({"graph": name, "repeat": repeat, "method": method, **result})
    cells, decision, agree = summarize(rows, graphs)
    return {"experiment": "v0.0.73 small non-planted graph routing audit",
            "environment": {"python": platform.python_version(),
                            "platform": platform.platform(),
                            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                            "omp_threads": os.environ.get("OMP_NUM_THREADS")},
            "decision": decision, "completed_optima_agree": agree,
            "cells": cells, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
