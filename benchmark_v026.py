from __future__ import annotations

import json
from statistics import mean

from neumann1 import (
    IRKind,
    Problem,
    builtin_family_registry,
    measure_repeated_structural_reuse,
)


REPEATS = 8


def fixtures():
    return (
        (
            "matching_3",
            IRKind.BIPARTITE_MATCHING,
            "S1 can use A or B; S2 can use B or C; S3 can use A or C",
        ),
        (
            "matching_5",
            IRKind.BIPARTITE_MATCHING,
            (
                "R1 can use A or B; R2 can use B or C; R3 can use C or D; "
                "R4 can use D or E; R5 can use A or E"
            ),
        ),
        (
            "linear_2",
            IRKind.LINEAR_SYSTEM,
            "x + y = 5; x - y = 1",
        ),
        (
            "linear_3",
            IRKind.LINEAR_SYSTEM,
            "x + y + z = 6; 2*x - y + z = 3; x + 2*y - z = 2",
        ),
    )


def run():
    registry = builtin_family_registry()
    rows = []

    for case_id, kind, text in fixtures():
        adapter = registry.get(kind)
        if adapter is None:
            raise RuntimeError(f"missing built-in adapter for {kind}")
        obs = measure_repeated_structural_reuse(
            Problem(text),
            adapter,
            repeats=REPEATS,
        )
        rows.append({
            "case_id": case_id,
            "family_id": obs.family_id,
            "repeats": obs.repeats,
            "raw_text_bytes": obs.raw_text_bytes,
            "representation_bytes": obs.representation_bytes,
            "representation_to_raw_byte_ratio": obs.representation_to_raw_byte_ratio,
            "compile_every_time": {
                "representation_steps": obs.compile_every_time.representation_steps,
                "solver_steps": obs.compile_every_time.solver_steps,
                "verification_steps": obs.compile_every_time.verification_steps,
                "wall_seconds": obs.compile_every_time.wall_seconds,
                "verified_rate": obs.compile_every_time.verified_rate,
            },
            "compile_once_reuse": {
                "representation_steps": obs.compile_once_reuse.representation_steps,
                "solver_steps": obs.compile_once_reuse.solver_steps,
                "verification_steps": obs.compile_once_reuse.verification_steps,
                "wall_seconds": obs.compile_once_reuse.wall_seconds,
                "verified_rate": obs.compile_once_reuse.verified_rate,
            },
            "answer_equivalence_rate": obs.answer_equivalence_rate,
            "representation_identity_stable": obs.representation_identity_stable,
            "representation_step_reduction_factor": (
                obs.representation_step_reduction_factor
            ),
            "compiler_input_byte_reduction_factor": (
                obs.compiler_input_byte_reduction_factor
            ),
            "wall_time_ratio_every_over_reuse": (
                obs.compile_every_time.wall_seconds
                / obs.compile_once_reuse.wall_seconds
                if obs.compile_once_reuse.wall_seconds > 0
                else None
            ),
        })

    keep = all(
        row["compile_every_time"]["verified_rate"] == 1.0
        and row["compile_once_reuse"]["verified_rate"] == 1.0
        and row["answer_equivalence_rate"] == 1.0
        and row["representation_identity_stable"]
        and row["compile_every_time"]["representation_steps"] == REPEATS
        and row["compile_once_reuse"]["representation_steps"] == 1
        and row["compile_every_time"]["solver_steps"]
        == row["compile_once_reuse"]["solver_steps"]
        and row["compile_every_time"]["verification_steps"]
        == row["compile_once_reuse"]["verification_steps"]
        for row in rows
    )

    return {
        "experiment": "v0.0.26 structural efficiency measurement contract",
        "repeats": REPEATS,
        "case_count": len(rows),
        "all_verified_and_answer_equivalent": all(
            row["answer_equivalence_rate"] == 1.0
            and row["compile_once_reuse"]["verified_rate"] == 1.0
            for row in rows
        ),
        "mean_representation_step_reduction_factor": mean(
            row["representation_step_reduction_factor"] for row in rows
        ),
        "mean_representation_to_raw_byte_ratio": mean(
            row["representation_to_raw_byte_ratio"] for row in rows
        ),
        "mean_wall_time_ratio_every_over_reuse": mean(
            row["wall_time_ratio_every_over_reuse"]
            for row in rows
            if row["wall_time_ratio_every_over_reuse"] is not None
        ),
        "keep_structural_efficiency_contract": keep,
        "rows": rows,
        "boundary": (
            "Representation steps are NEUMANN instrumentation, not FLOPs. "
            "Serialized byte ratios are interface-size proxies, not token counts. "
            "Wall-clock ratios are reported diagnostically and are not a CI keep gate. "
            "This experiment measures repeated solver-ready representation reuse on "
            "small deterministic fixtures; it does not establish LLM or energy efficiency."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
