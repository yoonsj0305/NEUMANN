"""Full-path constructed MIS compression mechanism audit."""

import argparse
import json
import os
from pathlib import Path
import platform
from statistics import median
from time import perf_counter_ns

from neumann1.twin_mis_v070 import constructed_graph, observe


def verified_ratio(methods):
    # A timeout is a capability failure, not an observation of optimal-solve
    # latency. Never use censored runs as the denominator of a speedup.
    if any(methods[method]["verified_calls"] != 9 for method in ("direct", "quotient")):
        return None
    return methods["quotient"]["median_total_ms"] / methods["direct"]["median_total_ms"]


def run():
    import highspy
    rows = []
    for k in (16, 32):
        for multiplicity in (1, 4, 8):
            for index in range(3):
                graph = constructed_graph(k, multiplicity, index)
                for compressed in (False, True):
                    try:
                        observe(graph, compressed=compressed)
                    except RuntimeError:
                        pass  # timed failures remain explicit below
                for repeat in range(3):
                    for compressed in (bool(repeat % 2), not bool(repeat % 2)):
                        start = perf_counter_ns()
                        try:
                            measurement = observe(graph, compressed=compressed)
                        except RuntimeError as error:
                            measurement = {"verified": False, "error": str(error),
                                           "total_ms": (perf_counter_ns() - start) / 1e6}
                        rows.append({"k": k, "multiplicity": multiplicity,
                                     "index": index, "repeat": repeat,
                                     "method": "quotient" if compressed else "direct",
                                     **measurement})
    cells = []
    for k in (16, 32):
        for multiplicity in (1, 4, 8):
            methods = {}
            for method in ("direct", "quotient"):
                subset = [row for row in rows if
                          (row["k"], row["multiplicity"], row["method"])
                          == (k, multiplicity, method)]
                case_medians = [median(row["total_ms"] for row in subset
                                       if row["index"] == index) for index in range(3)]
                methods[method] = {"median_total_ms": median(case_medians),
                                   "case_medians_ms": case_medians,
                                   "verified_calls": sum(row["verified"] for row in subset)}
            ratio = verified_ratio(methods)
            cells.append({"k": k, "multiplicity": multiplicity,
                          "methods": methods, "quotient_direct_ratio": ratio})
    all_verified = all(row["verified"] for row in rows)
    if all_verified:
        all_verified = all(len({row["optimum"] for row in rows
                                if (row["k"], row["multiplicity"], row["index"])
                                == (k, m, i)}) == 1
                           for k in (16, 32) for m in (1, 4, 8) for i in range(3))
    pass_gate = (all_verified
                 and all(cell["quotient_direct_ratio"] <= .5 for cell in cells
                         if cell["multiplicity"] > 1)
                 and all(cell["quotient_direct_ratio"] <= 1.2 for cell in cells
                         if cell["multiplicity"] == 1))
    return {"experiment": "v0.0.70 constructed twin MIS full-path opportunity",
            "environment": {"python": platform.python_version(),
                            "platform": platform.platform(),
                            "highspy": highspy.Highs().version(),
                            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                            "omp_threads": os.environ.get("OMP_NUM_THREADS")},
            "decision": ("CONSTRUCTED_TWIN_OPPORTUNITY" if pass_gate else
                         "NO_CONSTRUCTED_TWIN_ADVANTAGE" if all_verified else
                         "CAPABILITY_UNREACHED"),
            "all_independently_verified": all_verified, "cells": cells, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summarize-input", type=Path,
                        help="Correct summary ratios from archived raw trials, without new timing")
    args = parser.parse_args()
    if args.summarize_input:
        result = json.loads(args.summarize_input.read_text())
        for cell in result["cells"]:
            cell["quotient_direct_ratio"] = verified_ratio(cell["methods"])
        result["summary_correction"] = "Censored capability failures have null speed ratio; original rows unchanged"
    else:
        result = run()
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
