"""v0.0.82 constructed oracle-basis complete-cost headroom screen.

Protocol frozen before formal implementation/timing:
docs/experiments/v0.0.82.md @ 9d4baa434d9c97738603470653f899d360c57890

This is a non-blind constructed development screen.  It measures whether a
free optimal-basis oracle leaves enough *complete verified* cost headroom to
justify any later basis-discovery work.  It is not learned inference and does
not close Q3/Q4.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import random
from statistics import median
from time import perf_counter_ns
from typing import Any

import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.optimize._highspy import _core as _highs_core
from threadpoolctl import threadpool_limits

from neumann1.lp_certificate_v081 import verify_standard_form_certificate


PROTOCOL_COMMIT = "9d4baa434d9c97738603470653f899d360c57890"
ROWS = (16, 32, 64, 128)
RATIOS = (4, 16, 64)
REPEATS = 3
FIRST_SEED = 8201
SCHEDULE_SEED = 8291
TIME_LIMIT_S = 5.0
ROUTES = ("direct_highs", "direct_highs_ds", "direct_highs_ipm", "oracle_basis")
DIRECT_ROUTES = ROUTES[:3]


def specifications() -> tuple[dict, ...]:
    cells = []
    seed = FIRST_SEED
    for rows in ROWS:
        for ratio in RATIOS:
            cells.append(
                {
                    "id": f"m{rows}_r{ratio}",
                    "rows": rows,
                    "ratio": ratio,
                    "cols": rows * ratio,
                    "seed": seed,
                }
            )
            seed += 1
    return tuple(cells)


def _digest_array(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    payload = (
        str(array.dtype).encode()
        + b"|"
        + json.dumps(array.shape).encode()
        + b"|"
        + array.tobytes()
    )
    return hashlib.sha256(payload).hexdigest()


def generate_case(spec: dict) -> dict:
    expected = {s["id"]: s for s in specifications()}
    if spec.get("id") not in expected or spec != expected[spec["id"]]:
        raise ValueError("outside frozen v0.0.82 generator")

    m, n = spec["rows"], spec["cols"]
    rng = np.random.default_rng(spec["seed"])

    gaussian = rng.normal(size=(m, m))
    q, _ = np.linalg.qr(gaussian)

    matrix = np.empty((m, n), dtype=np.float64)
    matrix[:, :m] = q
    matrix[:, m:] = rng.normal(size=(m, n - m)) / math.sqrt(m)

    permutation = rng.permutation(n)
    matrix = matrix[:, permutation]
    basis = np.flatnonzero(permutation < m).astype(np.int64)

    planted_x = np.zeros(n, dtype=np.float64)
    planted_x[basis] = rng.uniform(0.5, 1.5, size=m)
    rhs = matrix @ planted_x

    planted_y = rng.normal(size=m)
    slack = rng.uniform(0.25, 2.0, size=n)
    slack[basis] = 0.0
    cost = matrix.T @ planted_y + slack

    planted_certificate = verify_standard_form_certificate(
        matrix, rhs, cost, planted_x, planted_y
    )
    if not planted_certificate["accepted"]:
        raise ValueError("constructed source failed its own original-LP certificate")

    return {
        "A": matrix,
        "b": rhs,
        "c": cost,
        "basis": basis,
        "planted_certificate": planted_certificate,
    }


def source_identity(case: dict) -> dict:
    return {
        "A_sha256": _digest_array(case["A"]),
        "b_sha256": _digest_array(case["b"]),
        "c_sha256": _digest_array(case["c"]),
        "basis_sha256": _digest_array(case["basis"]),
    }


def _direct_method(route: str) -> str:
    methods = {
        "direct_highs": "highs",
        "direct_highs_ds": "highs-ds",
        "direct_highs_ipm": "highs-ipm",
    }
    if route not in methods:
        raise ValueError("not a Direct route")
    return methods[route]


def observe(case: dict, spec: dict, route: str) -> dict:
    if route not in ROUTES:
        raise ValueError("undeclared v0.0.82 route")

    start = perf_counter_ns()
    solve_start = start
    error = None
    solver_status = None
    solver_message = None
    solver_nit = None
    x = y = None

    try:
        if route in DIRECT_ROUTES:
            result = linprog(
                case["c"],
                A_eq=case["A"],
                b_eq=case["b"],
                bounds=(0, None),
                method=_direct_method(route),
                options={"time_limit": TIME_LIMIT_S},
            )
            solver_status = int(result.status)
            solver_message = str(result.message)
            solver_nit = None if result.nit is None else int(result.nit)
            if not result.success or result.x is None:
                raise RuntimeError(f"HiGHS did not return an accepted optimum: {result.message}")
            marginals = getattr(getattr(result, "eqlin", None), "marginals", None)
            if marginals is None:
                raise RuntimeError("HiGHS equality dual marginals unavailable")
            x = np.asarray(result.x, dtype=np.float64)
            y = np.asarray(marginals, dtype=np.float64)
        else:
            basis = case["basis"]
            basis_matrix = case["A"][:, basis]
            basic_x = np.linalg.solve(basis_matrix, case["b"])
            y = np.linalg.solve(basis_matrix.T, case["c"][basis])
            x = np.zeros(spec["cols"], dtype=np.float64)
            x[basis] = basic_x
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    solve_ms = (perf_counter_ns() - solve_start) / 1e6

    certificate = None
    verify_ms = None
    if error is None:
        verify_start = perf_counter_ns()
        try:
            certificate = verify_standard_form_certificate(
                case["A"], case["b"], case["c"], x, y
            )
            if not certificate["accepted"]:
                raise ValueError("original-LP certificate rejected route output")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        verify_ms = (perf_counter_ns() - verify_start) / 1e6

    total_ms = (perf_counter_ns() - start) / 1e6
    accepted = bool(
        error is None
        and certificate is not None
        and certificate["accepted"]
    )

    return {
        "case_id": spec["id"],
        "route": route,
        "accepted": accepted,
        "error": error,
        "solver_status": solver_status,
        "solver_message": solver_message,
        "solver_nit": solver_nit,
        "solve_ms": solve_ms,
        "verify_ms": verify_ms,
        "total_ms": total_ms,
        "certificate": certificate,
    }


def _geometric_mean(values: list[float]) -> float:
    if not values or any(v <= 0 or not math.isfinite(v) for v in values):
        raise ValueError("geometric mean requires positive finite values")
    return math.exp(sum(math.log(v) for v in values) / len(values))


def summarize(rows: list[dict], warmups: list[dict]) -> dict:
    expected_rows = {
        (s["id"], route, repeat)
        for s in specifications()
        for route in ROUTES
        for repeat in range(REPEATS)
    }
    seen_rows = []
    for row in rows:
        key = (row.get("case_id"), row.get("route"), row.get("repeat"))
        seen_rows.append(key)
    if (
        len(seen_rows) != len(expected_rows)
        or len(set(seen_rows)) != len(expected_rows)
        or set(seen_rows) != expected_rows
    ):
        raise ValueError("timed observation coverage drift")

    expected_warmups = {
        (s["id"], route) for s in specifications() for route in ROUTES
    }
    warm_ids = [(w.get("case_id"), w.get("route")) for w in warmups]
    if (
        len(warm_ids) != len(expected_warmups)
        or len(set(warm_ids)) != len(expected_warmups)
        or set(warm_ids) != expected_warmups
    ):
        raise ValueError("warmup coverage drift")

    if not all(bool(r.get("accepted")) for r in rows + warmups):
        return {
            "decision": "CAPABILITY_UNREACHED",
            "timed_observations": len(rows),
            "accepted_timed": sum(bool(r.get("accepted")) for r in rows),
            "warmups": len(warmups),
            "accepted_warmups": sum(bool(r.get("accepted")) for r in warmups),
            "q3": "OPEN",
            "q4": "OPEN",
        }

    cells = []
    ratios = []
    win_cases = 0
    for spec in specifications():
        route_medians = {}
        for route in ROUTES:
            values = [
                r["total_ms"]
                for r in rows
                if r["case_id"] == spec["id"] and r["route"] == route
            ]
            route_medians[route] = median(values)
        direct_best_route = min(DIRECT_ROUTES, key=route_medians.__getitem__)
        direct_best_ms = route_medians[direct_best_route]
        oracle_ms = route_medians["oracle_basis"]
        ratio = oracle_ms / direct_best_ms
        ratios.append(ratio)
        if ratio <= 0.8:
            win_cases += 1
        cells.append(
            {
                "case_id": spec["id"],
                "rows": spec["rows"],
                "cols": spec["cols"],
                "ratio": spec["ratio"],
                "route_medians_ms": route_medians,
                "posthoc_fastest_direct_route": direct_best_route,
                "posthoc_fastest_direct_ms": direct_best_ms,
                "oracle_basis_ms": oracle_ms,
                "oracle_over_posthoc_fastest_direct": ratio,
            }
        )

    geometric_ratio = _geometric_mean(ratios)
    passed = geometric_ratio <= 0.8 and win_cases >= 8
    return {
        "decision": (
            "CONSTRUCTED_ORACLE_BASIS_HEADROOM_PRESENT"
            if passed
            else "REJECT_BASIS_DISCOVERY_TRAINING_ON_V082_FAMILY"
        ),
        "timed_observations": len(rows),
        "accepted_timed": len(rows),
        "warmups": len(warmups),
        "accepted_warmups": len(warmups),
        "geometric_mean_oracle_over_posthoc_fastest_direct": geometric_ratio,
        "twenty_percent_win_cases": win_cases,
        "required_win_cases": 8,
        "cells": cells,
        "q3": "OPEN",
        "q4": "OPEN",
    }


def run_audit(*, implementation_commit: str) -> dict:
    if not isinstance(implementation_commit, str) or len(implementation_commit) != 40:
        raise ValueError("exact 40-character implementation commit required")

    setups = []
    warmups = []
    rows = []

    with threadpool_limits(limits=1):
        for case_index, spec in enumerate(specifications()):
            setup_start = perf_counter_ns()
            case = generate_case(spec)
            setup_ms = (perf_counter_ns() - setup_start) / 1e6
            setups.append(
                {
                    **spec,
                    "setup_ms": setup_ms,
                    "source_identity": source_identity(case),
                    "planted_certificate_accepted": bool(
                        case["planted_certificate"]["accepted"]
                    ),
                }
            )

            for route in ROUTES:
                warmups.append(observe(case, spec, route))

            schedule = [
                (route, repeat)
                for route in ROUTES
                for repeat in range(REPEATS)
            ]
            random.Random(SCHEDULE_SEED + case_index).shuffle(schedule)
            for route, repeat in schedule:
                record = observe(case, spec, route)
                record["repeat"] = repeat
                rows.append(record)

    return {
        "experiment": "v0.0.82 constructed oracle-basis complete-cost headroom",
        "protocol_commit": PROTOCOL_COMMIT,
        "implementation_commit": implementation_commit,
        "summary": summarize(rows, warmups),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "highs": (
                f"{_highs_core.HIGHS_VERSION_MAJOR}."
                f"{_highs_core.HIGHS_VERSION_MINOR}."
                f"{_highs_core.HIGHS_VERSION_PATCH}"
            ),
        },
        "platform": platform.platform(),
        "protocol": {
            "rows": list(ROWS),
            "ratios": list(RATIOS),
            "repeats": REPEATS,
            "first_seed": FIRST_SEED,
            "schedule_seed": SCHEDULE_SEED,
            "time_limit_s": TIME_LIMIT_S,
            "routes": list(ROUTES),
        },
        "setups": setups,
        "warmups": warmups,
        "rows": rows,
        "source": (
            "Author-generated constructed development data; non-blind family "
            "selection; no learned model and no independent natural-workload claim."
        ),
    }


def validate_archive(report: dict) -> None:
    if report.get("protocol_commit") != PROTOCOL_COMMIT:
        raise ValueError("protocol commit drift")
    if report.get("protocol") != {
        "rows": list(ROWS),
        "ratios": list(RATIOS),
        "repeats": REPEATS,
        "first_seed": FIRST_SEED,
        "schedule_seed": SCHEDULE_SEED,
        "time_limit_s": TIME_LIMIT_S,
        "routes": list(ROUTES),
    }:
        raise ValueError("protocol drift")

    specs = specifications()
    setups = report.get("setups", [])
    if len(setups) != len(specs):
        raise ValueError("setup coverage drift")
    by_id = {s["id"]: s for s in specs}
    for setup in setups:
        spec = by_id.get(setup.get("id"))
        if spec is None or any(setup.get(k) != v for k, v in spec.items()):
            raise ValueError("setup specification drift")
        case = generate_case(spec)
        if setup.get("source_identity") != source_identity(case):
            raise ValueError("source identity drift")
        if setup.get("planted_certificate_accepted") is not True:
            raise ValueError("invalid constructed source")

    expected_summary = summarize(report.get("rows", []), report.get("warmups", []))
    if report.get("summary") != expected_summary:
        raise ValueError("summary drift")

    for record in report.get("rows", []) + report.get("warmups", []):
        if not isinstance(record.get("accepted"), bool):
            raise ValueError("invalid acceptance flag")
        for field in ("solve_ms", "total_ms"):
            value = record.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid charged time")
        verify_ms = record.get("verify_ms")
        if verify_ms is not None and (
            type(verify_ms) not in (int, float)
            or not math.isfinite(verify_ms)
            or verify_ms < 0
        ):
            raise ValueError("invalid verifier time")
        if record["total_ms"] < record["solve_ms"]:
            raise ValueError("total time smaller than route solve work")
        if record["accepted"]:
            cert = record.get("certificate")
            if not isinstance(cert, dict) or cert.get("accepted") is not True:
                raise ValueError("accepted route without accepted certificate")
