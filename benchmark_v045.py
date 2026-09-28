from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns

from neumann1.adversarial_v044 import exact_schur_witness
from neumann1.adversarial_v044_dataset import ALTERNATIVE_CELLS, HIGH_CELLS
from neumann1.anti_shortcut_dataset import CONTROL_CELLS
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.schur_cost_v045 import execute_v045
from neumann1.schur_cost_v045_dataset import prior_v045_signatures, v045_final_examples
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


def run() -> dict[str, object]:
    items = v045_final_examples()
    signatures = {item.example.signature for item in items}
    fresh = len(signatures) == len(items) and signatures.isdisjoint(prior_v045_signatures())
    cells_complete = all(
        sum(item.arm == arm and (item.example.core_dimension, item.example.apparent_dimension) == cell
            for item in items) == count
        for arm, cells, count in (("high_degree", HIGH_CELLS, 24),
                                  ("alternatives", ALTERNATIVE_CELLS, 48),
                                  ("control", CONTROL_CELLS, 16)) for cell in cells
    )
    scorer = fit_frozen_v033_scorer()
    grouped: dict[str, list[dict[str, object]]] = {arm: [] for arm in
                                                ("high_degree", "alternatives", "control")}
    for index, item in enumerate(items):
        example = item.example
        times = {False: [], True: []}
        outputs = {}
        for repetition in range(3):
            for new in ((False, True) if (index+repetition) % 2 == 0 else (True, False)):
                start = perf_counter_ns()
                result = (execute_v045(example, frozen_scorer=scorer) if new else
                          execute_peeling(example, frozen_scorer=scorer, indexed=True))
                times[new].append((perf_counter_ns()-start)/1_000_000)
                if new in outputs and outputs[new] != result:
                    raise AssertionError("execution output drift across paired repetitions")
                outputs[new] = result
        old, new = outputs[False], outputs[True]
        baseline, full_counts = solve_exact_gauss_jordan(example.full_system)
        full_verified, _ = verify_exact_full_system(example.full_system, baseline)
        old_ms = median(times[False])
        new_ms = median(times[True])
        row = {
            "k": example.core_dimension, "n": example.apparent_dimension,
            "verified": full_verified and old.verified and new.verified
                        and old.answer == new.answer == baseline,
            "old_eliminated": example.apparent_dimension-old.retained_dimension,
            "new_eliminated": example.apparent_dimension-new.retained_dimension,
            "mode": new.mode,
            "baseline_ops": full_counts.arithmetic_ops,
            "old_ops": old.solver_ops, "new_ops": new.solver_ops,
            "old_pairs": old.row_pair_examinations, "new_pairs": new.pair_examinations,
            "old_derivations": old.derivation_calls, "new_derivations": new.derivations,
            "old_checkers": old.checker_calls, "new_checkers": new.checkers,
            "old_posting_edges": old.posting_edges, "new_posting_edges": new.posting_edges,
            "old_posting_updates": old.posting_updates, "new_posting_updates": new.posting_updates,
            "old_attempts": old.materialization_attempts,
            "new_attempts": new.materialization_attempts,
            "old_rejections": old.rejected_materializations,
            "new_rejections": new.rejected_materializations,
            "schur_construction_ops": new.schur_construction_ops,
            "old_median_ms": old_ms, "new_median_ms": new_ms,
            "paired_runtime_ratio": new_ms/old_ms,
        }
        if item.arm == "high_degree":
            oracle = materialize_mixed_reference(example)
            if oracle is None or not oracle.verified or not oracle.ground_truth_equivalent:
                raise AssertionError("reference failed")
            row.update({
                "oracle_answer_equal": oracle.full_answer == baseline,
                "oracle_eliminated": example.oracle_elimination_count,
                "oracle_ops": oracle.solver_counts.arithmetic_ops,
                "oracle_positive": full_counts.arithmetic_ops > oracle.solver_counts.arithmetic_ops,
            })
        elif item.arm == "alternatives":
            witnesses = [exact_schur_witness(example.full_system, item.witness.row_pair, pair)
                         for pair in item.witness.target_pairs]
            row["two_valid_witnesses"] = all(
                witness and witness.verified and witness.answer == baseline
                and witness.retained_solver_ops < full_counts.arithmetic_ops
                for witness in witnesses
            ) and item.witness.target_pairs[0] != item.witness.target_pairs[1]
        grouped[item.arm].append(row)

    summaries = {}
    numeric_fields = ("old_eliminated", "new_eliminated", "baseline_ops", "old_ops", "new_ops",
                      "old_pairs", "new_pairs", "old_derivations", "new_derivations",
                      "old_checkers", "new_checkers", "old_posting_edges", "new_posting_edges",
                      "old_posting_updates", "new_posting_updates", "schur_construction_ops")
    for arm, arm_rows in grouped.items():
        summaries[arm] = {
            "count": len(arm_rows),
            "verified": all(row["verified"] for row in arm_rows),
            "modes": {mode: sum(row["mode"] == mode for row in arm_rows)
                      for mode in ("full", "sparse", "schur")},
            "old_attempts": sum(row["old_attempts"] for row in arm_rows),
            "new_attempts": sum(row["new_attempts"] for row in arm_rows),
            "old_rejections": sum(row["old_rejections"] for row in arm_rows),
            "new_rejections": sum(row["new_rejections"] for row in arm_rows),
            "old_median_ms": median(row["old_median_ms"] for row in arm_rows),
            "new_median_ms": median(row["new_median_ms"] for row in arm_rows),
            "median_paired_runtime_ratio": median(row["paired_runtime_ratio"] for row in arm_rows),
            **{f"mean_{key}": mean(row[key] for row in arm_rows) for key in numeric_fields},
        }
    high = grouped["high_degree"]
    alt = grouped["alternatives"]
    summaries["high_degree"].update({
        "oracle_verified": all(row["oracle_answer_equal"] for row in high),
        "positive_oracle_savings_each": all(row["oracle_positive"] for row in high),
        "full_recovery_count": sum(row["new_eliminated"] == row["oracle_eliminated"]
                                   and row["new_ops"] == row["oracle_ops"] for row in high),
        "mean_oracle_ops": mean(row["oracle_ops"] for row in high),
        "cells": {
            f"{k}x{n}": {
                "count": len(cell),
                "full_recovery_count": sum(row["new_eliminated"] == row["oracle_eliminated"]
                                           and row["new_ops"] == row["oracle_ops"] for row in cell),
                "median_paired_runtime_ratio": median(row["paired_runtime_ratio"] for row in cell),
            } for k, n in HIGH_CELLS
            for cell in [[row for row in high if (row["k"], row["n"]) == (k, n)]]
        },
    })
    summaries["alternatives"].update({
        "two_valid_witnesses": sum(row["two_valid_witnesses"] for row in alt),
        "two_variable_recovery_count": sum(row["new_eliminated"] == 2
                                           and row["new_ops"] < row["baseline_ops"] for row in alt),
    })
    controls = grouped["control"]
    valid = (len(items) == 224 and fresh and cells_complete
             and all(summary["verified"] for summary in summaries.values())
             and summaries["high_degree"]["oracle_verified"]
             and summaries["high_degree"]["positive_oracle_savings_each"]
             and summaries["alternatives"]["two_valid_witnesses"] == 96
             and all(row["new_eliminated"] == 0 and row["new_rejections"] == 0 for row in controls))
    decision = ("STRUCTURAL_REPAIR_CONFIRMED" if valid
                and summaries["high_degree"]["full_recovery_count"] == 96
                and summaries["alternatives"]["two_variable_recovery_count"] == 96
                else "REPAIR_FAILED")
    return {
        "experiment": "v0.0.45 exact Schur and incidence-six cost audit",
        "count": len(items), "fresh_signatures": fresh,
        "cells_complete": cells_complete, "decision": decision,
        "arms": summaries,
        "timing_environment": {"pythonhashseed": os.environ.get("PYTHONHASHSEED"),
                               "omp_num_threads": os.environ.get("OMP_NUM_THREADS")},
        "boundary": "Paired full-path wall time includes routing, search, exact checking, Schur construction, retained solve, reconstruction and original verification. Retained solver arithmetic is not total cost. No energy or peak RAM measurement.",
    }


if __name__ == "__main__":
    result = run()
    path = Path("docs/experiments/results/v045_first_audit.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
