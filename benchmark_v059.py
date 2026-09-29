"""Paired full-path LP relaxation audit after frozen v0.0.59 protocol."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import highspy
import numpy as np

from neumann1.affine_lp_v059 import check_original, reconstruct, reduce_lp, sparse


SOURCE_SHA = "94282c38edd6c83bb6c2d788d823fd82f218218e8e07c98d1d1ab42c1e91039e"


def trial(lp, original_matrix, mode: str) -> dict:
    start = perf_counter_ns()
    failed = False
    reduction = None
    try:
        if mode == "candidate":
            reduction = reduce_lp(lp)
            to_solve = reduction.model
        elif mode == "native":
            to_solve = lp
        else:
            raise ValueError("unknown mode")
        solver = highspy.Highs()
        solver.setOptionValue("output_flag", False)
        solver.setOptionValue("threads", 1)
        if solver.passModel(to_solve) != highspy.HighsStatus.kOk:
            raise ValueError("passModel failed")
        if solver.run() != highspy.HighsStatus.kOk or solver.getModelStatus() != highspy.HighsModelStatus.kOptimal:
            raise ValueError("LP solve failed")
        values = np.asarray(solver.getSolution().col_value)
        x = (reconstruct(reduction, values, lp.num_col_) if reduction else values)
        violation, objective = check_original(lp, original_matrix, x)
        if not np.isfinite(objective) or violation > 1e-7:
            raise ValueError("original LP verification failed")
    except Exception:
        if mode != "candidate":
            raise
        failed = True
        # No unsafe accepted reduction. Every discarded operation above
        # remains within the timed path before this native fallback.
        return {**trial(lp, original_matrix, "native"),
                "mode": "candidate", "fallback": True,
                "total_ns": perf_counter_ns() - start}
    return {"mode": mode, "total_ns": perf_counter_ns() - start,
            "fallback": failed, "objective_original": float(objective),
            "max_scaled_original_violation": float(violation),
            "eliminated": len(reduction.eliminated) if reduction else 0,
            "reduced_variables": reduction.model.num_col_ if reduction else lp.num_col_,
            "reduced_constraints": reduction.model.num_row_ if reduction else lp.num_row_,
            "reduced_nonzeros": len(reduction.model.a_matrix_.value_) if reduction else
                                len(lp.a_matrix_.value_),
            "rewritten_bound_rows": reduction.rewritten_bound_rows if reduction else 0}


def audit(path: Path) -> dict:
    if sha256(path.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("wrong original MPS")
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    if h.version() != "1.15.1" or h.readModel(str(path)) != highspy.HighsStatus.kOk:
        raise ValueError("unmatched HiGHS version or unreadable MPS")
    if (h.getNumCol(), h.getNumRow(), h.getNumNz()) != (2298, 1026, 4496):
        raise ValueError("wrong original model shape")
    for col in range(h.getNumCol()):
        h.changeColIntegrality(col, highspy.HighsVarType.kContinuous)
    lp = h.getLp()
    original_matrix = sparse(lp)
    for mode in ("native", "candidate"):
        trial(lp, original_matrix, mode)
    pairs = []
    for i in range(7):
        order = ("native", "candidate") if i % 2 == 0 else ("candidate", "native")
        pair = {mode: trial(lp, original_matrix, mode) for mode in order}
        if (pair["candidate"]["fallback"] or
            abs(pair["candidate"]["objective_original"] - pair["native"]["objective_original"])
            > 1e-6 * max(1., abs(pair["native"]["objective_original"]))):
            raise ValueError(f"invalid candidate paired trial {i}")
        pairs.append(pair)
    native = median(p["native"]["total_ns"] for p in pairs)
    candidate = median(p["candidate"]["total_ns"] for p in pairs)
    return {"protocol": "v0.0.59 nonblind LP-relaxation paired path",
            "source_sha256": SOURCE_SHA, "highs_version": h.version(),
            "integrality": "all relaxed to continuous before paired timing",
            "pairs": pairs, "summary": {"native_median_ns": native,
                                      "candidate_median_ns": candidate,
                                      "candidate_over_native": candidate / native,
                                      "decision": ("LOCAL_COMPRESSION_ADVANTAGE"
                                                   if candidate / native <= 0.8
                                                   else "NO_LOCAL_ADVANTAGE")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mps", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.mps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2))
