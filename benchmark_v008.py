from __future__ import annotations
import json

from neumann1 import Problem, CostLedger, IRKind
from neumann1.matching_ir import (
    ControlledMatchingStructureFormer,
    MatchingSemanticVerifier,
    edge_metrics,
)

VALID = [
    (
        "surface_can_use",
        "S1 can use A or C; S2 can use B or C; S3 can use A or D",
        {"S1":["A","C"],"S2":["B","C"],"S3":["A","D"]},
    ),
    (
        "surface_allowed_for",
        "Allowed for P1: J1, J3; Allowed for P2: J2 and J3; Allowed for P3: J1 or J4",
        {"P1":["J1","J3"],"P2":["J2","J3"],"P3":["J1","J4"]},
    ),
    (
        "surface_connect",
        "R1 can connect to X or Z; R2 can connect to Y and Z; R3 can connect to X or W",
        {"R1":["X","Z"],"R2":["Y","Z"],"R3":["X","W"]},
    ),
    (
        "duplicate_identical",
        "A1 can use X or Y; A1 can use Y or X; A2 can use Y or Z",
        {"A1":["X","Y"],"A2":["Y","Z"]},
    ),
]

REJECT = [
    ("partial_unparsed", "S1 can use A or C; S2 should prefer B; S3 can use A or D"),
    ("conflicting_duplicate", "S1 can use A or C; S1 can use B or C; S2 can use B or D"),
    ("negation", "S1 can use A or C except C; S2 can use B or C"),
    ("capacity", "S1 can use A or C; S2 can use B or C with capacity 2"),
    ("cost", "S1 can use A or C with cost 5; S2 can use B or C"),
    ("one_statement_only", "S1 can use A or C"),
    ("unrelated", "Compute a minimum spanning tree of this weighted graph."),
]


def run():
    former = ControlledMatchingStructureFormer()
    semantic = MatchingSemanticVerifier()
    valid_rows = []
    total_tp = total_fp = total_fn = 0
    for name, text, expected_edges in VALID:
        p = Problem(text, {"matching_semantic_contract":{"expected_edges": expected_edges}})
        ledger = CostLedger()
        rep = former.form(p, ledger)
        vr = semantic.verify_representation(p, rep, ledger)
        actual = rep.payload.get("edges", {}) if rep.kind == IRKind.BIPARTITE_MATCHING else {}
        metrics = edge_metrics(expected_edges, actual)
        total_tp += metrics.true_positive
        total_fp += metrics.false_positive
        total_fn += metrics.false_negative
        valid_rows.append({
            "name": name,
            "kind": rep.kind.value,
            "semantic_fidelity": vr.ok,
            "edge_precision": metrics.precision,
            "edge_recall": metrics.recall,
            "edge_f1": metrics.f1,
            "rationale": rep.rationale,
        })

    aggregate = edge_metrics(
        {"all_expected": [f"tp{i}" for i in range(total_tp + total_fn)]},
        {"all_expected": [f"tp{i}" for i in range(total_tp)] + [f"fp{i}" for i in range(total_fp)]},
    )
    # The synthetic aggregate above is only for convenient p/r arithmetic. Preserve raw counts too.
    reject_rows = []
    for name, text in REJECT:
        rep = former.form(Problem(text), CostLedger())
        reject_rows.append({
            "name": name,
            "kind": rep.kind.value,
            "fail_closed": rep.kind == IRKind.UNKNOWN,
            "rationale": rep.rationale,
        })

    return {
        "valid_rows": valid_rows,
        "reject_rows": reject_rows,
        "summary": {
            "valid_exact_match_rate": sum(r["semantic_fidelity"] for r in valid_rows) / len(valid_rows),
            "reject_fail_closed_rate": sum(r["fail_closed"] for r in reject_rows) / len(reject_rows),
            "edge_tp": total_tp,
            "edge_fp": total_fp,
            "edge_fn": total_fn,
            "edge_precision": total_tp / (total_tp + total_fp) if total_tp + total_fp else 1.0,
            "edge_recall": total_tp / (total_tp + total_fn) if total_tp + total_fn else 1.0,
        },
        "boundary": "Controlled grammar only. Rejection success is not general semantic understanding.",
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["summary"], indent=2))
    with open("benchmark_v008_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
