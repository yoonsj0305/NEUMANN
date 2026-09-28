from __future__ import annotations

import json

from neumann1.residual_headroom import (
    aggregate_residual_headroom,
    observe_residual_headroom,
)
from neumann1.residual_headroom_dataset import (
    v036_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run():
    frozen = fit_frozen_v033_scorer()
    examples = v036_final_examples()

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
        observe_residual_headroom(
            example,
            frozen_scorer=frozen,
        )
        for example in sample
    )
    result = aggregate_residual_headroom(rows)
    return {
        "experiment": "v0.0.36 smoke",
        "count": len(rows),
        "verified_retention": result[
            "verified_retention"
        ],
        "unsafe_accepted_reduction_count": result[
            "unsafe_accepted_reduction_count"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
