from __future__ import annotations
import json

from neumann1 import IRKind, CostLedger, Problem
from neumann1.open_set import TwoStageOpenSetStructureFormer
from neumann1.matching_ir import ControlledMatchingStructureFormer
from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.learned_compiler_gate import LearnedProposalCompilerGate
from neumann1.compiler_gate_dataset import (
    compiler_gate_training_examples,
    compiler_gate_validation_examples,
    compiler_gate_final_examples,
)


def build_gate():
    proposer = TwoStageOpenSetStructureFormer().fit(compiler_gate_training_examples())
    validation = proposer.tune_threshold(compiler_gate_validation_examples())
    gate = LearnedProposalCompilerGate(
        proposer,
        {
            IRKind.BIPARTITE_MATCHING: ControlledMatchingStructureFormer(),
            IRKind.LINEAR_SYSTEM: ControlledLinearSystemStructureFormer(),
        },
    )
    return proposer, gate, validation


def run():
    proposer, gate, validation = build_gate()
    rows = []

    for text, expected, bucket in compiler_gate_final_examples():
        proposed, proposal_conf = proposer.predict_kind(text)
        ledger = CostLedger()
        final = gate.form(Problem(text), ledger)

        rows.append({
            "text": text,
            "bucket": bucket,
            "expected": expected.value,
            "proposed": proposed.value,
            "proposal_confidence": proposal_conf,
            "final": final.kind.value,
            "final_correct": final.kind == expected,
            "proposal_correct": proposed == expected,
            "compiler_rescued_false_proposal": (
                expected == IRKind.UNKNOWN
                and proposed != IRKind.UNKNOWN
                and final.kind == IRKind.UNKNOWN
            ),
            "representation_steps": ledger.representation_steps,
            "rationale": final.rationale,
        })

    known = [r for r in rows if r["expected"] != IRKind.UNKNOWN.value]
    unknown = [r for r in rows if r["expected"] == IRKind.UNKNOWN.value]
    near = [r for r in rows if r["bucket"] == "near_unknown"]

    def false_route(items, key):
        return sum(r[key] != IRKind.UNKNOWN.value for r in items) / len(items) if items else 0.0

    return {
        "validation_threshold": proposer.threshold,
        "validation_known_coverage": validation.known_coverage,
        "rows": rows,
        "summary": {
            "known_final_coverage": sum(r["final"] != IRKind.UNKNOWN.value for r in known) / len(known),
            "known_final_accuracy": sum(r["final_correct"] for r in known) / len(known),
            "unknown_proposal_false_route_rate": false_route(unknown, "proposed"),
            "unknown_final_false_route_rate": false_route(unknown, "final"),
            "near_unknown_proposal_false_route_rate": false_route(near, "proposed"),
            "near_unknown_final_false_route_rate": false_route(near, "final"),
            "compiler_rescued_false_proposals": sum(r["compiler_rescued_false_proposal"] for r in rows),
            "mean_representation_steps": sum(r["representation_steps"] for r in rows) / len(rows),
        },
        "boundary": (
            "Tiny controlled data. The learned model proposes only a family; "
            "deterministic compilers remain the authority for solver-ready IR."
        ),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["summary"], indent=2))
    with open("benchmark_v010_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
