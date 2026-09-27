from __future__ import annotations

import json
from statistics import mean

from neumann1 import (
    CostLedger,
    IRKind,
    Problem,
    builtin_family_registry,
    canonical_representation_bytes,
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
from neumann1.open_set import TwoStageOpenSetStructureFormer


REPEATS = 8


def build_gate():
    proposer = TwoStageOpenSetStructureFormer().fit(compiler_gate_training_examples())
    validation = proposer.tune_threshold(compiler_gate_validation_examples())
    registry = builtin_family_registry()
    gate = LearnedProposalCompilerGate(proposer, registry.compilers_by_kind())
    return proposer, gate, registry, validation


def _false_route_rate(rows, key):
    items = [row for row in rows if row["expected"] == IRKind.UNKNOWN.value]
    if not items:
        return 0.0
    return sum(row[key] != IRKind.UNKNOWN.value for row in items) / len(items)


def run():
    proposer, gate, registry, validation = build_gate()
    footprint = inspect_two_stage_model(proposer)
    rows = []

    for text, expected, bucket in compiler_gate_final_examples():
        measured = measure_two_stage_proposal(proposer, text)
        public_kind, public_confidence = proposer.predict_kind(text)
        repeated = measure_repeated_proposal_reuse(
            proposer,
            text,
            repeats=REPEATS,
        )

        ledger = CostLedger()
        final_representation = gate.form(Problem(text), ledger)
        final_kind = final_representation.kind
        solver_verified = False
        representation_bytes = None

        if expected != IRKind.UNKNOWN and final_kind == expected:
            adapter = registry.get(expected)
            if adapter is None:
                raise RuntimeError(f"missing adapter for {expected}")
            answer = adapter.solver.solve(final_representation, ledger)
            verification = adapter.answer_verifier.verify(
                Problem(text), final_representation, answer, ledger
            )
            solver_verified = bool(verification.ok)
            representation_bytes = len(
                canonical_representation_bytes(final_representation)
            )

        rows.append({
            "text": text,
            "bucket": bucket,
            "expected": expected.value,
            "measured_proposal": measured.predicted_kind.value,
            "public_proposal": public_kind.value,
            "proposal_confidence": measured.confidence,
            "known_probability": measured.known_probability,
            "prediction_parity": (
                measured.predicted_kind == public_kind
                and abs(measured.confidence - public_confidence) <= 1e-12
            ),
            "stages_executed": measured.stages_executed,
            "known_active_features": measured.known_active_features,
            "kind_active_features": measured.kind_active_features,
            "score_dot_product_terms_proxy": (
                measured.score_dot_product_terms_proxy
            ),
            "proposal_wall_seconds": measured.wall_seconds,
            "final": final_kind.value,
            "solver_verified": solver_verified,
            "representation_bytes": representation_bytes,
            "compiler_rescued_false_proposal": (
                expected == IRKind.UNKNOWN
                and measured.predicted_kind != IRKind.UNKNOWN
                and final_kind == IRKind.UNKNOWN
            ),
            "representation_steps": ledger.representation_steps,
            "solver_steps": ledger.solver_steps,
            "verification_steps": ledger.verification_steps,
            "repeated_prediction_stable": repeated.prediction_stable,
            "repeated_score_terms_every_time": repeated.score_terms_every_time,
            "repeated_score_terms_once_reuse": repeated.score_terms_once_reuse,
            "repeated_score_term_reduction_factor": (
                repeated.score_term_reduction_factor
            ),
            "repeated_model_wall_seconds_every_time": (
                repeated.measured_model_wall_seconds_every_time
            ),
            "repeated_model_wall_seconds_once": (
                repeated.measured_model_wall_seconds_once
            ),
        })

    known = [row for row in rows if row["expected"] != IRKind.UNKNOWN.value]

    prediction_parity_rate = mean(float(row["prediction_parity"]) for row in rows)
    known_proposal_coverage = mean(
        float(row["measured_proposal"] != IRKind.UNKNOWN.value) for row in known
    )
    known_final_compiler_acceptance = mean(
        float(row["final"] == row["expected"]) for row in known
    )
    known_end_to_end_verified_coverage = mean(
        float(row["solver_verified"]) for row in known
    )
    unknown_proposal_false_route_rate = _false_route_rate(rows, "measured_proposal")
    unknown_final_false_route_rate = _false_route_rate(rows, "final")

    keep = (
        prediction_parity_rate == 1.0
        and known_proposal_coverage == 1.0
        and known_final_compiler_acceptance == 1.0
        and known_end_to_end_verified_coverage == 1.0
        and unknown_final_false_route_rate == 0.0
        and footprint.linear_parameter_count > 0
        and all(row["score_dot_product_terms_proxy"] > 0 for row in rows)
        and all(row["repeated_prediction_stable"] for row in rows)
        and all(
            row["repeated_score_term_reduction_factor"] == float(REPEATS)
            for row in rows
        )
    )

    return {
        "experiment": "v0.0.27 model-side structural proposal cost contract",
        "validation_threshold": proposer.threshold,
        "validation_known_coverage": validation.known_coverage,
        "repeats": REPEATS,
        "model_footprint": {
            "known_feature_count": footprint.known_feature_count,
            "kind_feature_count": footprint.kind_feature_count,
            "linear_parameter_count": footprint.linear_parameter_count,
            "vectorizer_idf_state_count": footprint.vectorizer_idf_state_count,
        },
        "summary": {
            "prediction_parity_rate": prediction_parity_rate,
            "known_proposal_coverage": known_proposal_coverage,
            "known_final_compiler_acceptance": known_final_compiler_acceptance,
            "known_end_to_end_verified_coverage": (
                known_end_to_end_verified_coverage
            ),
            "unknown_proposal_false_route_rate": (
                unknown_proposal_false_route_rate
            ),
            "unknown_final_false_route_rate": unknown_final_false_route_rate,
            "compiler_rescued_false_proposals": sum(
                int(row["compiler_rescued_false_proposal"]) for row in rows
            ),
            "mean_stages_executed": mean(row["stages_executed"] for row in rows),
            "mean_active_features": mean(
                row["known_active_features"] + row["kind_active_features"]
                for row in rows
            ),
            "mean_score_dot_product_terms_proxy": mean(
                row["score_dot_product_terms_proxy"] for row in rows
            ),
            "mean_proposal_wall_seconds": mean(
                row["proposal_wall_seconds"] for row in rows
            ),
            "mean_repeated_score_term_reduction_factor": mean(
                row["repeated_score_term_reduction_factor"] for row in rows
            ),
            "keep_model_side_cost_contract": keep,
        },
        "rows": rows,
        "boundary": (
            "The learned proposer is TF-IDF plus logistic regression, not an LLM. "
            "linear_parameter_count covers fitted logistic coefficients/intercepts only; "
            "TF-IDF IDF state is reported separately. score_dot_product_terms_proxy is "
            "sparse active features times coefficient rows, not FLOPs, instructions, "
            "memory traffic, or joules. Wall-clock is diagnostic only. Proposal reuse "
            "isolates learned routing work and does not remove deterministic compiler, "
            "solver, or verifier obligations."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
