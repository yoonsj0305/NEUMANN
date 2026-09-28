from __future__ import annotations

import json
import math

from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.utility_compression_dataset import (
    UTILITY_CALIBRATION_EXAMPLES_PER_CELL,
    UTILITY_FINAL_EXAMPLES_PER_CELL,
    UTILITY_TRAIN_EXAMPLES_PER_CELL,
    utility_calibration_examples,
    utility_final_examples,
    utility_training_examples,
)
from neumann1.utility_compression import (
    UTILITY_METHODS,
    UTILITY_THRESHOLD_GRID,
    aggregate_utility_observations,
    calibrate_utility_threshold,
    fit_utility_tree_once,
    observe_utility_policy,
    utility_prediction_metrics,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def _prior_signatures():
    signatures = _signatures(
        learned_compression_training_examples()
    )
    signatures.update(
        _signatures(
            learned_compression_validation_examples()
        )
    )
    signatures.update(
        _signatures(
            learned_compression_final_examples()
        )
    )
    signatures.update(
        _signatures(
            v034_calibration_examples()
        )
    )
    signatures.update(
        _signatures(
            v034_final_examples()
        )
    )
    return signatures


def run() -> dict[str, object]:
    training = utility_training_examples()
    calibration = utility_calibration_examples()
    final = utility_final_examples()

    training_signatures = _signatures(training)
    calibration_signatures = _signatures(calibration)
    final_signatures = _signatures(final)
    prior_signatures = _prior_signatures()

    split_disjoint = (
        training_signatures.isdisjoint(
            calibration_signatures
        )
        and training_signatures.isdisjoint(
            final_signatures
        )
        and calibration_signatures.isdisjoint(
            final_signatures
        )
    )
    disjoint_from_prior = (
        training_signatures.isdisjoint(prior_signatures)
        and calibration_signatures.isdisjoint(prior_signatures)
        and final_signatures.isdisjoint(prior_signatures)
    )

    utility_tree = fit_utility_tree_once(training)
    replay_tree = fit_utility_tree_once(training)
    tree_footprint = utility_tree.footprint()
    replay_footprint = replay_tree.footprint()
    tree_replay_identical = (
        tree_footprint.fitted_state_sha256
        == replay_footprint.fitted_state_sha256
    )

    frozen_reference = fit_frozen_v033_scorer()

    calibrations = {
        method: calibrate_utility_threshold(
            calibration,
            method,
            utility_tree=utility_tree,
            frozen_reference_scorer=frozen_reference,
        )
        for method in UTILITY_METHODS
    }

    final_results = {}
    for method in UTILITY_METHODS:
        observations = tuple(
            observe_utility_policy(
                example,
                method,
                calibrations[method],
                utility_tree=utility_tree,
                frozen_reference_scorer=frozen_reference,
            )
            for example in final
        )
        final_results[method] = (
            aggregate_utility_observations(
                observations
            )
        )

    prediction_metrics = utility_prediction_metrics(
        final,
        utility_tree,
    )

    deployable_methods = [
        method
        for method in UTILITY_METHODS
        if method != "oracle_one_step_utility"
    ]
    best_deployable = max(
        deployable_methods,
        key=lambda method: (
            final_results[method][
                "mean_solver_savings"
            ],
            -final_results[method][
                "mean_method_solver_ops"
            ],
            method,
        ),
    )

    final_cells_complete = all(
        len(
            [
                example
                for example in final
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == UTILITY_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    all_safe = all(
        result["verified_retention"] == 1.0
        and result[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        for result in final_results.values()
    )

    thresholds_on_grid = all(
        calibration_item.threshold
        in UTILITY_THRESHOLD_GRID
        for calibration_item
        in calibrations.values()
    )

    prediction_metrics_finite = all(
        value is None
        or math.isfinite(float(value))
        for key, value in prediction_metrics.items()
        if key != "count"
    )

    keep = (
        split_disjoint
        and disjoint_from_prior
        and tree_replay_identical
        and final_cells_complete
        and all_safe
        and thresholds_on_grid
        and prediction_metrics_finite
    )

    return {
        "experiment": (
            "v0.0.35 Utility-Directed Structural Compression"
        ),
        "data_contract": {
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in learned_scale_grid()
            ],
            "training_examples_per_cell": (
                UTILITY_TRAIN_EXAMPLES_PER_CELL
            ),
            "calibration_examples_per_cell": (
                UTILITY_CALIBRATION_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                UTILITY_FINAL_EXAMPLES_PER_CELL
            ),
            "training_examples": len(training),
            "calibration_examples": len(calibration),
            "final_examples": len(final),
            "split_signatures_disjoint": split_disjoint,
            "disjoint_from_v033_v034": (
                disjoint_from_prior
            ),
        },
        "utility_tree": {
            "input_feature_dimension": (
                tree_footprint.input_feature_dimension
            ),
            "max_depth_limit": (
                tree_footprint.max_depth_limit
            ),
            "min_samples_leaf": (
                tree_footprint.min_samples_leaf
            ),
            "fitted_node_count": (
                tree_footprint.fitted_node_count
            ),
            "fitted_max_depth": (
                tree_footprint.fitted_max_depth
            ),
            "fitted_leaf_count": (
                tree_footprint.fitted_leaf_count
            ),
            "fitted_state_sha256": (
                tree_footprint.fitted_state_sha256
            ),
            "replay_fitted_state_sha256": (
                replay_footprint.fitted_state_sha256
            ),
            "replay_identical": (
                tree_replay_identical
            ),
            "feature_importances": [
                float(value)
                for value
                in utility_tree.model.feature_importances_
            ],
            "final_one_step_prediction_metrics": (
                prediction_metrics
            ),
        },
        "threshold_grid": list(
            UTILITY_THRESHOLD_GRID
        ),
        "calibrations": {
            method: {
                "threshold": item.threshold,
                "mean_solver_savings": (
                    item.mean_solver_savings
                ),
                "mean_method_solver_ops": (
                    item.mean_method_solver_ops
                ),
                "mean_proposed_count": (
                    item.mean_proposed_count
                ),
                "verified_retention": (
                    item.verified_retention
                ),
                "unsafe_accepted_reductions": (
                    item.unsafe_accepted_reductions
                ),
            }
            for method, item in calibrations.items()
        },
        "final": final_results,
        "comparisons": {
            "best_deployable_method": best_deployable,
            "utility_tree_vs_reference_mlp_solver_savings_delta": (
                final_results["utility_tree"][
                    "mean_solver_savings"
                ]
                - final_results["reference_mlp"][
                    "mean_solver_savings"
                ]
            ),
            "utility_tree_vs_target_leaf_solver_savings_delta": (
                final_results["utility_tree"][
                    "mean_solver_savings"
                ]
                - final_results["target_leaf"][
                    "mean_solver_savings"
                ]
            ),
            "utility_tree_vs_markowitz_solver_savings_delta": (
                final_results["utility_tree"][
                    "mean_solver_savings"
                ]
                - final_results["markowitz"][
                    "mean_solver_savings"
                ]
            ),
            "utility_tree_vs_oracle_one_step_solver_savings_gap": (
                final_results[
                    "oracle_one_step_utility"
                ]["mean_solver_savings"]
                - final_results["utility_tree"][
                    "mean_solver_savings"
                ]
            ),
        },
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "all_methods_verified_retention_1": (
                all(
                    result["verified_retention"]
                    == 1.0
                    for result in final_results.values()
                )
            ),
            "all_methods_unsafe_accepted_0": (
                all(
                    result[
                        "unsafe_accepted_reduction_count"
                    ]
                    == 0
                    for result in final_results.values()
                )
            ),
            "thresholds_on_pre_registered_grid": (
                thresholds_on_grid
            ),
            "utility_tree_replay_identical": (
                tree_replay_identical
            ),
        },
        "keep_v035_contract": keep,
        "boundary": (
            "v0.0.35 optimizes one-step final-solver utility, not "
            "end-to-end total compute. The checker cost fields are "
            "lower bounds because failed tentative materializations "
            "may terminate before complete arithmetic counters exist. "
            "The oracle one-step utility scorer is non-deployable "
            "because it solves candidate reductions during scoring. "
            "The utility tree uses the same hand-designed 16 features "
            "as v0.0.33/v0.0.34. No method receives k or n-k at final "
            "inference. No natural-language, domain-general, total-"
            "compute, FLOP, energy, or asymptotic claim is made."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
