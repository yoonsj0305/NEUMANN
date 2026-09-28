from __future__ import annotations

import json
from statistics import mean

from neumann1.compression_utility import (
    aggregate_utility_oracle_observations,
    observe_dynamic_greedy_utility,
)
from neumann1.compression_utility_dataset import (
    v035_calibration_examples,
    v035_final_examples,
)
from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)
from neumann1.residual_utility import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    aggregate_residual_observations,
    observe_cheap_first_residual_utility,
)
from neumann1.residual_utility_dataset import (
    V036_DEVELOPMENT_EXAMPLES_PER_CELL,
    V036_FINAL_EXAMPLES_PER_CELL,
    v036_development_examples,
    v036_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def _prior_signatures():
    prior = _signatures(
        learned_compression_training_examples()
    )
    prior.update(
        _signatures(
            learned_compression_validation_examples()
        )
    )
    prior.update(
        _signatures(
            learned_compression_final_examples()
        )
    )
    prior.update(
        _signatures(v034_calibration_examples())
    )
    prior.update(
        _signatures(v034_final_examples())
    )
    prior.update(
        _signatures(v035_calibration_examples())
    )
    prior.update(
        _signatures(v035_final_examples())
    )
    return prior


def _cell_comparisons(residual_rows, dynamic_rows):
    grouped = {}
    for residual, dynamic in zip(
        residual_rows,
        dynamic_rows,
    ):
        key = (
            residual.core_dimension,
            residual.apparent_dimension,
        )
        grouped.setdefault(key, []).append(
            (residual, dynamic)
        )

    output = []
    for (k, n), rows in sorted(grouped.items()):
        cheap_ops = mean(
            residual.cheap_solver_ops
            for residual, _ in rows
        )
        residual_ops = mean(
            residual.residual_solver_ops
            for residual, _ in rows
        )
        dynamic_ops = mean(
            dynamic.method_solver_ops
            for _, dynamic in rows
        )
        residual_gain = cheap_ops - residual_ops
        dynamic_advantage = cheap_ops - dynamic_ops
        residual_trials = mean(
            residual.residual_trial_materializations
            for residual, _ in rows
        )
        dynamic_trials = mean(
            dynamic.trial_materializations
            for _, dynamic in rows
        )

        output.append(
            {
                "core_dimension": k,
                "apparent_dimension": n,
                "count": len(rows),
                "mean_cheap_solver_ops": cheap_ops,
                "mean_residual_solver_ops": residual_ops,
                "mean_full_dynamic_solver_ops": dynamic_ops,
                "mean_residual_additional_savings": (
                    residual_gain
                ),
                "mean_full_dynamic_advantage_over_cheap": (
                    dynamic_advantage
                ),
                "residual_advantage_recovery": (
                    residual_gain / dynamic_advantage
                    if dynamic_advantage > 0
                    else None
                ),
                "residual_remaining_work_reduction": (
                    residual_gain / cheap_ops
                    if cheap_ops > 0
                    else 0.0
                ),
                "mean_residual_trials": residual_trials,
                "mean_full_dynamic_trials": dynamic_trials,
                "trial_materialization_ratio": (
                    residual_trials / dynamic_trials
                    if dynamic_trials > 0
                    else 0.0
                ),
            }
        )

    return output


def run() -> dict[str, object]:
    development_examples = (
        v036_development_examples()
    )
    final_examples = v036_final_examples()
    frozen = fit_frozen_v033_scorer()

    prior = _prior_signatures()
    development_signatures = _signatures(
        development_examples
    )
    final_signatures = _signatures(
        final_examples
    )

    disjoint_from_prior = (
        development_signatures.isdisjoint(prior)
        and final_signatures.isdisjoint(prior)
    )
    development_final_disjoint = (
        development_signatures.isdisjoint(
            final_signatures
        )
    )

    residual_rows = tuple(
        observe_cheap_first_residual_utility(
            example,
            frozen_scorer=frozen,
        )
        for example in final_examples
    )
    dynamic_rows = tuple(
        observe_dynamic_greedy_utility(example)
        for example in final_examples
    )

    residual = aggregate_residual_observations(
        residual_rows
    )
    dynamic = aggregate_utility_oracle_observations(
        dynamic_rows
    )

    mean_cheap_ops = float(
        residual["mean_cheap_solver_ops"]
    )
    mean_residual_ops = float(
        residual["mean_residual_solver_ops"]
    )
    mean_dynamic_ops = float(
        dynamic["mean_solver_ops"]
    )

    residual_gain = (
        mean_cheap_ops - mean_residual_ops
    )
    dynamic_advantage = (
        mean_cheap_ops - mean_dynamic_ops
    )
    residual_remaining_work_reduction = (
        residual_gain / mean_cheap_ops
        if mean_cheap_ops > 0
        else 0.0
    )
    residual_advantage_recovery = (
        residual_gain / dynamic_advantage
        if dynamic_advantage > 0
        else None
    )

    residual_trials = float(
        residual[
            "mean_residual_trial_materializations"
        ]
    )
    dynamic_trials = float(
        dynamic["mean_trial_materializations"]
    )
    trial_ratio = (
        residual_trials / dynamic_trials
        if dynamic_trials > 0
        else 0.0
    )

    residual_success_ops = float(
        residual[
            "mean_residual_successful_trial_solver_ops"
        ]
    )
    dynamic_success_ops = float(
        dynamic[
            "mean_successful_trial_solver_ops"
        ]
    )
    successful_solver_ops_ratio = (
        residual_success_ops / dynamic_success_ops
        if dynamic_success_ops > 0
        else 0.0
    )

    cheap_safe = (
        residual["verified_retention_cheap"]
        == 1.0
    )
    residual_safe = (
        residual["verified_retention_residual"]
        == 1.0
        and residual[
            "unsafe_accepted_reduction_count"
        ]
        == 0
    )
    dynamic_safe = (
        dynamic["verified_retention"] == 1.0
        and dynamic[
            "unsafe_accepted_reduction_count"
        ]
        == 0
    )

    final_cells_complete = all(
        len(
            [
                example
                for example in final_examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == V036_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )
    development_cells_complete = all(
        len(
            [
                example
                for example in development_examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == V036_DEVELOPMENT_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    telescopes = all(
        row.residual_positive_gain_sum
        == row.residual_additional_savings
        for row in residual_rows
    )

    keep = (
        disjoint_from_prior
        and development_final_disjoint
        and development_cells_complete
        and final_cells_complete
        and FROZEN_TARGET_LEAF_THRESHOLD == 0.10
        and cheap_safe
        and residual_safe
        and dynamic_safe
        and telescopes
    )

    gate_1_material_residual = (
        residual_remaining_work_reduction
        >= 0.10
    )
    gate_2_dynamic_recovery = (
        dynamic_advantage > 0
        and residual_advantage_recovery is not None
        and residual_advantage_recovery >= 0.50
    )
    gate_3_search_reduction = (
        trial_ratio <= 0.50
    )
    gate_4_safety = (
        cheap_safe
        and residual_safe
        and dynamic_safe
    )
    go_learned_residual = (
        keep
        and gate_1_material_residual
        and gate_2_dynamic_recovery
        and gate_3_search_reduction
        and gate_4_safety
    )

    return {
        "experiment": (
            "v0.0.36 Cheap-First Residual Utility"
        ),
        "data_contract": {
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in learned_scale_grid()
            ],
            "development_examples_per_cell": (
                V036_DEVELOPMENT_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                V036_FINAL_EXAMPLES_PER_CELL
            ),
            "development_examples": len(
                development_examples
            ),
            "final_examples": len(
                final_examples
            ),
            "disjoint_from_all_v033_v034_v035_signatures": (
                disjoint_from_prior
            ),
            "development_final_disjoint": (
                development_final_disjoint
            ),
        },
        "frozen_cheap_stage": {
            "method": "target_leaf",
            "threshold": (
                FROZEN_TARGET_LEAF_THRESHOLD
            ),
            "recalibrated_on_v036": False,
        },
        "final_cheap_first_residual": residual,
        "final_full_dynamic_teacher": dynamic,
        "comparisons": {
            "mean_cheap_solver_ops": mean_cheap_ops,
            "mean_residual_solver_ops": (
                mean_residual_ops
            ),
            "mean_full_dynamic_solver_ops": (
                mean_dynamic_ops
            ),
            "mean_residual_additional_savings": (
                residual_gain
            ),
            "mean_full_dynamic_advantage_over_cheap": (
                dynamic_advantage
            ),
            "residual_remaining_work_reduction": (
                residual_remaining_work_reduction
            ),
            "residual_advantage_recovery": (
                residual_advantage_recovery
            ),
            "residual_trial_materialization_ratio": (
                trial_ratio
            ),
            "residual_successful_trial_solver_ops_ratio": (
                successful_solver_ops_ratio
            ),
            "cells": _cell_comparisons(
                residual_rows,
                dynamic_rows,
            ),
        },
        "go_no_go": {
            "gate_1_material_residual": {
                "threshold": 0.10,
                "observed": (
                    residual_remaining_work_reduction
                ),
                "pass": gate_1_material_residual,
            },
            "gate_2_dynamic_advantage_recovery": {
                "requires_positive_dynamic_advantage": True,
                "threshold": 0.50,
                "dynamic_advantage": dynamic_advantage,
                "observed": (
                    residual_advantage_recovery
                ),
                "pass": gate_2_dynamic_recovery,
            },
            "gate_3_trial_materialization_ratio": {
                "maximum": 0.50,
                "observed": trial_ratio,
                "pass": gate_3_search_reduction,
            },
            "gate_4_safety": {
                "cheap_verified_retention_1": (
                    cheap_safe
                ),
                "residual_verified_retention_1": (
                    residual_safe
                ),
                "full_dynamic_verified_retention_1": (
                    dynamic_safe
                ),
                "pass": gate_4_safety,
            },
            "go_learned_residual_v037": (
                go_learned_residual
            ),
        },
        "contract_checks": {
            "development_cells_complete": (
                development_cells_complete
            ),
            "final_cells_complete": (
                final_cells_complete
            ),
            "frozen_target_leaf_threshold_exact": (
                FROZEN_TARGET_LEAF_THRESHOLD
                == 0.10
            ),
            "residual_gain_telescopes": (
                telescopes
            ),
            "all_paths_safe": (
                gate_4_safety
            ),
        },
        "keep_v036_contract": keep,
        "boundary": (
            "v0.0.36 measures whether an exact residual "
            "state-aware teacher remains justified after a frozen "
            "cheap target-leaf stage. It does not train a learned "
            "residual model, prove global optimality, or establish "
            "end-to-end total-compute superiority. Teacher-search "
            "cost excludes partial work inside failed materializations."
        ),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2,
            sort_keys=True,
        )
    )
