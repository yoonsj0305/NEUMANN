from __future__ import annotations

import json
from statistics import mean

from neumann1 import (
    CostLedger,
    IRKind,
    Problem,
    builtin_family_registry,
    inspect_two_stage_model,
    measure_repeated_proposal_reuse,
    measure_two_stage_proposal,
)
from neumann1.compiler_gate_dataset import (
    compiler_gate_final_examples,
    compiler_gate_training_examples,
    compiler_gate_validation_examples,
)
from neumann1.learned_compiler_gate import LearnedProposalCompilerGate
from neumann1.neural_model_cost import (
    inspect_tiny_neural_model,
    measure_repeated_neural_proposal_reuse,
    measure_tiny_neural_proposal,
)
from neumann1.neural_open_set import TinyNeuralOpenSetStructureFormer
from neumann1.open_set import TwoStageOpenSetStructureFormer


REPEATS = 8


def build_models():
    training = compiler_gate_training_examples()
    validation = compiler_gate_validation_examples()

    logistic = TwoStageOpenSetStructureFormer().fit(training)
    logistic_validation = logistic.tune_threshold(validation)

    neural = TinyNeuralOpenSetStructureFormer(
        hidden_units=4,
        alpha=1e-3,
    ).fit(training)
    neural_validation = neural.tune_threshold(validation)

    registry = builtin_family_registry()
    compilers = registry.compilers_by_kind()

    return (
        logistic,
        LearnedProposalCompilerGate(logistic, compilers),
        logistic_validation,
        neural,
        LearnedProposalCompilerGate(neural, compilers),
        neural_validation,
        registry,
    )


def _false_route_rate(rows, key):
    unknown = [
        row
        for row in rows
        if row["expected"] == IRKind.UNKNOWN.value
    ]
    if not unknown:
        return 0.0
    return sum(
        row[key] != IRKind.UNKNOWN.value
        for row in unknown
    ) / len(unknown)


def _known_verified_rate(rows, key):
    known = [
        row
        for row in rows
        if row["expected"] != IRKind.UNKNOWN.value
    ]
    if not known:
        return 0.0
    return mean(float(row[key]) for row in known)


def run():
    (
        logistic,
        logistic_gate,
        logistic_validation,
        neural,
        neural_gate,
        neural_validation,
        registry,
    ) = build_models()

    logistic_footprint = inspect_two_stage_model(logistic)
    neural_footprint = inspect_tiny_neural_model(neural)
    rows = []

    for text, expected, bucket in compiler_gate_final_examples():
        logistic_cost = measure_two_stage_proposal(logistic, text)
        neural_cost = measure_tiny_neural_proposal(neural, text)

        logistic_ledger = CostLedger()
        logistic_final = logistic_gate.form(
            Problem(text),
            logistic_ledger,
        )

        neural_ledger = CostLedger()
        neural_final = neural_gate.form(
            Problem(text),
            neural_ledger,
        )

        neural_verified = False
        if (
            expected != IRKind.UNKNOWN
            and neural_final.kind == expected
        ):
            adapter = registry.get(expected)
            if adapter is None:
                raise RuntimeError(f"missing adapter for {expected}")
            answer = adapter.solver.solve(neural_final, neural_ledger)
            verification = adapter.answer_verifier.verify(
                Problem(text),
                neural_final,
                answer,
                neural_ledger,
            )
            neural_verified = bool(verification.ok)

        repeated_neural = measure_repeated_neural_proposal_reuse(
            neural,
            text,
            repeats=REPEATS,
        )

        rows.append({
            "text": text,
            "bucket": bucket,
            "expected": expected.value,
            "logistic_proposal": logistic_cost.predicted_kind.value,
            "neural_proposal": neural_cost.predicted_kind.value,
            "logistic_final": logistic_final.kind.value,
            "neural_final": neural_final.kind.value,
            "neural_solver_verified": neural_verified,
            "logistic_active_features": logistic_cost.total_active_features,
            "neural_active_features": neural_cost.total_active_features,
            "logistic_score_terms_proxy": (
                logistic_cost.score_dot_product_terms_proxy
            ),
            "neural_weighted_sum_terms_proxy": (
                neural_cost.weighted_sum_terms_proxy
            ),
            "logistic_stages_executed": logistic_cost.stages_executed,
            "neural_stages_executed": neural_cost.stages_executed,
            "logistic_wall_seconds": logistic_cost.wall_seconds,
            "neural_wall_seconds": neural_cost.wall_seconds,
            "neural_prediction_stable": (
                repeated_neural.prediction_stable
            ),
            "neural_repeated_weighted_sum_reduction_factor": (
                repeated_neural.weighted_sum_term_reduction_factor
            ),
        })

    logistic_mean_terms = mean(
        row["logistic_score_terms_proxy"] for row in rows
    )
    neural_mean_terms = mean(
        row["neural_weighted_sum_terms_proxy"] for row in rows
    )
    parameter_ratio = (
        neural_footprint.neural_parameter_count
        / logistic_footprint.linear_parameter_count
    )
    term_ratio = neural_mean_terms / logistic_mean_terms

    known = [
        row
        for row in rows
        if row["expected"] != IRKind.UNKNOWN.value
    ]

    neural_known_proposal_coverage = mean(
        float(row["neural_proposal"] != IRKind.UNKNOWN.value)
        for row in known
    )
    neural_known_family_accuracy = mean(
        float(row["neural_proposal"] == row["expected"])
        for row in known
    )
    neural_known_final_acceptance = mean(
        float(row["neural_final"] == row["expected"])
        for row in known
    )
    neural_verified_coverage = _known_verified_rate(
        rows,
        "neural_solver_verified",
    )
    neural_proposal_false_route = _false_route_rate(
        rows,
        "neural_proposal",
    )
    neural_final_false_route = _false_route_rate(
        rows,
        "neural_final",
    )
    logistic_proposal_false_route = _false_route_rate(
        rows,
        "logistic_proposal",
    )
    logistic_final_false_route = _false_route_rate(
        rows,
        "logistic_final",
    )

    keep = (
        neural_validation.known_coverage == 1.0
        and neural_known_proposal_coverage == 1.0
        and neural_known_family_accuracy == 1.0
        and neural_known_final_acceptance == 1.0
        and neural_verified_coverage == 1.0
        and neural_final_false_route == 0.0
        and neural_footprint.neural_parameter_count > 0
        and all(
            row["neural_weighted_sum_terms_proxy"] > 0
            for row in rows
        )
        and all(
            row["neural_prediction_stable"]
            for row in rows
        )
        and all(
            row["neural_repeated_weighted_sum_reduction_factor"]
            == float(REPEATS)
            for row in rows
        )
    )

    return {
        "experiment": "v0.0.28 tiny neural structural proposer contract",
        "repeats": REPEATS,
        "logistic_baseline": {
            "validation_threshold": logistic.threshold,
            "validation_known_coverage": (
                logistic_validation.known_coverage
            ),
            "linear_parameter_count": (
                logistic_footprint.linear_parameter_count
            ),
            "vectorizer_idf_state_count": (
                logistic_footprint.vectorizer_idf_state_count
            ),
            "proposal_false_route_rate": (
                logistic_proposal_false_route
            ),
            "final_false_route_rate": (
                logistic_final_false_route
            ),
            "mean_score_terms_proxy": logistic_mean_terms,
            "mean_wall_seconds": mean(
                row["logistic_wall_seconds"] for row in rows
            ),
        },
        "tiny_neural": {
            "validation_threshold": neural.threshold,
            "validation_known_coverage": (
                neural_validation.known_coverage
            ),
            "hidden_units": neural.hidden_units,
            "neural_parameter_count": (
                neural_footprint.neural_parameter_count
            ),
            "vectorizer_idf_state_count": (
                neural_footprint.vectorizer_idf_state_count
            ),
            "known_layer_shapes": (
                neural_footprint.known_layer_shapes
            ),
            "kind_layer_shapes": neural_footprint.kind_layer_shapes,
            "known_proposal_coverage": (
                neural_known_proposal_coverage
            ),
            "known_family_accuracy": (
                neural_known_family_accuracy
            ),
            "known_final_compiler_acceptance": (
                neural_known_final_acceptance
            ),
            "known_end_to_end_verified_coverage": (
                neural_verified_coverage
            ),
            "proposal_false_route_rate": (
                neural_proposal_false_route
            ),
            "final_false_route_rate": (
                neural_final_false_route
            ),
            "mean_active_features": mean(
                row["neural_active_features"] for row in rows
            ),
            "mean_weighted_sum_terms_proxy": neural_mean_terms,
            "mean_wall_seconds": mean(
                row["neural_wall_seconds"] for row in rows
            ),
            "mean_repeated_weighted_sum_reduction_factor": mean(
                row[
                    "neural_repeated_weighted_sum_reduction_factor"
                ]
                for row in rows
            ),
        },
        "comparison": {
            "neural_to_logistic_parameter_ratio": parameter_ratio,
            "neural_to_logistic_term_proxy_ratio": term_ratio,
            "proposal_false_route_delta_neural_minus_logistic": (
                neural_proposal_false_route
                - logistic_proposal_false_route
            ),
            "final_false_route_delta_neural_minus_logistic": (
                neural_final_false_route
                - logistic_final_false_route
            ),
        },
        "keep_tiny_neural_proposer_contract": keep,
        "rows": rows,
        "boundary": (
            "The tiny neural proposer is a one-hidden-layer MLP over TF-IDF "
            "features, not a language model. Parameter counts are fitted MLP "
            "weights and biases only. weighted_sum_terms_proxy counts sparse "
            "first-layer and dense later-layer weighted terms, not FLOPs, "
            "instructions, memory traffic, latency, or joules. Cost superiority "
            "over logistic regression is deliberately not a KEEP condition."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
