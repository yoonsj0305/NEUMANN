from __future__ import annotations

import json
import math

from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)
from neumann1.stopping_gauntlet import (
    METHODS,
    THRESHOLD_GRID,
    aggregate_stopping_observations,
    calibrate_threshold,
    fit_frozen_v033_scorer,
    observe_stopping_method,
)
from neumann1.stopping_gauntlet_dataset import (
    V034_CALIBRATION_EXAMPLES_PER_CELL,
    V034_FINAL_EXAMPLES_PER_CELL,
    v034_calibration_examples,
    v034_final_examples,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def _all_v033_signatures():
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
    return signatures


def run() -> dict[str, object]:
    calibration_examples = v034_calibration_examples()
    final_examples = v034_final_examples()
    frozen = fit_frozen_v033_scorer()

    v033_signatures = _all_v033_signatures()
    calibration_signatures = _signatures(
        calibration_examples
    )
    final_signatures = _signatures(final_examples)

    disjoint_from_v033 = (
        calibration_signatures.isdisjoint(v033_signatures)
        and final_signatures.isdisjoint(v033_signatures)
    )
    calibration_final_disjoint = (
        calibration_signatures.isdisjoint(
            final_signatures
        )
    )

    calibrations = {
        method: calibrate_threshold(
            calibration_examples,
            method,
            frozen_scorer=frozen,
        )
        for method in METHODS
    }

    final_results = {}
    for method in METHODS:
        observations = tuple(
            observe_stopping_method(
                example,
                method,
                calibrations[method],
                frozen_scorer=frozen,
            )
            for example in final_examples
        )
        final_results[method] = (
            aggregate_stopping_observations(
                observations
            )
        )

    learned = final_results["learned_mlp"]
    deterministic_methods = [
        method
        for method in METHODS
        if method
        not in {
            "learned_mlp",
            "deterministic_random",
        }
    ]
    best_deterministic_method = max(
        deterministic_methods,
        key=lambda method: (
            final_results[method][
                "raw_proposal_micro_f1"
            ],
            final_results[method][
                "mean_solver_savings_vs_baseline"
            ],
            method,
        ),
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
        == V034_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    no_oracle_cardinality_at_final = all(
        math.isfinite(
            float(result["threshold"])
        )
        for result in final_results.values()
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
        calibration.threshold
        in THRESHOLD_GRID
        for calibration in calibrations.values()
    )

    keep = (
        disjoint_from_v033
        and calibration_final_disjoint
        and final_cells_complete
        and no_oracle_cardinality_at_final
        and all_safe
        and thresholds_on_grid
    )

    return {
        "experiment": (
            "v0.0.34 Structural Baseline Gauntlet "
            "+ Confidence Stopping"
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
                V034_CALIBRATION_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                V034_FINAL_EXAMPLES_PER_CELL
            ),
            "calibration_examples": len(
                calibration_examples
            ),
            "final_examples": len(final_examples),
            "disjoint_from_all_v033_signatures": (
                disjoint_from_v033
            ),
            "calibration_final_disjoint": (
                calibration_final_disjoint
            ),
        },
        "frozen_learned_scorer": {
            "input_feature_dimension": (
                frozen.footprint.input_feature_dimension
            ),
            "hidden_units": (
                frozen.footprint.hidden_units
            ),
            "fitted_weight_bias_scalars": (
                frozen.footprint
                .fitted_weight_bias_scalars
            ),
            "scaler_state_scalars": (
                frozen.footprint.scaler_state_scalars
            ),
            "layer_shapes": [
                list(shape)
                for shape in frozen.footprint.layer_shapes
            ],
            "weighted_sum_terms_per_candidate": (
                frozen.footprint
                .weighted_sum_terms_per_candidate
            ),
        },
        "threshold_grid": list(THRESHOLD_GRID),
        "calibrations": {
            method: {
                "threshold": calibration.threshold,
                "micro_precision": (
                    calibration.micro_precision
                ),
                "micro_recall": (
                    calibration.micro_recall
                ),
                "micro_f1": calibration.micro_f1,
                "proposed_count": (
                    calibration.proposed_count
                ),
                "reference_count": (
                    calibration.reference_count
                ),
                "true_positive_count": (
                    calibration.true_positive_count
                ),
            }
            for method, calibration
            in calibrations.items()
        },
        "final": final_results,
        "comparisons": {
            "learned_vs_random_f1_delta": (
                learned["raw_proposal_micro_f1"]
                - final_results[
                    "deterministic_random"
                ]["raw_proposal_micro_f1"]
            ),
            "learned_vs_v033_simple_heuristic_f1_delta": (
                learned["raw_proposal_micro_f1"]
                - final_results[
                    "sparsity_incidence"
                ]["raw_proposal_micro_f1"]
            ),
            "best_pre_registered_deterministic_method": (
                best_deterministic_method
            ),
            "learned_vs_best_deterministic_f1_delta": (
                learned["raw_proposal_micro_f1"]
                - final_results[
                    best_deterministic_method
                ]["raw_proposal_micro_f1"]
            ),
            "learned_vs_best_deterministic_solver_savings_delta": (
                learned[
                    "mean_solver_savings_vs_baseline"
                ]
                - final_results[
                    best_deterministic_method
                ][
                    "mean_solver_savings_vs_baseline"
                ]
            ),
        },
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "no_oracle_cardinality_at_final": (
                no_oracle_cardinality_at_final
            ),
            "thresholds_on_pre_registered_grid": (
                thresholds_on_grid
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
        },
        "keep_v034_contract": keep,
        "boundary": (
            "v0.0.34 removes the oracle n-k proposal budget "
            "from final inference, but each method's global score "
            "threshold is selected on a labeled calibration split "
            "using the generator dependency reference. The generator "
            "reference is not assumed globally minimal or unique. "
            "The learned scorer remains a frozen 289-parameter "
            "hand-feature MLP from v0.0.33. Deterministic checker, "
            "solver, reconstruction, and verification costs remain "
            "separate from learned scoring proxies. This benchmark "
            "does not establish total-compute superiority, natural-"
            "language compression, or domain-general minimality."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
