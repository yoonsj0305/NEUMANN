from __future__ import annotations

import json

from neumann1.collision_boundary_v047 import analyze, matrix_for


ARMS = ("overlap", "repair", "disjoint")
EXPECTED = {
    "overlap": (3, ((0, 1), (1, 2)), True),
    "repair": (4, ((0, 1),), False),
    "disjoint": (4, ((0, 1), (2, 3)), False),
}


def run(*, count: int = 128, seed_base: int = 3_470_000) -> dict[str, object]:
    seen = set()
    arms = {}
    for index, arm in enumerate(ARMS):
        passed = 0
        rank_counts: dict[int, int] = {}
        for sample in range(count):
            matrix = matrix_for(arm, seed_base + 1000 * index + sample)
            assert matrix not in seen, (arm, sample, "reused matrix")
            seen.add(matrix)
            result = analyze(matrix)
            observed = (result.rank, result.pairs, result.overlapping_pairs)
            assert observed == EXPECTED[arm], (arm, sample, observed)
            passed += 1
            rank_counts[result.rank] = rank_counts.get(result.rank, 0) + 1
        arms[arm] = {"count": count, "passed": passed, "rank_counts": rank_counts,
                     "eligible_pairs": [list(pair) for pair in EXPECTED[arm][1]],
                     "overlap": EXPECTED[arm][2]}
    return {"version": "0.0.47", "scope": "exact integer square 4x4 fixture",
            "first_complete_audit": count == 128 and seed_base == 3_470_000,
            "total": len(seen), "unique_signatures": len(seen), "arms": arms,
            "decision": "BOUNDARY_CONFIRMED"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
