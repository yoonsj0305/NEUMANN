"""Opened retrospective v102 Q34: frozen learned EXPAND4 vs cheap residual fixed4m.
No training, no regenerated cases, no sealed/fresh admission, no historical overwrite.
This is an additional development-only performance observation with strict provenance.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
from collections import defaultdict
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import numpy as np
from threadpoolctl import threadpool_limits

from experiments.lp_expand4_holdout_register_v102 import load_registered
from experiments.lp_expand4_holdout_v102 import (
    SOURCE_MANIFEST, AUTHORITY_MANIFEST, raw_source, authority_and_models,
    observe_candidate, protocol as historic_protocol,
)
from neumann1.lp_expand4_holdout_archive_v102 import load_first_evaluation
from neumann1.lp_model_admission_v087 import features
from neumann1.lp_q34_support_v097 import restricted_original_checked
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

OUT = Path("research/development/q34_opened_direct_vs_learned_20261009")
ROUTES = ("DIRECT_NATIVE", "RESIDUAL_FIXED4M", "EXPAND4_s100001", "EXPAND4_s100002")
BUDGET_S = 5.0
REPEATS = (0, 1, 2)
ORDER_SEED = 102991
INVESTMENT_QUERIES = 10000
HISTORICAL_MANIFEST = "docs/experiments/results/v102_first_evaluation.manifest.json"


def elapsed(start):
    return (perf_counter_ns() - start) / 1e6


def deterministic_fixed4m(raw):
    start = perf_counter_ns()
    D, _rows, cols = features(**raw)
    m, n = D.shape
    ranking = np.argsort(cols[:, 1], kind="stable").tolist()
    proposal_ms = elapsed(start)
    remaining = BUDGET_S - proposal_ms / 1000.0
    restricted = None
    fallback = None
    accepted = False
    witness = None
    if remaining > 0:
        restricted = restricted_original_checked(**raw, indices=ranking[:min(n, 4*m)], budget_s=remaining)
        accepted = restricted["accepted"]
        witness = restricted["witness"]
    if not accepted and remaining > 0:
        remaining = BUDGET_S - elapsed(start) / 1000.0
        if remaining > 0:
            fallback = solve_native_checked(**raw, cold_fallback=False, budget_s=remaining)
            accepted = fallback["accepted"]
            witness = fallback["attempts"][-1]["witness"] if accepted else None
    total_ms = elapsed(start)
    return {"accepted": bool(accepted and total_ms <= BUDGET_S*1000),
            "total_ms": total_ms, "proposal_ms": proposal_ms,
            "post_ms": total_ms - proposal_ms, "amortized_investment_ms": 0.0,
            "fallback_used": fallback is not None,
            "subset_accepted": bool(restricted and restricted["accepted"]),
            "witness": witness, "ranking": ranking}


def direct_native(raw):
    start = perf_counter_ns()
    result = solve_native_checked(**raw, cold_fallback=False, budget_s=BUDGET_S)
    return {"accepted": result["accepted"], "total_ms": elapsed(start),
            "proposal_ms": 0.0, "post_ms": elapsed(start),
            "amortized_investment_ms": 0.0, "fallback_used": False,
            "subset_accepted": False,
            "witness": result["attempts"][-1]["witness"] if result["accepted"] else None}


def evaluate():
    import torch, scipy, sklearn, highspy, threadpoolctl, sys
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    runtime = {
        "python": list(sys.version_info[:2]), "numpy": np.__version__,
        "scipy": scipy.__version__, "sklearn": sklearn.__version__,
        "torch": torch.__version__, "highspy": highspy.Highs().version(),
        "threadpoolctl": threadpoolctl.__version__,
    }
    target_runtime = historic_protocol()["runtime"]
    for k, value in target_runtime.items():
        if runtime[k] != value:
            raise RuntimeError(f"Frozen runtime drift {k}: {runtime[k]} != {value}")
    if os.getenv("OPENBLAS_CORETYPE") != "HASWELL":
        raise RuntimeError("Frozen OpenBLAS dispatch environment missing")

    source_manifest, source_report = load_registered(SOURCE_MANIFEST)
    if len(source_report["sources"]) != 48:
        raise RuntimeError("Unexpected opened original population")
    archive = load_first_evaluation(HISTORICAL_MANIFEST)
    if archive["summary"]["decision"] != "Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5":
        raise RuntimeError("Historical verdict drift")
    first = {(row["case_id"], row["route"]): row for row in archive["records"]
             if row["repeat"] == 0}
    if len(first) != 48 * 4:
        raise RuntimeError("Original timed ranking trace incomplete")
    model_start = perf_counter_ns()
    _authority, models, training = authority_and_models()
    model_load_ms = elapsed(model_start)
    sources = {s["id"]: s for s in source_report["sources"]}
    raws = {name: raw_source(s) for name, s in sources.items()}
    records = []
    failures = []
    with threadpool_limits(limits=1):
        for repeat in (-1, *REPEATS):
            order = [(case_id, route) for case_id in sources for route in ROUTES]
            random.Random(ORDER_SEED + repeat).shuffle(order)
            for case_id, route in order:
                raw = raws[case_id]
                start = perf_counter_ns()
                try:
                    if route == "DIRECT_NATIVE":
                        outcome = direct_native(raw)
                    elif route == "RESIDUAL_FIXED4M":
                        outcome = deterministic_fixed4m(raw)
                    else:
                        outcome = observe_candidate(raw, route, models, training)
                        if outcome["ranking"] != first[case_id, route]["ranking"]:
                            raise RuntimeError(f"Frozen ranking mismatch {case_id} {route}")
                    accepted = bool(outcome["accepted"])
                    if accepted:
                        witness = outcome["witness"]
                        certificate = verify_standard_form_certificate(**raw, **witness)
                        if not certificate["accepted"]:
                            raise RuntimeError("Independent original certificate rejected accepted route")
                    row = {
                        "case_id": case_id, "pair_id": sources[case_id]["pair_id"],
                        "group": sources[case_id]["group"], "route": route,
                        "repeat": repeat, "accepted": accepted,
                        "total_ms": float(outcome["total_ms"]),
                        "proposal_ms": float(outcome["proposal_ms"]),
                        "post_ms": float(outcome["post_ms"]),
                        "investment_per_10000_query_ms": float(outcome["amortized_investment_ms"]),
                        "fallback_used": bool(outcome["fallback_used"]),
                        "subset_accepted": bool(outcome["subset_accepted"]),
                        "error": None,
                    }
                except Exception as exc:
                    row = {"case_id": case_id, "pair_id": sources[case_id]["pair_id"],
                           "group": sources[case_id]["group"], "route": route, "repeat": repeat,
                           "accepted": False, "total_ms": elapsed(start),
                           "proposal_ms": None, "post_ms": None,
                           "investment_per_10000_query_ms": None,
                           "fallback_used": None, "subset_accepted": False,
                           "error": f"{type(exc).__name__}: {exc}"}
                    failures.append(row)
                records.append(row)
        if any(r["error"] for r in records):
            status = "DIAGNOSTIC_WITH_ERRORS_NOT_ADMITTED"
        else:
            status = "COMPLETE_OPENED_RETROSPECTIVE"
    medians = []
    for case_id, source in sources.items():
        for route in ROUTES:
            rows = [r for r in records if r["case_id"] == case_id and
                    r["route"] == route and r["repeat"] in REPEATS]
            if len(rows) != 3:
                raise RuntimeError("Timed repeat coverage drift")
            if any(r["error"] for r in rows):
                continue
            if not all(r["accepted"] for r in rows):
                continue
            total = median(r["total_ms"] for r in rows)
            invested = rows[0]["investment_per_10000_query_ms"]
            medians.append({"case_id": case_id, "pair_id": source["pair_id"],
                            "group": source["group"], "route": route,
                            "median_ms": total, "investment_ms": invested,
                            "amortized_total_ms": total + invested,
                            "all_accepted": True})
    by_route = defaultdict(list)
    for row in medians:
        by_route[row["route"]].append(row)
    route_summary = {}
    for route, entries in by_route.items():
        reference = {r["case_id"]: r for r in by_route["DIRECT_NATIVE"]}
        shared = [r for r in entries if r["case_id"] in reference]
        route_summary[route] = {
            "accepted_view_count": len(entries),
            "matched_vs_direct": len(shared),
            "total_amortized_ms": sum(r["amortized_total_ms"] for r in entries),
            "sum_direct_over_sum_candidate_for_shared": (
                sum(reference[r["case_id"]]["amortized_total_ms"] for r in shared)/
                sum(r["amortized_total_ms"] for r in shared) if shared else None),
        }
    paired = []
    for case_id in sources:
        selection = {r["route"]: r for r in medians if r["case_id"] == case_id}
        if all(route in selection for route in ROUTES):
            fixed = selection["RESIDUAL_FIXED4M"]["amortized_total_ms"]
            paired.append({
                "case_id": case_id, "pair_id": sources[case_id]["pair_id"],
                "group": sources[case_id]["group"],
                "learned_seed100001_over_fixed4m": selection["EXPAND4_s100001"]["amortized_total_ms"]/fixed,
                "learned_seed100002_over_fixed4m": selection["EXPAND4_s100002"]["amortized_total_ms"]/fixed
            })
    report = {
        "status": status, "scope": "opened historical original retrospective, NOT fresh",
        "source_manifest_sha256": source_manifest["gzip_sha256"],
        "historical_evaluation_sha256": json.loads(Path(HISTORICAL_MANIFEST).read_text())["gzip_sha256"],
        "runtime": runtime, "model_load_ms_unamortized_descriptive": model_load_ms,
        "historical_decision_unchanged": archive["summary"]["decision"],
        "new_training": False, "new_model": False, "new_problem_generation": False,
        "originals": len({s["pair_id"] for s in sources.values()}),
        "views": len(sources), "routes": ROUTES, "warmups": 1,
        "timed_repeats": len(REPEATS), "records": len(records),
        "failed_records": len(failures),
        "route_summary": route_summary, "paired_view_count": len(paired),
        "records_sha256": hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest(),
        "caveat": "This is a new historical opened-set observation, not a replacement v102 result; per-view repeated equivalent surfaces are dependent."
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipts.json").write_text(json.dumps({"report": report, "records": records,
                                                   "medians": medians, "paired": paired},
                                                   indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print("Q34_OPENED_COMPARISON=" + json.dumps({
        "status": status, "routes": route_summary, "paired_view_count": len(paired),
        "failures": len(failures)}, sort_keys=True))
    if status != "COMPLETE_OPENED_RETROSPECTIVE":
        raise RuntimeError("Opened comparison errors retained; no evaluation PASS")
    return report


if __name__ == "__main__":
    try:
        evaluate()
    except Exception as e:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "fatal.txt").write_text(f"{type(e).__name__}: {e}\n")
        raise
