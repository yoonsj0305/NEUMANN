from __future__ import annotations

import json

from neumann1.coupled_block_replication import (
    aggregate_replication,
    run_replication_observations,
)
from neumann1.coupled_block_replication_dataset import (
    V039_FINAL_EXAMPLES_PER_CELL,
    prior_v039_signatures,
    v039_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.structural_compression import (
    scale_grid,
)


def run() -> dict[str, object]:
    examples = v039_final_examples()
    frozen = fit_frozen_v033_scorer()

    signatures = {
        example.signature
        for example in examples
    }
    disjoint = signatures.isdisjoint(
        prior_v039_signatures()
    )

    (
        coupled_rows,
        visibility_rows,
    ) = run_replication_observations(
        examples,
        frozen_scorer=frozen,
    )
    aggregate = aggregate_replication(
        coupled_rows,
        visibility_rows,
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
        == V039_FINAL_EXAMPLES_PER_CELL
        for k, n in scale_grid()
    )

    controls_unchanged = all(
        (
            row.one_row_total_accepted == 0
            and row.oracle_retained_dimension
            == row.apparent_dimension
        )
        for row in coupled_rows
        if row.oracle_elimination_count == 0
    )

    visibility_contract = (
        aggregate[
            "candidate_visibility"
        ][
            "all_active_candidate_counts_exact"
        ]
        and aggregate[
            "candidate_visibility"
        ][
            "all_active_candidate_algebra_valid"
        ]
    )

    safe = (
        aggregate[
            "one_row_verified_retention"
        ]
        == 1.0
        and aggregate[
            "oracle_verified_retention"
        ]
        == 1.0
        and aggregate[
            "unsafe_one_row_reductions"
        ]
        == 0
        and aggregate[
            "unsafe_block_reductions"
        ]
        == 0
    )

    keep = (
        disjoint
        and final_cells_complete
        and controls_unchanged
        and visibility_contract
        and safe
    )

    return {
        "experiment": (
            "v0.0.39 Coupled-Block "
            "Hardness Gate Replication"
        ),
        "data_contract": {
            "final_examples": len(
                examples
            ),
            "final_examples_per_cell": (
                V039_FINAL_EXAMPLES_PER_CELL
            ),
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in scale_grid()
            ],
            "fresh_signature_disjointness": (
                disjoint
            ),
        },
        "frozen_contract": {
            "generator": (
                "unchanged v0.0.38 coupled 2x2 family"
            ),
            "first_stage": (
                "target_leaf @ 0.10"
            ),
            "residual": (
                "markowitz @ 0.05"
            ),
            "block_checker": (
                "unchanged exact Fraction 2x2 checker"
            ),
        },
        "final": aggregate,
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "no_compression_controls_unchanged": (
                controls_unchanged
            ),
            "direct_candidate_visibility_contract": (
                visibility_contract
            ),
            "all_paths_verified_and_safe": (
                safe
            ),
        },
        "keep_v039_contract": keep,
        "boundary": (
            "v0.0.39 is a fresh-data confirmatory "
            "replication of coupled-block family hardness. "
            "It does not test learned block discovery."
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
