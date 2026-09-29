"""Fixed-capability full original-MIP comparison, single inspected instance."""

import argparse
import json
import math
from hashlib import sha256
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import highspy
import numpy as np

from neumann1.affine_lp_v059 import (check_integrality, check_original,
                                     reconstruct, reduce_lp, sparse)


SOURCE_SHA = "94282c38edd6c83bb6c2d788d823fd82f218218e8e07c98d1d1ab42c1e91039e"
BUDGET_S = 20.0
SOLVER_RESERVE_S = 1.0
GAP_TARGET = 0.003
OBJECTIVE_CEILING = 6742.21


def finite_or_none(value: float) -> float | None:
    number = float(value)
    return number if math.isfinite(number) else None


def arm(lp, original_matrix, mode: str, *, allow_fallback: bool = True) -> dict:
    start = perf_counter_ns()
    reduction = None
    fallback = False
    if mode == "candidate":
        try:
            reduction = reduce_lp(lp, retain_integrality=True)
            if len(reduction.eliminated) == 0:
                raise ValueError("no affine reduction")
        except (ValueError, ArithmeticError):
            if not allow_fallback:
                raise
            fallback = True
    elif mode != "native":
        raise ValueError("unknown mode")
    construction_ns = perf_counter_ns() - start
    model = reduction.model if reduction is not None else lp
    solver = highspy.Highs()
    solver.setOptionValue("output_flag", False)
    solver.setOptionValue("threads", 1)
    solver.setOptionValue("mip_rel_gap", GAP_TARGET)
    remaining = BUDGET_S - SOLVER_RESERVE_S - (perf_counter_ns() - start) / 1e9
    solver.setOptionValue("time_limit", max(0.001, remaining))
    if solver.passModel(model) != highspy.HighsStatus.kOk:
        raise ValueError("invalid model passed to HiGHS")
    run_status = solver.run()
    info = solver.getInfo()
    result = solver.getSolution()
    if result.value_valid:
        values = np.asarray(result.col_value)
        x = reconstruct(reduction, values, lp.num_col_) if reduction else values
        violation, objective = check_original(lp, original_matrix, x)
        integrality = check_integrality(lp, x)
        solver_objective = float(info.objective_function_value)
        objective_agreement = abs(objective - solver_objective) / max(1., abs(solver_objective))
        if (not np.isfinite(violation) or not np.isfinite(integrality) or
            not np.isfinite(objective_agreement) or violation > 1e-7 or
            integrality > 1e-6 or objective_agreement > 1e-6):
            # Incorrect candidate reduction is never accepted or relabeled a
            # performance failure; it invalidates the entire audit.
            raise ValueError(f"unsafe original-model answer: {mode} / {violation} / {integrality} / {objective_agreement}")
    else:
        violation = integrality = objective = None
        objective_agreement = None
    elapsed = (perf_counter_ns() - start) / 1e9
    gap = finite_or_none(info.mip_gap)
    target = bool(result.value_valid and elapsed <= BUDGET_S and
                  objective <= OBJECTIVE_CEILING and gap is not None and
                  gap <= GAP_TARGET + 1e-10)
    return {"mode": mode, "total_s": elapsed, "construction_s": construction_ns / 1e9,
            "solver_status": str(solver.getModelStatus()), "run_status": str(run_status),
            "fallback": fallback, "target_reached": target,
            "original_objective": float(objective) if objective is not None else None,
            "original_primal_violation": float(violation) if violation is not None else None,
            "original_integrality_violation": float(integrality) if integrality is not None else None,
            "objective_agreement": float(objective_agreement) if objective_agreement is not None else None,
            "native_dual_bound": finite_or_none(info.mip_dual_bound), "native_relative_gap": gap,
            "native_nodes": int(info.mip_node_count),
            "eliminated": len(reduction.eliminated) if reduction else 0,
            "model_variables": model.num_col_, "model_constraints": model.num_row_,
            "model_nonzeros": len(model.a_matrix_.value_)}


def audit(path: Path) -> dict:
    if sha256(path.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("original source hash mismatch")
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    if h.version() != "1.15.1" or h.readModel(str(path)) != highspy.HighsStatus.kOk:
        raise ValueError("unmatched solver or MPS")
    if (h.getNumCol(), h.getNumRow(), h.getNumNz()) != (2298, 1026, 4496):
        raise ValueError("unexpected source shape")
    lp = h.getLp()
    original_matrix = sparse(lp)
    if sum(kind == highspy.HighsVarType.kInteger for kind in lp.integrality_) != 170:
        raise ValueError("original integrality was lost")
    pairs = []
    try:
        for mode in ("native", "candidate"):
            arm(lp, original_matrix, mode)  # discarded full warmup
        for i in range(3):
            order = ("native", "candidate") if i % 2 == 0 else ("candidate", "native")
            pair = {}
            for mode in order:
                pair[mode] = arm(lp, original_matrix, mode)
            pairs.append(pair)
    except ValueError as exc:
        return {"protocol": "v0.0.60 invalid first audit",
                "source_sha256": SOURCE_SHA, "highs_version": h.version(),
                "completed_pairs": pairs, "error": str(exc),
                "summary": {"decision": "INVALID_MIP_TRANSFORMATION_OR_VERIFICATION"}}
    all_rows = [p[mode] for p in pairs for mode in ("native", "candidate")]
    all_capable = all(r["target_reached"] and not r["fallback"] for r in all_rows)
    native = median(p["native"]["total_s"] for p in pairs)
    candidate = median(p["candidate"]["total_s"] for p in pairs)
    return {"protocol": "v0.0.60 nonblind original-MIP fixed-capability comparison",
            "source_sha256": SOURCE_SHA, "highs_version": h.version(),
            "budget_s": BUDGET_S, "solver_reserve_s": SOLVER_RESERVE_S,
            "relative_gap_target": GAP_TARGET, "objective_ceiling": OBJECTIVE_CEILING,
            "pairs": pairs, "summary": {"all_six_target_reached": all_capable,
                                      "native_median_s": native,
                                      "candidate_median_s": candidate,
                                      "candidate_over_native": candidate / native,
                                      "decision": ("LOCAL_MIP_ADVANTAGE" if all_capable and
                                                   candidate / native <= 0.8 else
                                                   "NO_LOCAL_MIP_ADVANTAGE")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mps", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.mps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result["summary"], indent=2))
