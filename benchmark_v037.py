from __future__ import annotations

import json
from statistics import mean

from neumann1.learned_compression_dataset import (
    learned_scale_grid,
)
from neumann1.residual_learning import (
    DETERMINISTIC_RESIDUAL_METHODS,
    LEARNED_RESIDUAL_METHODS,
    aggregate_residual_policy,
    final_learned_value_decision,
    fit_residual_models,
    inspect_residual_model,
    observe_deterministic_residual_policy,
    observe_exact_residual_teacher,
    observe_learned_residual_policy,
    select_residual_models,
)
from neumann1.residual_learning_dataset import (
    V037_FINAL_EXAMPLES_PER_CELL,
    V037_TRAIN_EXAMPLES_PER_CELL,
    V037_VALIDATION_EXAMPLES_PER_CELL,
    prior_v037_signatures,
    v037_final_examples,
    v037_train_examples,
    v037_validation_examples,
)
from neumann1.residual_headroom import (
    FROZEN_TARGET_LEAF_THRESHOLD,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def _recovery(
    savings: float,
    teacher_value: float,
) -> float | None:
    if teacher_value <= 0:
        return None
    return savings / teacher_value


def run() -> dict[str, object]:
    train = v037_train_examples()
    validation = v037_validation_examples()
    final = v037_final_examples()
    frozen = fit_frozen_v033_scorer()

    prior = prior_v037_signatures()
    train_sig = _signatures(train)
    validation_sig = _signatures(validation)
    final_sig = _signatures(final)

    disjoint = (
        train_sig.isdisjoint(prior)
        and validation_sig.isdisjoint(prior)
        and final_sig.isdisjoint(prior)
        and train_sig.isdisjoint(validation_sig)
        and train_sig.isdisjoint(final_sig)
        and validation_sig.isdisjoint(final_sig)
    )

    models, training_rows = fit_residual_models(
        train,
        frozen_scorer=frozen,
    )
    footprints = {
        method: inspect_residual_model(model)
        for method, model in models.items()
    }

    (
        selection,
        learned_calibrations,
        deterministic_calibrations,
    ) = select_residual_models(
        validation,
        models,
        frozen_scorer=frozen,
    )

    teacher_final_rows = tuple(
        observe_exact_residual_teacher(
            example,
            frozen_scorer=frozen,
        )
        for example in final
    )
    teacher_final = aggregate_residual_policy(
        teacher_final_rows
    )
    teacher_value = teacher_final[
        "mean_residual_additional_savings"
    ]

    learned_final = {}
    for method in LEARNED_RESIDUAL_METHODS:
        calibration = learned_calibrations[method]
        rows = tuple(
            observe_learned_residual_policy(
                example,
                models[method],
                calibration.threshold,
                frozen_scorer=frozen,
            )
            for example in final
        )
        aggregate = aggregate_residual_policy(rows)
        aggregate["teacher_savings_recovery"] = (
            _recovery(
                aggregate[
                    "mean_residual_additional_savings"
                ],
                teacher_value,
            )
        )
        learned_final[method] = aggregate

    deterministic_final = {}
    for method in DETERMINISTIC_RESIDUAL_METHODS:
        calibration = deterministic_calibrations[
            method
        ]
        rows = tuple(
            observe_deterministic_residual_policy(
                example,
                method,
                calibration.threshold,
                frozen_scorer=frozen,
            )
            for example in final
        )
        aggregate = aggregate_residual_policy(rows)
        aggregate["teacher_savings_recovery"] = (
            _recovery(
                aggregate[
                    "mean_residual_additional_savings"
                ],
                teacher_value,
            )
        )
        deterministic_final[method] = aggregate

    selected_learned = learned_final[
        selection.learned_method
    ]
    selected_deterministic = deterministic_final[
        selection.deterministic_method
    ]
    deterministic_recovery = selected_deterministic[
        "teacher_savings_recovery"
    ]

    decision = final_learned_value_decision(
        learned_additional_savings=(
            selected_learned[
                "mean_residual_additional_savings"
            ]
        ),
        deterministic_additional_savings=(
            selected_deterministic[
                "mean_residual_additional_savings"
            ]
        ),
        teacher_additional_savings=teacher_value,
        learned_verified_retention=(
            selected_learned[
                "verified_retention"
            ]
        ),
        learned_unsafe_count=(
            selected_learned[
                "unsafe_accepted_reduction_count"
            ]
        ),
        deterministic_recovery=(
            deterministic_recovery
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
        == V037_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    deployable_aggregates = (
        list(learned_final.values())
        + list(deterministic_final.values())
    )
    all_deployable_safe = all(
        aggregate["verified_retention"] == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        for aggregate in deployable_aggregates
    )
    teacher_safe = (
        teacher_final["verified_retention"] == 1.0
        and teacher_final[
            "unsafe_accepted_reduction_count"
        ]
        == 0
    )

    positive_training_rows = sum(
        1
        for row in training_rows
        if row.exact_gain > 0
    )
    invalid_training_rows = sum(
        1
        for row in training_rows
        if not row.valid
    )

    keep = (
        disjoint
        and FROZEN_TARGET_LEAF_THRESHOLD == 0.10
        and final_cells_complete
        and all_deployable_safe
        and teacher_safe
        and len(train)
        == 8 * V037_TRAIN_EXAMPLES_PER_CELL
        and len(validation)
        == 8 * V037_VALIDATION_EXAMPLES_PER_CELL
        and len(final)
        == 8 * V037_FINAL_EXAMPLES_PER_CELL
    )

    return {
        "experiment": (
            "v0.0.37 Smallest Adequate "
            "State-Aware Residual Predictor"
        ),
        "data_contract": {
            "train_examples": len(train),
            "validation_examples": len(validation),
            "final_examples": len(final),
            "train_examples_per_cell": (
                V037_TRAIN_EXAMPLES_PER_CELL
            ),
            "validation_examples_per_cell": (
                V037_VALIDATION_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                V037_FINAL_EXAMPLES_PER_CELL
            ),
            "disjoint_from_all_prior_and_each_other": (
                disjoint
            ),
        },
        "training_contract": {
            "teacher_rows": len(training_rows),
            "positive_gain_rows": positive_training_rows,
            "positive_gain_fraction": (
                positive_training_rows
                / len(training_rows)
            ),
            "invalid_rows": invalid_training_rows,
            "invalid_fraction": (
                invalid_training_rows
                / len(training_rows)
            ),
            "feature_dimension": 22,
            "target": (
                "clipped exact marginal solver gain / "
                "current solver ops; invalid=-1"
            ),
        },
        "model_footprints": {
            method: {
                "input_feature_dimension": (
                    footprint.input_feature_dimension
                ),
                "fitted_weight_bias_scalars": (
                    footprint.fitted_weight_bias_scalars
                ),
                "scaler_state_scalars": (
                    footprint.scaler_state_scalars
                ),
                "weighted_sum_terms_per_candidate": (
                    footprint.weighted_sum_terms_per_candidate
                ),
                "hidden_units": (
                    footprint.hidden_units
                ),
            }
            for method, footprint in footprints.items()
        },
        "validation_selection": {
            "selected_learned_method": (
                selection.learned_method
            ),
            "selected_learned_threshold": (
                selection.learned_threshold
            ),
            "selected_learned_recovery": (
                selection.learned_validation_recovery
            ),
            "learned_status": (
                selection.learned_validation_status
            ),
            "best_learned_recovery": (
                selection.best_learned_validation_recovery
            ),
            "selected_deterministic_method": (
                selection.deterministic_method
            ),
            "selected_deterministic_threshold": (
                selection.deterministic_threshold
            ),
            "selected_deterministic_recovery": (
                selection.deterministic_validation_recovery
            ),
            "teacher_validation_additional_savings": (
                selection.teacher_validation_additional_savings
            ),
            "learned_calibrations": {
                method: {
                    "threshold": calibration.threshold,
                    "mean_residual_additional_savings": (
                        calibration.mean_residual_additional_savings
                    ),
                    "mean_final_solver_ops": (
                        calibration.mean_final_solver_ops
                    ),
                    "mean_attempted_proposals": (
                        calibration.mean_attempted_proposals
                    ),
                }
                for method, calibration
                in learned_calibrations.items()
            },
            "deterministic_calibrations": {
                method: {
                    "threshold": calibration.threshold,
                    "mean_residual_additional_savings": (
                        calibration.mean_residual_additional_savings
                    ),
                    "mean_final_solver_ops": (
                        calibration.mean_final_solver_ops
                    ),
                    "mean_attempted_proposals": (
                        calibration.mean_attempted_proposals
                    ),
                }
                for method, calibration
                in deterministic_calibrations.items()
            },
        },
        "final_exact_residual_teacher": teacher_final,
        "final_learned_methods": learned_final,
        "final_deterministic_methods": (
            deterministic_final
        ),
        "primary_final": {
            "selected_learned_method": (
                selection.learned_method
            ),
            "selected_deterministic_method": (
                selection.deterministic_method
            ),
            "teacher_additional_savings": (
                teacher_value
            ),
            "learned_additional_savings": (
                selected_learned[
                    "mean_residual_additional_savings"
                ]
            ),
            "deterministic_additional_savings": (
                selected_deterministic[
                    "mean_residual_additional_savings"
                ]
            ),
            "learned_recovery": (
                decision["learned_recovery"]
            ),
            "deterministic_recovery": (
                deterministic_recovery
            ),
            "learned_advantage_fraction": (
                decision[
                    "learned_advantage_fraction"
                ]
            ),
            "decision": decision["decision"],
            "gates": {
                key: value
                for key, value in decision.items()
                if key.startswith("gate_")
            },
        },
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "all_deployable_methods_verified_and_safe": (
                all_deployable_safe
            ),
            "teacher_verified_and_safe": (
                teacher_safe
            ),
            "first_stage_threshold_frozen_0_10": (
                FROZEN_TARGET_LEAF_THRESHOLD
                == 0.10
            ),
        },
        "keep_v037_contract": keep,
        "boundary": (
            "v0.0.37 compares tiny state-aware residual "
            "predictors against cheap residual heuristics and an "
            "exact teacher on one generated affine-linear family. "
            "It does not establish total-compute superiority or "
            "domain-general Structural Compression."
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
