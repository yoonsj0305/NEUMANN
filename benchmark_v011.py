from __future__ import annotations
import json

from neumann1 import IRKind
from neumann1.family_registry import builtin_family_registry
from neumann1.family_conformance import run_family_conformance


FIXTURES = {
    IRKind.BIPARTITE_MATCHING: {
        "valid": [
            "S1 can use A or C; S2 can use B or C",
            "Allowed for R1: X, Z; Allowed for R2: Y and Z",
            "P1 may be assigned to J1 or J3; P2 may be assigned to J2 or J4",
        ],
        "reject": [
            "S1 can use A or C with cost 5; S2 can use B or C",
            "S1 can use A or C; S2 can use B with capacity 2",
            "Find a minimum spanning tree.",
        ],
    },
    IRKind.LINEAR_SYSTEM: {
        "valid": [
            "x + y = 5; x - y = 1",
            "2*a + 3*b = 9; a - b = 1",
            "Solve: p + q = 10; 2*p - q = 4",
        ],
        "reject": [
            "x*x + y = 3; x - y = 1",
            "x + y <= 5; x - y = 1",
            "Find the shortest path from A to B.",
        ],
    },
}


def run():
    registry = builtin_family_registry()
    rows = []

    for kind, fixture in FIXTURES.items():
        adapter = registry.get(kind)
        result = run_family_conformance(
            adapter,
            valid_texts=fixture["valid"],
            reject_texts=fixture["reject"],
        )
        rows.append({
            "family_id": result.family_id,
            "valid_compile_rate": result.valid_compile_rate,
            "valid_verified_rate": result.valid_verified_rate,
            "reject_fail_closed_rate": result.reject_fail_closed_rate,
        })

    return {
        "contract_version": "neumann.family.v1",
        "registered_family_count": len(registry.adapters()),
        "rows": rows,
        "all_families_conform": all(
            r["valid_compile_rate"] == 1.0
            and r["valid_verified_rate"] == 1.0
            and r["reject_fail_closed_rate"] == 1.0
            for r in rows
        ),
        "known_limitation": (
            "IRKind is still a closed enum, so third-party families cannot add a new "
            "kind without a core change. This must be addressed before claiming a "
            "truly open plugin ecosystem."
        ),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
    with open("benchmark_v011_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
