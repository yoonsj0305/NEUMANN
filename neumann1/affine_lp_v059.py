"""Bounded affine elimination in a continuous LP, with full reconstruction.

Exploratory single-instance research path. highspy is an optional audit
dependency, not part of the NEUMANN production runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix


INF = 1e20  # HiGHS uses finite sentinels for unbounded sides.


@dataclass(frozen=True)
class Reduction:
    model: object
    retained: tuple[int, ...]
    eliminated: tuple[tuple[int, int, float, float, tuple[tuple[int, float], ...]], ...]
    # Each tuple: (column, source row, pivot coefficient, RHS, remaining row).
    original_rows: int
    rewritten_bound_rows: int


def sparse(lp) -> csc_matrix:
    a = lp.a_matrix_
    if str(a.format_).endswith("kColwise") is False:
        raise ValueError("column-wise LP matrix required")
    return csc_matrix((np.asarray(a.value_), np.asarray(a.index_),
                       np.asarray(a.start_)), shape=(lp.num_row_, lp.num_col_))


def reduce_lp(lp) -> Reduction:
    import highspy

    if any(kind != highspy.HighsVarType.kContinuous for kind in lp.integrality_):
        raise ValueError("this transformation requires a continuous LP")
    a = sparse(lp).tocsr()
    col_degree = np.diff(a.tocsc().indptr)
    selected = {}
    for i in range(lp.num_row_):
        rhs = lp.row_lower_[i]
        if rhs != lp.row_upper_[i] or abs(rhs) >= INF:
            continue
        first, end = a.indptr[i:i+2]
        choices = [int(j) for j, coeff in zip(a.indices[first:end], a.data[first:end])
                   if col_degree[j] == 1 and coeff != 0]
        if choices:
            selected[i] = min(choices)
    eliminated_columns = set(selected.values())
    retained = tuple(j for j in range(lp.num_col_) if j not in eliminated_columns)
    mapping = {j: k for k, j in enumerate(retained)}
    costs = np.asarray(lp.col_cost_, dtype=float)[list(retained)].copy()
    offset = float(lp.offset_)
    row_data = []
    row_lower = []
    row_upper = []
    reconstruction = []
    translated = 0
    for i in range(lp.num_row_):
        first, end = a.indptr[i:i+2]
        terms = tuple((int(j), float(v)) for j, v in
                      zip(a.indices[first:end], a.data[first:end]))
        if i not in selected:
            row_data.append({mapping[j]: v for j, v in terms})
            row_lower.append(float(lp.row_lower_[i]))
            row_upper.append(float(lp.row_upper_[i]))
            continue
        pivot = selected[i]
        coefficient = next(v for j, v in terms if j == pivot)
        rest = tuple((j, v) for j, v in terms if j != pivot)
        rhs = float(lp.row_lower_[i])
        reconstruction.append((pivot, i, coefficient, rhs, rest))
        c = float(lp.col_cost_[pivot])
        offset += c * rhs / coefficient
        for j, v in rest:
            costs[mapping[j]] -= c * v / coefficient
        # s = sum(a_j*y_j) = rhs - a_pivot*x_pivot. Translate the
        # original pivot variable's bounds into a bounded row on s.
        lower = float(lp.col_lower_[pivot])
        upper = float(lp.col_upper_[pivot])
        endpoints = [rhs - coefficient * bound for bound in (lower, upper)]
        low, high = min(endpoints), max(endpoints)
        if lower <= -INF or upper >= INF:
            if (coefficient > 0 and upper >= INF) or (coefficient < 0 and lower <= -INF):
                low = -highspy.kHighsInf
            if (coefficient > 0 and lower <= -INF) or (coefficient < 0 and upper >= INF):
                high = highspy.kHighsInf
        if low > -INF or high < INF:
            row_data.append({mapping[j]: v for j, v in rest})
            row_lower.append(low)
            row_upper.append(high)
            translated += 1
    from scipy.sparse import csr_matrix
    ii, jj, vv = [], [], []
    for i, row in enumerate(row_data):
        for j, v in row.items():
            ii.append(i); jj.append(j); vv.append(v)
    reduced = csr_matrix((vv, (ii, jj)), shape=(len(row_data), len(retained))).tocsc()
    model = highspy.HighsLp()
    model.num_col_, model.num_row_ = reduced.shape[1], reduced.shape[0]
    model.col_cost_ = costs.tolist()
    model.col_lower_ = [float(lp.col_lower_[j]) for j in retained]
    model.col_upper_ = [float(lp.col_upper_[j]) for j in retained]
    model.row_lower_, model.row_upper_ = row_lower, row_upper
    model.offset_, model.sense_ = offset, lp.sense_
    model.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    model.a_matrix_.num_col_, model.a_matrix_.num_row_ = model.num_col_, model.num_row_
    model.a_matrix_.start_ = reduced.indptr.tolist()
    model.a_matrix_.index_ = reduced.indices.tolist()
    model.a_matrix_.value_ = reduced.data.tolist()
    return Reduction(model, retained, tuple(reconstruction), lp.num_row_, translated)


def reconstruct(reduction: Reduction, values: np.ndarray, n: int) -> np.ndarray:
    x = np.empty(n)
    x[list(reduction.retained)] = values
    for j, _, coefficient, rhs, rest in reduction.eliminated:
        x[j] = (rhs - sum(v * x[k] for k, v in rest)) / coefficient
    return x


def check_original(lp, matrix: csc_matrix, x: np.ndarray) -> tuple[float, float]:
    """Maximum scaled primal bound/row violation and original objective."""
    if len(x) != lp.num_col_ or not np.isfinite(x).all():
        return float("inf"), float("nan")
    values = matrix @ x
    row_scale = np.maximum(1., np.asarray(abs(matrix).max(axis=1).toarray()).ravel())
    row_scale = np.maximum(row_scale, np.abs(values))
    max_error = 0.
    for observed, low, high, scale in zip(values, lp.row_lower_, lp.row_upper_, row_scale):
        if low > -INF:
            max_error = max(max_error, max(0., low - observed) / max(scale, abs(low)))
        if high < INF:
            max_error = max(max_error, max(0., observed - high) / max(scale, abs(high)))
    for value, low, high in zip(x, lp.col_lower_, lp.col_upper_):
        scale = max(1., abs(value))
        if low > -INF:
            max_error = max(max_error, max(0., low - value) / max(scale, abs(low)))
        if high < INF:
            max_error = max(max_error, max(0., value - high) / max(scale, abs(high)))
    return max_error, float(np.dot(lp.col_cost_, x) + lp.offset_)
