from __future__ import annotations

import json

from neumann1.mixed_coupled import (
    FROZEN_FIRST_STAGE_THRESHOLD,
    FROZEN_RESIDUAL_METHOD,
    FROZEN_RESIDUAL_THRESHOLD,
    aggregate_mixed_coupled,
    observe_mixed_coupled,
)
from neumann1.mixed_coupled_dataset import (
    V0381_FINAL_EXAMPLES_PER_CELL,
    prior_v0381_signatures,
    v0381_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.structural_compression import (
    scale_grid,
)


def run() -> dict[str, object]:
    examples = v0381_final_examples()
    frozen = fit_frozen_v033_scorer()

    signatures = {
        example.signature
        for example in examples
    }
    disjoint = signatures.isdisjoint(
        prior_v0381_signatures()
    )

    rows = tuple(
        observe_mixed_coupled(
            example,
            frozen_scorer=frozen,
        )
        for example in examples
    )
    aggregate = (
        aggregate_mixed_coupled(
            rows
        )
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
        == V0381_FINAL_EXAMPLES_PER_CELL
        for k, n in scale_grid()
    )

    controls_unchanged = all(
        (
            row.one_row_total_accepted
            == 0
            and row.oracle_retained_dimension
            == row.apparent_dimension
        )
        for row in rows
        if row.oracle_elimination_count
        == 0
    )

    motif_contract = all(
        (
            (
                row.apparent_dimension
                - row.core_dimension
                == 0
                and row.easy_leaf_count
                == 0
                and row.block_count
                == 0
            )
            or (
                row.apparent_dimension
                - row.core_dimension
                == 2
                and row.easy_leaf_count
                == 0
                and row.block_count
                == 1
            )
            or (
                row.apparent_dimension
                - row.core_dimension
                >= 4
                and row.easy_leaf_count
                == 2
                and row.block_count
                == (
                    (
                        row.apparent_dimension
                        - row.core_dimension
                        - 2
                    )
                    // 2
                )
            )
        )
        for row in rows
    )

    candidate_contract = all(
        row.candidate_count_exact
        for row in rows
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
            "unsafe_reference_reductions"
        ]
        == 0
    )

    keep = (
        disjoint
        and final_cells_complete
        and controls_unchanged
        and motif_contract
        and candidate_contract
        and safe
        and FROZEN_FIRST_STAGE_THRESHOLD
        == 0.10
        and FROZEN_RESIDUAL_METHOD
        == "markowitz"
        and FROZEN_RESIDUAL_THRESHOLD
        == 0.05
    )

    return {
        "experiment": (
            "v0.0.38.1 Mixed Local + "
            "Coupled Harder-Family Gate"
        ),
        "data_contract": {
            "final_examples": len(
                examples
            ),
            "final_examples_per_cell": (
                V0381_FINAL_EXAMPLES_PER_CELL
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
            "first_stage": (
                "target_leaf @ 0.10"
            ),
            "residual": (
                "markowitz @ 0.05"
            ),
            "hardness_gates": (
                "unchanged v0.0.38 H1-H5"
            ),
            "mixed_rule": (
                "d>=4: exactly two easy leaves, "
                "remaining derived variables in 2x2 blocks; "
                "d=2: pure coupled"
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
            "motif_contract": (
                motif_contract
            ),
            "candidate_count_contract": (
                candidate_contract
            ),
            "all_paths_verified_and_safe": (
                safe
            ),
        },
        "keep_v0381_contract": keep,
        "boundary": (
            "v0.0.38.1 validates or rejects a mixed "
            "local-plus-multi-row family using the original "
            "v0.0.38 H1-H5 thresholds. It does not test "
            "block discovery or learned routing."
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
