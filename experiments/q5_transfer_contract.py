"""Preregistered new-family admission, never a replacement for first Q5."""
from __future__ import annotations

import math
import random
from statistics import median

FAMILIES = ("assignment", "basis_pursuit")
LEVELS = (8, 16, 32, 64)


def protocol():
    return {"schema": "neumann.q5-transfer-admission.v104.v1",
        "families": list(FAMILIES), "levels": list(LEVELS), "replicates": 4,
        "base_cases": 32, "seed_base": 104000, "order_seed": 104991,
        "budget_s": 5.0, "warmups": 1, "timed_repeats": 3,
        "amortization_queries": 10000, "large_cell_ratio_max": 0.80,
        "small_control_ratio_max": 1.20, "large_cell_min_20pct_wins": 3,
        "models": 0, "new_fitting": False, "cross_domain_pass": False,
        "oracle_authority": "free_exact_primal_support_and_original_optimal_dual",
        "order": "all_shuffled_warmups_before_shuffled_timed_repeats",
        "global_q5_closed": False, "scope": "two_construction_classes_shared_LP_backend"}


def specs():
    result = []
    for family in FAMILIES:
        for level in LEVELS:
            for replicate in range(4):
                m, n = ((2*level-1, level*level) if family == "assignment"
                        else (2*level, 32*level))
                result.append({"id": f"v104_{family}_k{level}_r{replicate}",
                    "family": family, "level": level, "replicate": replicate,
                    "rows": m, "cols": n, "seed": 104000 + len(result)})
    return result


def routes(family):
    if family not in FAMILIES:
        raise ValueError("unregistered family")
    return ("NATIVE", "IPM", "ASSIGNMENT", "ORACLE") if family == "assignment" else ("NATIVE", "IPM", "ORACLE")


def schedule():
    rows = [(s["id"], route, repeat) for s in specs() for route in routes(s["family"])
            for repeat in (-1, 0, 1, 2)]
    warm = [r for r in rows if r[2] == -1]
    timed = [r for r in rows if r[2] >= 0]
    rng = random.Random(104991)
    rng.shuffle(warm); rng.shuffle(timed)
    return warm + timed


def summarize(records, cold_ms):
    if [(r["case_id"], r["route"], r["repeat"]) for r in records] != schedule():
        raise ValueError("first transfer coverage/order drift")
    if set(cold_ms) != {"NATIVE", "IPM", "ASSIGNMENT", "ORACLE"}:
        raise ValueError("missing cold route")
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in cold_ms.values()):
        raise ValueError("invalid cold cost")
    for row in records:
        if (type(row["total_ms"]) not in (int, float) or not math.isfinite(row["total_ms"])
                or row["total_ms"] <= 0 or type(row["accepted"]) is not bool
                or row["accounted"] is not True):
            raise ValueError("unverified/unaccounted transfer record")
    cases, cells, decisions = [], [], {}
    for s in specs():
        by_route = {}
        for route in routes(s["family"]):
            selected = [r for r in records if r["case_id"] == s["id"] and r["route"] == route]
            timed = [r["total_ms"] for r in selected if r["repeat"] >= 0]
            charge = 0 if route == "ORACLE" else cold_ms[route] / 10000
            by_route[route] = {"capable": all(r["accepted"] for r in selected),
                "complete_ms": median(timed) + charge,
                "q1_ms": median(timed) + (0 if route == "ORACLE" else cold_ms[route])}
        capable = all(r["capable"] for r in by_route.values())
        direct = min(r["complete_ms"] for name, r in by_route.items() if name != "ORACLE")
        ratio = by_route["ORACLE"]["complete_ms"] / direct if capable else None
        cases.append({**s, "routes": by_route, "capable": capable, "ratio": ratio,
                      "best_declared_direct_ms": direct if capable else None})
    for family in FAMILIES:
        current = []
        for level in LEVELS:
            group = [r for r in cases if r["family"] == family and r["level"] == level]
            capable = all(r["capable"] for r in group)
            ratio = (sum(r["routes"]["ORACLE"]["complete_ms"] for r in group)
                     / sum(r["best_declared_direct_ms"] for r in group)) if capable else None
            wins = sum(r["ratio"] is not None and r["ratio"] <= .8 for r in group)
            passed = bool(capable and ratio <= (1.2 if level == 8 else .8)
                          and (level == 8 or wins >= 3))
            cell = {"family": family, "level": level, "capable": capable,
                    "ratio": ratio, "wins": wins, "passed": passed}
            cells.append(cell); current.append(cell)
        decisions[family] = ("CAPABILITY_UNREACHED_NO_TRANSFER_BUDGET"
            if not all(r["capable"] for r in current) else
            "ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING" if all(r["passed"] for r in current)
            else "STOP_FAMILY_NO_ORACLE_HEADROOM")
    return {"decisions": decisions, "cells": cells, "cases": cases,
        "observations": len(records), "failed_observations": sum(not r["accepted"] for r in records),
        "model_forwards": 0, "new_fitting": False, "global_q5_closed": False,
        "cross_domain_pass": False, "evidence_scope": protocol()["scope"]}
