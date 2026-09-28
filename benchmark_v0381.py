from __future__ import annotations

import json

from neumann1.mixed_block import (
    aggregate_mixed_family,
    observe_mixed_family,
)
from neumann1.mixed_block_dataset import (
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


def _motif_contract(example) -> bool:
    derived = (
        example.apparent_dimension
        - example.core_dimension
    )

    if derived == 0:
        return (
            example.easy_leaf_count == 0
            and example.block_count == 0
        )
    if derived == 2:
        return (
            example.easy_leaf_count == 0
            and example.block_count == 1
        )

    return (
        derived >= 4
        and derived % 2 == 0
        and example.easy_leaf_count == 2
        and example.block_count
        == (derived - 2) // 2
    )


def run() -> dict[str, object]:
    examples = (
        v0381_final_examples()
    )
    frozen = (
        fit_frozen_v033_scorer()
    )

    signatures = {
        example.signature
        for example in examples
    }
    disjoint = (
        signatures.isdisjoint(
            prior_v0381_signatures()
        )
    )

    rows = tuple(
        observe_mixed_family(
            example,
            frozen_scorer=frozen,
        )
        for example in examples
    )
    aggregate = (
        aggregate_mixed_family(
            rows
        )
    )

    final_cells_complete = all(
        len(
            [
                example
                for example
                in examples
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

    motif_contract = all(
        _motif_contract(
            example
        )
        and (
            example.oracle_elimination_count
            == (
                example.apparent_dimension
                - example.core_dimension
            )
        )
        for example in examples
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

    safety = (
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
            "unsafe_mixed_oracle_reductions"
        ]
        == 0
    )

    keep = (
        disjoint
        and final_cells_complete
        and motif_contract
        and controls_unchanged
        and aggregate[
            "motif_visibility_contract"
        ]
        and safety
    )

    return {
        "experiment": (
            "v0.0.38.1 Mixed Local + Coupled "
            "Harder-Family Gate"
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
                for k, n
                in scale_grid()
            ],
            "disjoint_from_prior_signatures": (
                disjoint
            ),
        },
        "frozen_one_row_pipeline": {
            "first_stage": (
                "target_leaf"
            ),
            "first_stage_threshold": (
                0.10
            ),
            "residual": (
                "markowitz"
            ),
            "residual_threshold": (
                0.05
            ),
        },
        "mixed_family_contract": {
            "derived_0": (
                "0 easy leaves + 0 coupled blocks"
            ),
            "derived_2": (
                "0 easy leaves + 1 coupled block"
            ),
            "derived_ge_4": (
                "2 easy leaves + remaining variables in coupled pairs"
            ),
            "motif_count_contract": (
                motif_contract
            ),
            "motif_visibility_contract": (
                aggregate[
                    "motif_visibility_contract"
                ]
            ),
        },
        "final": (
            aggregate
        ),
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "no_compression_controls_unchanged": (
                controls_unchanged
            ),
            "all_paths_verified_and_safe": (
                safety
            ),
        },
        "keep_v0381_contract": (
            keep
        ),
        "boundary": (
            "v0.0.38.1 validates whether a mixed local-plus-coupled "
            "family satisfies the unchanged harder-family gates. "
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
