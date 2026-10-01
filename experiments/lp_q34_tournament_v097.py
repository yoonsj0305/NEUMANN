"""v0.0.97 frozen-support Q34 development tournament.

The timed runner is executed exactly once by a dedicated workflow after this
protocol/code has passed smoke CI. Normal CI tests contracts only.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import numpy as np
import scipy
import torch
from threadpoolctl import threadpool_limits

from experiments.lp_input_compaction_v094 import features
from experiments.lp_shortlist_screen_v089 import raw_source, restore_models
from experiments.lp_state_models_v087 import tensor_input
from neumann1 import lp_model_admission_v087 as admission
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_q34_support_v097 import adaptive_support_checked, restricted_original_checked
from neumann1.lp_shortlist_v089 import solve_shortlist_checked

SEEDS = (87001, 87002)
CASES = 16
ROUTES = (
    "DIRECT", "ORACLE", "A_DETERMINISTIC",
    "B_POINT_s87001", "B_POINT_s87002",
    "C_FULL_s87001", "C_FULL_s87002",
    "D_ADAPTIVE_s87001", "D_ADAPTIVE_s87002",
)


def protocol():
    return {
        "schema": "neumann.q34-support-tournament-v097.v1",
        "runtime": admission.RUNTIME,
        "opened_source_manifest": "docs/experiments/results/v088_completed.manifest.json",
        "cases": CASES,
        "case_slice": [0, CASES],
        "routes": list(ROUTES),
        "new_fitting": False,
        "final_evaluation": False,
        "threads": 1,
        "order_seed": 97991,
        "warmups": 1,
        "repeats": 3,
        "budget_s": 5.0,
        "support_factor": 2,
        "adaptive_factors": [1, 2, 4],
        "utility_floor": 0.80,
        "discovery_burden_max": 0.20,
        "complete_ratio_max": 1.0,
        "amortization_queries": 10000,
        "requires_both_seeds": True,
        "decision_pass": "ADMIT_FRESH_Q34_HOLDOUT",
        "decision_fail": "NO_FROZEN_FAMILY_Q34_CANDIDATE",
        "global_q3": "OPEN",
        "global_q4": "OPEN",
    }


def _runtime():
    import highspy
    env = {
        "python": list(sys.version_info[:2]),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "torch": torch.__version__,
        "highspy": highspy.Highs().version(),
    }
    if env != protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE") != "HASWELL":
        raise RuntimeError(f"runtime drift: {env!r}")
    return env


def _point_ranking(raw, model):
    started = perf_counter_ns()
    D, rows, cols = features(raw)
    matrix, rt, ct = tensor_input(D, rows, cols)
    with torch.inference_mode():
        score = model.head(model.cols(ct)).squeeze(1)
    if not torch.isfinite(score).all():
        raise ValueError("nonfinite point ranking")
    ranking = torch.argsort(score, descending=True, stable=True).tolist()
    return ranking, (perf_counter_ns() - started) / 1e6


def _full_ranking(raw, model):
    started = perf_counter_ns()
    D, rows, cols = features(raw)
    matrix, rt, ct = tensor_input(D, rows, cols)
    with torch.inference_mode():
        out = model(matrix, rt, ct)
        score = out["scores"]
    if not torch.isfinite(score).all():
        raise ValueError("nonfinite full ranking")
    ranking = torch.argsort(score, descending=True, stable=True).tolist()
    return ranking, (perf_counter_ns() - started) / 1e6


def _deterministic_ranking(raw):
    started = perf_counter_ns()
    D, rows, cols = features(raw)
    del D, rows
    ranking = np.argsort(cols[:, 1], kind="stable").tolist()
    return ranking, (perf_counter_ns() - started) / 1e6


def observe(raw, label, route, models):
    m, n = raw["A"].shape
    budget = protocol()["budget_s"]
    if route == "DIRECT":
        result = solve_native_checked(**raw, cold_fallback=False, budget_s=budget)
        return {
            "accepted": result["accepted"], "discovery_ms": 0.0,
            "post_ms": result["total_ms"], "total_ms": result["total_ms"],
            "no_full_fallback": False, "result": result,
        }
    if route == "ORACLE":
        result = restricted_original_checked(**raw, indices=list(label["indices"]), budget_s=budget)
        return {
            "accepted": result["accepted"], "discovery_ms": 0.0,
            "post_ms": result["total_ms"], "total_ms": result["total_ms"],
            "no_full_fallback": result["accepted"], "result": result,
        }

    if route == "A_DETERMINISTIC":
        ranking, disc = _deterministic_ranking(raw)
        execution = solve_shortlist_checked(**raw, indices=ranking[:min(n, 2*m)],
                                            budget_s=max(1e-9, budget-disc/1000.0))
    else:
        name, seed_text = route.rsplit("_s", 1)
        seed = int(seed_text)
        if name in ("B_POINT", "D_ADAPTIVE"):
            ranking, disc = _point_ranking(raw, models[f"point16_s{seed}"])
        elif name == "C_FULL":
            ranking, disc = _full_ranking(raw, models[f"full16_s{seed}"])
        else:
            raise ValueError(f"unknown route {route}")
        left = max(1e-9, budget-disc/1000.0)
        if name == "D_ADAPTIVE":
            execution = adaptive_support_checked(**raw, ranking=ranking, budget_s=left,
                                                 factors=tuple(protocol()["adaptive_factors"]))
        else:
            execution = solve_shortlist_checked(**raw, indices=ranking[:min(n, 2*m)], budget_s=left)

    total = disc + execution["total_ms"]
    accepted = bool(execution["accepted"] and total <= budget*1000.0)
    no_full = bool(accepted and not execution["fallback_used"])
    return {
        "accepted": accepted, "discovery_ms": disc,
        "post_ms": execution["total_ms"], "total_ms": total,
        "no_full_fallback": no_full, "result": execution,
    }


def _medians(records, case_id, route):
    rows = [r for r in records if r["case_id"] == case_id
            and r["route"] == route and r["repeat"] >= 0]
    if len(rows) != protocol()["repeats"]:
        raise ValueError("timed repeat coverage drift")
    return {
        key: median(r[key] for r in rows)
        for key in ("discovery_ms", "post_ms", "total_ms")
    } | {
        "all_accepted": all(r["accepted"] for r in rows),
        "no_full_fallback": all(r["no_full_fallback"] for r in rows),
    }


def _investment_per_query(route, retained):
    if route.startswith(("B_POINT_", "D_ADAPTIVE_")):
        seed = int(route.rsplit("_s", 1)[1])
        key = f"point16_s{seed}"
    elif route.startswith("C_FULL_"):
        seed = int(route.rsplit("_s", 1)[1])
        key = f"full16_s{seed}"
    else:
        return 0.0
    return (retained["training_setup_ms"] + retained["training"][key]["fit_ms"]) / protocol()["amortization_queries"]


def route_metrics(records, sources, route, retained):
    direct = {s["id"]: _medians(records, s["id"], "DIRECT") for s in sources}
    oracle = {s["id"]: _medians(records, s["id"], "ORACLE") for s in sources}
    cand = {s["id"]: _medians(records, s["id"], route) for s in sources}
    if not all(v["all_accepted"] for v in direct.values()) or not all(v["all_accepted"] for v in oracle.values()):
        raise ValueError("Direct/oracle capability drift")
    capability = all(v["all_accepted"] for v in cand.values())
    direct_sum = sum(v["post_ms"] for v in direct.values())
    oracle_post = sum(v["post_ms"] for v in oracle.values())
    disc_sum = sum(v["discovery_ms"] for v in cand.values())
    post_sum = sum(v["post_ms"] for v in cand.values())
    oracle_savings = direct_sum - oracle_post
    candidate_savings = direct_sum - post_sum
    utility = candidate_savings / oracle_savings if oracle_savings > 0 else None
    burden = disc_sum / candidate_savings if candidate_savings > 0 else None
    complete = (disc_sum + post_sum) / direct_sum
    invest = _investment_per_query(route, retained) * len(sources)
    amortized = (disc_sum + post_sum + invest) / direct_sum
    no_full = sum(v["no_full_fallback"] for v in cand.values())
    passed = bool(
        capability and oracle_savings > 0 and candidate_savings > 0
        and utility is not None and utility >= protocol()["utility_floor"]
        and burden is not None and burden <= protocol()["discovery_burden_max"]
        and complete < protocol()["complete_ratio_max"]
        and amortized < protocol()["complete_ratio_max"]
    )
    return {
        "route": route,
        "capability": capability,
        "direct_sum_ms": direct_sum,
        "oracle_post_sum_ms": oracle_post,
        "discovery_sum_ms": disc_sum,
        "post_sum_ms": post_sum,
        "oracle_savings_ms": oracle_savings,
        "candidate_savings_ms": candidate_savings,
        "utility_recovery": utility,
        "discovery_burden": burden,
        "complete_ratio": complete,
        "training_amortized_complete_ratio_at_10000": amortized,
        "no_full_fallback_cases": no_full,
        "cases": len(sources),
        "passed": passed,
    }


def summarize(records, sources, retained):
    expected = {(s["id"], route, repeat)
                for s in sources for route in ROUTES for repeat in (-1, 0, 1, 2)}
    keys = [(r["case_id"], r["route"], r["repeat"]) for r in records]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("tournament coverage drift")
    if any(type(r["accepted"]) is not bool or not math.isfinite(r["total_ms"])
           or r["total_ms"] <= 0 for r in records):
        raise ValueError("record cost drift")

    candidate_routes = [r for r in ROUTES if r not in ("DIRECT", "ORACLE")]
    metrics = {route: route_metrics(records, sources, route, retained)
               for route in candidate_routes}

    families = {
        "A_DETERMINISTIC": ["A_DETERMINISTIC"],
        "B_POINT": [f"B_POINT_s{s}" for s in SEEDS],
        "C_FULL": [f"C_FULL_s{s}" for s in SEEDS],
        "D_ADAPTIVE": [f"D_ADAPTIVE_s{s}" for s in SEEDS],
    }
    family_rows = {}
    for family, routes in families.items():
        rows = [metrics[r] for r in routes]
        family_rows[family] = {
            "routes": routes,
            "utility_recovery": min(r["utility_recovery"] if r["utility_recovery"] is not None else float("-inf") for r in rows),
            "discovery_burden": max(r["discovery_burden"] if r["discovery_burden"] is not None else float("inf") for r in rows),
            "complete_ratio": max(r["complete_ratio"] for r in rows),
            "amortized_complete_ratio_at_10000": max(r["training_amortized_complete_ratio_at_10000"] for r in rows),
            "no_full_fallback_cases": min(r["no_full_fallback_cases"] for r in rows),
            "passed": all(r["passed"] for r in rows),
        }

    for name, row in family_rows.items():
        dominated_by = []
        for other, challenger in family_rows.items():
            if other == name:
                continue
            no_worse = (challenger["utility_recovery"] >= row["utility_recovery"]
                        and challenger["complete_ratio"] <= row["complete_ratio"]
                        and challenger["discovery_burden"] <= row["discovery_burden"])
            strict = (challenger["utility_recovery"] > row["utility_recovery"]
                      or challenger["complete_ratio"] < row["complete_ratio"]
                      or challenger["discovery_burden"] < row["discovery_burden"])
            if no_worse and strict:
                dominated_by.append(other)
        row["dominated_by"] = dominated_by
        row["pareto_survivor"] = not dominated_by

    survivors = [name for name, row in family_rows.items()
                 if row["passed"] and row["pareto_survivor"]]
    return {
        "decision": protocol()["decision_pass"] if survivors else protocol()["decision_fail"],
        "route_metrics": metrics,
        "families": family_rows,
        "pareto_q34_survivors": survivors,
        "development_only": True,
        "global_q3": "OPEN",
        "global_q4": "OPEN",
    }


def run(output):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    env = _runtime()
    loading = perf_counter_ns()
    retained = load_study(protocol()["opened_source_manifest"])
    models = restore_models(retained["training"])
    sources = retained["train_sources"][:CASES]
    setup_ms = (perf_counter_ns() - loading) / 1e6
    report = {
        "protocol": protocol(),
        "environment": env,
        "setup_ms": setup_ms,
        "source_ids": [s["id"] for s in sources],
        "source_sha256": [s["sha256"] for s in sources],
        "records": [],
    }
    raws = {s["id"]: raw_source(s) for s in sources}
    labels = {s["id"]: s["label"] for s in sources}

    with threadpool_limits(1):
        for repeat in (-1, 0, 1, 2):
            order = [(s["id"], route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"] + repeat).shuffle(order)
            for case_id, route in order:
                row = observe(raws[case_id], labels[case_id], route, models)
                report["records"].append({"case_id": case_id, "route": route,
                                          "repeat": repeat, **row})
                print(case_id, route, repeat, f'{row["total_ms"]:.6f}', flush=True)

    report["summary"] = summarize(report["records"], sources, retained)
    report["stage"] = "completed"
    path = Path(output)
    with path.open("x") as fh:
        json.dump(report, fh, sort_keys=True, separators=(",", ":"))
        fh.write("\n")
    print("V097_SUMMARY=" + json.dumps(report["summary"], separators=(",", ":")), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.output)


if __name__ == "__main__":
    main()
