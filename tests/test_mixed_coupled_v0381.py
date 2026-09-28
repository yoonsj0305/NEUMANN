from __future__ import annotations

from dataclasses import replace

from neumann1.learned_compression import (
    enumerate_affine_candidates,
)
from neumann1.mixed_coupled import (
    materialize_mixed_reference,
    oracle_easy_leaf_candidates,
    run_frozen_one_row_pipeline,
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


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v0381_cardinality_and_prior_disjointness():
    examples = v0381_final_examples()

    assert len(examples) == (
        8 * V0381_FINAL_EXAMPLES_PER_CELL
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
                for example in examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        ) == V0381_FINAL_EXAMPLES_PER_CELL


def test_v0381_motif_contract():
    for example in v0381_final_examples():
        d = (
            example.apparent_dimension
            - example.core_dimension
        )

        if d == 0:
            assert example.easy_leaf_count == 0
            assert example.block_count == 0
        elif d == 2:
            assert example.easy_leaf_count == 0
            assert example.block_count == 1
        else:
            assert d >= 4
            assert example.easy_leaf_count == 2
            assert (
                example.block_count
                == (d - 2) // 2
            )

        assert (
            example.oracle_elimination_count
            == d
        )


def test_v0381_candidate_count_matches_declared_motifs():
    for example in v0381_final_examples():
        candidates = enumerate_affine_candidates(
            example.full_system
        )
        assert len(candidates) == (
            example.expected_one_row_candidate_count
        )


def test_v0381_exact_reference_reaches_declared_core():
    for example in v0381_final_examples()[:24]:
        materialized = (
            materialize_mixed_reference(
                example
            )
        )
        assert materialized is not None
        assert materialized.verified
        assert (
            materialized.ground_truth_equivalent
        )
        assert (
            materialized.retained_system.dimension
            == example.core_dimension
        )


def test_v0381_easy_leaf_metadata_is_checker_visible():
    example = next(
        example
        for example in v0381_final_examples()
        if example.easy_leaf_count == 2
    )

    candidates = (
        oracle_easy_leaf_candidates(
            example
        )
    )
    assert len(candidates) == 2
    assert {
        candidate.key
        for candidate in candidates
    } == {
        (
            leaf.row_index,
            leaf.target,
        )
        for leaf in example.oracle_easy_leaves
    }


def test_v0381_frozen_pipeline_makes_progress_on_mixed_sample():
    frozen = fit_frozen_v033_scorer()
    examples = [
        example
        for example in v0381_final_examples()
        if example.easy_leaf_count == 2
    ][:4]

    for example in examples:
        trace = run_frozen_one_row_pipeline(
            example,
            frozen_scorer=frozen,
        )
        assert trace.final_verified
        assert (
            trace.unsafe_accepted_reductions
            == 0
        )
        assert len(
            trace.all_accepted
        ) > 0


def test_v0381_oracle_leaf_identity_is_not_core_metadata_dependent():
    example = next(
        example
        for example in v0381_final_examples()
        if example.easy_leaf_count == 2
    )
    shadow = replace(
        example,
        core_dimension=(
            example.core_dimension + 1
            if (
                example.core_dimension + 1
                < example.apparent_dimension
            )
            else max(
                1,
                example.core_dimension - 1,
            )
        ),
    )

    assert oracle_easy_leaf_candidates(
        example
    ) == oracle_easy_leaf_candidates(
        shadow
    )
