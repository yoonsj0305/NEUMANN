"""First external-graph ordering opportunity audit; requires pinned PACE checkout."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns

from neumann1.pace_order_v051 import (
    bounded_proposals, greedy_order, order_cost, reference_cost, selected_public,
)


PINNED_COMMIT = "8cb56d0b9a832401713aa8c1456b619bf3e47ea2"


def run(root: Path) -> dict[str, object]:
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                       text=True).strip()
    if revision != PINNED_COMMIT:
        raise ValueError(f"expected PACE checkout {PINNED_COMMIT}, found {revision}")
    entries = selected_public(root)
    if len(entries) != 28:
        raise ValueError(f"expected all 28 public graphs with n <= 128, got {len(entries)}")
    results = []
    for name, graph, digest in entries:
        t0 = perf_counter_ns()
        degree_order = greedy_order(graph, "min_degree")
        fill_order = greedy_order(graph, "min_fill")
        base_search_ms = (perf_counter_ns() - t0) / 1e6
        t0 = perf_counter_ns()
        proposals = bounded_proposals(graph, name)
        proposal_search_ms = (perf_counter_ns() - t0) / 1e6
        baseline_orders = (degree_order, fill_order)
        all_orders = baseline_orders + proposals
        costs = [order_cost(graph, order) for order in all_orders]
        valid = all(order_cost(graph, order) == reference_cost(graph, order)
                    for order in all_orders)
        baseline = min(cost.arithmetic_ops for cost in costs[:2])
        best = min(cost.arithmetic_ops for cost in costs)
        best_fill = min(cost.fill_edges for cost in costs)
        density = sum(row.bit_count() for row in graph) / (len(graph) * (len(graph) - 1))
        results.append({"name": name, "sha256": digest, "vertices": len(graph),
                        "edges": sum(row.bit_count() for row in graph) // 2,
                        "density": density, "sparse": density < 0.20,
                        "verified": valid, "min_degree_ops": costs[0].arithmetic_ops,
                        "min_fill_ops": costs[1].arithmetic_ops,
                        "best_bounded_ops": best, "best_bounded_fill": best_fill,
                        "base_fill": min(cost.fill_edges for cost in costs[:2]),
                        "headroom": (baseline - best) / baseline,
                        "base_search_ms": base_search_ms,
                        "proposal_search_ms": proposal_search_ms})
    sparse = [row for row in results if row["sparse"]]
    qualifying = sum(row["headroom"] >= 0.10 for row in sparse)
    contract = (len(sparse) == 11 and all(row["verified"] for row in results)
                and len({row["sha256"] for row in results}) == 28)
    decision = ("INVALID_CORPUS" if not contract else
                "BOUNDED_OPPORTUNITY_VISIBLE" if qualifying >= 4 else
                "NO_BOUNDED_OPPORTUNITY")
    return {"version": "0.0.51", "dataset": "PACE 2017 minimum fill-in public",
            "source_commit": PINNED_COMMIT, "count": len(results),
            "sparse_count": len(sparse), "qualifying_sparse_10pct": qualifying,
            "contract": contract, "decision": decision,
            "mean_sparse_headroom": mean(row["headroom"] for row in sparse),
            "median_sparse_headroom": median(row["headroom"] for row in sparse),
            "median_baseline_search_ms": median(row["base_search_ms"] for row in results),
            "median_bounded_search_ms": median(row["proposal_search_ms"] for row in results),
            "rows": results,
            "boundary": "Bounded search is not an optimum or learned inference; symbolic arithmetic and fill are not full solve cost."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pace-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.pace_root), indent=2, sort_keys=True))
