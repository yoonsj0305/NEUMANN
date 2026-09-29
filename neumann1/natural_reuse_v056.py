"""Corrective numerical-validation audit, preserving v0.0.55 candidate.

The v0.0.55 warmup aborted before a complete audit. This separate protocol
uses a declared 1e-6 planted-solution tolerance while retaining its strict
original-equation backward-error check, corpus, policies and decision.
"""

from __future__ import annotations

from dataclasses import asdict
from random import Random

import numpy as np
from scipy.sparse import csr_matrix

from neumann1.natural_reuse_v055 import MATRICES, POLICIES, run_trial


BACKWARD_TOL = 1e-10
SOLUTION_TOL = 1e-6


def numerically_valid(backward_error: float, solution_error: float) -> bool:
    return bool(np.isfinite(backward_error) and np.isfinite(solution_error)
                and backward_error <= BACKWARD_TOL and solution_error <= SOLUTION_TOL)


def audit_case(matrix: csr_matrix, name: str) -> dict:
    if name not in MATRICES:
        raise ValueError("outside pinned corpus")
    truth = np.sin(np.arange(matrix.shape[0], dtype=np.float64) + 1)
    rhs = matrix @ truth
    for policy in POLICIES:
        warmup = run_trial(matrix, rhs, truth, policy)
        if not numerically_valid(warmup.backward_error, warmup.solution_error):
            raise ValueError(f"corrective warmup failed: {name}/{policy}")
    rows = {policy: [] for policy in POLICIES}
    for repetition in range(7):
        policies = list(POLICIES)
        Random(55 + list(MATRICES).index(name) * 100 + repetition).shuffle(policies)
        for policy in policies:
            trial = run_trial(matrix, rhs, truth, policy)
            valid_v056 = numerically_valid(trial.backward_error, trial.solution_error)
            if not valid_v056:
                raise ValueError(f"corrective numerical verification failed: {name}/{policy}/{repetition}")
            row = asdict(trial)
            row["valid_v055_stricter_forward_gate"] = row.pop("valid")
            row["valid_v056"] = valid_v056
            rows[policy].append(row)
    medians = {p: float(np.median([row["total_ns"] for row in rows[p]])) for p in POLICIES}
    observed = rows["GATED_REUSE"][0]
    if any((r["components"], r["distinct_blocks"]) !=
           (observed["components"], observed["distinct_blocks"])
           for r in rows["GATED_REUSE"]):
        raise ValueError("nondeterministic repeat detection")
    best_native = min(medians["NATURAL"], medians["COLAMD"])
    return {"name": name, "n": matrix.shape[0], "nnz": matrix.nnz,
            "components": observed["components"], "distinct_blocks": observed["distinct_blocks"],
            "rows": rows, "median_total_ns": medians,
            "gate_vs_natural": (medians["NATURAL"] - medians["GATED_REUSE"]) / medians["NATURAL"],
            "gate_vs_best_native_diagnostic": (best_native - medians["GATED_REUSE"]) / best_native}
