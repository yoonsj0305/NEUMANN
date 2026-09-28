from __future__ import annotations

import json

from neumann1.coupled_block import (
    aggregate_coupled_block,
    observe_coupled_block,
)
from neumann1.coupled_block_dataset import (
    V038_FINAL_EXAMPLES_PER_CELL,
    prior_v038_signatures,
    v038_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.structural_compression import (
    scale_grid,
)


def run() -> dict[str, object]:
    examples = v038_final_examples()
    frozen = fit_frozen_v033_scorer()

    signatures = {
        example.signature
        for example in examples
    }
    disjoint = signatures.isdisjoint(
        prior_v038_signatures()
    )

    rows = tuple(
        observe_coupled_block(
            example,
            frozen_scorer=frozen,
        )
        for example in examples
    )
    aggregate = aggregate_coupled_block(
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
        == V038_FINAL_EXAMPLES_PER_CELL
        for k, n in scale_grid()
    )

    one_row_candidates_present = all(
        (
            row.oracle_elimination_count == 0
            or row.one_row_candidate_count > 0
        )
        for row in rows
    )
    controls_unchanged = all(
        (
            row.one_row_total_accepted == 0
            and row.oracle_retained_dimension
            == row.apparent_dimension
        )
        for row in rows
        if row.oracle_elimination_count == 0
    )

    keep = (
        disjoint
        and final_cells_complete
        and one_row_candidates_present
        and controls_unchanged
        and aggregate[
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

    return {
        "experiment": (
            "v0.0.38 Coupled-Block "
            "Harder Structural Family Gate"
        ),
        "data_contract": {
            "final_examples": len(
                examples
            ),
            "final_examples_per_cell": (
                V038_FINAL_EXAMPLES_PER_CELL
            ),
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in scale_grid()
            ],
            "disjoint_from_prior_signatures": (
                disjoint
            ),
        },
        "frozen_one_row_pipeline": {
            "first_stage": "target_leaf",
            "first_stage_threshold": 0.10,
            "residual": "markowitz",
            "residual_threshold": 0.05,
        },
        "family": {
            "motif": (
                "two derived variables coupled by "
                "two exact rows"
            ),
            "single_row_candidates_remain_visible": (
                one_row_candidates_present
            ),
            "oracle_uses_generator_block_identity_only_for_reference": True,
            "block_checker_rederives_exact_2x2_algebra": True,
        },
        "final": aggregate,
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "one_row_candidates_present_on_active_examples": (
                one_row_candidates_present
            ),
            "no_compression_controls_unchanged": (
                controls_unchanged
            ),
            "all_paths_verified_and_safe": (
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
            ),
        },
        "keep_v038_contract": keep,
        "boundary": (
            "v0.0.38 validates family hardness and "
            "the sufficiency of an exact 2x2 block "
            "compression primitive. It does not test "
            "learned block discovery."
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
