"""v0.0.82: pre-registered zero-discovery LP basis headroom screen.

This module does not train or run a learned model.  It asks whether exact
knowledge of the optimal basis/support has enough complete-path value to
justify spending any later budget on basis discovery.

Both the strongest measured Direct diagnostic and the oracle-basis route pay
the identical v0.0.81 original-LP primal/dual certificate verifier.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import warnings
from statistics import geometric_mean, median
from time import perf_counter_ns
from typing import Any

import numpy as np
import scipy
from scipy.linalg import LinAlgWarning, lu_factor, lu_solve
from scipy.optimize import OptimizeWarning, linprog
import threadpoolctl
from threadpoolctl import threadpool_limits

from neumann1.lp_certificate_v081 import verify_standard_form_certificate


ROWS = (32, 64, 128)
CONDITION_NUMBERS = (1, 1000)
WIDTH_FACTORS = (1, 16)
PAIR_REPLICATES = 2
DIRECT_METHODS = ("highs", "highs-ds", "highs-ipm")
REPEATS = 3
TIME_LIMIT_S = 5.0
ORDER_SEED = 82991
SEED_BASE = 82100

FROZEN_PYTHON_MAJOR_MINOR = (3, 11)
FROZEN_NUMPY_VERSION = "2.4.6"
FROZEN_SCIPY_VERSION = "1.17.1"
FROZEN_THREADPOOLCTL_VERSION = "3.7.0"

EXPANDED_ORACLE_GEOMEAN_MAX = 0.50
TWENTY_PERCENT_RATIO = 0.80
MIN_EXPANDED_TWENTY_PERCENT_WINS = 8
MIN_SCALING_AMPLIFICATION = 2.0
MIN_SCALING_PAIRS = 8

DECISION_ADMIT = "ADMIT_BASIS_DISCOVERY_SEARCH_NOT_MODEL_TRAINING"
DECISION_REJECT = "REJECT_BASIS_DISCOVERY_TRAINING"
DECISION_CAPABILITY = "CAPABILITY_UNREACHED"


def _elapsed_ms(start_ns: int) -> float:
    return (perf_counter_ns() - start_ns) / 1e6


def _array_digest(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    h = hashlib.sha256()
    h.update(str(array.dtype).encode())
    h.update(json.dumps(array.shape).encode())
    h.update(array.tobytes())
    return h.hexdigest()


def specifications() -> tuple[dict, ...]:
    specs = []
    pair_index = 0
    for rows in ROWS:
        for condition in CONDITION_NUMBERS:
            for replicate in range(PAIR_REPLICATES):
                seed = SEED_BASE + pair_index
                pair_id = f"m{rows}_c{condition}_r{replicate}"
                for width_factor in WIDTH_FACTORS:
                    specs.append({
                        "id": f"{pair_id}_w{width_factor}",
                        "pair_id": pair_id,
                        "rows": rows,
                        "width_factor": width_factor,
                        "cols": rows * width_factor,
                        "condition_number": condition,
                        "replicate": replicate,
                        "seed": seed,
                    })
                pair_index += 1
    return tuple(specs)


def _orthogonal(rng: np.random.Generator, n: int) -> np.ndarray:
    q, _ = np.linalg.qr(rng.normal(size=(n, n)))
    return np.asarray(q, dtype=np.float64)


def generate_case(spec: dict) -> dict:
    return _generate_case(spec, ROWS, WIDTH_FACTORS)


def generate_q5_case(spec: dict) -> dict:
    """Same constructed family, on the separately frozen Q5 size/width grid.

    Do not mutate v082 globals or broaden the authority of generate_case.
    """
    return _generate_case(spec, (32, 64, 128, 256), (1, 16, 32))


def _generate_case(spec: dict, rows_grid, width_grid) -> dict:
    """Generate one constructed nondegenerate standard-form LP.

    Control and expanded cases sharing pair_id use the same basis matrix,
    positive basic solution and dual vector.  The expanded case adds strictly
    positive reduced-cost nonbasic columns, then hides basis positions behind
    a random column permutation.  The basis indices are oracle-only metadata.
    """
    required = {
        "id", "pair_id", "rows", "width_factor", "cols",
        "condition_number", "replicate", "seed",
    }
    if set(spec) != required:
        raise ValueError("specification schema drift")
    m = spec["rows"]
    factor = spec["width_factor"]
    n = spec["cols"]
    condition = spec["condition_number"]
    if m not in rows_grid or factor not in width_grid or n != m * factor:
        raise ValueError("outside frozen size grid")
    if condition not in CONDITION_NUMBERS:
        raise ValueError("outside frozen conditioning grid")

    rng = np.random.default_rng(spec["seed"])
    u = _orthogonal(rng, m)
    v = _orthogonal(rng, m)
    singular = np.geomspace(1.0, 1.0 / float(condition), m)
    basis_matrix = (u * singular) @ v.T

    x_basic = rng.uniform(0.5, 1.5, size=m)
    rhs = basis_matrix @ x_basic
    dual = rng.normal(size=m)

    if factor == 1:
        matrix = basis_matrix.copy()
        reduced_slack = np.zeros(m, dtype=np.float64)
    else:
        nonbasic = rng.normal(size=(m, n - m)) / math.sqrt(m)
        matrix = np.concatenate((basis_matrix, nonbasic), axis=1)
        reduced_slack = np.concatenate((
            np.zeros(m, dtype=np.float64),
            rng.uniform(0.25, 2.0, size=n - m),
        ))

    cost = matrix.T @ dual + reduced_slack
    permutation = rng.permutation(n)
    matrix = np.asarray(matrix[:, permutation], dtype=np.float64)
    cost = np.asarray(cost[permutation], dtype=np.float64)
    basis = np.flatnonzero(permutation < m).astype(np.int64)

    if basis.size != m:
        raise AssertionError("basis cardinality drift")

    raw_digest = hashlib.sha256(
        (_array_digest(matrix) + _array_digest(rhs) + _array_digest(cost)).encode()
    ).hexdigest()
    basis_digest = _array_digest(basis)
    latent_pair_digest = hashlib.sha256(
        (
            _array_digest(basis_matrix)
            + _array_digest(x_basic)
            + _array_digest(rhs)
            + _array_digest(dual)
        ).encode()
    ).hexdigest()

    return {
        "spec": dict(spec),
        "A": matrix,
        "b": np.asarray(rhs, dtype=np.float64),
        "c": cost,
        "oracle_basis": basis,
        "raw_observable_sha256": raw_digest,
        "oracle_basis_sha256": basis_digest,
        "latent_pair_sha256": latent_pair_digest,
        "actual_basis_condition": float(np.linalg.cond(matrix[:, basis])),
    }


def direct_once(case: dict, method: str) -> dict:
    if method not in DIRECT_METHODS:
        raise ValueError("undeclared Direct method")
    start = perf_counter_ns()
    solve_start = perf_counter_ns()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"Unrecognized options detected:.*",
                category=OptimizeWarning,
            )
            result = linprog(
                case["c"],
                A_eq=case["A"],
                b_eq=case["b"],
                bounds=(0, None),
                method=method,
                options={
                    "presolve": True,
                    "time_limit": TIME_LIMIT_S,
                    "threads": 1,
                    "parallel": "off",
                },
            )
        solve_ms = _elapsed_ms(solve_start)
        verify_start = perf_counter_ns()
        certificate = None
        if result.success and result.x is not None and result.eqlin.marginals is not None:
            certificate = verify_standard_form_certificate(
                case["A"], case["b"], case["c"],
                result.x, result.eqlin.marginals,
            )
        verify_ms = _elapsed_ms(verify_start)
        accepted = bool(
            result.success
            and certificate is not None
            and certificate["accepted"]
        )
        return {
            "path": "direct",
            "method": method,
            "accepted": accepted,
            "solver_success": bool(result.success),
            "solver_status": int(result.status),
            "solver_message": str(result.message),
            "solve_ms": solve_ms,
            "verify_ms": verify_ms,
            "total_ms": _elapsed_ms(start),
            "objective": (
                float(result.fun)
                if result.success and result.fun is not None and np.isfinite(result.fun)
                else None
            ),
            "certificate": certificate,
            "error": None,
        }
    except Exception as exc:
        return {
            "path": "direct",
            "method": method,
            "accepted": False,
            "solver_success": False,
            "solver_status": None,
            "solver_message": None,
            "solve_ms": _elapsed_ms(solve_start),
            "verify_ms": 0.0,
            "total_ms": _elapsed_ms(start),
            "objective": None,
            "certificate": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _validate_basis(case: dict, basis: Any) -> np.ndarray:
    indices = np.asarray(basis)
    if indices.ndim != 1 or indices.size != case["A"].shape[0]:
        raise ValueError("oracle basis must contain exactly m indices")
    if not np.issubdtype(indices.dtype, np.integer):
        raise ValueError("oracle basis indices must be integers")
    indices = indices.astype(np.int64, copy=False)
    if (
        np.any(indices < 0)
        or np.any(indices >= case["A"].shape[1])
        or np.unique(indices).size != indices.size
    ):
        raise ValueError("oracle basis indices invalid or duplicated")
    return indices


def oracle_basis_once(case: dict, basis: Any) -> dict:
    """Solve only the oracle-supplied basis, then verify the original LP."""
    start = perf_counter_ns()
    try:
        extract_start = perf_counter_ns()
        indices = _validate_basis(case, basis)
        basis_matrix = np.asarray(case["A"][:, indices], dtype=np.float64)
        basis_cost = np.asarray(case["c"][indices], dtype=np.float64)
        extract_ms = _elapsed_ms(extract_start)

        factor_start = perf_counter_ns()
        with warnings.catch_warnings():
            warnings.simplefilter("error", LinAlgWarning)
            lu, piv = lu_factor(basis_matrix, check_finite=False)
        x_basic = lu_solve((lu, piv), case["b"], check_finite=False)
        dual = lu_solve((lu, piv), basis_cost, trans=1, check_finite=False)
        factor_solve_ms = _elapsed_ms(factor_start)

        reconstruct_start = perf_counter_ns()
        primal = np.zeros(case["A"].shape[1], dtype=np.float64)
        primal[indices] = x_basic
        reconstruct_ms = _elapsed_ms(reconstruct_start)

        verify_start = perf_counter_ns()
        certificate = verify_standard_form_certificate(
            case["A"], case["b"], case["c"], primal, dual
        )
        verify_ms = _elapsed_ms(verify_start)
        return {
            "path": "oracle_basis",
            "method": "free_exact_basis",
            "accepted": bool(certificate["accepted"]),
            "extract_ms": extract_ms,
            "factor_solve_ms": factor_solve_ms,
            "reconstruct_ms": reconstruct_ms,
            "verify_ms": verify_ms,
            "total_ms": _elapsed_ms(start),
            "objective": float(case["c"] @ primal),
            "certificate": certificate,
            "error": None,
        }
    except Exception as exc:
        return {
            "path": "oracle_basis",
            "method": "free_exact_basis",
            "accepted": False,
            "extract_ms": 0.0,
            "factor_solve_ms": 0.0,
            "reconstruct_ms": 0.0,
            "verify_ms": 0.0,
            "total_ms": _elapsed_ms(start),
            "objective": None,
            "certificate": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _median_total(records: list[dict]) -> float:
    return float(median(r["total_ms"] for r in records))


def summarize(records: list[dict], warmups: list[dict] | None = None) -> dict:
    expected = {
        (s["id"], path, repeat)
        for s in specifications()
        for path in (*DIRECT_METHODS, "oracle_basis")
        for repeat in range(REPEATS)
    }
    seen = set()
    for row in records:
        identity = (row["case_id"], row["route_id"], row["repeat"])
        if identity not in expected or identity in seen:
            raise ValueError("timed observation identity/coverage error")
        seen.add(identity)
        if (
            type(row["accepted"]) is not bool
            or type(row["total_ms"]) not in (int, float)
            or not np.isfinite(row["total_ms"])
            or row["total_ms"] < 0
        ):
            raise ValueError("invalid timed observation")
    if seen != expected:
        raise ValueError("all frozen timed observations required")

    warmup_map = None
    if warmups is not None:
        warm_expected = {
            (s["id"], path)
            for s in specifications()
            for path in (*DIRECT_METHODS, "oracle_basis")
        }
        warm_ids = [(w["case_id"], w["route_id"]) for w in warmups]
        if (
            len(warm_ids) != len(warm_expected)
            or set(warm_ids) != warm_expected
            or len(set(warm_ids)) != len(warm_ids)
        ):
            raise ValueError("warmup observation identity/coverage error")
        if any(type(w["accepted"]) is not bool for w in warmups):
            raise ValueError("invalid warmup capability flag")
        warmup_map = {
            (w["case_id"], w["route_id"]): w["accepted"] for w in warmups
        }

    cells = []
    for spec in specifications():
        by_method = {}
        for method in DIRECT_METHODS:
            group = [
                r for r in records
                if r["case_id"] == spec["id"] and r["route_id"] == method
            ]
            eligible = (
                len(group) == REPEATS
                and all(r["accepted"] for r in group)
                and (
                    warmup_map is None
                    or warmup_map[(spec["id"], method)]
                )
            )
            by_method[method] = {
                "eligible": eligible,
                "median_total_ms": _median_total(group) if eligible else None,
            }
        eligible_direct = {
            method: data["median_total_ms"]
            for method, data in by_method.items() if data["eligible"]
        }
        oracle_group = [
            r for r in records
            if r["case_id"] == spec["id"] and r["route_id"] == "oracle_basis"
        ]
        oracle_eligible = (
            len(oracle_group) == REPEATS
            and all(r["accepted"] for r in oracle_group)
            and (
                warmup_map is None
                or warmup_map[(spec["id"], "oracle_basis")]
            )
        )
        if not eligible_direct or not oracle_eligible:
            cells.append({
                "case_id": spec["id"],
                "pair_id": spec["pair_id"],
                "width_factor": spec["width_factor"],
                "direct_methods": by_method,
                "oracle_eligible": oracle_eligible,
                "best_direct_method": None,
                "best_direct_median_ms": None,
                "oracle_median_ms": None,
                "oracle_over_best_direct": None,
            })
            continue
        best_method = min(eligible_direct, key=eligible_direct.get)
        best_ms = float(eligible_direct[best_method])
        oracle_ms = _median_total(oracle_group)
        cells.append({
            "case_id": spec["id"],
            "pair_id": spec["pair_id"],
            "width_factor": spec["width_factor"],
            "direct_methods": by_method,
            "oracle_eligible": True,
            "best_direct_method": best_method,
            "best_direct_median_ms": best_ms,
            "oracle_median_ms": oracle_ms,
            "oracle_over_best_direct": oracle_ms / best_ms,
        })

    if any(c["oracle_over_best_direct"] is None for c in cells):
        return {
            "decision": DECISION_CAPABILITY,
            "q3": "OPEN",
            "q4": "OPEN",
            "cells": cells,
        }

    expanded = [c for c in cells if c["width_factor"] == 16]
    expanded_ratios = [c["oracle_over_best_direct"] for c in expanded]
    expanded_geomean = float(geometric_mean(expanded_ratios))
    expanded_wins = sum(r <= TWENTY_PERCENT_RATIO for r in expanded_ratios)

    by_pair = {}
    for cell in cells:
        by_pair.setdefault(cell["pair_id"], {})[cell["width_factor"]] = cell
    scaling = []
    for pair_id, pair in sorted(by_pair.items()):
        if set(pair) != {1, 16}:
            raise ValueError("matched control/expanded pair missing")
        control, wide = pair[1], pair[16]
        direct_growth = wide["best_direct_median_ms"] / control["best_direct_median_ms"]
        oracle_growth = wide["oracle_median_ms"] / control["oracle_median_ms"]
        amplification = direct_growth / oracle_growth
        scaling.append({
            "pair_id": pair_id,
            "direct_width_growth": direct_growth,
            "oracle_width_growth": oracle_growth,
            "structural_scaling_amplification": amplification,
        })
    scaling_pairs = sum(
        s["structural_scaling_amplification"] >= MIN_SCALING_AMPLIFICATION
        for s in scaling
    )

    admit = (
        expanded_geomean <= EXPANDED_ORACLE_GEOMEAN_MAX
        and expanded_wins >= MIN_EXPANDED_TWENTY_PERCENT_WINS
        and scaling_pairs >= MIN_SCALING_PAIRS
    )
    return {
        "decision": DECISION_ADMIT if admit else DECISION_REJECT,
        "q3": "OPEN",
        "q4": "OPEN",
        "expanded_geomean_oracle_over_best_direct": expanded_geomean,
        "expanded_twenty_percent_win_cases": expanded_wins,
        "expanded_case_count": len(expanded),
        "scaling_pairs_ge_2x": scaling_pairs,
        "scaling_pair_count": len(scaling),
        "cells": cells,
        "scaling": scaling,
    }



def protocol() -> dict:
    """Return the JSON-stable frozen v0.0.82 measurement contract."""
    return {
        "rows": list(ROWS),
        "condition_numbers": list(CONDITION_NUMBERS),
        "width_factors": list(WIDTH_FACTORS),
        "pair_replicates": PAIR_REPLICATES,
        "direct_methods": list(DIRECT_METHODS),
        "repeats": REPEATS,
        "time_limit_s": TIME_LIMIT_S,
        "highs_threads": 1,
        "highs_parallel": "off",
        "order_seed": ORDER_SEED,
        "seed_base": SEED_BASE,
        "runtime": {
            "python_major_minor": list(FROZEN_PYTHON_MAJOR_MINOR),
            "numpy": FROZEN_NUMPY_VERSION,
            "scipy": FROZEN_SCIPY_VERSION,
            "threadpoolctl": FROZEN_THREADPOOLCTL_VERSION,
        },
        "expanded_oracle_geomean_max": EXPANDED_ORACLE_GEOMEAN_MAX,
        "twenty_percent_ratio": TWENTY_PERCENT_RATIO,
        "min_expanded_twenty_percent_wins": MIN_EXPANDED_TWENTY_PERCENT_WINS,
        "min_scaling_amplification": MIN_SCALING_AMPLIFICATION,
        "min_scaling_pairs": MIN_SCALING_PAIRS,
    }


def validate_archive(report: dict) -> None:
    """Validate a preserved audit without rerunning any timed solve."""
    expected_protocol = protocol()
    if report.get("protocol") != expected_protocol:
        raise ValueError("protocol drift")
    environment = report.get("environment", {})
    if not environment.get("declared_single_thread"):
        raise ValueError("audit did not preserve the frozen single-thread boundary")
    if (
        environment.get("python_major_minor") != list(FROZEN_PYTHON_MAJOR_MINOR)
        or environment.get("numpy") != FROZEN_NUMPY_VERSION
        or environment.get("scipy") != FROZEN_SCIPY_VERSION
        or environment.get("threadpoolctl") != FROZEN_THREADPOOLCTL_VERSION
    ):
        raise ValueError("frozen runtime version drift")

    specs = {s["id"]: s for s in specifications()}
    sources = report.get("sources", [])
    if len(sources) != len(specs) or {s.get("id") for s in sources} != set(specs):
        raise ValueError("source coverage drift")
    for source in sources:
        spec = specs[source["id"]]
        if any(source.get(k) != v for k, v in spec.items()):
            raise ValueError("source specification drift")
        regenerated = generate_case(spec)
        for key in (
            "raw_observable_sha256",
            "oracle_basis_sha256",
            "latent_pair_sha256",
        ):
            if source.get(key) != regenerated[key]:
                raise ValueError(f"{key} drift")
        if not math.isclose(
            float(source.get("actual_basis_condition")),
            regenerated["actual_basis_condition"],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("basis condition drift")

    records = report.get("records", [])
    warmups = report.get("warmups", [])
    for row in [*records, *warmups]:
        if type(row.get("accepted")) is not bool:
            raise ValueError("invalid capability flag")
        for key, value in row.items():
            if key.endswith("_ms") and (
                type(value) not in (int, float)
                or not np.isfinite(value)
                or value < 0
            ):
                raise ValueError("invalid charged timing")

        if row.get("accepted"):
            certificate = row.get("certificate")
            if not isinstance(certificate, dict) or not certificate.get("accepted"):
                raise ValueError("accepted route lacks accepted original certificate")

        if row.get("path") == "direct":
            if row["total_ms"] + 1e-12 < row["solve_ms"] + row["verify_ms"]:
                raise ValueError("Direct total omits charged stages")
        elif row.get("path") == "oracle_basis":
            components = (
                row["extract_ms"]
                + row["factor_solve_ms"]
                + row["reconstruct_ms"]
                + row["verify_ms"]
            )
            if row["total_ms"] + 1e-12 < components:
                raise ValueError("oracle total omits charged stages")
        else:
            raise ValueError("unknown route path")

    expected_summary = summarize(records, warmups)
    if report.get("summary") != expected_summary:
        raise ValueError("summary drift")

def single_thread_environment() -> dict:
    keys = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
    values = {key: os.environ.get(key) for key in keys}
    values["declared_single_thread"] = all(values[k] == "1" for k in keys)
    return values


def run_audit(
    *,
    require_single_thread: bool = True,
    require_frozen_versions: bool = True,
) -> dict:
    env = single_thread_environment()
    if require_single_thread and not env["declared_single_thread"]:
        raise RuntimeError("frozen audit requires OMP/OPENBLAS/MKL thread counts = 1")
    actual_versions = {
        "python_major_minor": [int(x) for x in platform.python_version_tuple()[:2]],
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "threadpoolctl": threadpoolctl.__version__,
    }
    expected_versions = protocol()["runtime"]
    if require_frozen_versions and actual_versions != expected_versions:
        raise RuntimeError(
            f"frozen runtime version drift: expected {expected_versions}, got {actual_versions}"
        )

    records = []
    warmups = []
    sources = []
    with threadpool_limits(limits=1):
        for spec in specifications():
            case = generate_case(spec)
            sources.append({
                **spec,
                "raw_observable_sha256": case["raw_observable_sha256"],
                "oracle_basis_sha256": case["oracle_basis_sha256"],
                "latent_pair_sha256": case["latent_pair_sha256"],
                "actual_basis_condition": case["actual_basis_condition"],
            })

            for method in DIRECT_METHODS:
                warmups.append({
                    "case_id": spec["id"],
                    "route_id": method,
                    **direct_once(case, method),
                })
            warmups.append({
                "case_id": spec["id"],
                "route_id": "oracle_basis",
                **oracle_basis_once(case, case["oracle_basis"]),
            })

            schedule = [
                (route, repeat)
                for route in (*DIRECT_METHODS, "oracle_basis")
                for repeat in range(REPEATS)
            ]
            random.Random(ORDER_SEED + spec["seed"] + spec["width_factor"]).shuffle(schedule)
            for route, repeat in schedule:
                if route == "oracle_basis":
                    observation = oracle_basis_once(case, case["oracle_basis"])
                else:
                    observation = direct_once(case, route)
                records.append({
                    "case_id": spec["id"],
                    "route_id": route,
                    "repeat": repeat,
                    **observation,
                })

    summary = summarize(records, warmups)

    return {
        "experiment": "v0.0.82 constructed LP oracle-basis headroom",
        "status": "opened-development mechanism screen; no learned model",
        "protocol": protocol(),
        "environment": {
            **env,
            "python": platform.python_version(),
            "python_major_minor": actual_versions["python_major_minor"],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "numpy": actual_versions["numpy"],
            "scipy": actual_versions["scipy"],
            "threadpoolctl": actual_versions["threadpoolctl"],
        },
        "sources": sources,
        "warmups": warmups,
        "records": records,
        "summary": summary,
    }
