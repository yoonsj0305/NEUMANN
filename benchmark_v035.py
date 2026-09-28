from __future__ import annotations

import json
from statistics import mean

from neumann1.compression_utility import (
    aggregate_utility_calibrated_methods,
    aggregate_utility_oracle_observations,
    calibrate_utility_threshold,
    observe_dynamic_greedy_utility,
    observe_static_isolated_utility,
    observe_utility_calibrated_method,
)
from neumann1.compression_utility_dataset import (
    V035_CALIBRATION_EXAMPLES_PER_CELL,
    V035_FINAL_EXAMPLES_PER_CELL,
    v035_calibration_examples,
    v035_final_examples,
)
from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)
from neumann1.stopping_gauntlet import (
    METHODS,
    THRESHOLD_GRID,
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
    return prior


def _interaction_cells(static_rows, dynamic_rows):
    grouped = {}
    for static, dynamic in zip(
        static_rows,
        dynamic_rows,
    ):
        key = (
            static.core_dimension,
            static.apparent_dimension,
        )
        grouped.setdefault(key, []).append(
            dynamic.solver_savings
            - static.solver_savings
        )

    return [
        {
            "core_dimension": k,
            "apparent_dimension": n,
            "mean_interaction_gain": mean(values),
        }
        for (k, n), values in sorted(grouped.items())
    ]


def run() -> dict[str, object]:
    calibration_examples = (
        v035_calibration_examples()
    )
    final_examples = v035_final_examples()
    frozen = fit_frozen_v033_scorer()

    prior = _prior_signatures()
    calibration_signatures = _signatures(
        calibration_examples
    )
    final_signatures = _signatures(
        final_examples
    )

    disjoint_from_prior = (
        calibration_signatures.isdisjoint(prior)
        and final_signatures.isdisjoint(prior)
    )
    calibration_final_disjoint = (
        calibration_signatures.isdisjoint(
            final_signatures
        )
    )

    calibrations = {
        method: calibrate_utility_threshold(
            calibration_examples,
            method,
            frozen_scorer=frozen,
        )
        for method in METHODS
    }

    calibrated_rows = {}
    calibrated_aggregates = {}
    for method in METHODS:
        rows = tuple(
            observe_utility_calibrated_method(
                example,
                calibrations[method],
                frozen_scorer=frozen,
            )
            for example in final_examples
        )
        calibrated_rows[method] = rows
        calibrated_aggregates[method] = (
            aggregate_utility_calibrated_methods(
                rows
            )
        )

    static_rows = tuple(
        observe_static_isolated_utility(example)
        for example in final_examples
    )
    dynamic_rows = tuple(
        observe_dynamic_greedy_utility(example)
        for example in final_examples
    )
    static_aggregate = (
        aggregate_utility_oracle_observations(
            static_rows
        )
    )
    dynamic_aggregate = (
        aggregate_utility_oracle_observations(
            dynamic_rows
        )
    )

    deterministic_methods = [
        method
        for method in METHODS
        if method not in {
            "learned_mlp",
            "deterministic_random",
        }
    ]
    best_deterministic = max(
        deterministic_methods,
        key=lambda method: (
            calibrated_aggregates[method][
                "mean_solver_savings_vs_baseline"
            ],
            -calibrated_aggregates[method][
                "mean_method_solver_ops"
            ],
            method,
        ),
    )

    interaction_gain = mean(
        dynamic.solver_savings
        - static.solver_savings
        for static, dynamic in zip(
            static_rows,
            dynamic_rows,
        )
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
        == V035_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    calibrated_safe = all(
        aggregate["verified_retention"] == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        for aggregate in calibrated_aggregates.values()
    )
    oracle_safe = (
        static_aggregate["verified_retention"] == 1.0
        and dynamic_aggregate["verified_retention"] == 1.0
        and static_aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        and dynamic_aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
    )
    thresholds_on_grid = all(
        calibration.threshold in THRESHOLD_GRID
        for calibration in calibrations.values()
    )

    keep = (
        disjoint_from_prior
        and calibration_final_disjoint
        and final_cells_complete
        and calibrated_safe
        and oracle_safe
        and thresholds_on_grid
    )

    return {
        "experiment": (
            "v0.0.35 Compression Utility / "
            "Value-of-Reduction Oracle"
        ),
        "data_contract": {
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in learned_scale_grid()
            ],
            "calibration_examples_per_cell": (
                V035_CALIBRATION_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                V035_FINAL_EXAMPLES_PER_CELL
            ),
            "calibration_examples": len(
                calibration_examples
            ),
            "final_examples": len(
                final_examples
            ),
            "disjoint_from_all_v033_v034_signatures": (
                disjoint_from_prior
            ),
            "calibration_final_disjoint": (
                calibration_final_disjoint
            ),
        },
        "utility_definition": (
            "VoR(c|R)=solver_ops(R)-"
            "solver_ops(R union {c})"
        ),
        "threshold_grid": list(THRESHOLD_GRID),
        "utility_calibrations": {
            method: {
                "threshold": calibration.threshold,
                "mean_solver_savings": (
                    calibration.mean_solver_savings
                ),
                "mean_solver_ops": (
                    calibration.mean_solver_ops
                ),
                "mean_proposed_count": (
                    calibration.mean_proposed_count
                ),
            }
            for method, calibration
            in calibrations.items()
        },
        "final_utility_calibrated_scorers": (
            calibrated_aggregates
        ),
        "final_static_isolated_utility": (
            static_aggregate
        ),
        "final_dynamic_greedy_utility": (
            dynamic_aggregate
        ),
        "comparisons": {
            "best_pre_registered_deterministic_method": (
                best_deterministic
            ),
            "dynamic_vs_static_mean_solver_savings_delta": (
                dynamic_aggregate[
                    "mean_solver_savings_vs_baseline"
                ]
                - static_aggregate[
                    "mean_solver_savings_vs_baseline"
                ]
            ),
            "dynamic_vs_best_deterministic_mean_solver_savings_delta": (
                dynamic_aggregate[
                    "mean_solver_savings_vs_baseline"
                ]
                - calibrated_aggregates[
                    best_deterministic
                ][
                    "mean_solver_savings_vs_baseline"
                ]
            ),
            "static_vs_best_deterministic_mean_solver_savings_delta": (
                static_aggregate[
                    "mean_solver_savings_vs_baseline"
                ]
                - calibrated_aggregates[
                    best_deterministic
                ][
                    "mean_solver_savings_vs_baseline"
                ]
            ),
            "utility_calibrated_learned_vs_best_deterministic_delta": (
                calibrated_aggregates[
                    "learned_mlp"
                ][
                    "mean_solver_savings_vs_baseline"
                ]
                - calibrated_aggregates[
                    best_deterministic
                ][
                    "mean_solver_savings_vs_baseline"
                ]
            ),
            "mean_interaction_gain": (
                interaction_gain
            ),
            "interaction_cells": (
                _interaction_cells(
                    static_rows,
                    dynamic_rows,
                )
            ),
        },
        "oracle_search_cost_boundary": {
            "static_successful_trial_solver_ops_mean": (
                static_aggregate[
                    "mean_successful_trial_solver_ops"
                ]
            ),
            "dynamic_successful_trial_solver_ops_mean": (
                dynamic_aggregate[
                    "mean_successful_trial_solver_ops"
                ]
            ),
            "note": (
                "trial solver work is diagnostic teacher-search "
                "cost and is not included in downstream solver savings; "
                "partial work from invalid materializations is not instrumented"
            ),
        },
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "thresholds_on_pre_registered_grid": (
                thresholds_on_grid
            ),
            "all_calibrated_methods_verified_retention_1": (
                calibrated_safe
            ),
            "utility_oracles_verified_retention_1": (
                oracle_safe
            ),
            "dynamic_selected_gain_telescopes_to_savings": all(
                row.positive_marginal_gain_sum
                == row.solver_savings
                for row in dynamic_rows
            ),
        },
        "keep_v035_contract": keep,
        "boundary": (
            "v0.0.35 validates a solver-work utility target "
            "using expensive exact teacher/oracle search. "
            "It does not train a learned utility model, prove global "
            "minimality, or establish total-compute superiority."
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
