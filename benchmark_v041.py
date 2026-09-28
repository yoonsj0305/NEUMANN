from __future__ import annotations

import json
from statistics import mean

from neumann1.anti_shortcut_dataset import (
    ACTIVE_CELLS, ARMS, CONTROL_CELLS, FINAL_PER_CELL,
    prior_v041_signatures, v041_final_examples,
)
from neumann1.block_discovery import (
    DISCOVERY_METHODS, aggregate_discovery_method, observe_discovery_method,
    select_best_deterministic,
)
from neumann1.learned_compression import enumerate_affine_candidates
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def _visibility(example) -> tuple[int, int]:
    visible = {candidate.key for candidate in
               enumerate_affine_candidates(example.full_system)}
    declared = {
        (row, target)
        for block in example.oracle_blocks
        for row in block.row_indices
        for target in block.targets
    }
    return len(visible & declared), len(declared)


def run() -> dict[str, object]:
    examples = v041_final_examples()
    scorer = fit_frozen_v033_scorer()
    signatures = {example.signature for _, example in examples}
    fresh = len(signatures) == len(examples) and signatures.isdisjoint(
        prior_v041_signatures()
    )
    cells_complete = all(
        sum(1 for candidate_arm, example in examples
            if candidate_arm == arm and
            (example.core_dimension, example.apparent_dimension) == cell)
        == FINAL_PER_CELL
        for arm, cells in (("control", CONTROL_CELLS),
                           *((name, ACTIVE_CELLS) for name in ARMS))
        for cell in cells
    )

    arms: dict[str, object] = {}
    oracle_all_verified = True
    methods_all_verified = True
    zero_unsafe = True
    for arm in (*ARMS, "control"):
        arm_examples = tuple(e for a, e in examples if a == arm)
        oracle = tuple(materialize_mixed_reference(e) for e in arm_examples)
        oracle_ok = all(r is not None and r.verified and
                        r.ground_truth_equivalent for r in oracle)
        oracle_all_verified &= oracle_ok
        if not oracle_ok:
            raise AssertionError(f"{arm}: exact oracle failed")

        observations = {
            method: tuple(observe_discovery_method(e, method,
                          frozen_scorer=scorer) for e in arm_examples)
            for method in DISCOVERY_METHODS
        }
        if arm == "control":
            aggregates = {
                method: {
                    "count": len(rows),
                    "verified_retention": mean(row.final_verified for row in rows),
                    "unsafe_accepted_reduction_count": sum(
                        row.unsafe_accepted_reductions for row in rows),
                    "mean_final_solver_ops": mean(row.final_solver_ops for row in rows),
                    "mean_eliminations": mean(row.total_eliminated_variables for row in rows),
                } for method, rows in observations.items()
            }
            best_name, best_agg = None, None
        else:
            aggregates = {method: aggregate_discovery_method(rows)
                          for method, rows in observations.items()}
            best_name, best_agg = select_best_deterministic(aggregates)
        counts = [_visibility(e) for e in arm_examples]
        visibility = (sum(x for x, _ in counts) /
                      sum(y for _, y in counts)) if any(y for _, y in counts) else None
        oracle_savings = [row.oracle_solver_savings for row in
                          observations[DISCOVERY_METHODS[0]]]
        valid_savings = all(x > 0 for x in oracle_savings) if arm != "control" else True
        arm_safe = all(all(row.final_verified and
                           row.unsafe_accepted_reductions == 0
                           for row in rows) for rows in observations.values())
        methods_all_verified &= arm_safe
        zero_unsafe &= all(aggregate["unsafe_accepted_reduction_count"] == 0
                           for aggregate in aggregates.values())

        if arm == "coefficient" and visibility is not None and visibility < 0.95:
            decision = "REPRESENTATION_LIMIT"
        elif arm == "overlap" and visibility is not None and visibility >= 0.95:
            decision = ("DISCOVERY_HEADROOM" if
                        best_agg["mean_solver_savings_recovery"] < 0.95
                        and arm_safe else "DETERMINISTIC_SUFFICIENT")
        else:
            decision = "INTERACTION_OR_CONTROL" if arm in {"combined", "control"} else "INCONCLUSIVE"

        arms[arm] = {
            "count": len(arm_examples),
            "candidate_visibility": visibility,
            "oracle_verified": oracle_ok,
            "oracle_positive_savings_each_example": valid_savings,
            "mean_oracle_solver_savings_ops": mean(oracle_savings),
            "mean_oracle_reconstruction_ops": mean(
                row.reconstruction_counts.arithmetic_ops for row in oracle
                if row is not None),
            "mean_oracle_verification_ops": mean(
                row.verification_counts.arithmetic_ops for row in oracle
                if row is not None),
            "best_deterministic_method": best_name,
            "decision": decision,
            "methods": {
                method: {**aggregate, "rejected_materializations": sum(
                    row.rejected_materialization_count for row in observations[method]
                )} for method, aggregate in aggregates.items()
            },
        }

    return {
        "experiment": "v0.0.41 anti-shortcut causal audit",
        "total_examples": len(examples),
        "fresh_signatures": fresh,
        "cells_complete": cells_complete,
        "all_oracles_verified": oracle_all_verified,
        "all_methods_verified": methods_all_verified,
        "unsafe_accepted_reductions_zero": zero_unsafe,
        "keep_audit": len(examples) == 224 and fresh and cells_complete
                      and oracle_all_verified and methods_all_verified and zero_unsafe,
        "arms": arms,
        "claim_boundary": "Synthetic exact linear systems only; solver ops exclude discovery and checking cost.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
