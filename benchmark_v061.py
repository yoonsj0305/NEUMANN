"""Openly corrective v0.0.60 rerun: only the evaluation ceiling changes."""

import argparse
import json
from pathlib import Path
from statistics import median

from benchmark_v060 import BUDGET_S, GAP_TARGET, audit


CORRECTIVE_CEILING = 6747.32


def corrective_audit(path: Path) -> dict:
    result = audit(path)  # Fresh warmups and three new pairs, same solver path.
    if len(result.get("pairs", [])) != 3:
        return {"protocol": "v0.0.61 post-result correction",
                "original_v060_audit": result,
                "summary": {"decision": "INVALID_CORRECTIVE_AUDIT"}}
    for pair in result["pairs"]:
        for mode in ("native", "candidate"):
            row = pair[mode]
            row["v060_target_reached"] = row["target_reached"]
            row["target_reached"] = bool(
                not row["fallback"] and row["original_objective"] is not None
                and row["original_objective"] <= CORRECTIVE_CEILING
                and row["native_relative_gap"] is not None
                and row["native_relative_gap"] <= GAP_TARGET + 1e-10
                and row["original_primal_violation"] <= 1e-7
                and row["original_integrality_violation"] <= 1e-6
                and row["total_s"] <= BUDGET_S)
    all_target = all(pair[mode]["target_reached"] for pair in result["pairs"]
                     for mode in ("native", "candidate"))
    native = median(pair["native"]["total_s"] for pair in result["pairs"])
    candidate = median(pair["candidate"]["total_s"] for pair in result["pairs"])
    decision = ("CORRECTIVE_LOCAL_ADVANTAGE" if all_target and candidate <= 0.8 * native
                else "NO_CORRECTIVE_LOCAL_ADVANTAGE" if all_target
                else "CORRECTIVE_GATE_UNREACHED")
    result.update({"protocol": "v0.0.61 post-result corrective rerun",
                   "v060_objective_ceiling": result["objective_ceiling"],
                   "objective_ceiling": CORRECTIVE_CEILING,
                   "summary": {"all_six_target_reached": all_target,
                               "native_median_s": native, "candidate_median_s": candidate,
                               "candidate_over_native": candidate / native,
                               "decision": decision}})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mps", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = corrective_audit(args.mps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result["summary"], indent=2))
