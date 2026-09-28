from __future__ import annotations

import json

from neumann1.mixed_coupled import (
    materialize_mixed_reference,
    run_frozen_one_row_pipeline,
)
from neumann1.mixed_coupled_dataset import (
    v0381_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run() -> dict[str, object]:
    frozen = fit_frozen_v033_scorer()
    examples = v0381_final_examples()

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

    local_safe = True
    reference_safe = True
    reference_core_exact = True
    mixed_progress = True

    for example in sample:
        local = run_frozen_one_row_pipeline(
            example,
            frozen_scorer=frozen,
        )
        reference = materialize_mixed_reference(
            example
        )

        local_safe = (
            local_safe
            and local.final_verified
            and local.unsafe_accepted_reductions == 0
        )
        reference_safe = (
            reference_safe
            and reference is not None
            and reference.verified
            and reference.ground_truth_equivalent
        )

        if reference is not None:
            reference_core_exact = (
                reference_core_exact
                and reference.retained_system.dimension
                == example.core_dimension
            )

        if example.easy_leaf_count > 0:
            mixed_progress = (
                mixed_progress
                and len(local.all_accepted) > 0
            )

    keep = (
        local_safe
        and reference_safe
        and reference_core_exact
        and mixed_progress
    )

    return {
        "experiment": (
            "v0.0.38.1 bounded mixed-family "
            "regression smoke"
        ),
        "sample_cells": len(sample),
        "local_verified_and_safe": (
            local_safe
        ),
        "reference_verified_and_safe": (
            reference_safe
        ),
        "reference_core_exact": (
            reference_core_exact
        ),
        "mixed_cells_show_local_progress": (
            mixed_progress
        ),
        "keep_smoke_contract": keep,
        "smoke_only": True,
        "boundary": (
            "This bounded smoke does not reproduce or replace "
            "the frozen 256-system v0.0.38.1 full result."
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
