"""Frozen exact elimination-order headroom screen, no training or oracle runtime."""

import argparse
import json
import math
import os
from pathlib import Path
import platform
from statistics import median
from time import perf_counter_ns

from neumann1.elimination_v074 import generated_graph, observe


METHODS = ("minfill", "mindegree", "best8")
FAMILIES = ("random", "bipartite", "ring_chords")


def corpus():
    number = 0
    for family in FAMILIES:
        for n in (16, 24, 32):
            for replicate in range(3):
                seed = 740001 + number
                yield f"{family}_{n}_{replicate}", family, n, seed, generated_graph(family, n, seed)
                number += 1


def summarize(rows):
    cells = []
    complete = True
    for name, family, n, seed, graph in corpus():
        methods = {}
        counts = set()
        for method in METHODS:
            subset = [r for r in rows if r["graph"] == name and r["method"] == method]
            okay = len(subset) == 3 and all(r["verified"] for r in subset)
            complete &= okay
            counts.update(r["count"] for r in subset if r["verified"])
            methods[method] = {"verified_calls": sum(r["verified"] for r in subset)}
            for field in ("total_ms", "planning_ms", "execution_ms", "verification_ms",
                          "table_assignment_proxy", "induced_width", "retained_proof_entries",
                          "peak_active_table_entries"):
                methods[method][field] = median(r[field] for r in subset) if okay else None
            methods[method]["zero_planning_ms"] = (median(r["execution_ms"] + r["verification_ms"]
                                                         for r in subset) if okay else None)
        agree = len(counts) == 1
        complete &= agree
        reference = (min(methods[m]["total_ms"] for m in METHODS[:2])
                     if all(methods[m]["verified_calls"] == 3 for m in METHODS) and agree else None)
        cells.append({"graph": name, "family": family, "n": n, "seed": seed,
                      "edges": sum(map(len, graph)) // 2, "counts_agree": agree,
                      "methods": methods,
                      "best8_reference_ratio": methods["best8"]["total_ms"] / reference
                      if reference is not None else None,
                      "zero_planning_reference_ratio": methods["best8"]["zero_planning_ms"] / reference
                      if reference is not None else None})
    summary = {"complete_verified": complete, "graphs": len(cells)}
    for label, field in (("charged", "best8_reference_ratio"),
                         ("zero_planning_diagnostic", "zero_planning_reference_ratio")):
        ratios = [c[field] for c in cells]
        gm = math.exp(sum(map(math.log, ratios)) / len(ratios)) if complete else None
        wins = sum(r <= .8 for r in ratios) if complete else None
        summary[label] = {"geometric_mean_ratio": gm, "twenty_percent_wins": wins,
                          "passes_cost_screen": complete and gm <= .8 and wins >= 9}
    if not complete:
        decision = "CAPABILITY_UNREACHED"
    elif summary["charged"]["passes_cost_screen"]:
        decision = "CLASSICAL_PLANNING_OPPORTUNITY_NOT_LEARNED_EVIDENCE"
    elif summary["zero_planning_diagnostic"]["passes_cost_screen"]:
        decision = "ZERO_COST_PLANNER_HEADROOM_ONLY_REQUIRES_NEW_LEARNED_GATE"
    else:
        decision = "NO_LEARNED_PLANNER_HEADROOM_ON_FROZEN_DISTRIBUTION"
    return cells, summary, decision


def run():
    rows, warmups = [], []
    for name, family, n, seed, graph in corpus():
        for method in METHODS:
            try:
                result = observe(graph, method, seed)
                warmups.append({"graph": name, "method": method, "verified": result["verified"]})
            except RuntimeError as exc:
                warmups.append({"graph": name, "method": method, "verified": False, "error": str(exc)})
        for repeat in range(3):
            for method in METHODS[repeat:] + METHODS[:repeat]:
                start = perf_counter_ns()
                try:
                    result = observe(graph, method, seed)
                except RuntimeError as exc:
                    result = {"verified": False, "error": str(exc),
                              "total_ms": (perf_counter_ns() - start) / 1e6}
                rows.append({"graph": name, "family": family, "n": n, "seed": seed,
                             "method": method, "repeat": repeat, **result})
        print(json.dumps({"completed_graph": name}), flush=True)
    cells, summary, decision = summarize(rows)
    return {"experiment": "v0.0.74 elimination-order headroom screen",
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                            "omp_threads": os.environ.get("OMP_NUM_THREADS")},
            "decision": decision, "summary": summary, "cells": cells,
            "warmups": warmups, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"decision": result["decision"], "summary": result["summary"]}, indent=2))
