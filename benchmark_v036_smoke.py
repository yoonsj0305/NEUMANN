from __future__ import annotations

import json

from neumann1.compression_utility import (
    observe_dynamic_greedy_utility,
)
from neumann1.learned_compression_dataset import (
    learned_scale_grid,
)
from neumann1.residual_utility import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    observe_cheap_first_residual_utility,
)
from neumann1.residual_utility_dataset import (
    v036_development_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def _one_per_cell(examples):
    output = []
    for k, n in learned_scale_grid():
        output.append(
            next(
                example
                for example in examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            )
        )
    return tuple(output)


def run():
    examples = _one_per_cell(
        v036_development_examples()
    )
    frozen = fit_frozen_v033_scorer()

    residual = tuple(
        observe_cheap_first_residual_utility(
            example,
            frozen_scorer=frozen,
        )
        for example in examples
    )
    dynamic = tuple(
        observe_dynamic_greedy_utility(example)
        for example in examples
    )

    keep = (
        FROZEN_TARGET_LEAF_THRESHOLD == 0.10
        and all(row.cheap_verified for row in residual)
        and all(row.final_verified for row in residual)
        and all(row.final_verified for row in dynamic)
        and all(
            row.residual_positive_gain_sum
            == row.residual_additional_savings
            for row in residual
        )
    )

    return {
        "experiment": "v0.0.36 development smoke",
        "smoke_only": True,
        "uses_final_split": False,
        "examples": len(examples),
        "frozen_target_leaf_threshold": (
            FROZEN_TARGET_LEAF_THRESHOLD
        ),
        "cheap_verified": all(
            row.cheap_verified
            for row in residual
        ),
        "residual_verified": all(
            row.final_verified
            for row in residual
        ),
        "full_dynamic_verified": all(
            row.final_verified
            for row in dynamic
        ),
        "residual_gain_telescopes": all(
            row.residual_positive_gain_sum
            == row.residual_additional_savings
            for row in residual
        ),
        "keep_smoke_contract": keep,
        "boundary": (
            "Development-split regression smoke only. "
            "It never imports or evaluates v0.0.36 final examples "
            "and does not establish the GO/NO-GO result."
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
