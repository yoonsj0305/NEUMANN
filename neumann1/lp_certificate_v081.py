"""v0.0.81: independent certificate checks for standard-form linear programs.

Task contract:
    minimize c^T x
    subject to A x = b
               x >= 0

A primal/dual certificate is (x, y).  The verifier never calls an optimizer.
For this standard form, primal feasibility, dual feasibility A^T y <= c,
and equality of primal/dual objectives certify optimality up to the frozen
numerical tolerances.  Complementarity is checked as an additional fault
signal, not as a substitute for the primal/dual conditions.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse


DEFAULT_ATOL = 1e-8
DEFAULT_RTOL = 1e-8
CERTIFICATE_SCHEMA = "neumann.lp-standard-form-certificate.v1"


def _vector(value: Any, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite one-dimensional vector")
    return array


def _matrix(value: Any):
    if len(getattr(value, "shape", ())) != 2:
        raise ValueError("A must be a two-dimensional matrix")
    if sparse.issparse(value):
        if not np.all(np.isfinite(value.data)):
            raise ValueError("A must be finite")
        return value.astype(np.float64)
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise ValueError("A must be a finite two-dimensional matrix")
    return array


def verify_standard_form_certificate(
    A: Any,
    b: Any,
    c: Any,
    x: Any,
    y: Any,
    *,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
) -> dict:
    """Check one original LP and one claimed primal/dual optimum.

    This function is deliberately solver-free.  It checks the original
    coefficients supplied by the caller rather than a reduced model or a
    cached gold answer.  The returned metrics are descriptive and keep the
    exact frozen tolerances used for the acceptance decision.
    """
    matrix = _matrix(A)
    rhs = _vector(b, "b")
    cost = _vector(c, "c")
    primal = _vector(x, "x")
    dual = _vector(y, "y")

    rows, cols = matrix.shape
    if rhs.size != rows or cost.size != cols or primal.size != cols or dual.size != rows:
        raise ValueError("certificate shape mismatch")
    if (
        type(atol) not in (int, float)
        or type(rtol) not in (int, float)
        or not np.isfinite([atol, rtol]).all()
        or atol < 0
        or rtol < 0
    ):
        raise ValueError("invalid certificate tolerance")

    ax = np.asarray(matrix @ primal, dtype=np.float64).reshape(-1)
    aty = np.asarray(matrix.T @ dual, dtype=np.float64).reshape(-1)
    dual_slack = cost - aty

    primal_objective = float(cost @ primal)
    dual_objective = float(rhs @ dual)

    equality_abs = float(np.max(np.abs(ax - rhs), initial=0.0))
    equality_tol = float(
        atol + rtol * max(1.0, float(np.max(np.abs(rhs), initial=0.0)))
    )

    nonnegative_abs = float(max(0.0, -float(np.min(primal, initial=0.0))))
    nonnegative_tol = float(
        atol + rtol * max(1.0, float(np.max(np.abs(primal), initial=0.0)))
    )

    dual_feasibility_abs = float(
        max(0.0, -float(np.min(dual_slack, initial=0.0)))
    )
    dual_feasibility_tol = float(
        atol
        + rtol
        * max(
            1.0,
            float(np.max(np.abs(cost), initial=0.0)),
            float(np.max(np.abs(aty), initial=0.0)),
        )
    )

    objective_gap_abs = float(abs(primal_objective - dual_objective))
    objective_gap_tol = float(
        atol + rtol * max(1.0, abs(primal_objective), abs(dual_objective))
    )

    complementarity_abs = float(
        np.max(np.abs(primal * dual_slack), initial=0.0)
    )
    complementarity_tol = objective_gap_tol

    accepted = bool(
        equality_abs <= equality_tol
        and nonnegative_abs <= nonnegative_tol
        and dual_feasibility_abs <= dual_feasibility_tol
        and objective_gap_abs <= objective_gap_tol
        and complementarity_abs <= complementarity_tol
    )

    return {
        "schema": CERTIFICATE_SCHEMA,
        "accepted": accepted,
        "rows": int(rows),
        "cols": int(cols),
        "nnz": int(matrix.nnz if sparse.issparse(matrix) else np.count_nonzero(matrix)),
        "atol": float(atol),
        "rtol": float(rtol),
        "primal_objective": primal_objective,
        "dual_objective": dual_objective,
        "equality_abs": equality_abs,
        "equality_tol": equality_tol,
        "nonnegative_abs": nonnegative_abs,
        "nonnegative_tol": nonnegative_tol,
        "dual_feasibility_abs": dual_feasibility_abs,
        "dual_feasibility_tol": dual_feasibility_tol,
        "objective_gap_abs": objective_gap_abs,
        "objective_gap_tol": objective_gap_tol,
        "complementarity_abs": complementarity_abs,
        "complementarity_tol": complementarity_tol,
    }


def highs_candidate(A: Any, b: Any, c: Any) -> dict:
    """Produce a candidate with HiGHS, then verify it through the solver-free path.

    This wrapper exists for integration tests and future cost screens.  The
    verifier above remains the authority and does not trust HiGHS status alone.
    """
    from scipy.optimize import linprog

    matrix = _matrix(A)
    rhs = _vector(b, "b")
    cost = _vector(c, "c")
    result = linprog(cost, A_eq=matrix, b_eq=rhs, bounds=(0, None), method="highs")
    if not result.success or result.x is None or result.eqlin.marginals is None:
        return {
            "solver_success": False,
            "solver_status": int(result.status),
            "solver_message": str(result.message),
            "certificate": None,
        }
    certificate = verify_standard_form_certificate(
        matrix, rhs, cost, result.x, result.eqlin.marginals
    )
    return {
        "solver_success": True,
        "solver_status": int(result.status),
        "solver_message": str(result.message),
        "x": np.asarray(result.x, dtype=np.float64),
        "y": np.asarray(result.eqlin.marginals, dtype=np.float64),
        "certificate": certificate,
    }


def contract_fixture(seed: int = 8101, rows: int = 6, cols: int = 30) -> dict:
    """Construct one bounded fixture with a known certificate for contract tests.

    The planted certificate is test-only authority.  It must not be used as
    inference input, a future performance label, or a production verifier.
    """
    if type(seed) is not int or type(rows) is not int or type(cols) is not int:
        raise ValueError("fixture parameters must be integers")
    if rows < 2 or cols <= rows:
        raise ValueError("fixture requires 2 <= rows < cols")

    rng = np.random.default_rng(seed)
    q, _ = np.linalg.qr(rng.normal(size=(rows, rows)))
    matrix = np.empty((rows, cols), dtype=np.float64)
    matrix[:, :rows] = q
    matrix[:, rows:] = rng.normal(size=(rows, cols - rows)) / np.sqrt(rows)

    permutation = rng.permutation(cols)
    matrix = matrix[:, permutation]
    basis = np.flatnonzero(permutation < rows)

    primal = np.zeros(cols, dtype=np.float64)
    primal[basis] = rng.uniform(0.5, 1.5, size=rows)
    rhs = matrix @ primal

    dual = rng.normal(size=rows)
    slack = rng.uniform(0.25, 2.0, size=cols)
    slack[basis] = 0.0
    cost = matrix.T @ dual + slack

    return {
        "A": matrix,
        "b": rhs,
        "c": cost,
        "known_x": primal,
        "known_y": dual,
        "known_basis": basis,
        "seed": seed,
    }
