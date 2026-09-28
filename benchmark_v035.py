from __future__ import annotations

import json

from neumann1.frozen_v035_checkpoints import (
    V035_REFERENCE_STATE_SHA256,
    V035_UTILITY_STATE_SHA256,
    checkpoint_fingerprints,
)
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
from neumann1.utility_compression_dataset import (
    V035_CALIBRATION_EXAMPLES_PER_CELL,
    V035_FINAL_EXAMPLES_PER_CELL,
    V035_TRAIN_EXAMPLES_PER_CELL,
    v035_calibration_examples,
    v035_final_examples,
    v035_training_examples,
)
from neumann1.utility_gauntlet import (
    V035_DEPLOYABLE_METHODS,
    V035_METHODS,
    aggregate_utility_observations,
    calibrate_utility_threshold,
    make_v035_scorers,
    observe_utility_policy,
    utility_regressor_diagnostics,
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
        _signatures(v034_calibration_examples())
    )
    signatures.update(
        _signatures(v034_final_examples())
    )
    return signatures


def run() -> dict[str, object]:
    training = v035_training_examples()
    calibration = v035_calibration_examples()
    final = v035_final_examples()

    prior = _prior_signatures()
    train_signatures = _signatures(training)
    calibration_signatures = _signatures(calibration)
    final_signatures = _signatures(final)

    disjoint_from_prior = (
        train_signatures.isdisjoint(prior)
        and calibration_signatures.isdisjoint(prior)
        and final_signatures.isdisjoint(prior)
    )
    mutually_disjoint = (
        train_signatures.isdisjoint(calibration_signatures)
        and train_signatures.isdisjoint(final_signatures)
        and calibration_signatures.isdisjoint(final_signatures)
    )

    fingerprints = checkpoint_fingerprints()
    checkpoint_identity = (
        fingerprints["reference"]
        == V035_REFERENCE_STATE_SHA256
        and fingerprints["utility"]
        == V035_UTILITY_STATE_SHA256
    )

    scorers = make_v035_scorers()

    calibrations = {
        method: calibrate_utility_threshold(
            calibration,
            method,
            scorers=scorers,
        )
        for method in V035_METHODS
    }

    final_results = {}
    for method in V035_METHODS:
        observations = tuple(
            observe_utility_policy(
                example,
                method,
                calibrations[method],
                scorers=scorers,
            )
            for example in final
        )
        final_results[method] = (
            aggregate_utility_observations(
                observations
            )
        )

    utility_diagnostics = utility_regressor_diagnostics(
        final,
        scorers=scorers,
    )

    deterministic_structural = (
        "target_leaf",
        "markowitz",
        "sparsity_incidence",
    )
    best_deterministic = max(
        deterministic_structural,
        key=lambda method: (
            final_results[method][
                "mean_solver_savings_vs_baseline"
            ],
            -final_results[method][
                "mean_method_solver_ops"
            ],
            method,
        ),
    )

    all_deployable_safe = all(
        final_results[method]["verified_retention"] == 1.0
        and final_results[method][
            "unsafe_accepted_reduction_count"
        ]
        == 0
        for method in V035_DEPLOYABLE_METHODS
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
        == V035_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    matched_capacity = (
        scorers.matched_reference.state_sha256
        == V035_REFERENCE_STATE_SHA256
        and scorers.matched_utility.state_sha256
        == V035_UTILITY_STATE_SHA256
    )

    keep = (
        disjoint_from_prior
        and mutually_disjoint
        and checkpoint_identity
        and matched_capacity
        and all_deployable_safe
        and final_cells_complete
    )

    utility = final_results["matched_utility"]
    reference = final_results["matched_reference"]

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
                V035_TRAIN_EXAMPLES_PER_CELL
            ),
            "calibration_examples_per_cell": (
                V035_CALIBRATION_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                V035_FINAL_EXAMPLES_PER_CELL
            ),
            "training_examples": len(training),
            "calibration_examples": len(calibration),
            "final_examples": len(final),
            "disjoint_from_v033_v034": (
                disjoint_from_prior
            ),
            "v035_splits_mutually_disjoint": (
                mutually_disjoint
            ),
        },
        "checkpoints": {
            "matched_reference_sha256": (
                fingerprints["reference"]
            ),
            "matched_utility_sha256": (
                fingerprints["utility"]
            ),
            "identity_valid": checkpoint_identity,
            "matched_feature_dimension": 16,
            "matched_hidden_units": 16,
            "matched_fitted_weight_bias_scalars": 289,
        },
        "calibrations": {
            method: {
                "threshold": row.threshold,
                "mean_solver_savings": (
                    row.mean_solver_savings
                ),
                "proposed_count": row.proposed_count,
            }
            for method, row in calibrations.items()
        },
        "final": final_results,
        "utility_regressor_diagnostics": (
            utility_diagnostics
        ),
        "comparisons": {
            "utility_minus_matched_reference_solver_savings": (
                utility["mean_solver_savings_vs_baseline"]
                - reference[
                    "mean_solver_savings_vs_baseline"
                ]
            ),
            "utility_minus_matched_reference_solver_ops": (
                utility["mean_method_solver_ops"]
                - reference["mean_method_solver_ops"]
            ),
            "utility_minus_matched_reference_reference_f1": (
                utility["proposal_f1"]
                - reference["proposal_f1"]
            ),
            "best_deterministic_method": (
                best_deterministic
            ),
            "utility_minus_best_deterministic_solver_savings": (
                utility["mean_solver_savings_vs_baseline"]
                - final_results[best_deterministic][
                    "mean_solver_savings_vs_baseline"
                ]
            ),
            "oracle_one_step_utility_solver_savings": (
                final_results[
                    "oracle_one_step_utility"
                ]["mean_solver_savings_vs_baseline"]
            ),
        },
        "contract_checks": {
            "checkpoint_identity": checkpoint_identity,
            "matched_capacity": matched_capacity,
            "all_deployable_verified_retention_1": (
                all(
                    final_results[method][
                        "verified_retention"
                    ]
                    == 1.0
                    for method in V035_DEPLOYABLE_METHODS
                )
            ),
            "all_deployable_unsafe_accepted_0": (
                all(
                    final_results[method][
                        "unsafe_accepted_reduction_count"
                    ]
                    == 0
                    for method in V035_DEPLOYABLE_METHODS
                )
            ),
            "final_cells_complete": (
                final_cells_complete
            ),
        },
        "keep_v035_contract": keep,
        "boundary": (
            "v0.0.35 directly supervises a matched small regressor "
            "on certified one-step solver arithmetic reduction. "
            "Thresholds are calibrated on downstream certified solver "
            "savings, not reference-rule F1. Checker activity, "
            "reconstruction, verification, and learned scoring remain "
            "separate categories; no synthetic total-compute score or "
            "total-compute superiority claim is made. The oracle one-"
            "step utility method is descriptive and non-deployable."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
