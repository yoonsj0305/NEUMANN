"""Exploratory dual-derived two-stage recourse cut path for SIPLIB SEMI.

This developmental path charges every master and recourse solve. It does not
independently check dual certificates or claim a fixed-capability win.
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

import highspy
import numpy as np
from scipy.sparse import csc_matrix, hstack, vstack

from benchmark_v063 import FIRST_COLS, FIRST_ROWS, extensive_form, load_source, verify_original


def _pass(matrix, costs, col_lower, col_upper, row_lower, row_upper,
          integrality=None):
    lp = highspy.HighsLp()
    lp.num_row_, lp.num_col_ = matrix.shape
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = list(costs), list(col_lower), list(col_upper)
    lp.row_lower_, lp.row_upper_ = list(row_lower), list(row_upper)
    if integrality is not None:
        lp.integrality_ = list(integrality)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.num_row_, lp.a_matrix_.num_col_ = matrix.shape
    lp.a_matrix_.start_ = matrix.indptr.tolist()
    lp.a_matrix_.index_ = matrix.indices.tolist()
    lp.a_matrix_.value_ = matrix.data.tolist()
    solver = highspy.Highs()
    solver.setOptionValue("output_flag", False)
    solver.setOptionValue("threads", 1)
    if solver.passModel(lp) != highspy.HighsStatus.kOk:
        raise ValueError("solver rejected a decomposition model")
    return solver


class Recourse:
    def __init__(self, source):
        core = source.core
        self.T = source.matrix[FIRST_ROWS:, :FIRST_COLS]
        self.W = source.matrix[FIRST_ROWS:, FIRST_COLS:]
        self.q = np.asarray(core.col_cost_[FIRST_COLS:])
        self.lower = np.asarray(core.row_lower_[FIRST_ROWS:])
        self.upper = np.asarray(core.row_upper_[FIRST_ROWS:])
        self.ylow = np.asarray(core.col_lower_[FIRST_COLS:])
        self.yhigh = np.asarray(core.col_upper_[FIRST_COLS:])
        self.lo_indices = np.flatnonzero(np.isfinite(self.lower))
        self.hi_indices = np.flatnonzero(np.isfinite(self.upper))
        a = vstack([self.W[self.lo_indices], self.W[self.hi_indices]], format="csc")
        slack = csc_matrix(np.r_[np.ones(len(self.lo_indices)),
                                  -np.ones(len(self.hi_indices))][:, None])
        self.elastic = hstack([a, slack], format="csc")

    def _bounds(self, x, deltas):
        shifts = np.zeros(self.W.shape[0])
        for row, value in deltas.items():
            shifts[row - FIRST_ROWS] = value
        tx = self.T @ x
        return self.lower + shifts - tx, self.upper + shifts - tx

    def feasibility(self, x, deltas):
        low, high = self._bounds(x, deltas)
        solver = _pass(self.elastic, np.r_[np.zeros(len(self.q)), 1.0],
                       np.r_[self.ylow, 0.0], np.r_[self.yhigh, highspy.kHighsInf],
                       np.r_[low[self.lo_indices],
                             np.full(len(self.hi_indices), -highspy.kHighsInf)],
                       np.r_[np.full(len(self.lo_indices), highspy.kHighsInf),
                             high[self.hi_indices]])
        if solver.run() != highspy.HighsStatus.kOk or solver.getModelStatus() != highspy.HighsModelStatus.kOptimal:
            raise ValueError("elastic recourse was not solved to optimality")
        solution = solver.getSolution()
        if not solution.dual_valid:
            raise ValueError("missing feasibility dual")
        dual = np.asarray(solution.row_dual)
        gradient = -(self.T[self.lo_indices].T @ dual[:len(self.lo_indices)] +
                     self.T[self.hi_indices].T @ dual[len(self.lo_indices):])
        violation = float(solver.getInfo().objective_function_value)
        if abs(violation - solution.col_value[-1]) > 1e-6:
            raise ValueError("elastic primal/dual objective mismatch")
        return violation, np.asarray(gradient).ravel()

    def optimize(self, x, deltas):
        low, high = self._bounds(x, deltas)
        solver = _pass(self.W, self.q, self.ylow, self.yhigh, low, high)
        if solver.run() != highspy.HighsStatus.kOk or solver.getModelStatus() != highspy.HighsModelStatus.kOptimal:
            raise ValueError("recourse LP failed despite zero elastic violation")
        solution = solver.getSolution()
        if not solution.dual_valid:
            raise ValueError("missing optimality dual")
        objective = float(solver.getInfo().objective_function_value)
        gradient = -(self.T.T @ np.asarray(solution.row_dual))
        return objective, np.asarray(gradient).ravel(), np.asarray(solution.col_value)


def sparsify_valid_cut(row, rhs, lower, upper, threshold=1e-9):
    """Relax RHS by the worst contribution of removed, bounded coefficients."""
    row = np.asarray(row).copy()
    drop = np.flatnonzero((abs(row) > 0) & (abs(row) <= threshold))
    if len(drop):
        lo = np.asarray(lower)[drop]
        hi = np.asarray(upper)[drop]
        if not np.isfinite(lo).all() or not np.isfinite(hi).all():
            raise ValueError("cannot bound dropped cut coefficients")
        rhs -= float(np.minimum(row[drop] * lo, row[drop] * hi).sum())
        row[drop] = 0.0
    return row, rhs


def exploratory(source, budget_s=20.0, max_iterations=10, recourse_type=Recourse):
    start = perf_counter()
    core = source.core
    count = len(source.scenarios)
    top = source.matrix[:FIRST_ROWS, :FIRST_COLS]
    master_a = hstack([top, csc_matrix((FIRST_ROWS, count))], format="csc")
    master = _pass(master_a,
                   list(core.col_cost_[:FIRST_COLS]) + [p for _, p, _ in source.scenarios],
                   list(core.col_lower_[:FIRST_COLS]) + [0.0] * count,
                   list(core.col_upper_[:FIRST_COLS]) + [highspy.kHighsInf] * count,
                   core.row_lower_[:FIRST_ROWS], core.row_upper_[:FIRST_ROWS],
                   list(core.integrality_[:FIRST_COLS]) + [highspy.HighsVarType.kContinuous] * count)
    master.setOptionValue("mip_rel_gap", 0.0)
    recourse = recourse_type(source)
    history = []
    best = None
    for iteration in range(max_iterations):
        remaining = budget_s - (perf_counter() - start)
        if remaining <= 0.5:
            break
        master.setOptionValue("time_limit", remaining)
        status = master.run()
        info = master.getInfo()
        solution = master.getSolution()
        if not solution.value_valid:
            history.append({"iteration": iteration, "master_status": str(master.getModelStatus()),
                            "outcome": "NO_MASTER_INCUMBENT"})
            break
        x = np.asarray(solution.col_value[:FIRST_COLS])
        theta = np.asarray(solution.col_value[FIRST_COLS:])
        if max(abs(x - np.rint(x))) > 1e-6:
            raise ValueError("master integer solution invalid")
        record = {"iteration": iteration, "master_status": str(master.getModelStatus()),
                  "master_dual_bound": float(info.mip_dual_bound),
                  "master_objective": float(info.objective_function_value),
                  "elapsed_s": perf_counter() - start, "cuts": []}
        if status not in (highspy.HighsStatus.kOk, highspy.HighsStatus.kWarning):
            raise ValueError("master solver error")
        all_feasible = True
        y_values = []
        for s, (_, probability, deltas) in enumerate(source.scenarios):
            if perf_counter() - start >= budget_s:
                record["outcome"] = "BUDGET_EXHAUSTED"
                all_feasible = False
                break
            violation, f_gradient = recourse.feasibility(x, deltas)
            if violation > 1e-7:
                all_feasible = False
                gradient = f_gradient
                rhs = float(gradient @ x - violation)
                if gradient @ x - rhs < 1e-7:
                    raise ValueError("feasibility cut does not separate current point")
                kind = "feasibility"
                row = np.r_[gradient, np.zeros(count)]
            else:
                objective, gradient, y = recourse.optimize(x, deltas)
                y_values.append((s, y))
                rhs = float(gradient @ x - objective)
                row = np.r_[gradient, np.zeros(count)]
                row[FIRST_COLS + s] = -1.0
                if theta[s] + 1e-7 >= objective + gradient @ (x - x):
                    # No violated optimality cut at this point is necessary.
                    continue
                kind = "optimality"
            # Dropping a coefficient d_j from a·z <= rhs keeps the inequality
            # valid only if its RHS is relaxed by -min(d_j * bounded_x_j).
            # SEMI's first-stage integers have finite [0,100] bounds.
            row, rhs = sparsify_valid_cut(
                row, rhs, list(core.col_lower_[:FIRST_COLS]) + [0.0] * count,
                list(core.col_upper_[:FIRST_COLS]) + [highspy.kHighsInf] * count)
            cut_indices = np.flatnonzero(abs(row) > 1e-9).astype(np.int32)
            cut_values = row[cut_indices]
            cut_status = master.addRow(-highspy.kHighsInf, rhs, len(cut_indices), cut_indices,
                                       cut_values)
            if cut_status != highspy.HighsStatus.kOk:
                raise ValueError(f"master rejected cut: iteration={iteration}, scenario={s}, "
                                 f"type={kind}, violation={violation}, nnz={len(cut_indices)}, "
                                 f"rhs={rhs}, gradient_dot_x={float(gradient @ x)}, "
                                 f"status={cut_status}, min_coeff={min(cut_values)}, "
                                 f"max_coeff={max(cut_values)}")
            record["cuts"].append({"scenario": s, "type": kind,
                                    "violation": violation, "nonzeros": len(cut_indices)})
        if all_feasible:
            if len(y_values) != count:
                raise ValueError("missing recourse solution")
            full = np.r_[x, *[y for _, y in y_values]]
            primal, integrality, objective = verify_original(source, full)
            if primal > 1e-7 or integrality > 1e-6:
                raise ValueError("independent original verification failed")
            if best is None or objective < best["objective"]:
                best = {"objective": objective, "primal_error": primal,
                        "integrality_error": integrality, "elapsed_s": perf_counter() - start}
            record["verified_objective"] = objective
        if not record["cuts"] and record.get("outcome") != "BUDGET_EXHAUSTED":
            record["outcome"] = "NO_VIOLATED_CUT"
            history.append(record)
            break
        history.append(record)
    return {"protocol": "v0.0.64 exploratory decomposition, no frozen performance gate",
            "budget_s": budget_s, "elapsed_s": perf_counter() - start,
            "iterations": history, "best_original_feasible": best,
            "recourse_lp_builds": getattr(recourse, "lp_builds", None),
            "recourse_lp_runs": getattr(recourse, "lp_runs", None),
            "scope": "single nonblind instance; no iso-capability speedup claim"}


def native_diagnostic(source, budget_s=20.0):
    start = perf_counter()
    lp = extensive_form(source)
    solver = highspy.Highs()
    solver.setOptionValue("output_flag", False)
    solver.setOptionValue("threads", 1)
    solver.setOptionValue("mip_rel_gap", 0.0)
    solver.setOptionValue("time_limit", max(0.1, budget_s - 1.0 - (perf_counter() - start)))
    if solver.passModel(lp) != highspy.HighsStatus.kOk:
        raise ValueError("native model transfer failed")
    status = solver.run()
    solution = solver.getSolution()
    info = solver.getInfo()
    verification = None
    if solution.value_valid:
        primal, integrality, objective = verify_original(source, solution.col_value)
        verification = {"original_primal_violation": primal,
                        "original_integrality_violation": integrality,
                        "original_objective": objective,
                        "objective_agreement": abs(objective - info.objective_function_value)}
        if primal > 1e-7 or integrality > 1e-6 or verification["objective_agreement"] > 1e-6:
            raise ValueError("native answer failed original verification")
    return {"protocol": "v0.0.64 exploratory native diagnostic, no frozen performance gate",
            "budget_s": budget_s, "elapsed_s": perf_counter() - start,
            "run_status": str(status), "solver_status": str(solver.getModelStatus()),
            "dual_bound": info.mip_dual_bound, "relative_gap": info.mip_gap,
            "original_verification": verification,
            "scope": "nonblind descriptive baseline; source parsing excluded, no paired iso-capability comparison"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget-s", type=float, default=20.0)
    parser.add_argument("--mode", choices=("candidate", "native"), default="candidate")
    args = parser.parse_args()
    source = load_source(args.archive, 2)
    result = (exploratory(source, budget_s=args.budget_s) if args.mode == "candidate"
              else native_diagnostic(source, budget_s=args.budget_s))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result if args.mode == "native" else
                     {"elapsed_s": result["elapsed_s"],
                      "best_original_feasible": result["best_original_feasible"],
                      "iterations": len(result["iterations"])}, indent=2))
