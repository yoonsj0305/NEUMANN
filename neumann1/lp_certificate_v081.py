"""v0.0.81: independent certificate checks for standard-form linear programs.

Task contract:
    minimize c^T x
    subject to A x = b
               x >= 0

A primal/dual certificate is (x, y). The verifier never calls an optimizer.
For this standard form, primal feasibility, dual feasibility A^T y <= c,
and equality of primal/dual objectives certify optimality up to the frozen
numerical tolerances. Complementarity is reported as an additional diagnostic;
it is not an independent acceptance requirement once those conditions hold.
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
        matrix = value.astype(np.float64)
    else:
        matrix = np.asarray(value, dtype=np.float64)
        if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
            raise ValueError("A must be a finite two-dimensional matrix")
    if matrix.shape[0] <= 0 or matrix.shape[1] <= 0:
        raise ValueError("A must have at least one row and one column")
    return matrix


def _tolerance(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise ValueError(f"{name} must be a finite non-negative number")
    number = float(value)
    if not np.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return number


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

    The acceptance test is a componentwise, scale-aware numerical certificate.
    Equality and dual residuals are normalized by the magnitudes of the
    original dot-product terms, which avoids rejecting a numerically valid
    certificate merely because large terms cancel to a small right-hand side.

    This function is deliberately solver-free. It checks the original
    coefficients supplied by the caller rather than a reduced model or a
    cached gold answer.
    """
    matrix = _matrix(A)
    rhs = _vector(b, "b")
    cost = _vector(c, "c")
    primal = _vector(x, "x")
    dual = _vector(y, "y")
    atol = _tolerance(atol, "atol")
    rtol = _tolerance(rtol, "rtol")

    rows, cols = matrix.shape
    if rhs.size != rows or cost.size != cols or primal.size != cols or dual.size != rows:
        raise ValueError("certificate shape mismatch")

    abs_matrix = abs(matrix) if sparse.issparse(matrix) else np.abs(matrix)
    with np.errstate(over="ignore", invalid="ignore"):
        ax = np.asarray(matrix @ primal, dtype=np.float64).reshape(-1)
        aty = np.asarray(matrix.T @ dual, dtype=np.float64).reshape(-1)
        dual_slack = cost - aty

        equality_scale = np.asarray(
            abs_matrix @ np.abs(primal), dtype=np.float64
        ).reshape(-1) + np.abs(rhs)
        equality_allowance = atol + rtol * np.maximum(1.0, equality_scale)
        equality_residual = np.abs(ax - rhs)

        nonnegative_violation = np.maximum(-primal, 0.0)
        nonnegative_allowance = atol + rtol * np.maximum(1.0, np.abs(primal))

        dual_scale = np.asarray(
            abs_matrix.T @ np.abs(dual), dtype=np.float64
        ).reshape(-1) + np.abs(cost)
        dual_allowance = atol + rtol * np.maximum(1.0, dual_scale)
        dual_violation = np.maximum(-dual_slack, 0.0)

        primal_objective = float(cost @ primal)
        dual_objective = float(rhs @ dual)
        objective_gap_abs = float(abs(primal_objective - dual_objective))
        objective_scale = float(
            np.abs(cost) @ np.abs(primal) + np.abs(rhs) @ np.abs(dual)
        )
        objective_gap_allowance = float(
            atol + rtol * max(1.0, objective_scale)
        )

        complementarity_terms = np.abs(primal * dual_slack)
        complementarity_scale = np.abs(primal) * (np.abs(cost) + np.abs(aty))
        complementarity_allowance = atol + rtol * np.maximum(
            1.0, complementarity_scale
        )

    numerical_finite = bool(
        np.all(np.isfinite(ax))
        and np.all(np.isfinite(aty))
        and np.all(np.isfinite(equality_scale))
        and np.all(np.isfinite(dual_scale))
        and np.isfinite(primal_objective)
        and np.isfinite(dual_objective)
        and np.isfinite(objective_scale)
    )

    if numerical_finite:
        equality_ratio = float(
            np.max(equality_residual / equality_allowance, initial=0.0)
        )
        nonnegative_ratio = float(
            np.max(nonnegative_violation / nonnegative_allowance, initial=0.0)
        )
        dual_feasibility_ratio = float(
            np.max(dual_violation / dual_allowance, initial=0.0)
        )
        objective_gap_ratio = float(objective_gap_abs / objective_gap_allowance)
        complementarity_ratio = float(
            np.max(
                complementarity_terms / complementarity_allowance,
                initial=0.0,
            )
        )
    else:
        equality_ratio = float("inf")
        nonnegative_ratio = float("inf")
        dual_feasibility_ratio = float("inf")
        objective_gap_ratio = float("inf")
        complementarity_ratio = float("inf")

    accepted = bool(
        numerical_finite
        and equality_ratio <= 1.0
        and nonnegative_ratio <= 1.0
        and dual_feasibility_ratio <= 1.0
        and objective_gap_ratio <= 1.0
    )

    return {
        "schema": CERTIFICATE_SCHEMA,
        "accepted": accepted,
        "numerical_finite": numerical_finite,
        "rows": int(rows),
        "cols": int(cols),
        "nnz": int(matrix.nnz if sparse.issparse(matrix) else np.count_nonzero(matrix)),
        "atol": atol,
        "rtol": rtol,
        "primal_objective": primal_objective,
        "dual_objective": dual_objective,
        "equality_abs": float(np.max(equality_residual, initial=0.0)),
        "equality_tol": float(np.max(equality_allowance, initial=atol)),
        "equality_ratio": equality_ratio,
        "nonnegative_abs": float(np.max(nonnegative_violation, initial=0.0)),
        "nonnegative_tol": float(np.max(nonnegative_allowance, initial=atol)),
        "nonnegative_ratio": nonnegative_ratio,
        "dual_feasibility_abs": float(np.max(dual_violation, initial=0.0)),
        "dual_feasibility_tol": float(np.max(dual_allowance, initial=atol)),
        "dual_feasibility_ratio": dual_feasibility_ratio,
        "objective_gap_abs": objective_gap_abs,
        "objective_gap_tol": objective_gap_allowance,
        "objective_gap_ratio": objective_gap_ratio,
        "complementarity_abs": float(np.max(complementarity_terms, initial=0.0)),
        "complementarity_tol": float(
            np.max(complementarity_allowance, initial=atol)
        ),
        "complementarity_ratio": complementarity_ratio,
        "complementarity_diagnostic_only": True,
    }


def highs_candidate(A: Any, b: Any, c: Any) -> dict:
    """Produce a candidate with HiGHS, then verify it through the solver-free path.

    This wrapper exists for integration tests and future cost screens. The
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

    The planted certificate is test-only authority. It must not be used as
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
