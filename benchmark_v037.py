from __future__ import annotations

import json

from neumann1.residual_predictor import (
    POLICIES,
    RESIDUAL_FEATURE_DIMENSION,
    TRIAL_BUDGET_PER_STATE,
    aggregate_policy_against_teacher,
    evaluate_policy,
    evaluate_teacher,
    fit_residual_models,
    policy_footprint,
    select_smallest_adequate_policy,
    teacher_aggregate,
)
from neumann1.residual_predictor_dataset import (
    V037_FINAL_EXAMPLES_PER_CELL,
    V037_TRAIN_EXAMPLES_PER_CELL,
    V037_VALIDATION_EXAMPLES_PER_CELL,
    prior_v037_signatures,
    v037_final_examples,
    v037_train_examples,
    v037_validation_examples,
)
from neumann1.learned_compression_dataset import (
    learned_scale_grid,
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


def _aggregate_policy(
    examples,
    method,
    teacher_rows,
    *,
    frozen,
    models,
):
    rows = evaluate_policy(
        examples,
        method,
        frozen_scorer=frozen,
        models=models,
    )
    footprint = policy_footprint(
        method,
        models,
    )
    aggregate = aggregate_policy_against_teacher(
        rows,
        teacher_rows,
        fitted_parameter_count=(
            footprint.fitted_weight_bias_scalars
        ),
        scaler_state_count=(
            footprint.scaler_state_scalars
        ),
        weighted_sum_terms_per_candidate=(
            footprint.weighted_sum_terms_per_candidate
        ),
    )
    return rows, aggregate


def run() -> dict[str, object]:
    train = v037_train_examples()
    validation = v037_validation_examples()
    final = v037_final_examples()

    train_signatures = _signatures(train)
    validation_signatures = _signatures(
        validation
    )
    final_signatures = _signatures(final)
    prior = prior_v037_signatures()

    disjoint_prior = (
        train_signatures.isdisjoint(prior)
        and validation_signatures.isdisjoint(prior)
        and final_signatures.isdisjoint(prior)
    )
    mutually_disjoint = (
        train_signatures.isdisjoint(
            validation_signatures
        )
        and train_signatures.isdisjoint(
            final_signatures
        )
        and validation_signatures.isdisjoint(
            final_signatures
        )
    )

    frozen = fit_frozen_v033_scorer()
    models = fit_residual_models(
        train,
        frozen_scorer=frozen,
    )

    validation_teacher = evaluate_teacher(
        validation,
        frozen_scorer=frozen,
    )
    validation_teacher_aggregate = (
        teacher_aggregate(validation_teacher)
    )

    validation_rows = {}
    validation_aggregates = {}
    for method in POLICIES:
        rows, aggregate = _aggregate_policy(
            validation,
            method,
            validation_teacher,
            frozen=frozen,
            models=models,
        )
        validation_rows[method] = rows
        validation_aggregates[method] = (
            aggregate
        )

    selected = select_smallest_adequate_policy(
        validation_aggregates
    )

    final_teacher = evaluate_teacher(
        final,
        frozen_scorer=frozen,
    )
    final_teacher_aggregate = (
        teacher_aggregate(final_teacher)
    )

    final_rows = {}
    final_aggregates = {}
    for method in POLICIES:
        rows, aggregate = _aggregate_policy(
            final,
            method,
            final_teacher,
            frozen=frozen,
            models=models,
        )
        final_rows[method] = rows
        final_aggregates[method] = aggregate

    selected_final_adequate = (
        bool(
            final_aggregates[selected][
                "adequate"
            ]
        )
        if selected is not None
        else False
    )

    if selected is None:
        decision = (
            "HOLD_NO_VALIDATION_ADEQUATE_POLICY"
        )
    elif not selected_final_adequate:
        decision = (
            "HOLD_FINAL_CONFIRMATION_FAIL"
        )
    elif selected in {
        "state_target_leaf",
        "state_markowitz",
    }:
        decision = (
            "DELETE_LEARNED_RESIDUAL"
        )
    else:
        decision = (
            "KEEP_LEARNED_RESIDUAL"
        )

    train_cells_complete = all(
        len(
            [
                example
                for example in train
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == V037_TRAIN_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )
    validation_cells_complete = all(
        len(
            [
                example
                for example in validation
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == V037_VALIDATION_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
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

    all_validation_safe = all(
        aggregate["verified_retention"] == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        and aggregate[
            "nonpositive_accepted_count"
        ]
        == 0
        for aggregate
        in validation_aggregates.values()
    )
    all_final_safe = all(
        aggregate["verified_retention"] == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        and aggregate[
            "nonpositive_accepted_count"
        ]
        == 0
        for aggregate
        in final_aggregates.values()
    )

    keep = (
        disjoint_prior
        and mutually_disjoint
        and train_cells_complete
        and validation_cells_complete
        and final_cells_complete
        and FROZEN_TARGET_LEAF_THRESHOLD
        == 0.10
        and TRIAL_BUDGET_PER_STATE == 4
        and RESIDUAL_FEATURE_DIMENSION == 28
        and all_validation_safe
        and all_final_safe
        and validation_teacher_aggregate[
            "verified_retention"
        ]
        == 1.0
        and final_teacher_aggregate[
            "verified_retention"
        ]
        == 1.0
    )

    return {
        "experiment": (
            "v0.0.37 Smallest Adequate "
            "State-Aware Residual Predictor"
        ),
        "data_contract": {
            "train_examples": len(train),
            "validation_examples": len(
                validation
            ),
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
            "disjoint_from_v033_v036": (
                disjoint_prior
            ),
            "splits_mutually_disjoint": (
                mutually_disjoint
            ),
        },
        "architecture_contract": {
            "target_leaf_threshold": (
                FROZEN_TARGET_LEAF_THRESHOLD
            ),
            "trial_budget_per_state": (
                TRIAL_BUDGET_PER_STATE
            ),
            "feature_dimension": (
                RESIDUAL_FEATURE_DIMENSION
            ),
            "policy_order": list(POLICIES),
        },
        "training": {
            "teacher_candidate_samples": (
                models.training_sample_count
            ),
            "positive_teacher_samples": (
                models.positive_training_sample_count
            ),
            "ridge_footprint": (
                models.ridge_footprint.__dict__
            ),
            "mlp8_footprint": (
                models.mlp8_footprint.__dict__
            ),
        },
        "validation_teacher": (
            validation_teacher_aggregate
        ),
        "validation_policies": (
            validation_aggregates
        ),
        "validation_selected_policy": (
            selected
        ),
        "final_teacher": (
            final_teacher_aggregate
        ),
        "final_policies": final_aggregates,
        "selected_policy_final_adequate": (
            selected_final_adequate
        ),
        "architecture_decision": decision,
        "contract_checks": {
            "train_cells_complete": (
                train_cells_complete
            ),
            "validation_cells_complete": (
                validation_cells_complete
            ),
            "final_cells_complete": (
                final_cells_complete
            ),
            "all_validation_policies_safe": (
                all_validation_safe
            ),
            "all_final_policies_safe": (
                all_final_safe
            ),
        },
        "keep_v037_contract": keep,
        "boundary": (
            "v0.0.37 selects the smallest policy that "
            "recovers residual solver-work value under a "
            "bounded exact positive-gain gate on one generated "
            "exact affine-linear family. It does not establish "
            "total-compute superiority or domain generality."
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
