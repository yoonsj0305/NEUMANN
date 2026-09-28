from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from neumann1.adversarial_v044 import exact_schur_witness
from neumann1.adversarial_v044_dataset import (
    ALTERNATIVE_CELLS, HIGH_CELLS, prior_v044_signatures, v044_final_examples,
)
from neumann1.anti_shortcut_dataset import CONTROL_CELLS
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


def _mean(rows: list[dict[str, object]], name: str) -> float:
    return mean(row[name] for row in rows)


def run() -> dict[str, object]:
    items = v044_final_examples()
    signatures = {item.example.signature for item in items}
    fresh = len(signatures) == len(items) and signatures.isdisjoint(prior_v044_signatures())
    cells_complete = all(
        sum(item.arm == arm and (item.example.core_dimension, item.example.apparent_dimension) == cell
            for item in items) == count
        for arm, cells, count in (("high_degree", HIGH_CELLS, 24),
                                  ("alternatives", ALTERNATIVE_CELLS, 48),
                                  ("control", CONTROL_CELLS, 16))
        for cell in cells
    )
    scorer = fit_frozen_v033_scorer()
    rows: dict[str, list[dict[str, object]]] = {arm: [] for arm in
                                               ("high_degree", "alternatives", "control")}
    for item in items:
        example = item.example
        system = example.full_system
        baseline_answer, baseline_counts = solve_exact_gauss_jordan(system)
        baseline_verified, _ = verify_exact_full_system(system, baseline_answer)
        result = execute_peeling(example, frozen_scorer=scorer, indexed=True)
        common = {
            "k": example.core_dimension, "n": example.apparent_dimension,
            "verified": baseline_verified and result.verified and result.answer == baseline_answer,
            "rejections": result.rejected_materializations,
            "eliminated": example.apparent_dimension - result.retained_dimension,
            "baseline_ops": baseline_counts.arithmetic_ops,
            "final_ops": result.solver_ops,
            "pair_examinations": result.row_pair_examinations,
            "posting_edges": result.posting_edges,
            "posting_updates": result.posting_updates,
            "derivations": result.derivation_calls,
            "checkers": result.checker_calls,
        }
        if item.arm == "high_degree":
            oracle = materialize_mixed_reference(example)
            if oracle is None or not oracle.verified or not oracle.ground_truth_equivalent:
                raise AssertionError("high-incidence exact reference failed")
            degrees = [sum(row[system.variables.index(name)] != 0 for row in system.A)
                       for name in item.high_targets]
            oracle_ops = oracle.solver_counts.arithmetic_ops
            common.update({
                "six_incidence_targets": sum(degree == 6 for degree in degrees),
                "oracle_verified": oracle.full_answer == baseline_answer,
                "oracle_ops": oracle_ops,
                "positive_oracle_savings": baseline_counts.arithmetic_ops > oracle_ops,
                "elimination_recovery": common["eliminated"] / example.oracle_elimination_count,
                "solver_savings_recovery": (
                    (baseline_counts.arithmetic_ops-result.solver_ops)
                    / (baseline_counts.arithmetic_ops-oracle_ops)
                    if baseline_counts.arithmetic_ops > oracle_ops else None
                ),
            })
        elif item.arm == "alternatives":
            witness_results = [exact_schur_witness(system, item.witness.row_pair, pair)
                               for pair in item.witness.target_pairs]
            valid_witnesses = all(
                witness is not None and witness.verified
                and witness.answer == baseline_answer
                and witness.retained_solver_ops < baseline_counts.arithmetic_ops
                for witness in witness_results
            ) and item.witness.target_pairs[0] != item.witness.target_pairs[1]
            common.update({
                "two_valid_positive_witnesses": valid_witnesses,
                "witness_retained_solver_ops": [w.retained_solver_ops if w else None
                                                for w in witness_results],
                "witness_construction_ops": [w.construction_ops if w else None
                                             for w in witness_results],
                "missed_both": valid_witnesses and common["eliminated"] == 0,
            })
        rows[item.arm].append(common)

    high_cells = {}
    for k, n in HIGH_CELLS:
        subset = [row for row in rows["high_degree"] if (row["k"], row["n"]) == (k, n)]
        high_cells[f"{k}x{n}"] = {
            "count": len(subset),
            "mean_elimination_recovery": _mean(subset, "elimination_recovery"),
            "mean_solver_savings_recovery": _mean(subset, "solver_savings_recovery"),
            "missed_any_elimination": sum(row["elimination_recovery"] < 1 for row in subset),
        }
    summaries = {}
    for arm, arm_rows in rows.items():
        summaries[arm] = {
            "count": len(arm_rows),
            "verified": all(row["verified"] for row in arm_rows),
            "rejected_materializations": sum(row["rejections"] for row in arm_rows),
            "mean_eliminated": _mean(arm_rows, "eliminated"),
            "mean_baseline_ops": _mean(arm_rows, "baseline_ops"),
            "mean_final_solver_ops": _mean(arm_rows, "final_ops"),
            "mean_pair_examinations": _mean(arm_rows, "pair_examinations"),
            "mean_posting_edges": _mean(arm_rows, "posting_edges"),
            "mean_posting_updates": _mean(arm_rows, "posting_updates"),
            "mean_derivations": _mean(arm_rows, "derivations"),
            "mean_checkers": _mean(arm_rows, "checkers"),
        }
    high = rows["high_degree"]
    alt = rows["alternatives"]
    summaries["high_degree"].update({
        "cells": high_cells,
        "six_incidence_targets": sum(row["six_incidence_targets"] for row in high),
        "oracle_verified": all(row["oracle_verified"] for row in high),
        "positive_oracle_savings_each": all(row["positive_oracle_savings"] for row in high),
        "mean_oracle_solver_ops": _mean(high, "oracle_ops"),
        "mean_elimination_recovery": _mean(high, "elimination_recovery"),
        "mean_solver_savings_recovery": _mean(high, "solver_savings_recovery"),
        "missed_any_elimination": sum(row["elimination_recovery"] < 1 for row in high),
    })
    summaries["alternatives"].update({
        "two_valid_positive_witnesses": sum(row["two_valid_positive_witnesses"] for row in alt),
        "missed_both": sum(row["missed_both"] for row in alt),
        "mean_witness_retained_solver_ops": [mean(row["witness_retained_solver_ops"][i]
                                                  for row in alt) for i in (0, 1)],
        "mean_witness_construction_ops": [mean(row["witness_construction_ops"][i]
                                                  for row in alt) for i in (0, 1)],
    })
    valid_family = (
        len(items) == 224 and fresh and cells_complete
        and all(summaries[arm]["verified"] for arm in rows)
        and summaries["high_degree"]["six_incidence_targets"] == 192
        and summaries["high_degree"]["oracle_verified"]
        and summaries["high_degree"]["positive_oracle_savings_each"]
        and summaries["alternatives"]["two_valid_positive_witnesses"] == 96
        and all(row["eliminated"] == 0 and row["rejections"] == 0
                for row in rows["control"])
    )
    if not valid_family:
        decision = "INVALID_FAMILY"
    elif (summaries["high_degree"]["missed_any_elimination"] > 0
          and summaries["alternatives"]["missed_both"] > 0):
        decision = "BOUNDARY_CONFIRMED"
    else:
        decision = "BOUNDARY_NOT_REPRODUCED"
    return {
        "experiment": "v0.0.44 frozen indexed-peeling adversarial boundary audit",
        "count": len(items), "fresh_signatures": fresh,
        "cells_complete": cells_complete,
        "decision": decision, "arms": summaries,
        "boundary": "Exact synthetic systems. Schur witnesses are independent reference alternatives, not F1 actions. Retained-solver operation savings exclude Schur construction, routing, checking, reconstruction and verification.",
    }


if __name__ == "__main__":
    result = run()
    path = Path("docs/experiments/results/v044_first_audit.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
