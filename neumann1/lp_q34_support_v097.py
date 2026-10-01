"""Q34 support execution contracts for v0.0.97."""
from __future__ import annotations

import math
from time import perf_counter_ns

import numpy as np

from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_native_warm_start_v086 import solve_native_checked, _raw


def restricted_original_checked(A, b, c, indices, *, budget_s):
    """Solve only selected columns, then verify the lifted witness on the original LP."""
    started = perf_counter_ns()
    A, b, c = _raw(A, b, c)
    m, n = A.shape
    if (type(indices) is not list or not m <= len(indices) <= n
            or len(indices) != len(set(indices))
            or any(type(i) is not int or not 0 <= i < n for i in indices)):
        raise ValueError("valid unique support with at least m columns required")
    if type(budget_s) not in (int, float) or not math.isfinite(budget_s) or budget_s <= 0:
        raise ValueError("positive finite budget required")
    native = solve_native_checked(A[:, indices], b, c[indices],
                                  cold_fallback=False, budget_s=budget_s)
    witness = certificate = None
    if native["accepted"]:
        small = native["attempts"][-1]["witness"]
        x = np.zeros(n)
        x[indices] = small["x"]
        witness = {"x": x.tolist(), "y": small["y"]}
        certificate = verify_standard_form_certificate(A, b, c, **witness)
    total_ms = (perf_counter_ns() - started) / 1e6
    return {
        "accepted": bool(certificate and certificate["accepted"]
                         and total_ms <= budget_s * 1000.0),
        "indices": indices,
        "native": native,
        "witness": witness,
        "original_certificate": certificate,
        "total_ms": total_ms,
    }


def support_with_fallback_checked(A, b, c, indices, *, budget_s=5.0):
    """Try one restricted support, then charge a cold full Direct fallback."""
    started = perf_counter_ns()
    A, b, c = _raw(A, b, c)
    if type(budget_s) not in (int, float) or not math.isfinite(budget_s) or budget_s <= 0:
        raise ValueError("positive finite budget required")

    def remaining():
        return budget_s - (perf_counter_ns() - started) / 1e9

    restricted = None
    fallback = None
    witness = None
    accepted = False
    left = remaining()
    if left > 0:
        restricted = restricted_original_checked(A, b, c, list(indices), budget_s=left)
        if restricted["accepted"]:
            accepted = True
            witness = restricted["witness"]

    if not accepted and remaining() > 0:
        fallback = solve_native_checked(A, b, c, cold_fallback=False, budget_s=remaining())
        if fallback["accepted"]:
            accepted = True
            witness = fallback["attempts"][-1]["witness"]

    total_ms = (perf_counter_ns() - started) / 1e6
    return {
        "accepted": bool(accepted and total_ms <= budget_s * 1000.0),
        "restricted": restricted,
        "fallback": fallback,
        "fallback_used": fallback is not None,
        "subset_accepted": bool(restricted and restricted["accepted"]),
        "witness": witness,
        "total_ms": total_ms,
        "budget_s": budget_s,
    }


def adaptive_support_checked(A, b, c, ranking, *, budget_s=5.0, factors=(1, 2, 4)):
    """Try progressively larger supports, then a charged cold full Direct fallback."""
    started = perf_counter_ns()
    A, b, c = _raw(A, b, c)
    m, n = A.shape
    ranking = list(ranking)
    if (len(ranking) != n or len(set(ranking)) != n
            or any(type(i) is not int or not 0 <= i < n for i in ranking)):
        raise ValueError("ranking must be a full permutation")
    attempts = []
    seen_sizes = set()
    witness = None
    accepted = False

    def remaining():
        return budget_s - (perf_counter_ns() - started) / 1e9

    for factor in factors:
        size = min(n, factor * m)
        if size in seen_sizes or size == n:
            continue
        seen_sizes.add(size)
        left = remaining()
        if left <= 0:
            break
        attempt = restricted_original_checked(A, b, c, ranking[:size], budget_s=left)
        attempts.append({"kind": "restricted", "support_size": size, "result": attempt})
        if attempt["accepted"]:
            accepted = True
            witness = attempt["witness"]
            break

    fallback = None
    if not accepted and remaining() > 0:
        fallback = solve_native_checked(A, b, c, cold_fallback=False, budget_s=remaining())
        if fallback["accepted"]:
            accepted = True
            witness = fallback["attempts"][-1]["witness"]

    total_ms = (perf_counter_ns() - started) / 1e6
    return {
        "accepted": bool(accepted and total_ms <= budget_s * 1000.0),
        "attempts": attempts,
        "fallback": fallback,
        "fallback_used": fallback is not None,
        "witness": witness,
        "total_ms": total_ms,
        "budget_s": budget_s,
    }
