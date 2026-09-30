"""Observable-only classical discovery; no oracle input or learned model."""
from __future__ import annotations
import hashlib
import math
import platform
import random
import warnings
from statistics import geometric_mean, median
from time import perf_counter_ns
import numpy as np
import scipy
from scipy.optimize import linprog, OptimizeWarning
import threadpoolctl
from threadpoolctl import threadpool_limits
from . import lp_basis_headroom_v082 as base
from .lp_certificate_v081 import verify_standard_form_certificate

REPEATS, ORDER_SEED, SEED_BASE = 3, 83991, 83100
FORMS = ("raw", "normalized")
ROUTES = (*base.DIRECT_METHODS, "norm_discovery")


def direct_once(raw, method):
    if method not in base.DIRECT_METHODS:
        raise ValueError("undeclared native method")
    start = perf_counter_ns()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Unrecognized options detected:.*", category=OptimizeWarning)
            result = linprog(raw['c'], A_eq=raw['A'], b_eq=raw['b'], bounds=(0, None),
                             method=method, options={'presolve': True, 'time_limit': 5.,
                                                     'threads': 1, 'parallel': False})
        solve_ms = base._elapsed_ms(start)
        check_start = perf_counter_ns()
        certificate = (verify_standard_form_certificate(raw['A'], raw['b'], raw['c'],
                        result.x, result.eqlin.marginals) if result.success else None)
        verify_ms = base._elapsed_ms(check_start)
        return {'path': 'direct', 'method': method, 'accepted': bool(certificate and certificate['accepted']),
                'solver_success': bool(result.success), 'solver_status': int(result.status),
                'solve_ms': solve_ms, 'verify_ms': verify_ms, 'total_ms': base._elapsed_ms(start),
                'certificate': certificate, 'error': None}
    except Exception as exc:
        return {'path': 'direct', 'method': method, 'accepted': False, 'solver_success': False,
                'solver_status': None, 'solve_ms': None, 'verify_ms': None,
                'total_ms': base._elapsed_ms(start), 'certificate': None,
                'error': f'{type(exc).__name__}: {exc}'}


def specifications():
    result = []
    for old in base.specifications():
        spec = {**old, "seed": old["seed"] - base.SEED_BASE + SEED_BASE}
        for form in FORMS:
            result.append({**spec, "id": spec["id"] + "_" + form, "form": form})
    return tuple(result)


def generate_case(spec):
    original = {k: v for k, v in spec.items() if k != "form"}
    original["id"] = original["id"].removesuffix("_" + spec["form"])
    generated = base.generate_case(original)
    A, b, c = generated["A"], generated["b"], generated["c"]
    if spec["form"] == "normalized":
        lengths = np.linalg.norm(A, axis=0)
        if np.any(lengths <= 0):
            raise ValueError("zero source column")
        A, c = A / lengths, c / lengths
    elif spec["form"] != "raw":
        raise ValueError("undeclared form")
    digest = hashlib.sha256(''.join(base._array_digest(a) for a in (A, b, c)).encode()).hexdigest()
    return {"A": A, "b": b, "c": c}, digest


def propose(A, b, c):
    """Only received coefficients; stable tie-breaking, no generator metadata."""
    m, n = A.shape
    if n < m or b.shape != (m,) or c.shape != (n,):
        raise ValueError("invalid standard-form dimensions")
    if not all(np.all(np.isfinite(a)) for a in (A, b, c)):
        raise ValueError("non-finite received coefficients")
    norms = np.linalg.norm(A, axis=0)
    order = np.argsort(norms, kind="stable")
    sorted_norms = norms[order]
    width = sorted_norms[m - 1:] - sorted_norms[:n - m + 1]
    start = int(np.argmin(width))
    result, seen = [], set()
    for name, indices in (("tight_norm_window", order[start:start + m]),
                          ("smallest_norm", order[:m])):
        identity = tuple(sorted(map(int, indices)))
        if identity not in seen:
            result.append((name, np.asarray(identity, dtype=np.int64)))
            seen.add(identity)
    return result


def discovery_once(A, b, c):
    start = perf_counter_ns()
    raw = {"A": A, "b": b, "c": c}
    discover_start = perf_counter_ns()
    proposals = propose(A, b, c)
    discovery_ms = base._elapsed_ms(discover_start)
    attempts = []
    for name, indices in proposals:
        attempt = base.oracle_basis_once(raw, indices)
        attempt.update(path="basis_candidate", method=name, indices=indices.tolist())
        if attempt["error"]:
            for key in ("extract_ms", "factor_solve_ms", "reconstruct_ms", "verify_ms"):
                attempt[key] = None  # failed-stage split unavailable; full total retained
        attempts.append(attempt)
        if attempt["accepted"]:
            return {"path": "norm_discovery", "accepted": True, "fallback_used": False,
                    "discovery_ms": discovery_ms, "attempts": attempts, "fallback": None,
                    "certificate": attempt["certificate"], "total_ms": base._elapsed_ms(start)}
    fallback = direct_once(raw, "highs")
    return {"path": "norm_discovery", "accepted": fallback["accepted"], "fallback_used": True,
            "discovery_ms": discovery_ms, "attempts": attempts, "fallback": fallback,
            "certificate": fallback["certificate"], "total_ms": base._elapsed_ms(start)}


def observe(raw, route):
    if route == "norm_discovery":
        return discovery_once(raw["A"], raw["b"], raw["c"])
    return direct_once(raw, route)


def summarize(records, warmups):
    specs = specifications()
    for observations, timed in ((records, True), (warmups, False)):
        expected = {(s["id"], r, i) for s in specs for r in ROUTES
                    for i in (range(REPEATS) if timed else (-1,))}
        seen = set()
        for row in observations:
            i = row["repeat"] if timed else -1
            key = (row["case_id"], row["route_id"], i)
            if type(i) is not int or key not in expected or key in seen:
                raise ValueError("observation identity drift")
            if type(row["accepted"]) is not bool or type(row["total_ms"]) not in (int, float):
                raise ValueError("invalid observation")
            if not math.isfinite(row["total_ms"]) or row["total_ms"] <= 0:
                raise ValueError("invalid complete cost")
            seen.add(key)
        if seen != expected:
            raise ValueError("incomplete coverage")
    warm = {(r["case_id"], r["route_id"]): r for r in warmups}
    cells = []
    for spec in specs:
        groups = {route: [r for r in records if r["case_id"] == spec["id"] and r["route_id"] == route]
                  for route in ROUTES}
        eligible = {r: median(x["total_ms"] for x in groups[r]) for r in ROUTES
                    if warm[(spec["id"], r)]["accepted"] and all(x["accepted"] for x in groups[r])}
        native = {r: v for r, v in eligible.items() if r != "norm_discovery"}
        if not native or "norm_discovery" not in eligible:
            cells.append({"case_id": spec["id"], "ratio": None})
            continue
        fastest = min(native, key=native.get)
        no_fallback = not any(r["fallback_used"] for r in
                             [warm[(spec["id"], "norm_discovery")], *groups["norm_discovery"]])
        cells.append({"case_id": spec["id"], "form": spec["form"],
                      "width_factor": spec["width_factor"], "best_native": fastest,
                      "native_ms": native[fastest], "discovery_ms": eligible["norm_discovery"],
                      "ratio": eligible["norm_discovery"] / native[fastest],
                      "no_fallback": no_fallback})
    result = {"q3": "OPEN", "q4": "OPEN", "cells": cells}
    if any(c["ratio"] is None for c in cells):
        return {**result, "decision": "CAPABILITY_UNREACHED"}
    forms = {}
    for form in FORMS:
        expanded = [c for c in cells if c["form"] == form and c["width_factor"] == 16]
        ratio = geometric_mean(c["ratio"] for c in expanded)
        wins = sum(c["ratio"] <= .8 for c in expanded)
        independent = sum(c["no_fallback"] for c in expanded)
        forms[form] = {"geomean_ratio": ratio, "twenty_percent_wins": wins,
                       "no_fallback_cases": independent,
                       "gate_pass": ratio <= .5 and wins >= 8 and independent >= 8}
    return {**result, "forms": forms,
            "normalization_sensitive": forms["raw"]["gate_pass"] and not forms["normalized"]["gate_pass"],
            "decision": "CHEAP_DISCOVERY_CONSUMES_RAW_FAMILY_HEADROOM" if forms["raw"]["gate_pass"]
            else "RESIDUAL_HEADROOM_UNRESOLVED"}


def protocol():
    return {"seed_base": SEED_BASE, "order_seed": ORDER_SEED, "repeats": REPEATS,
            "forms": list(FORMS), "routes": list(ROUTES), "runtime": base.protocol()["runtime"],
            "proposal_order": ["tight_norm_window", "smallest_norm"], "fallback": "highs",
            "native_threads": 1, "native_parallel": False,
            "geomean_max": .5, "ratio_win": .8, "min_wins": 8, "min_no_fallback": 8}


def run_audit():
    env = base.single_thread_environment()
    versions = {"python_major_minor": list(map(int, platform.python_version_tuple()[:2])),
                "numpy": np.__version__, "scipy": scipy.__version__,
                "threadpoolctl": threadpoolctl.__version__}
    if not env["declared_single_thread"] or versions != protocol()["runtime"]:
        raise RuntimeError("frozen runtime/thread boundary drift")
    records, warmups, sources = [], [], []
    with threadpool_limits(limits=1):
        for spec in specifications():
            started = perf_counter_ns()
            raw, digest = generate_case(spec)
            sources.append({**spec, "raw_sha256": digest, "setup_ms": base._elapsed_ms(started)})
            for route in ROUTES:
                warmups.append({"case_id": spec["id"], "route_id": route, **observe(raw, route)})
            schedule = [(r, i) for r in ROUTES for i in range(REPEATS)]
            random.Random(ORDER_SEED + spec["seed"] + spec["width_factor"] + FORMS.index(spec["form"])).shuffle(schedule)
            for route, repeat in schedule:
                records.append({"case_id": spec["id"], "route_id": route, "repeat": repeat,
                                **observe(raw, route)})
    return {"experiment": "v0.0.83 observable-only norm discovery", "protocol": protocol(),
            "environment": {**env, **versions, "platform": platform.platform()},
            "sources": sources, "warmups": warmups, "records": records,
            "summary": summarize(records, warmups)}


def validate_archive(report):
    if report["protocol"] != protocol() or not report["environment"]["declared_single_thread"]:
        raise ValueError("protocol/thread drift")
    if any(report["environment"][k] != v for k, v in protocol()["runtime"].items()):
        raise ValueError("runtime drift")
    if len(report["sources"]) != len(specifications()):
        raise ValueError("source count drift")
    for source, spec in zip(report["sources"], specifications()):
        if any(source[k] != v for k, v in spec.items()):
            raise ValueError("source specification drift")
        if generate_case(spec)[1] != source["raw_sha256"]:
            raise ValueError("source hash drift")
    for row in [*report["warmups"], *report["records"]]:
        if row["accepted"] and not (isinstance(row["certificate"], dict) and row["certificate"].get("accepted") is True):
            raise ValueError("unverified acceptance")
        if row["route_id"] == "norm_discovery":
            stages = row["discovery_ms"] + sum(a["total_ms"] for a in row["attempts"])
            if row["fallback_used"]:
                stages += row["fallback"]["total_ms"]
            elif row["fallback"] is not None:
                raise ValueError("fallback drift")
            if row["total_ms"] < stages:
                raise ValueError("omitted attempt/fallback cost")
        elif row["error"] is None and row["total_ms"] < row["solve_ms"] + row["verify_ms"]:
            raise ValueError("omitted Direct cost")
    if summarize(report["records"], report["warmups"]) != report["summary"]:
        raise ValueError("summary drift")
