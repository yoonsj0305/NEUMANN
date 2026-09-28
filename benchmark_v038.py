from __future__ import annotations

import json

from neumann1.block_compression_dataset import (
    BLOCK_FINAL_EXAMPLES_PER_CELL,
    block_scale_grid,
    v038_final_examples,
)
from neumann1.block_compression_experiment import (
    aggregate_block_compression,
    observe_block_compression,
)


def run() -> dict[str, object]:
    examples = v038_final_examples()

    observations = tuple(
        observe_block_compression(example)
        for example in examples
    )
    aggregate = aggregate_block_compression(
        observations
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
        == BLOCK_FINAL_EXAMPLES_PER_CELL
        for k, n in block_scale_grid()
    )

    keep = (
        len(examples)
        == 8 * BLOCK_FINAL_EXAMPLES_PER_CELL
        and final_cells_complete
        and aggregate[
            "all_nonzero_coefficients_abs_ge_2"
        ]
        and aggregate[
            "scalar_candidate_count_zero_everywhere"
        ]
        and aggregate[
            "oracle_block_count_exact_everywhere"
        ]
        and aggregate[
            "verified_retention"
        ]
        == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        and aggregate[
            "retained_dimension_exact_everywhere"
        ]
    )

    return {
        "experiment": (
            "v0.0.38 Coupled Block "
            "Structural Compression Oracle"
        ),
        "data_contract": {
            "final_examples": len(examples),
            "final_examples_per_cell": (
                BLOCK_FINAL_EXAMPLES_PER_CELL
            ),
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in block_scale_grid()
            ],
            "final_cells_complete": (
                final_cells_complete
            ),
        },
        "final": aggregate,
        "keep_v038_contract": keep,
        "boundary": (
            "v0.0.38 is a generator-oracle capability "
            "test for certified 2x2 coupled block "
            "compression. It does not test learned block "
            "discovery or establish end-to-end total-compute "
            "superiority."
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
