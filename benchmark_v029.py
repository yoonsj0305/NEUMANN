from __future__ import annotations

import json
import math
from statistics import mean

from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.paired_linear_dataset import (
    make_near_negative,
    paired_linear_final_examples,
    paired_linear_training_examples,
    paired_linear_validation_examples,
)
from neumann1.paired_token_baseline import (
    direct_solution,
    fit_matched_token_models,
    inspect_matched_token_models,
    measure_token_model,
    structural_accepts_linear,
)
from neumann1.solvers import LinearSystemSolver
from neumann1.types import CostLedger, IRKind, Problem
from neumann1.verifier import DeterministicVerifier


def _reference_representation(text: str):
    ledger = CostLedger()
    representation = ControlledLinearSystemStructureFormer().form(
        Problem(text),
        ledger,
    )
    if representation.kind != IRKind.LINEAR_SYSTEM:
        raise RuntimeError(
            "generated positive example failed reference compiler"
        )
    return representation


def _max_equation_residual(
    representation,
    values: tuple[float, float],
) -> float:
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


def run():
    training = paired_linear_training_examples()
    validation = paired_linear_validation_examples()
    final = paired_linear_final_examples()

    models = fit_matched_token_models(
        training,
        validation,
        hidden_units=8,
        validation_negative_margin=0.10,
    )
    footprint = inspect_matched_token_models(models)
    solver = LinearSystemSolver()
    verifier = DeterministicVerifier()
    compiler = ControlledLinearSystemStructureFormer()

    rows = []
    direct_verified_count = 0
    structural_verified_count = 0
    structural_proposal_count = 0
    direct_squared_error = []
    direct_max_residuals = []

    for example in final:
        reference = _reference_representation(example.text)

        direct_observation = measure_token_model(
            models.direct_model,
            models.encoder,
            example.text,
        )
        structural_observation = measure_token_model(
            models.structural_model,
            models.encoder,
            example.text,
        )

        predicted_solution = direct_solution(
            models,
            direct_observation,
        )
        direct_answer = dict(
            zip(
                reference.payload["variables"],
                predicted_solution,
            )
        )
        direct_verification_ledger = CostLedger()
        direct_verification = verifier.verify(
            Problem(example.text),
            reference,
            direct_answer,
            direct_verification_ledger,
        )
        if direct_verification.ok:
            direct_verified_count += 1

        for predicted, expected in zip(
            predicted_solution,
            example.solution,
        ):
            direct_squared_error.append(
                (float(predicted) - float(expected)) ** 2
            )
        direct_residual = _max_equation_residual(
            reference,
            predicted_solution,
        )
        direct_max_residuals.append(direct_residual)

        accepted = structural_accepts_linear(
            models,
            structural_observation,
        )
        if accepted:
            structural_proposal_count += 1

        structural_ledger = CostLedger()
        structural_representation = None
        structural_verification = None
        if accepted:
            structural_representation = compiler.form(
                Problem(example.text),
                structural_ledger,
            )
            if structural_representation.kind == IRKind.LINEAR_SYSTEM:
                structural_answer = solver.solve(
                    structural_representation,
                    structural_ledger,
                )
                structural_verification = verifier.verify(
                    Problem(example.text),
                    structural_representation,
                    structural_answer,
                    structural_ledger,
                )
                if structural_verification.ok:
                    structural_verified_count += 1

        rows.append(
            {
                "text": example.text,
                "expected_solution": list(example.solution),
                "direct_solution": list(predicted_solution),
                "direct_verified": direct_verification.ok,
                "direct_max_equation_residual": direct_residual,
                "structural_proposed_linear": accepted,
                "structural_compiler_kind": (
                    structural_representation.kind.value
                    if structural_representation is not None
                    else IRKind.UNKNOWN.value
                ),
                "structural_verified": bool(
                    structural_verification
                    and structural_verification.ok
                ),
                "direct_dense_weighted_sum_terms_proxy": (
                    direct_observation.dense_weighted_sum_terms_proxy
                ),
                "structural_dense_weighted_sum_terms_proxy": (
                    structural_observation.dense_weighted_sum_terms_proxy
                ),
                "direct_active_input_scalars": (
                    direct_observation.active_input_scalars
                ),
                "structural_active_input_scalars": (
                    structural_observation.active_input_scalars
                ),
                "direct_wall_seconds": direct_observation.wall_seconds,
                "structural_wall_seconds": (
                    structural_observation.wall_seconds
                ),
                "structural_solver_steps": (
                    structural_ledger.solver_steps
                ),
                "structural_verification_steps": (
                    structural_ledger.verification_steps
                ),
                "direct_evaluation_verification_steps": (
                    direct_verification_ledger.verification_steps
                ),
            }
        )

    negative_rows = []
    proposal_false_routes = 0
    compiler_false_routes = 0
    for index, example in enumerate(final):
        text = make_near_negative(example, index)
        observation = measure_token_model(
            models.structural_model,
            models.encoder,
            text,
        )
        proposed = structural_accepts_linear(models, observation)
        if proposed:
            proposal_false_routes += 1

        ledger = CostLedger()
        representation = (
            compiler.form(Problem(text), ledger)
            if proposed
            else None
        )
        final_linear = bool(
            representation is not None
            and representation.kind == IRKind.LINEAR_SYSTEM
        )
        if final_linear:
            compiler_false_routes += 1

        negative_rows.append(
            {
                "text": text,
                "structural_proposed_linear": proposed,
                "compiler_final_linear_route": final_linear,
            }
        )

    count = len(final)
    direct_verified_rate = direct_verified_count / count
    structural_verified_rate = structural_verified_count / count
    structural_proposal_coverage = structural_proposal_count / count
    proposal_false_route_rate = proposal_false_routes / count
    compiler_false_route_rate = compiler_false_routes / count
    direct_rmse = math.sqrt(mean(direct_squared_error))

    matched_parameters = (
        footprint.structural_parameter_count
        == footprint.direct_parameter_count
    )
    matched_proxy = (
        footprint.structural_dense_weighted_sum_terms_proxy
        == footprint.direct_dense_weighted_sum_terms_proxy
    )
    all_finite = all(
        math.isfinite(value)
        for row in rows
        for value in row["direct_solution"]
    )

    keep = (
        matched_parameters
        and matched_proxy
        and footprint.structural_parameter_count > 0
        and all_finite
        and compiler_false_route_rate == 0.0
        and all(
            row["direct_dense_weighted_sum_terms_proxy"] > 0
            and row["structural_dense_weighted_sum_terms_proxy"] > 0
            for row in rows
        )
    )

    return {
        "experiment": (
            "v0.0.29 matched-capacity token direct-vs-structure"
        ),
        "corpus": {
            "training_positive_count": len(training),
            "training_structural_near_negative_count": len(training),
            "validation_positive_count": len(validation),
            "validation_structural_near_negative_count": len(validation),
            "final_positive_count": len(final),
            "final_structural_near_negative_count": len(final),
            "solution_range": [-4, 4],
            "system_shape": "2x2 nonsingular integer linear systems",
        },
        "matched_learned_capacity": {
            "hidden_units": models.hidden_units,
            "encoder_input_dimension": models.encoder.input_dimension,
            "structural_parameter_count": (
                footprint.structural_parameter_count
            ),
            "direct_parameter_count": footprint.direct_parameter_count,
            "parameter_ratio_structural_over_direct": (
                footprint.structural_parameter_count
                / footprint.direct_parameter_count
            ),
            "structural_layer_shapes": (
                footprint.structural_layer_shapes
            ),
            "direct_layer_shapes": footprint.direct_layer_shapes,
            "structural_dense_weighted_sum_terms_proxy": (
                footprint.structural_dense_weighted_sum_terms_proxy
            ),
            "direct_dense_weighted_sum_terms_proxy": (
                footprint.direct_dense_weighted_sum_terms_proxy
            ),
            "learned_proxy_ratio_structural_over_direct": (
                footprint.structural_dense_weighted_sum_terms_proxy
                / footprint.direct_dense_weighted_sum_terms_proxy
            ),
        },
        "structural_path": {
            "validation_margin_threshold": (
                models.structural_margin_threshold
            ),
            "final_positive_proposal_coverage": (
                structural_proposal_coverage
            ),
            "final_verified_coverage": structural_verified_rate,
            "near_negative_proposal_false_route_rate": (
                proposal_false_route_rate
            ),
            "near_negative_final_false_route_after_compiler": (
                compiler_false_route_rate
            ),
            "mean_model_wall_seconds": mean(
                row["structural_wall_seconds"]
                for row in rows
            ),
            "mean_solver_steps": mean(
                row["structural_solver_steps"] for row in rows
            ),
        },
        "direct_path": {
            "final_verified_coverage": direct_verified_rate,
            "solution_rmse": direct_rmse,
            "mean_max_equation_residual": mean(
                direct_max_residuals
            ),
            "median_max_equation_residual": sorted(
                direct_max_residuals
            )[len(direct_max_residuals) // 2],
            "mean_model_wall_seconds": mean(
                row["direct_wall_seconds"] for row in rows
            ),
        },
        "paired_outcome": {
            "verified_coverage_delta_structure_minus_direct": (
                structural_verified_rate - direct_verified_rate
            ),
            "same_parameter_count": matched_parameters,
            "same_dense_weighted_sum_proxy": matched_proxy,
        },
        "keep_paired_measurement_contract": keep,
        "rows": rows,
        "negative_rows": negative_rows,
        "boundary": (
            "This is a narrow generated 2x2 linear-system benchmark. "
            "Both learned paths use the same fixed-position token encoder, "
            "8-unit tanh MLP architecture, two-output head, and forward "
            "weighted-sum proxy. The direct model learns numeric solutions "
            "from positive systems only; the structural model sees the same "
            "positive systems plus paired near-negatives to learn abstention, "
            "so inference capacity is matched but supervision cardinality is "
            "not. The direct path receives no compiler or solver output during "
            "inference. A deterministic compiler is used only as an evaluation "
            "oracle so the existing verifier can judge direct numeric answers. "
            "The structural path actually executes proposal -> compiler -> "
            "solver -> verifier. This does not establish LLM, energy, FLOP, "
            "or open-domain reasoning efficiency."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
