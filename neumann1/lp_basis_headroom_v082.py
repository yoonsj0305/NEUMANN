"""v0.0.82: zero-model basis-support headroom screen for constructed LPs.

The exact optimal basis is supplied only to a non-deployable diagnostic path.
This version measures maximum mechanism headroom before any model training.
A positive result is not Q3/Q4 and is not evidence of learnability.
"""
from __future__ import annotations

import hashlib
import json
import platform
import random
from statistics import mean, median
from time import perf_counter_ns
from typing import Any

import numpy as np
import scipy
from scipy.optimize import linprog

from neumann1.lp_certificate_v081 import verify_standard_form_certificate


DIRECT_POLICIES = ("highs", "highs-ds", "highs-ipm")
POLICIES = DIRECT_POLICIES + ("oracle_basis",)
REPEATS = 5
ORDER_SEED = 8291
TIME_LIMIT_S = 10.0
MIN_WIN_CASES = 9
MAX_RATIO = 0.80
GENERATOR_VERSION = "v082.dense-planted-basis.v1"


def specifications() -> tuple[dict, ...]:
    dims = (
        (16, 256),
        (16, 1024),
        (32, 512),
        (32, 2048),
        (64, 1024),
        (64, 4096),
    )
    return tuple(
        {
            "id": f"lp_{rows:03d}x{cols:04d}_r{replicate}",
            "rows": rows,
            "cols": cols,
            "seed": 8201 + i * 2 + replicate,
        }
        for i, (rows, cols) in enumerate(dims)
        for replicate in range(2)
    )


def array_digest(value: Any) -> str:
    arr = np.ascontiguousarray(np.asarray(value))
    meta = json.dumps(
        {"shape": arr.shape, "dtype": str(arr.dtype)}, separators=(",", ":")
    ).encode()
    return hashlib.sha256(meta + arr.tobytes()).hexdigest()


def generate(spec: dict) -> dict:
    if spec not in specifications():
        raise ValueError("outside frozen v0.0.82 specification")
    rows, cols, seed = spec["rows"], spec["cols"], spec["seed"]
    rng = np.random.default_rng(seed)

    # Stable planted basis, then hide its positions by a random permutation.
    q, _ = np.linalg.qr(rng.normal(size=(rows, rows)))
    matrix = np.empty((rows, cols), dtype=np.float64)
    matrix[:, :rows] = q
    matrix[:, rows:] = rng.normal(size=(rows, cols - rows)) / np.sqrt(rows)
    permutation = rng.permutation(cols)
    matrix = matrix[:, permutation]
    basis = np.flatnonzero(permutation < rows).astype(np.int64)

    primal = np.zeros(cols, dtype=np.float64)
    primal[basis] = rng.uniform(0.5, 1.5, size=rows)
    rhs = matrix @ primal

    dual = rng.normal(size=rows)
    reduced_cost = rng.uniform(0.25, 2.0, size=cols)
    reduced_cost[basis] = 0.0
    cost = matrix.T @ dual + reduced_cost

    planted = verify_standard_form_certificate(matrix, rhs, cost, primal, dual)
    if not planted["accepted"]:
        raise ValueError("generator produced invalid planted certificate")

    return {
        "A": matrix,
        "b": rhs,
        "c": cost,
        "basis": basis,
        "planted_x": primal,
        "planted_y": dual,
    }


def _failure(policy: str, start_ns: int, exc: Exception) -> dict:
    return {
        "policy": policy,
        "accepted": False,
        "error": f"{type(exc).__name__}: {exc}",
        "solve_ms": None,
        "verify_ms": None,
        "total_ms": (perf_counter_ns() - start_ns) / 1e6,
        "objective": None,
        "certificate": None,
    }


def observe_direct(case: dict, policy: str) -> dict:
    if policy not in DIRECT_POLICIES:
        raise ValueError("undeclared direct policy")
    start = perf_counter_ns()
    try:
        solve_start = perf_counter_ns()
        result = linprog(
            case["c"],
            A_eq=case["A"],
            b_eq=case["b"],
            bounds=(0.0, None),
            method=policy,
            options={"presolve": True, "time_limit": TIME_LIMIT_S},
        )
        solve_ms = (perf_counter_ns() - solve_start) / 1e6
        if not result.success or result.x is None or result.eqlin.marginals is None:
            raise RuntimeError(
                f"HiGHS status={result.status} success={result.success}: {result.message}"
            )
        x = np.asarray(result.x, dtype=np.float64)
        y = np.asarray(result.eqlin.marginals, dtype=np.float64)

        verify_start = perf_counter_ns()
        certificate = verify_standard_form_certificate(
            case["A"], case["b"], case["c"], x, y
        )
        verify_ms = (perf_counter_ns() - verify_start) / 1e6
        if not certificate["accepted"]:
            raise RuntimeError("original LP certificate rejected")

        return {
            "policy": policy,
            "accepted": True,
            "error": None,
            "solve_ms": solve_ms,
            "verify_ms": verify_ms,
            "total_ms": (perf_counter_ns() - start) / 1e6,
            "objective": certificate["primal_objective"],
            "nit": int(result.nit),
            "certificate": certificate,
        }
    except Exception as exc:
        return _failure(policy, start, exc)


def observe_oracle(case: dict) -> dict:
    """Diagnostic lower bound with the exact basis supplied at zero discovery cost."""
    start = perf_counter_ns()
    try:
        solve_start = perf_counter_ns()
        basis = case["basis"]
        basis_matrix = np.asarray(case["A"][:, basis], dtype=np.float64)

        basic_x = np.linalg.solve(basis_matrix, case["b"])
        x = np.zeros(case["A"].shape[1], dtype=np.float64)
        x[basis] = basic_x
        y = np.linalg.solve(basis_matrix.T, case["c"][basis])
        solve_ms = (perf_counter_ns() - solve_start) / 1e6

        verify_start = perf_counter_ns()
        certificate = verify_standard_form_certificate(
            case["A"], case["b"], case["c"], x, y
        )
        verify_ms = (perf_counter_ns() - verify_start) / 1e6
        if not certificate["accepted"]:
            raise RuntimeError("oracle basis failed original LP certificate")

        return {
            "policy": "oracle_basis",
            "accepted": True,
            "error": None,
            "solve_ms": solve_ms,
            "verify_ms": verify_ms,
            "total_ms": (perf_counter_ns() - start) / 1e6,
            "objective": certificate["primal_objective"],
            "basis_size": int(basis.size),
            "certificate": certificate,
        }
    except Exception as exc:
        return _failure("oracle_basis", start, exc)


def observe(case: dict, policy: str) -> dict:
    return observe_oracle(case) if policy == "oracle_basis" else observe_direct(case, policy)


def summarize(rows: list[dict]) -> dict:
    expected = {
        (spec["id"], policy, repeat)
        for spec in specifications()
        for policy in POLICIES
        for repeat in range(REPEATS)
    }
    seen = set()
    for row in rows:
        key = (row["case_id"], row["policy"], row["repeat"])
        if key not in expected or key in seen:
            raise ValueError("observation coverage/identity error")
        seen.add(key)
    if seen != expected:
        raise ValueError("all v0.0.82 timed observations required")

    if not all(row["accepted"] for row in rows):
        return {
            "decision": "CAPABILITY_UNREACHED",
            "accepted": sum(row["accepted"] for row in rows),
            "observations": len(rows),
            "q3": "OPEN",
            "q4": "OPEN",
        }

    cells = []
    for spec in specifications():
        totals = {
            policy: median(
                row["total_ms"]
                for row in rows
                if row["case_id"] == spec["id"] and row["policy"] == policy
            )
            for policy in POLICIES
        }
        cells.append({
            "case_id": spec["id"],
            "total_medians_ms": totals,
            "direct_per_case_oracle_ms": min(totals[p] for p in DIRECT_POLICIES),
            "oracle_basis_ms": totals["oracle_basis"],
        })

    fixed_direct_means = {
        policy: mean(cell["total_medians_ms"][policy] for cell in cells)
        for policy in DIRECT_POLICIES
    }
    strongest_fixed = min(fixed_direct_means, key=fixed_direct_means.get)
    direct_oracle_mean = mean(cell["direct_per_case_oracle_ms"] for cell in cells)
    oracle_mean = mean(cell["oracle_basis_ms"] for cell in cells)
    ratio = oracle_mean / direct_oracle_mean
    wins = sum(
        cell["oracle_basis_ms"] <= MAX_RATIO * cell["direct_per_case_oracle_ms"]
        for cell in cells
    )
    admit = ratio <= MAX_RATIO and wins >= MIN_WIN_CASES

    return {
        "decision": (
            "MECHANISM_HEADROOM_PRESENT_MODEL_TRAINING_NOT_YET_ADMITTED"
            if admit
            else "REJECT_BASIS_DISCOVERY_TRAINING_ON_THIS_CONSTRUCTED_FAMILY"
        ),
        "observations": len(rows),
        "accepted": len(rows),
        "strongest_fixed_direct": strongest_fixed,
        "fixed_direct_mean_of_case_medians_ms": fixed_direct_means,
        "nondeployable_direct_per_case_oracle_mean_ms": direct_oracle_mean,
        "nondeployable_basis_oracle_mean_ms": oracle_mean,
        "basis_oracle_vs_direct_per_case_oracle_ratio": ratio,
        "twenty_percent_win_cases": wins,
        "required_win_cases": MIN_WIN_CASES,
        "required_ratio": MAX_RATIO,
        "cells": cells,
        "q3": "OPEN",
        "q4": "OPEN",
        "boundary": (
            "Basis/support supplied free only for maximum mechanism headroom; "
            "no learnability, natural incidence, novelty, or deployable speedup follows."
        ),
    }


def run_audit() -> dict:
    specs = specifications()
    cases = {spec["id"]: generate(spec) for spec in specs}
    source, warmups = [], []

    for spec in specs:
        case = cases[spec["id"]]
        source.append({
            **spec,
            "generator_version": GENERATOR_VERSION,
            "sha256": {
                "A": array_digest(case["A"]),
                "b": array_digest(case["b"]),
                "c": array_digest(case["c"]),
                "basis": array_digest(case["basis"]),
            },
        })
        for policy in POLICIES:
            warmups.append({"case_id": spec["id"], **observe(case, policy)})

    schedule = [
        (spec["id"], policy, repeat)
        for spec in specs
        for policy in POLICIES
        for repeat in range(REPEATS)
    ]
    random.Random(ORDER_SEED).shuffle(schedule)

    rows = []
    for case_id, policy, repeat in schedule:
        rows.append({
            "case_id": case_id,
            "repeat": repeat,
            **observe(cases[case_id], policy),
        })

    summary = summarize(rows)
    if not all(row["accepted"] for row in warmups):
        summary = {
            "decision": "CAPABILITY_UNREACHED",
            "warmup_failure": True,
            "q3": "OPEN",
            "q4": "OPEN",
        }

    return {
        "experiment": "v0.0.82 constructed LP zero-model basis headroom",
        "protocol": {
            "repeats": REPEATS,
            "order_seed": ORDER_SEED,
            "time_limit_s": TIME_LIMIT_S,
            "max_ratio": MAX_RATIO,
            "min_win_cases": MIN_WIN_CASES,
            "direct_policies": list(DIRECT_POLICIES),
            "oracle_policy": "oracle_basis",
            "verifier": "neumann.lp-standard-form-certificate.v1",
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "platform": platform.platform(),
        "source": source,
        "warmups": warmups,
        "rows": rows,
        "summary": summary,
    }
