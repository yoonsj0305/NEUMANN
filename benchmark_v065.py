"""Nonblind basis-reuse diagnostic for the SEMI recourse decomposition.

The same cut policy as v0.0.64 is used. This tests whether retaining the LP
basis removes a measured rebuild cost, not whether decomposition is novel.
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

import highspy
import numpy as np

from benchmark_v063 import load_source
from benchmark_v064 import Recourse, _pass, exploratory


class WarmRecourse(Recourse):
    def __init__(self, source):
        super().__init__(source)
        self.feasibility_solvers = {}
        self.optimality_solvers = {}
        self.elastic_indices = np.arange(self.elastic.shape[0], dtype=np.int32)
        self.original_indices = np.arange(self.W.shape[0], dtype=np.int32)
        self.lp_runs = 0
        self.lp_builds = 0

    def _solve(self, cache, key, matrix, costs, column_lower, column_upper,
               row_lower, row_upper, indices):
        solver = cache.get(key)
        if solver is None:
            solver = _pass(matrix, costs, column_lower, column_upper,
                           row_lower, row_upper)
            cache[key] = solver
            self.lp_builds += 1
        else:
            if solver.changeRowsBounds(len(indices), indices, row_lower, row_upper) != highspy.HighsStatus.kOk:
                raise ValueError("recourse bound update failed")
        if solver.run() != highspy.HighsStatus.kOk or solver.getModelStatus() != highspy.HighsModelStatus.kOptimal:
            raise ValueError("recourse LP failed")
        self.lp_runs += 1
        solution = solver.getSolution()
        if not solution.dual_valid or not solver.getBasis().valid:
            raise ValueError("missing LP dual or valid basis")
        return solver, solution

    def feasibility(self, x, deltas):
        low, high = self._bounds(x, deltas)
        row_lower = np.r_[low[self.lo_indices],
                          np.full(len(self.hi_indices), -highspy.kHighsInf)]
        row_upper = np.r_[np.full(len(self.lo_indices), highspy.kHighsInf),
                          high[self.hi_indices]]
        solver, solution = self._solve(
            self.feasibility_solvers, id(deltas), self.elastic,
            np.r_[np.zeros(len(self.q)), 1.0], np.r_[self.ylow, 0.0],
            np.r_[self.yhigh, highspy.kHighsInf], row_lower, row_upper,
            self.elastic_indices)
        dual = np.asarray(solution.row_dual)
        gradient = -(self.T[self.lo_indices].T @ dual[:len(self.lo_indices)] +
                     self.T[self.hi_indices].T @ dual[len(self.lo_indices):])
        violation = float(solver.getInfo().objective_function_value)
        if abs(violation - solution.col_value[-1]) > 1e-6:
            raise ValueError("elastic primal objective mismatch")
        return violation, np.asarray(gradient).ravel()

    def optimize(self, x, deltas):
        low, high = self._bounds(x, deltas)
        solver, solution = self._solve(
            self.optimality_solvers, id(deltas), self.W, self.q,
            self.ylow, self.yhigh, low, high, self.original_indices)
        gradient = -(self.T.T @ np.asarray(solution.row_dual))
        return (float(solver.getInfo().objective_function_value),
                np.asarray(gradient).ravel(), np.asarray(solution.col_value))


def diagnostic(archive: Path, scenario_count: int, budget_s: float):
    start = perf_counter()
    source = load_source(archive, scenario_count)
    parsing_s = perf_counter() - start
    remaining = max(0.0, budget_s - parsing_s - 0.1)
    # Recourse construction and all solves are charged inside exploratory.
    result = exploratory(source, budget_s=remaining, max_iterations=1000,
                         recourse_type=WarmRecourse)
    result.update({"protocol": "v0.0.65 basis reuse, nonblind mechanism diagnostic",
                   "scenario_count": scenario_count, "parsing_s": parsing_s,
                   "total_elapsed_s": perf_counter() - start,
                   "scope": "same core as SEMI2; no independent holdout or speedup claim"})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenarios", type=int, choices=(2, 3, 4), default=3)
    parser.add_argument("--budget-s", type=float, default=20.0)
    args = parser.parse_args()
    result = diagnostic(args.archive, args.scenarios, args.budget_s)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"elapsed_s": result["total_elapsed_s"],
                      "iterations": len(result["iterations"]),
                      "best": result["best_original_feasible"]}, indent=2))
