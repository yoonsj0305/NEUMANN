from __future__ import annotations

import json
import math
from statistics import mean

from neumann1.direct_frontier import (
    fit_direct_frontier_models,
    frontier_configs,
    model_footprint,
    predict_direct,
    solution_pair_to_class,
)
from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.paired_linear_dataset import (
    direct_frontier_final_examples,
    direct_frontier_training_pool,
    direct_frontier_validation_examples,
    make_near_negative,
    paired_linear_training_examples,
    paired_linear_validation_examples,
)
from neumann1.paired_token_baseline import (
    fit_matched_token_models,
    measure_token_model,
    structural_accepts_linear,
)
from neumann1.solvers import LinearSystemSolver
from neumann1.types import CostLedger, IRKind, Problem
from neumann1.verifier import DeterministicVerifier


METHODS = (
    "raw_regression",
    "rounded_regression",
    "discrete_classification",
)


def _reference_representation(compiler, text):
    representation = compiler.form(Problem(text), CostLedger())
    if representation.kind != IRKind.LINEAR_SYSTEM:
        raise RuntimeError("frontier positive failed reference compiler")
    return representation


def _verify_solution(verifier, representation, values):
    answer = dict(zip(representation.payload["variables"], values))
    result = verifier.verify(
        Problem("evaluation-only"),
        representation,
        answer,
        CostLedger(),
    )
    return bool(result.ok)


def _max_equation_residual(representation, values):
    residuals = []
    for row, target in zip(
        representation.payload["A"],
        representation.payload["b"],
    ):
        lhs = sum(
            float(coefficient) * float(value)
            for coefficient, value in zip(row, values)
        )
        residuals.append(abs(lhs - float(target)))
    return max(residuals)


def _evaluate_direct(models, examples, compiler, verifier):
    verified = {method: 0 for method in METHODS}
    squared_error = {method: [] for method in METHODS}
    residuals = {method: [] for method in METHODS}
    regression_wall = []
    classifier_wall = []
    all_finite = True

    for example in examples:
        representation = _reference_representation(compiler, example.text)
        prediction = predict_direct(models, example.text)
        values_by_method = {
            "raw_regression": prediction.raw_regression,
            "rounded_regression": prediction.rounded_regression,
            "discrete_classification": prediction.discrete_classification,
        }

        regression_wall.append(prediction.regression_wall_seconds)
        classifier_wall.append(prediction.classifier_wall_seconds)

        for method, values in values_by_method.items():
            if not all(math.isfinite(value) for value in values):
                all_finite = False

            if _verify_solution(verifier, representation, values):
                verified[method] += 1

            for predicted, expected in zip(values, example.solution):
                squared_error[method].append(
                    (float(predicted) - float(expected)) ** 2
                )
            residuals[method].append(
                _max_equation_residual(representation, values)
            )

    count = len(examples)
    return {
        "verified_coverage": {
            method: verified[method] / count for method in METHODS
        },
        "rmse": {
            method: math.sqrt(mean(squared_error[method]))
            for method in METHODS
        },
        "mean_max_equation_residual": {
            method: mean(residuals[method]) for method in METHODS
        },
        "mean_regression_wall_seconds": mean(regression_wall),
        "mean_classifier_wall_seconds": mean(classifier_wall),
        "all_predictions_finite": all_finite,
    }


def _evaluate_structural(models, examples, compiler, solver, verifier):
    proposed = 0
    verified = 0
    model_wall = []
    solver_steps = []

    for example in examples:
        observation = measure_token_model(
            models.structural_model,
            models.encoder,
            example.text,
        )
        model_wall.append(observation.wall_seconds)

        if not structural_accepts_linear(models, observation):
            solver_steps.append(0)
            continue

        proposed += 1
        ledger = CostLedger()
        representation = compiler.form(Problem(example.text), ledger)
        if representation.kind != IRKind.LINEAR_SYSTEM:
            solver_steps.append(0)
            continue

        answer = solver.solve(representation, ledger)
        verification = verifier.verify(
            Problem(example.text),
            representation,
            answer,
            ledger,
        )
        solver_steps.append(ledger.solver_steps)
        if verification.ok:
            verified += 1

    count = len(examples)
    return {
        "proposal_coverage": proposed / count,
        "verified_coverage": verified / count,
        "mean_model_wall_seconds": mean(model_wall),
        "mean_solver_steps": mean(solver_steps),
    }


def _structural_negative_false_routes(models, examples, compiler):
    proposal_false = 0
    final_false = 0

    for index, example in enumerate(examples):
        text = make_near_negative(example, index)
        observation = measure_token_model(
            models.structural_model,
            models.encoder,
            text,
        )
        proposed = structural_accepts_linear(models, observation)
        if not proposed:
            continue

        proposal_false += 1
        representation = compiler.form(Problem(text), CostLedger())
        if representation.kind == IRKind.LINEAR_SYSTEM:
            final_false += 1

    count = len(examples)
    return {
        "proposal_false_route_rate": proposal_false / count,
        "compiler_gated_false_route_rate": final_false / count,
    }


def _method_cost(row, method):
    if method in {"raw_regression", "rounded_regression"}:
        return (
            row["regression_parameter_count"],
            row["regression_dense_weighted_sum_terms_proxy"],
        )
    return (
        row["classifier_parameter_count"],
        row["classifier_dense_weighted_sum_terms_proxy"],
    )


def _candidate_records(rows, split):
    records = []
    for row in rows:
        for method in METHODS:
            params, proxy = _method_cost(row, method)
            records.append(
                {
                    "training_size": row["training_size"],
                    "hidden_units": row["hidden_units"],
                    "method": method,
                    "verified_coverage": row[split]["verified_coverage"][method],
                    "parameter_count": params,
                    "dense_weighted_sum_terms_proxy": proxy,
                }
            )
    return records


def _best_candidate(records):
    return min(
        records,
        key=lambda record: (
            -record["verified_coverage"],
            record["dense_weighted_sum_terms_proxy"],
            record["parameter_count"],
            record["training_size"],
            record["hidden_units"],
            record["method"],
        ),
    )


def _break_even_candidate(records, target):
    eligible = [
        record
        for record in records
        if record["verified_coverage"] >= target
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda record: (
            record["dense_weighted_sum_terms_proxy"],
            record["parameter_count"],
            record["training_size"],
            record["hidden_units"],
            record["method"],
        ),
    )


def run():
    training_pool = direct_frontier_training_pool()
    validation = direct_frontier_validation_examples()
    final = direct_frontier_final_examples()

    compiler = ControlledLinearSystemStructureFormer()
    solver = LinearSystemSolver()
    verifier = DeterministicVerifier()

    structural_models = fit_matched_token_models(
        paired_linear_training_examples(),
        paired_linear_validation_examples(),
        hidden_units=8,
        validation_negative_margin=0.10,
    )

    structural_validation = _evaluate_structural(
        structural_models,
        validation,
        compiler,
        solver,
        verifier,
    )
    structural_final = _evaluate_structural(
        structural_models,
        final,
        compiler,
        solver,
        verifier,
    )
    structural_validation_negatives = _structural_negative_false_routes(
        structural_models,
        validation,
        compiler,
    )
    structural_final_negatives = _structural_negative_false_routes(
        structural_models,
        final,
        compiler,
    )

    fitted = []
    validation_rows = []

    for config in frontier_configs():
        models = fit_direct_frontier_models(
            training_pool,
            config,
            random_state=29,
        )
        reg_footprint = model_footprint(models.regressor)
        clf_footprint = model_footprint(models.classifier)
        validation_metrics = _evaluate_direct(
            models,
            validation,
            compiler,
            verifier,
        )

        fitted.append(models)
        validation_rows.append(
            {
                "training_size": config.training_size,
                "hidden_units": config.hidden_units,
                "regression_parameter_count": reg_footprint.parameter_count,
                "regression_layer_shapes": reg_footprint.layer_shapes,
                "regression_dense_weighted_sum_terms_proxy": (
                    reg_footprint.dense_weighted_sum_terms_proxy
                ),
                "classifier_parameter_count": clf_footprint.parameter_count,
                "classifier_layer_shapes": clf_footprint.layer_shapes,
                "classifier_dense_weighted_sum_terms_proxy": (
                    clf_footprint.dense_weighted_sum_terms_proxy
                ),
                "regression_training_seconds": (
                    models.regression_training_seconds
                ),
                "classifier_training_seconds": (
                    models.classifier_training_seconds
                ),
                "regression_convergence_warning": (
                    models.regression_convergence_warning
                ),
                "classifier_convergence_warning": (
                    models.classifier_convergence_warning
                ),
                "validation": validation_metrics,
            }
        )

    validation_candidates = _candidate_records(
        validation_rows,
        "validation",
    )
    validation_best = _best_candidate(validation_candidates)
    validation_break_even = _break_even_candidate(
        validation_candidates,
        structural_validation["verified_coverage"],
    )

    final_rows = []
    all_finite = True

    for models, validation_row in zip(fitted, validation_rows):
        final_metrics = _evaluate_direct(
            models,
            final,
            compiler,
            verifier,
        )
        all_finite = (
            all_finite
            and final_metrics["all_predictions_finite"]
            and validation_row["validation"]["all_predictions_finite"]
        )
        row = dict(validation_row)
        row["final"] = final_metrics
        final_rows.append(row)

    final_candidates = _candidate_records(final_rows, "final")
    observed_final_best = _best_candidate(final_candidates)
    observed_final_break_even = _break_even_candidate(
        final_candidates,
        structural_final["verified_coverage"],
    )

    validation_selected_final = None
    for record in final_candidates:
        if (
            record["training_size"] == validation_best["training_size"]
            and record["hidden_units"] == validation_best["hidden_units"]
            and record["method"] == validation_best["method"]
        ):
            validation_selected_final = record
            break

    if validation_selected_final is None:
        raise RuntimeError(
            "validation-selected configuration missing from final grid"
        )

    train_texts = {example.text for example in training_pool}
    validation_texts = {example.text for example in validation}
    final_texts = {example.text for example in final}
    split_disjoint = (
        train_texts.isdisjoint(validation_texts)
        and train_texts.isdisjoint(final_texts)
        and validation_texts.isdisjoint(final_texts)
    )

    all_classes = set(range(81))
    prefix_class_coverage = {
        str(size): (
            {
                solution_pair_to_class(example.solution)
                for example in training_pool[:size]
            }
            == all_classes
        )
        for size in (128, 512, 2048)
    }

    keep = (
        len(frontier_configs()) == 12
        and split_disjoint
        and all(prefix_class_coverage.values())
        and all_finite
        and (
            structural_validation_negatives[
                "compiler_gated_false_route_rate"
            ]
            == 0.0
        )
        and (
            structural_final_negatives[
                "compiler_gated_false_route_rate"
            ]
            == 0.0
        )
        and all(
            row["regression_parameter_count"] > 0
            and row["classifier_parameter_count"] > 0
            and row["regression_dense_weighted_sum_terms_proxy"] > 0
            and row["classifier_dense_weighted_sum_terms_proxy"] > 0
            for row in final_rows
        )
    )

    return {
        "experiment": "v0.0.30 direct capacity/data break-even frontier",
        "pre_registered_grid": {
            "training_sizes": [128, 512, 2048],
            "hidden_units": [8, 16, 32, 64],
            "config_count": len(frontier_configs()),
            "direct_methods": list(METHODS),
            "training_pool_count": len(training_pool),
            "validation_count": len(validation),
            "final_count": len(final),
            "prefix_has_all_81_solution_classes": prefix_class_coverage,
            "splits_text_disjoint": split_disjoint,
        },
        "fixed_structural_reference": {
            "architecture": "640 -> 8 -> 2",
            "training_positive_count": 128,
            "training_near_negative_count": 128,
            "validation": structural_validation,
            "validation_near_negatives": structural_validation_negatives,
            "final": structural_final,
            "final_near_negatives": structural_final_negatives,
        },
        "validation_selection": {
            "best_direct_candidate": validation_best,
            "break_even_against_structural": validation_break_even,
        },
        "final_report": {
            "validation_selected_candidate_on_final": (
                validation_selected_final
            ),
            "observed_best_pre_registered_final_candidate": (
                observed_final_best
            ),
            "observed_final_break_even_against_structural": (
                observed_final_break_even
            ),
        },
        "grid_rows": final_rows,
        "keep_direct_break_even_frontier_contract": keep,
        "boundary": (
            "The Direct sweep is a pre-registered controlled challenge to "
            "v0.0.29. It includes raw regression, regression rounded/clipped "
            "to the known integer support, and an 81-class discrete Direct "
            "classifier so strict verification does not by itself handicap "
            "Direct. Validation is evaluated before final. All final grid "
            "cells were pre-registered; observed final best is descriptive "
            "and is not used to tune training. Training size is not inference "
            "cost. Learned weighted-sum proxies and deterministic solver steps "
            "remain different units and are not added. This remains a narrow "
            "fixed-position token benchmark, not an LLM, FLOP, memory, energy, "
            "or open-domain reasoning result."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
