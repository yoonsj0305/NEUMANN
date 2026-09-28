from __future__ import annotations

import json

from neumann1.coupled_block import (
    observe_coupled_block,
)
from neumann1.coupled_block_dataset import (
    v038_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run() -> dict[str, object]:
    frozen = fit_frozen_v033_scorer()
    examples = v038_final_examples()

    sample = []
    seen = set()
    for example in examples:
        key = (
            example.core_dimension,
            example.apparent_dimension,
        )
        if key in seen:
            continue
        seen.add(key)
        sample.append(example)

    rows = tuple(
        observe_coupled_block(
            example,
            frozen_scorer=frozen,
        )
        for example in sample
    )

    safe = all(
        row.one_row_verified
        and row.oracle_verified
        and row.unsafe_one_row_reductions == 0
        and row.unsafe_block_reductions == 0
        for row in rows
    )
    oracle_core_exact = all(
        row.oracle_retained_dimension
        == row.core_dimension
        for row in rows
    )
    visible = all(
        (
            row.oracle_elimination_count == 0
            or row.one_row_candidate_count > 0
        )
        for row in rows
    )

    return {
        "experiment": "v0.0.38 bounded regression smoke",
        "count": len(rows),
        "all_paths_safe": safe,
        "oracle_core_exact": oracle_core_exact,
        "one_row_candidates_visible": visible,
        "keep_smoke_contract": (
            safe
            and oracle_core_exact
            and visible
        ),
        "canonical_full_result": {
            "run": 171,
            "family_status": "FAMILY_NOT_HARD_ENOUGH",
            "failed_gate": "H4_one_row_progress_rate_ge_0_75",
        },
        "boundary": (
            "This smoke preserves correctness only. "
            "It does not replace the frozen 256-system "
            "v0.0.38 full hardness result."
        ),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2,
            sort_keys=True,
        )
    )
