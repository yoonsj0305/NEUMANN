from __future__ import annotations

import json

from neumann1.mixed_block import (
    observe_mixed_family,
)
from neumann1.mixed_block_dataset import (
    v0381_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run() -> dict[str, object]:
    frozen = (
        fit_frozen_v033_scorer()
    )
    examples = (
        v0381_final_examples()
    )

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
        sample.append(
            example
        )

    rows = tuple(
        observe_mixed_family(
            example,
            frozen_scorer=frozen,
        )
        for example in sample
    )

    safe = all(
        row.one_row_verified
        and row.oracle_verified
        and row.unsafe_one_row_reductions == 0
        and row.unsafe_mixed_oracle_reductions == 0
        for row in rows
    )

    oracle_core_exact = all(
        (
            row.oracle_elimination_count == 0
            or row.oracle_retained_dimension
            == row.core_dimension
        )
        for row in rows
    )

    visibility = all(
        (
            row.oracle_elimination_count == 0
            or (
                row.expected_coupled_candidates_visible
                and (
                    row.easy_oracle_count == 0
                    or row.easy_candidates_visible
                )
            )
        )
        for row in rows
    )

    return {
        "experiment": (
            "v0.0.38.1 bounded regression smoke"
        ),
        "sample_cells": len(
            rows
        ),
        "all_paths_verified_and_safe": (
            safe
        ),
        "oracle_core_exact": (
            oracle_core_exact
        ),
        "motif_visibility_contract": (
            visibility
        ),
        "keep_smoke_contract": (
            safe
            and oracle_core_exact
            and visibility
        ),
        "canonical_full_result": {
            "run": 184,
            "family_status": (
                "HARDER_FAMILY_VALIDATED"
            ),
            "all_h1_h5": "PASS",
        },
        "boundary": (
            "This bounded smoke preserves correctness only. "
            "It does not replace the frozen 256-system "
            "v0.0.38.1 full hardness result."
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
