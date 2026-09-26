from __future__ import annotations
import json

from neumann1 import (
    Problem, NeumannEngine, BipartiteMatchingSolver, LinearSystemSolver,
    DeterministicVerifier, IRKind,
)
from neumann1.matching_ir import ControlledMatchingStructureFormer
from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.composite import CompositeStructureFormer


FIXTURES = [
    (
        "matching_satellites",
        "S1 can use A or C; S2 can use B or C; S3 can use A or D",
        IRKind.BIPARTITE_MATCHING,
        "augmenting_path_matching",
    ),
    (
        "matching_workers",
        "Allowed for P1: J1, J3; Allowed for P2: J2 and J3",
        IRKind.BIPARTITE_MATCHING,
        "augmenting_path_matching",
    ),
    (
        "linear_basic",
        "Solve: x + y = 5; x - y = 1",
        IRKind.LINEAR_SYSTEM,
        "gaussian_elimination",
    ),
    (
        "linear_coefficients",
        "2*x + 3*y = 13; 5*x - y = 7",
        IRKind.LINEAR_SYSTEM,
        "gaussian_elimination",
    ),
]


REJECT = [
    "Find a minimum spanning tree of the weighted graph.",
    "x*x + y = 3; x - y = 1",
    "S1 can use A or C; S2 can use B with capacity 2",
]


def run():
    former = CompositeStructureFormer([
        ControlledMatchingStructureFormer(),
        ControlledLinearSystemStructureFormer(),
    ])
    engine = NeumannEngine(
        former,
        [BipartiteMatchingSolver(), LinearSystemSolver()],
        DeterministicVerifier(),
    )

    rows = []
    for name, text, expected_kind, expected_solver in FIXTURES:
        result = engine.solve(Problem(text))
        rows.append({
            "name": name,
            "expected_kind": expected_kind.value,
            "actual_kind": result.representation.kind.value,
            "expected_solver": expected_solver,
            "actual_solver": result.solver_name,
            "verified": result.verified,
            "route_correct": result.representation.kind == expected_kind and result.solver_name == expected_solver,
        })

    rejected = []
    for text in REJECT:
        result = engine.solve(Problem(text))
        rejected.append({
            "text": text,
            "kind": result.representation.kind.value,
            "fail_closed": result.representation.kind == IRKind.UNKNOWN,
        })

    return {
        "summary": {
            "supported_route_accuracy": sum(r["route_correct"] and r["verified"] for r in rows) / len(rows),
            "unsupported_fail_closed_rate": sum(r["fail_closed"] for r in rejected) / len(rejected),
            "supported_families": 2,
        },
        "rows": rows,
        "rejected": rejected,
        "boundary": "Two controlled complete-IR families only; not general natural-language routing.",
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["summary"], indent=2))
    with open("benchmark_v009_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
