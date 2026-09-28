from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns

from neumann1.adversarial_v044 import exact_schur_witness
from neumann1.adversarial_v044_dataset import ALTERNATIVE_CELLS, HIGH_CELLS
from neumann1.anti_shortcut_dataset import CONTROL_CELLS
from neumann1.cached_cost_v046 import execute_v046
from neumann1.cached_cost_v046_dataset import prior_v046_signatures, v046_final_examples
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.schur_cost_v045 import execute_v045
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


def run() -> dict[str, object]:
    items = v046_final_examples()
    signatures = {item.example.signature for item in items}
    fresh = len(signatures) == len(items) and signatures.isdisjoint(prior_v046_signatures())
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
        methods = {
            "F1": lambda: execute_peeling(example, frozen_scorer=scorer, indexed=True),
            "F2": lambda: execute_v045(example, frozen_scorer=scorer),
            "F3": lambda: execute_v046(example, frozen_scorer=scorer),
        }
        times = {name: [] for name in methods}
        outputs = {}
        names = tuple(methods)
        for repetition in range(3):
            for name in names[(index+repetition) % 3:] + names[:(index+repetition) % 3]:
                start = perf_counter_ns()
                result = methods[name]()
                times[name].append((perf_counter_ns()-start)/1_000_000)
                if name in outputs and outputs[name] != result:
                    raise AssertionError("nondeterministic method output")
                outputs[name] = result
        f1, f2, f3 = (outputs[name] for name in names)
        baseline, baseline_counts = solve_exact_gauss_jordan(example.full_system)
        verified, _ = verify_exact_full_system(example.full_system, baseline)
        old_ms, mid_ms, new_ms = (median(times[name]) for name in names)
        row = {
            "k": example.core_dimension, "n": example.apparent_dimension,
            "verified": verified and all(result.verified and result.answer == baseline
                                        for result in (f1, f2, f3)),
            "f1_keys": (f1.local_keys, f1.block_keys),
            "f2_keys": (f2.local_keys, f2.block_keys),
            "f3_keys": (f3.local_keys, f3.block_keys),
            "f1_dimension": f1.retained_dimension,
            "f2_dimension": f2.retained_dimension,
            "f3_dimension": f3.retained_dimension,
            "f1_ops": f1.solver_ops, "f2_ops": f2.solver_ops, "f3_ops": f3.solver_ops,
            "f2_pairs": f2.pair_examinations,
            "f3_pairs": f3.pair_examinations,
            "f3_stale_pops": f3.stale_heap_pops,
            "f2_derivations": f2.derivations, "f3_derivations": f3.derivations,
            "f2_checkers": f2.checkers, "f3_checkers": f3.checkers,
            "f2_posting_edges": f2.posting_edges, "f3_posting_edges": f3.posting_edges,
            "f2_posting_updates": f2.posting_updates,
            "f3_posting_updates": f3.posting_updates,
            "f1_rejections": f1.rejected_materializations,
            "f2_rejections": f2.rejected_materializations,
            "f3_rejections": f3.rejected_materializations,
            "f1_attempts": f1.materialization_attempts,
            "f2_attempts": f2.materialization_attempts,
            "f3_attempts": f3.materialization_attempts,
            "f1_median_ms": old_ms, "f2_median_ms": mid_ms,
            "f3_median_ms": new_ms,
            "f3_f2_ratio": new_ms/mid_ms,
            "f3_f1_ratio": new_ms/old_ms,
        }
        if item.arm == "high_degree":
            oracle = materialize_mixed_reference(example)
            if oracle is None or not oracle.verified or not oracle.ground_truth_equivalent:
                raise AssertionError("exact reference failed")
            row.update({"oracle_equal": oracle.full_answer == baseline,
                        "oracle_positive": baseline_counts.arithmetic_ops > oracle.solver_counts.arithmetic_ops,
                        "oracle_dimension": oracle.retained_system.dimension,
                        "oracle_ops": oracle.solver_counts.arithmetic_ops})
        elif item.arm == "alternatives":
            witnesses = [exact_schur_witness(example.full_system, item.witness.row_pair, pair)
                         for pair in item.witness.target_pairs]
            row["two_valid_witnesses"] = all(w and w.verified and w.answer == baseline
                                             and w.retained_solver_ops < baseline_counts.arithmetic_ops
                                             for w in witnesses)
        grouped[item.arm].append(row)

    fields = ("f2_pairs", "f3_pairs", "f3_stale_pops", "f2_derivations", "f3_derivations",
              "f2_checkers", "f3_checkers", "f2_posting_edges", "f3_posting_edges",
              "f2_posting_updates", "f3_posting_updates", "f1_ops", "f2_ops", "f3_ops")
    summaries = {}
    for arm, arm_rows in grouped.items():
        summaries[arm] = {
            "count": len(arm_rows),
            "verified": all(row["verified"] for row in arm_rows),
            "rejected_materializations": {name: sum(row[f"{name}_rejections"] for row in arm_rows)
                                          for name in ("f1", "f2", "f3")},
            "materialization_attempts": {name: sum(row[f"{name}_attempts"] for row in arm_rows)
                                         for name in ("f1", "f2", "f3")},
            "median_f3_f2_runtime_ratio": median(row["f3_f2_ratio"] for row in arm_rows),
            "median_f3_f1_runtime_ratio": median(row["f3_f1_ratio"] for row in arm_rows),
            "median_f1_ms": median(row["f1_median_ms"] for row in arm_rows),
            "median_f2_ms": median(row["f2_median_ms"] for row in arm_rows),
            "median_f3_ms": median(row["f3_median_ms"] for row in arm_rows),
            **{f"mean_{field}": mean(row[field] for row in arm_rows) for field in fields},
        }
    high = grouped["high_degree"]
    alt = grouped["alternatives"]
    controls = grouped["control"]
    high_equal = all(row["f3_keys"] == row["f2_keys"]
                     and row["f3_dimension"] == row["f2_dimension"] == row["oracle_dimension"]
                     and row["f3_ops"] == row["f2_ops"] == row["oracle_ops"]
                     for row in high)
    dense_equal = all(row["f3_keys"] == row["f1_keys"]
                      and row["f3_dimension"] == row["f1_dimension"]
                      and row["f3_ops"] == row["f1_ops"] for row in alt)
    controls_equal = all(row["f3_keys"] == row["f1_keys"]
                         and row["f3_dimension"] == row["f1_dimension"] == row["n"]
                         and row["f3_ops"] == row["f1_ops"]
                         and row["f3_rejections"] == 0 for row in controls)
    summaries["high_degree"].update({
        "exact_f2_oracle_equivalence": high_equal,
        "oracle_verified": all(row["oracle_equal"] and row["oracle_positive"] for row in high),
        "derivation_ratio": summaries["high_degree"]["mean_f3_derivations"]
                            / summaries["high_degree"]["mean_f2_derivations"],
        "checker_ratio": summaries["high_degree"]["mean_f3_checkers"]
                         / summaries["high_degree"]["mean_f2_checkers"],
        "cells": {
            f"{k}x{n}": {"count": len(cell),
                         "equivalent": all(row["f3_keys"] == row["f2_keys"]
                                           and row["f3_ops"] == row["oracle_ops"] for row in cell),
                         "median_f3_f1_runtime_ratio": median(row["f3_f1_ratio"] for row in cell)}
            for k, n in HIGH_CELLS
            for cell in [[row for row in high if (row["k"], row["n"]) == (k, n)]]
        },
    })
    summaries["alternatives"].update({
        "exact_f1_abstention": dense_equal,
        "two_valid_witnesses": sum(row["two_valid_witnesses"] for row in alt),
    })
    summaries["control"]["exact_f1_abstention"] = controls_equal
    valid_family = (len(items) == 224 and fresh and cells_complete
                    and all(s["verified"] for s in summaries.values())
                    and summaries["high_degree"]["oracle_verified"]
                    and summaries["alternatives"]["two_valid_witnesses"] == 96)
    decision = ("INVALID_FAMILY" if not valid_family else
                "CACHE_CORRECT" if high_equal and dense_equal and controls_equal
                and summaries["high_degree"]["derivation_ratio"] <= 0.5
                and summaries["high_degree"]["checker_ratio"] <= 0.5
                else "CACHE_FAILED")
    return {"experiment": "v0.0.46 cached exact candidates and dense abstention",
            "count": len(items), "fresh_signatures": fresh,
            "cells_complete": cells_complete, "decision": decision,
            "arms": summaries,
            "timing_environment": {"pythonhashseed": os.environ.get("PYTHONHASHSEED"),
                                   "omp_num_threads": os.environ.get("OMP_NUM_THREADS")},
            "boundary": "Paired end-to-end local wall time, not energy or peak RAM. Exact candidate cache and heap still have construction/maintenance costs; no learned model."}


if __name__ == "__main__":
    result = run()
    path = Path("docs/experiments/results/v046_first_audit.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
