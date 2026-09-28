from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns

from neumann1.anti_shortcut_dataset import ACTIVE_CELLS, ARMS, CONTROL_CELLS, FINAL_PER_CELL
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.indexed_peeling_v043_dataset import prior_v043_signatures, v043_final_examples
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan


def run() -> dict[str, object]:
    examples = v043_final_examples()
    scorer = fit_frozen_v033_scorer()
    signatures = {example.signature for _, example in examples}
    fresh = len(signatures) == len(examples) and signatures.isdisjoint(prior_v043_signatures())
    cells_complete = all(
        sum(a == arm and (e.core_dimension, e.apparent_dimension) == cell
            for a, e in examples) == FINAL_PER_CELL
        for arm, cells in (("control", CONTROL_CELLS), *((name, ACTIVE_CELLS) for name in ARMS))
        for cell in cells
    )
    rows: dict[str, list[dict[str, object]]] = {arm: [] for arm in (*ARMS, "control")}
    for index, (arm, example) in enumerate(examples):
        measured = {False: [], True: []}
        outputs = {}
        for repeat in range(3):
            for indexed in ((False, True) if (index + repeat) % 2 == 0 else (True, False)):
                start = perf_counter_ns()
                result = execute_peeling(example, frozen_scorer=scorer, indexed=indexed)
                elapsed = perf_counter_ns() - start
                measured[indexed].append(elapsed / 1_000_000)
                if indexed in outputs and result != outputs[indexed]:
                    raise AssertionError("execution path is nondeterministic")
                outputs[indexed] = result
        old, new = outputs[False], outputs[True]
        baseline, full_counts = solve_exact_gauss_jordan(example.full_system)
        oracle = materialize_mixed_reference(example)
        if oracle is None or not oracle.verified or not oracle.ground_truth_equivalent:
            raise AssertionError("exact oracle failed")
        old_ms, new_ms = median(measured[False]), median(measured[True])
        rows[arm].append({
            "k": example.core_dimension, "n": example.apparent_dimension,
            "old_verified": old.verified, "new_verified": new.verified,
            "same_local_keys": old.local_keys == new.local_keys,
            "same_block_keys": old.block_keys == new.block_keys,
            "same_answer": old.answer == new.answer == baseline,
            "same_dimension": old.retained_dimension == new.retained_dimension,
            "same_solver_ops": old.solver_ops == new.solver_ops,
            "old_pairs": old.row_pair_examinations, "new_pairs": new.row_pair_examinations,
            "posting_edges": new.posting_edges, "posting_updates": new.posting_updates,
            "old_derivations": old.derivation_calls, "new_derivations": new.derivation_calls,
            "old_checkers": old.checker_calls, "new_checkers": new.checker_calls,
            "old_attempts": old.materialization_attempts,
            "new_attempts": new.materialization_attempts,
            "old_rejections": old.rejected_materializations,
            "new_rejections": new.rejected_materializations,
            "new_eliminations": example.apparent_dimension - new.retained_dimension,
            "oracle_eliminations": example.oracle_elimination_count,
            "baseline_ops": full_counts.arithmetic_ops,
            "oracle_ops": oracle.solver_counts.arithmetic_ops,
            "new_ops": new.solver_ops,
            "old_median_ms": old_ms, "new_median_ms": new_ms,
            "paired_runtime_ratio": new_ms / old_ms,
        })

    summaries = {}
    for arm, arm_rows in rows.items():
        old_pairs = mean(row["old_pairs"] for row in arm_rows)
        new_pairs = mean(row["new_pairs"] for row in arm_rows)
        summaries[arm] = {
            "count": len(arm_rows),
            "equivalent": all(row["same_local_keys"] and row["same_block_keys"]
                              and row["same_answer"] and row["same_dimension"]
                              and row["same_solver_ops"] for row in arm_rows),
            "verified": all(row["old_verified"] and row["new_verified"] for row in arm_rows),
            "old_mean_pairs": old_pairs, "new_mean_pairs": new_pairs,
            "pair_ratio": new_pairs / old_pairs if old_pairs else None,
            "mean_posting_edges": mean(row["posting_edges"] for row in arm_rows),
            "mean_posting_updates": mean(row["posting_updates"] for row in arm_rows),
            "old_mean_derivations": mean(row["old_derivations"] for row in arm_rows),
            "new_mean_derivations": mean(row["new_derivations"] for row in arm_rows),
            "old_mean_checkers": mean(row["old_checkers"] for row in arm_rows),
            "new_mean_checkers": mean(row["new_checkers"] for row in arm_rows),
            "old_attempts": sum(row["old_attempts"] for row in arm_rows),
            "new_attempts": sum(row["new_attempts"] for row in arm_rows),
            "old_rejections": sum(row["old_rejections"] for row in arm_rows),
            "new_rejections": sum(row["new_rejections"] for row in arm_rows),
            "mean_solver_savings_recovery": mean(
                (row["baseline_ops"] - row["new_ops"])
                / (row["baseline_ops"] - row["oracle_ops"])
                for row in arm_rows) if arm != "control" else None,
            "mean_elimination_recovery": mean(
                row["new_eliminations"] / row["oracle_eliminations"]
                for row in arm_rows) if arm != "control" else None,
            "old_median_ms": median(row["old_median_ms"] for row in arm_rows),
            "new_median_ms": median(row["new_median_ms"] for row in arm_rows),
            "median_paired_runtime_ratio": median(row["paired_runtime_ratio"] for row in arm_rows),
        }

    active = [summaries[arm] for arm in ARMS]
    controls = rows["control"]
    gate = (
        len(examples) == 224 and fresh and cells_complete
        and all(row["equivalent"] and row["verified"] for row in active)
        and all(row["pair_ratio"] <= 0.1 for row in active)
        and all(row["old_verified"] and row["new_verified"]
                and row["new_eliminations"] == 0 and row["new_rejections"] == 0
                for row in controls)
        and all(row["new_verified"] for arm_rows in rows.values() for row in arm_rows)
    )
    return {
        "experiment": "v0.0.43 frozen E2 versus incremental indexed peeling",
        "count": len(examples), "fresh_signatures": fresh,
        "cells_complete": cells_complete, "keep_indexed": gate,
        "arms": summaries,
        "boundary": "Paired local timings include routing, discovery, checking, retained solve and original verification; exclude scorer fit, generation, oracle, and benchmark baseline. No energy or peak-memory measurement.",
        "timing_environment": {"pythonhashseed": os.environ.get("PYTHONHASHSEED"),
                               "omp_num_threads": os.environ.get("OMP_NUM_THREADS")},
    }


if __name__ == "__main__":
    result = run()
    destination = Path("docs/experiments/results/v043_first_audit.json")
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
