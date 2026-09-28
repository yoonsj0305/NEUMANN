from __future__ import annotations

import json

from neumann1.residual_policy import (
    DETERMINISTIC_METHODS,
    DETERMINISTIC_THRESHOLD_GRID,
    RESIDUAL_FEATURE_DIMENSION,
    TREE_DEPTHS,
    aggregate_policy_observations,
    calibrate_residual_policy,
    prepare_initial_state,
    rollout_exact_residual_teacher,
    rollout_residual_policy,
    select_smallest_adequate_tree,
    teacher_training_rows,
)
from neumann1.residual_policy_dataset import (
    V037_CALIBRATION_EXAMPLES_PER_CELL,
    V037_FINAL_EXAMPLES_PER_CELL,
    V037_TRAIN_EXAMPLES_PER_CELL,
    prior_v037_signatures,
    v037_calibration_examples,
    v037_final_examples,
    v037_train_examples,
)
from neumann1.learned_compression_dataset import (
    learned_scale_grid,
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
    method_gain: float,
    teacher_gain: float,
):
    if teacher_gain <= 0:
        return None
    return (
        method_gain
        / teacher_gain
    )


def run() -> dict[str, object]:
    train_examples = (
        v037_train_examples()
    )
    calibration_examples = (
        v037_calibration_examples()
    )
    final_examples = (
        v037_final_examples()
    )
    frozen = fit_frozen_v033_scorer()

    train_signatures = _signatures(
        train_examples
    )
    calibration_signatures = _signatures(
        calibration_examples
    )
    final_signatures = _signatures(
        final_examples
    )
    prior = prior_v037_signatures()

    data_disjoint = (
        train_signatures.isdisjoint(prior)
        and calibration_signatures.isdisjoint(prior)
        and final_signatures.isdisjoint(prior)
        and train_signatures.isdisjoint(
            calibration_signatures
        )
        and train_signatures.isdisjoint(
            final_signatures
        )
        and calibration_signatures.isdisjoint(
            final_signatures
        )
    )

    train_states = tuple(
        prepare_initial_state(
            example,
            frozen_scorer=frozen,
        )
        for example in train_examples
    )
    calibration_states = tuple(
        prepare_initial_state(
            example,
            frozen_scorer=frozen,
        )
        for example in calibration_examples
    )

    training_rows = (
        teacher_training_rows(
            train_states
        )
    )

    (
        selected_tree,
        selected_tree_calibration,
        tree_candidates,
    ) = select_smallest_adequate_tree(
        training_rows,
        calibration_states,
    )

    deterministic_calibrations = {
        method: calibrate_residual_policy(
            calibration_states,
            method=method,
            thresholds=(
                DETERMINISTIC_THRESHOLD_GRID
            ),
        )
        for method in DETERMINISTIC_METHODS
    }

    final_states = tuple(
        prepare_initial_state(
            example,
            frozen_scorer=frozen,
        )
        for example in final_examples
    )

    teacher_rows = tuple(
        rollout_exact_residual_teacher(
            initial
        )
        for initial in final_states
    )
    teacher = (
        aggregate_policy_observations(
            teacher_rows
        )
    )

    learned_rows = tuple(
        rollout_residual_policy(
            initial,
            method="learned_tree",
            threshold=(
                selected_tree_calibration.threshold
            ),
            tree_model=selected_tree,
        )
        for initial in final_states
    )
    learned = (
        aggregate_policy_observations(
            learned_rows
        )
    )

    deterministic_rows = {}
    deterministic = {}
    for method in DETERMINISTIC_METHODS:
        calibration = (
            deterministic_calibrations[
                method
            ]
        )
        rows = tuple(
            rollout_residual_policy(
                initial,
                method=method,
                threshold=(
                    calibration.threshold
                ),
            )
            for initial in final_states
        )
        deterministic_rows[
            method
        ] = rows
        deterministic[
            method
        ] = (
            aggregate_policy_observations(
                rows
            )
        )

    best_deterministic_method = min(
        DETERMINISTIC_METHODS,
        key=lambda method: (
            deterministic[
                method
            ][
                "mean_final_solver_ops"
            ],
            deterministic[
                method
            ][
                "mean_proposal_materializations"
            ],
            method,
        ),
    )
    best_deterministic = (
        deterministic[
            best_deterministic_method
        ]
    )

    teacher_gain = float(
        teacher[
            "mean_residual_additional_solver_savings"
        ]
    )
    learned_gain = float(
        learned[
            "mean_residual_additional_solver_savings"
        ]
    )
    learned_recovery = _recovery(
        learned_gain,
        teacher_gain,
    )

    deterministic_recovery = {
        method: _recovery(
            float(
                deterministic[
                    method
                ][
                    "mean_residual_additional_solver_savings"
                ]
            ),
            teacher_gain,
        )
        for method in DETERMINISTIC_METHODS
    }

    learned_final_ops = float(
        learned[
            "mean_final_solver_ops"
        ]
    )
    learned_proposals = float(
        learned[
            "mean_proposal_materializations"
        ]
    )
    best_det_ops = float(
        best_deterministic[
            "mean_final_solver_ops"
        ]
    )
    best_det_proposals = float(
        best_deterministic[
            "mean_proposal_materializations"
        ]
    )

    route_a = (
        learned_final_ops
        <= 0.90 * best_det_ops
        and learned_proposals
        <= 2.0 * best_det_proposals
    )
    route_b = (
        all(
            learned_final_ops
            < float(
                deterministic[
                    method
                ][
                    "mean_final_solver_ops"
                ]
            )
            for method
            in DETERMINISTIC_METHODS
        )
        and learned_proposals
        <= best_det_proposals
    )

    learned_recovery_gate = (
        learned_recovery is not None
        and learned_recovery >= 0.75
    )
    meaningful_teacher_headroom = (
        teacher_gain
        >= 0.05
        * float(
            teacher[
                "mean_target_leaf_solver_ops"
            ]
        )
    )

    all_methods_safe = (
        teacher[
            "verified_retention"
        ]
        == 1.0
        and teacher[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        and learned[
            "verified_retention"
        ]
        == 1.0
        and learned[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        and all(
            aggregate[
                "verified_retention"
            ]
            == 1.0
            and aggregate[
                "unsafe_accepted_reduction_count"
            ]
            == 0
            for aggregate
            in deterministic.values()
        )
    )

    if (
        all_methods_safe
        and learned_recovery_gate
        and (
            route_a
            or route_b
        )
    ):
        decision = (
            "KEEP_LEARNED_RESIDUAL"
        )
    elif (
        all_methods_safe
        and learned_recovery_gate
    ):
        decision = (
            "KEEP_DETERMINISTIC_RESIDUAL"
        )
    elif (
        all_methods_safe
        and meaningful_teacher_headroom
    ):
        decision = (
            "ESCALATE_MODEL_CLASS"
        )
    else:
        decision = (
            "DELETE_RESIDUAL_MODEL"
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
        == V037_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    feature_contract_ok = (
        selected_tree.feature_dimension
        == RESIDUAL_FEATURE_DIMENSION
    )
    depth_contract_ok = (
        selected_tree.requested_max_depth
        in TREE_DEPTHS
    )
    target_leaf_nonworsening = all(
        row.final_solver_ops
        <= row.target_leaf_solver_ops
        for row in learned_rows
    ) and all(
        row.final_solver_ops
        <= row.target_leaf_solver_ops
        for rows
        in deterministic_rows.values()
        for row in rows
    )

    keep = (
        data_disjoint
        and final_cells_complete
        and feature_contract_ok
        and depth_contract_ok
        and all_methods_safe
        and target_leaf_nonworsening
    )

    return {
        "experiment": (
            "v0.0.37 State-Aware "
            "Residual Policy Gauntlet"
        ),
        "data_contract": {
            "train_examples_per_cell": (
                V037_TRAIN_EXAMPLES_PER_CELL
            ),
            "calibration_examples_per_cell": (
                V037_CALIBRATION_EXAMPLES_PER_CELL
            ),
            "final_examples_per_cell": (
                V037_FINAL_EXAMPLES_PER_CELL
            ),
            "train_examples": len(
                train_examples
            ),
            "calibration_examples": len(
                calibration_examples
            ),
            "final_examples": len(
                final_examples
            ),
            "all_splits_and_prior_disjoint": (
                data_disjoint
            ),
            "training_state_action_rows": len(
                training_rows
            ),
        },
        "selected_learned_tree": {
            "feature_dimension": (
                selected_tree.feature_dimension
            ),
            "requested_max_depth": (
                selected_tree.requested_max_depth
            ),
            "fitted_depth": (
                selected_tree.fitted_depth
            ),
            "fitted_node_count": (
                selected_tree.fitted_node_count
            ),
            "fitted_leaf_count": (
                selected_tree.fitted_leaf_count
            ),
            "threshold": (
                selected_tree_calibration.threshold
            ),
            "calibration_mean_residual_additional_savings": (
                selected_tree_calibration
                .mean_residual_additional_savings
            ),
            "calibration_mean_final_solver_ops": (
                selected_tree_calibration
                .mean_final_solver_ops
            ),
            "calibration_mean_proposal_materializations": (
                selected_tree_calibration
                .mean_proposal_materializations
            ),
        },
        "tree_capacity_calibration": [
            {
                "requested_max_depth": (
                    model.requested_max_depth
                ),
                "fitted_depth": (
                    model.fitted_depth
                ),
                "node_count": (
                    model.fitted_node_count
                ),
                "leaf_count": (
                    model.fitted_leaf_count
                ),
                "threshold": (
                    calibration.threshold
                ),
                "mean_residual_additional_savings": (
                    calibration
                    .mean_residual_additional_savings
                ),
                "mean_final_solver_ops": (
                    calibration
                    .mean_final_solver_ops
                ),
                "mean_proposal_materializations": (
                    calibration
                    .mean_proposal_materializations
                ),
            }
            for model, calibration
            in tree_candidates
        ],
        "deterministic_calibrations": {
            method: {
                "threshold": (
                    calibration.threshold
                ),
                "mean_residual_additional_savings": (
                    calibration
                    .mean_residual_additional_savings
                ),
                "mean_final_solver_ops": (
                    calibration
                    .mean_final_solver_ops
                ),
                "mean_proposal_materializations": (
                    calibration
                    .mean_proposal_materializations
                ),
            }
            for method, calibration
            in deterministic_calibrations.items()
        },
        "final": {
            "exact_residual_teacher": (
                teacher
            ),
            "learned_tree": (
                learned
            ),
            "deterministic": (
                deterministic
            ),
        },
        "comparisons": {
            "best_deterministic_method": (
                best_deterministic_method
            ),
            "teacher_residual_gain": (
                teacher_gain
            ),
            "learned_residual_gain": (
                learned_gain
            ),
            "learned_teacher_gain_recovery": (
                learned_recovery
            ),
            "deterministic_teacher_gain_recovery": (
                deterministic_recovery
            ),
            "learned_vs_best_deterministic_final_solver_ops_delta": (
                learned_final_ops
                - best_det_ops
            ),
            "learned_vs_best_deterministic_proposal_delta": (
                learned_proposals
                - best_det_proposals
            ),
        },
        "retention_gate": {
            "learned_recovery_ge_0_75": (
                learned_recovery_gate
            ),
            "route_a_material_solver_advantage": (
                route_a
            ),
            "route_b_pareto_advantage": (
                route_b
            ),
            "meaningful_teacher_headroom": (
                meaningful_teacher_headroom
            ),
            "decision": decision,
        },
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "feature_contract_ok": (
                feature_contract_ok
            ),
            "depth_contract_ok": (
                depth_contract_ok
            ),
            "all_methods_safe": (
                all_methods_safe
            ),
            "positive_utility_guard_never_worsens_target_leaf": (
                target_leaf_nonworsening
            ),
        },
        "keep_v037_contract": keep,
        "boundary": (
            "v0.0.37 tests a tiny state-aware learned residual "
            "ranker against state-aware deterministic residual "
            "baselines. All proposals remain advisory and require "
            "measured positive marginal solver gain plus full "
            "original-problem verification."
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
