from __future__ import annotations

from dataclasses import replace

from neumann1.learned_compression import (
    enumerate_affine_candidates,
    materialize_reduction,
)
from neumann1.mixed_block import (
    materialize_mixed_reduction,
    mixed_oracle_materialization,
    oracle_block_candidates,
    oracle_easy_candidates,
)
from neumann1.mixed_block_dataset import (
    V0381_FINAL_EXAMPLES_PER_CELL,
    prior_v0381_signatures,
    v0381_final_examples,
)
from neumann1.structural_compression import (
    scale_grid,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v0381_final_cardinality_and_prior_disjointness():
    examples = v0381_final_examples()

    assert len(examples) == (
        8
        * V0381_FINAL_EXAMPLES_PER_CELL
    )
    assert _signatures(
        examples
    ).isdisjoint(
        prior_v0381_signatures()
    )

    for k, n in scale_grid():
        assert len(
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
        ) == V0381_FINAL_EXAMPLES_PER_CELL


def test_v0381_motif_counts_follow_frozen_contract():
    for example in v0381_final_examples():
        derived = (
            example.apparent_dimension
            - example.core_dimension
        )

        if derived == 0:
            assert (
                example.easy_leaf_count
                == 0
            )
            assert (
                example.block_count
                == 0
            )
        elif derived == 2:
            assert (
                example.easy_leaf_count
                == 0
            )
            assert (
                example.block_count
                == 1
            )
        else:
            assert derived >= 4
            assert derived % 2 == 0
            assert (
                example.easy_leaf_count
                == 2
            )
            assert (
                example.block_count
                == (derived - 2) // 2
            )

        assert (
            example.oracle_elimination_count
            == derived
        )


def test_v0381_easy_leaves_are_visible_incidence_one_and_individually_safe():
    for example in v0381_final_examples()[:64]:
        candidates = (
            enumerate_affine_candidates(
                example.full_system
            )
        )
        candidate_keys = {
            candidate.key
            for candidate
            in candidates
        }

        column_counts = tuple(
            sum(
                1
                for row
                in example.full_system.A
                if row[column] != 0
            )
            for column
            in range(
                example.apparent_dimension
            )
        )

        for rule in (
            example.oracle_easy_rules
        ):
            assert (
                rule.row_index,
                rule.target,
            ) in candidate_keys

            column = (
                example.full_system.variables.index(
                    rule.target
                )
            )
            assert (
                column_counts[column]
                == 1
            )

        for candidate in (
            oracle_easy_candidates(
                example
            )
        ):
            materialized = (
                materialize_reduction(
                    example,
                    (candidate,),
                )
            )
            assert (
                materialized
                is not None
            )
            assert (
                materialized.verified
            )
            assert (
                materialized.ground_truth_equivalent
            )


def test_v0381_coupled_rows_keep_expected_local_candidates_visible():
    for example in v0381_final_examples()[:64]:
        candidates = (
            enumerate_affine_candidates(
                example.full_system
            )
        )
        block_rows = {
            row
            for block
            in example.oracle_blocks
            for row
            in block.row_indices
        }
        coupled_candidates = [
            candidate
            for candidate
            in candidates
            if candidate.row_index
            in block_rows
        ]

        assert len(
            coupled_candidates
        ) >= (
            4
            * example.block_count
        )


def test_v0381_mixed_oracle_materializes_to_exact_core():
    for example in v0381_final_examples()[:24]:
        materialized = (
            mixed_oracle_materialization(
                example
            )
        )
        assert (
            materialized.verified
        )
        assert (
            materialized.ground_truth_equivalent
        )
        assert (
            materialized.retained_system.dimension
            == example.core_dimension
        )
        assert (
            len(
                materialized.easy_candidates
            )
            == example.easy_leaf_count
        )
        assert (
            len(
                materialized.block_candidates
            )
            == example.block_count
        )


def test_v0381_mixed_checker_rejects_corrupted_easy_algebra():
    example = next(
        example
        for example
        in v0381_final_examples()
        if example.easy_leaf_count > 0
    )

    easy = list(
        oracle_easy_candidates(
            example
        )
    )
    blocks = (
        oracle_block_candidates(
            example
        )
    )

    first = easy[0]
    easy[0] = replace(
        first,
        constant=(
            first.constant + 1
        ),
    )

    assert (
        materialize_mixed_reduction(
            example,
            tuple(easy),
            blocks,
        )
        is None
    )


def test_v0381_controls_have_no_motifs():
    controls = [
        example
        for example
        in v0381_final_examples()
        if (
            example.apparent_dimension
            == example.core_dimension
        )
    ]

    assert controls
    assert all(
        example.easy_leaf_count == 0
        and example.block_count == 0
        and example.oracle_elimination_count == 0
        for example in controls
    )
