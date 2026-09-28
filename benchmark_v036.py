from __future__ import annotations

import json

from neumann1.residual_headroom import (
    FROZEN_TARGET_LEAF_THRESHOLD,
    aggregate_residual_headroom,
    observe_residual_headroom,
)
from neumann1.residual_headroom_dataset import (
    V036_FINAL_EXAMPLES_PER_CELL,
    prior_v036_signatures,
    v036_final_examples,
)
from neumann1.learned_compression_dataset import (
    learned_scale_grid,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run() -> dict[str, object]:
    examples = v036_final_examples()
    frozen = fit_frozen_v033_scorer()

    final_signatures = {
        example.signature
        for example in examples
    }
    disjoint_from_prior = (
        final_signatures.isdisjoint(
            prior_v036_signatures()
        )
    )

    rows = tuple(
        observe_residual_headroom(
            example,
            frozen_scorer=frozen,
        )
        for example in examples
    )
    aggregate = aggregate_residual_headroom(
        rows
    )

    final_cells_complete = all(
        len(
            [
                example
                for example in examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == V036_FINAL_EXAMPLES_PER_CELL
        for k, n in learned_scale_grid()
    )

    residual_telescopes = all(
        row.residual_selected_gain_sum
        == row.residual_additional_solver_savings
        for row in rows
    )
    target_leaf_never_worsened = all(
        row.residual_solver_ops
        <= row.target_leaf_solver_ops
        for row in rows
    )
    verified = (
        aggregate["verified_retention"] == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
    )

    keep = (
        disjoint_from_prior
        and FROZEN_TARGET_LEAF_THRESHOLD == 0.10
        and final_cells_complete
        and residual_telescopes
        and target_leaf_never_worsened
        and verified
    )

    return {
        "experiment": (
            "v0.0.36 Cheap-First Residual "
            "Headroom Contract"
        ),
        "data_contract": {
            "final_examples": len(examples),
            "final_examples_per_cell": (
                V036_FINAL_EXAMPLES_PER_CELL
            ),
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in learned_scale_grid()
            ],
            "disjoint_from_all_v033_v034_v035_signatures": (
                disjoint_from_prior
            ),
        },
        "frozen_cheap_component": {
            "method": "target_leaf",
            "threshold": (
                FROZEN_TARGET_LEAF_THRESHOLD
            ),
            "threshold_source": (
                "transferred unchanged from v0.0.35"
            ),
        },
        "final": aggregate,
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "residual_selected_gain_telescopes": (
                residual_telescopes
            ),
            "residual_never_worsens_target_leaf": (
                target_leaf_never_worsened
            ),
            "verified_retention_1_and_unsafe_0": (
                verified
            ),
        },
        "keep_v036_contract": keep,
        "boundary": (
            "v0.0.36 measures residual headroom after a frozen "
            "cheap target-leaf component. It trains no new model "
            "and makes no total-compute or global-optimality claim."
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
