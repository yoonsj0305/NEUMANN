from __future__ import annotations

import json
from statistics import mean

from neumann1.anti_shortcut_dataset import (
    ACTIVE_CELLS, ARMS, CONTROL_CELLS, FINAL_PER_CELL,
)
from neumann1.anti_shortcut_v042 import E_METHODS, observe_peeling_method
from neumann1.anti_shortcut_v042_dataset import (
    prior_v042_signatures, v042_final_examples,
)
from neumann1.block_discovery import (
    DISCOVERY_METHODS, observe_discovery_method,
)
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def _visibility(examples, method):
    visible = total = 0
    for example in examples:
        system = example.full_system
        incidence = {
            name: sum(row[col] != 0 for row in system.A)
            for col, name in enumerate(system.variables)
        }
        for block in example.oracle_blocks:
            for row in block.row_indices:
                for target in block.targets:
                    total += 1
                    col = system.variables.index(target)
                    if (system.A[row][col] != 0 and
                        (incidence[target] == 2 if method == "E1_static_nonunit"
                         else 2 <= incidence[target] <= 4)):
                        visible += 1
    return visible / total if total else None


def _summarize_e(rows):
    active = [row for row in rows if row.oracle_elimination_count > 0]
    grouped = {}
    for row in rows:
        grouped.setdefault((row.core_dimension, row.apparent_dimension), []).append(row)
    return {
        "count": len(rows),
        "verified_retention": mean(row.verified for row in rows),
        "unsafe_accepted_reductions": sum(row.unsafe_accepted_reductions for row in rows),
        "mean_solver_savings_recovery": mean(row.solver_savings_recovery for row in active)
            if active else None,
        "mean_elimination_recovery": mean(row.elimination_recovery for row in active)
            if active else None,
        "block_label_recall": (sum(row.block_true_positive_count for row in rows)
                               / sum(row.block_reference_count for row in rows))
            if any(row.block_reference_count for row in rows) else None,
        "mean_final_solver_ops": mean(row.final_solver_ops for row in rows),
        "mean_row_pair_examinations": mean(row.row_pair_examinations for row in rows),
        "mean_derivation_calls": mean(row.derivation_calls for row in rows),
        "mean_checker_calls": mean(row.checker_calls for row in rows),
        "final_materialization_attempts": sum(row.final_materialization_attempts for row in rows),
        "rejected_joint_materializations": sum(row.rejected_joint_materializations for row in rows),
        "cells": [
            {"k": k, "n": n, "count": len(cell),
             "verified_retention": mean(row.verified for row in cell),
             "mean_solver_savings_recovery": mean(
                 row.solver_savings_recovery for row in cell)
                if cell[0].oracle_elimination_count else None,
             "mean_elimination_recovery": mean(
                 row.elimination_recovery for row in cell)
                if cell[0].oracle_elimination_count else None}
            for (k, n), cell in sorted(grouped.items())
        ],
    }


def run() -> dict[str, object]:
    examples = v042_final_examples()
    scorer = fit_frozen_v033_scorer()
    signatures = {example.signature for _, example in examples}
    fresh = len(signatures) == len(examples) and signatures.isdisjoint(
        prior_v042_signatures())
    cells_complete = all(
        sum(a == arm and (e.core_dimension, e.apparent_dimension) == cell
            for a, e in examples) == FINAL_PER_CELL
        for arm, cells in (("control", CONTROL_CELLS),
                           *((name, ACTIVE_CELLS) for name in ARMS))
        for cell in cells
    )
    oracle_verified = methods_verified = controls_unchanged = True
    unsafe_zero = True
    arms = {}
    for arm in (*ARMS, "control"):
        items = tuple(e for a, e in examples if a == arm)
        references = tuple(materialize_mixed_reference(e) for e in items)
        valid_oracles = all(row is not None and row.verified
                            and row.ground_truth_equivalent for row in references)
        if not valid_oracles:
            raise AssertionError(f"{arm} oracle failure")
        oracle_verified &= valid_oracles
        old = {
            method: tuple(observe_discovery_method(e, method,
                          frozen_scorer=scorer) for e in items)
            for method in DISCOVERY_METHODS
        }
        new = {
            method: tuple(observe_peeling_method(e, method,
                          frozen_scorer=scorer) for e in items)
            for method in E_METHODS
        }
        methods_verified &= all(
            all(row.final_verified for row in rows) for rows in old.values()
        ) and all(all(row.verified for row in rows) for rows in new.values())
        unsafe_zero &= all(
            all(row.unsafe_accepted_reductions == 0 for row in rows)
            for rows in (*old.values(), *new.values())
        )
        if arm == "control":
            controls_unchanged &= all(
                all(row.total_eliminated_variables == 0 for row in rows)
                for rows in old.values()
            ) and all(all(row.accepted_local_count == 0
                          and row.accepted_block_count == 0 for row in rows)
                      for rows in new.values())

        baseline = {
            method: {
                "verified_retention": mean(row.final_verified for row in rows),
                "mean_solver_savings_recovery": mean(
                    row.solver_savings_recovery for row in rows)
                    if arm != "control" else None,
                "mean_final_solver_ops": mean(row.final_solver_ops for row in rows),
                "rejected_joint_materializations": sum(
                    row.rejected_materialization_count for row in rows),
            } for method, rows in old.items()
        }
        new_stats = {method: _summarize_e(rows) for method, rows in new.items()}
        e2 = new_stats["E2_residual_peeling"]
        positive_oracle = all(
            row.baseline_solver_ops > row.oracle_solver_ops
            for row in new[E_METHODS[0]]) if arm != "control" else True
        if not positive_oracle:
            decision = "INVALID_FAMILY"
        elif arm == "control":
            decision = "CONTROL"
        elif (e2["mean_solver_savings_recovery"] >= 0.95
              and e2["mean_elimination_recovery"] >= 0.95
              and e2["verified_retention"] == 1
              and e2["unsafe_accepted_reductions"] == 0):
            decision = "DETERMINISTIC_SUFFICIENT"
        else:
            decision = "RESIDUAL_HEADROOM"
        if arm == "coefficient" and _visibility(items, E_METHODS[0]) < 1:
            decision = "PARSER_REPAIR_FAILED"
        arms[arm] = {
            "count": len(items),
            "oracle_verified": valid_oracles,
            "oracle_positive_savings_each_example": positive_oracle,
            "nonunit_candidate_visibility_e1": _visibility(items, E_METHODS[0]),
            "nonunit_candidate_visibility_e2": _visibility(items, E_METHODS[1]),
            "decision": decision,
            "old_baselines": baseline,
            "new_methods": new_stats,
        }
    return {
        "experiment": "v0.0.42 deterministic nonunit visibility and residual peeling",
        "count": len(examples),
        "fresh_signatures": fresh,
        "cells_complete": cells_complete,
        "oracle_verified": oracle_verified,
        "methods_verified": methods_verified,
        "unsafe_accepted_reductions_zero": unsafe_zero,
        "controls_unchanged": controls_unchanged,
        "keep_audit": (len(examples) == 224 and fresh and cells_complete
                       and oracle_verified and methods_verified
                       and unsafe_zero and controls_unchanged),
        "arms": arms,
        "boundary": "Generated exact linear systems; final solver ops exclude discovery, checker, and router work.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
