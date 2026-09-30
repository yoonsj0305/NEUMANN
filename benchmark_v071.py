"""Fresh held-out exact MIS proof-DP versus MIP comparison."""

import argparse
import json
import os
from pathlib import Path
import platform
from statistics import median
from time import perf_counter_ns

from neumann1.proof_mis_v071 import observe_dp
from neumann1.twin_mis_v070 import constructed_graph, observe

METHODS = ("direct_dp", "quotient_dp", "quotient_mip")


def _observe(graph, method):
    if method == "direct_dp":
        return observe_dp(graph, compressed=False)
    if method == "quotient_dp":
        return observe_dp(graph, compressed=True)
    return observe(graph, compressed=True)


def summarize(rows):
    cells = []
    for k in (16, 32):
        for multiplicity in (1, 4, 8):
            methods = {}
            for method in METHODS:
                subset = [r for r in rows if (r["k"], r["multiplicity"], r["method"])
                          == (k, multiplicity, method)]
                if not subset:
                    raise ValueError("incomplete experiment")
                case_medians = [median(r["total_ms"] for r in subset if r["index"] == i)
                                for i in range(3)]
                methods[method] = {
                    "median_total_ms": median(case_medians),
                    "case_medians_ms": case_medians,
                    "verified_calls": sum(r["verified"] for r in subset),
                    "median_proof_bytes": (median(r["proof_bytes"] for r in subset)
                                           if method != "quotient_mip"
                                           and all(r["verified"] for r in subset) else None),
                    "median_proof_states": (median(r["proof_states"] for r in subset)
                                            if method != "quotient_mip"
                                            and all(r["verified"] for r in subset) else None),
                }
            def ratio(a, b):
                if methods[a]["verified_calls"] != 9 or methods[b]["verified_calls"] != 9:
                    return None
                return methods[a]["median_total_ms"] / methods[b]["median_total_ms"]
            cells.append({"k": k, "multiplicity": multiplicity,
                          "methods": methods,
                          "dp_mip_ratio": ratio("quotient_dp", "quotient_mip"),
                          "compression_ratio": ratio("quotient_dp", "direct_dp")})
    results_agree = all(len({r["optimum"] for r in rows if r["verified"] and
                             (r["k"], r["multiplicity"], r["index"]) == (k, m, i)}) <= 1
                        for k in (16, 32) for m in (1, 4, 8) for i in range(3))
    complete = lambda method: all(c["methods"][method]["verified_calls"] == 9 for c in cells)
    large = [c for c in cells if c["k"] == 32 and c["multiplicity"] in (4, 8)]
    control = [c for c in cells if c["multiplicity"] == 1]
    mip_pass = (results_agree and complete("quotient_dp") and complete("quotient_mip")
                and all(c["dp_mip_ratio"] <= .8 for c in large)
                and all(c["dp_mip_ratio"] <= 1.2 for c in control))
    compression_pass = (results_agree and complete("direct_dp")
                        and complete("quotient_dp")
                        and all(c["compression_ratio"] <= .8 for c in large))
    if not complete("quotient_dp") or not complete("quotient_mip") or not results_agree:
        verdict = "CAPABILITY_UNREACHED"
    elif not complete("direct_dp"):
        verdict = "DIRECT_CAPABILITY_UNREACHED"
    else:
        verdict = ("BOTH_GATES_PASS" if mip_pass and compression_pass else
                   "MIP_DELETION_ONLY" if mip_pass else "NO_COMPLETE_COST_GATE")
    return cells, verdict, results_agree, mip_pass, compression_pass


def run(seed_base=710_000):
    import highspy
    rows = []
    for k in (16, 32):
        for multiplicity in (1, 4, 8):
            for index in range(3):
                graph = constructed_graph(k, multiplicity, index, seed_base=seed_base)
                for method in METHODS:
                    try:
                        _observe(graph, method)
                    except RuntimeError:
                        pass
                for repeat in range(3):
                    order = METHODS[repeat:] + METHODS[:repeat]
                    for method in order:
                        start = perf_counter_ns()
                        try:
                            measurement = _observe(graph, method)
                        except RuntimeError as error:
                            measurement = {"verified": False, "error": str(error),
                                           "total_ms": (perf_counter_ns() - start) / 1e6}
                        rows.append({"k": k, "multiplicity": multiplicity,
                                     "index": index, "repeat": repeat,
                                     "method": method, **measurement})
    cells, decision, agree, mip_pass, compression_pass = summarize(rows)
    return {"experiment": "MIS proof-DP executor audit", "seed_base": seed_base,
            "environment": {"python": platform.python_version(),
                            "platform": platform.platform(),
                            "highspy": highspy.Highs().version(),
                            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                            "omp_threads": os.environ.get("OMP_NUM_THREADS")},
            "decision": decision, "completed_optima_agree": agree,
            "mip_deletion_gate": mip_pass, "compression_gate": compression_pass,
            "cells": cells, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed-base", type=int, default=710_000)
    args = parser.parse_args()
    result = run(args.seed_base)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
