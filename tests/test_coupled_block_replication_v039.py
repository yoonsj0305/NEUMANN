from __future__ import annotations

from neumann1.coupled_block import (
    materialize_block_reduction,
    oracle_block_candidates,
)
from neumann1.coupled_block_replication import (
    observe_candidate_visibility,
)
from neumann1.coupled_block_replication_dataset import (
    V039_FINAL_EXAMPLES_PER_CELL,
    prior_v039_signatures,
    v039_final_examples,
)
from neumann1.learned_compression import (
    enumerate_affine_candidates,
    validate_candidate_against_system,
)
from neumann1.structural_compression import (
    scale_grid,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v039_final_cardinality_and_prior_disjointness():
    examples = v039_final_examples()

    assert len(examples) == (
        8 * V039_FINAL_EXAMPLES_PER_CELL
    )
    assert _signatures(
        examples
    ).isdisjoint(
        prior_v039_signatures()
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
        ) == V039_FINAL_EXAMPLES_PER_CELL


def test_v039_active_candidate_visibility_contract():
    for example in v039_final_examples():
        visibility = observe_candidate_visibility(
            example
        )
        if example.block_count == 0:
            assert (
                visibility.enumerated_candidate_count
                == 0
            )
            continue

        assert (
            visibility.enumerated_candidate_count
            == 4 * example.block_count
        )
        assert (
            visibility.expected_candidate_count
            == 4 * example.block_count
        )
        assert (
            visibility.all_candidate_algebra_valid
        )


def test_v039_every_enumerated_candidate_matches_original_row():
    for example in v039_final_examples()[:32]:
        for candidate in enumerate_affine_candidates(
            example.full_system
        ):
            ok, _ = validate_candidate_against_system(
                example.full_system,
                candidate,
            )
            assert ok


def test_v039_block_oracle_remains_safe_on_sample():
    for example in v039_final_examples()[:16]:
        oracle = oracle_block_candidates(
            example
        )
        materialized = materialize_block_reduction(
            example,
            oracle,
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


def test_v039_controls_remain_candidate_free():
    controls = [
        example
        for example in v039_final_examples()
        if example.block_count == 0
    ]
    assert controls
    assert all(
        not enumerate_affine_candidates(
            example.full_system
        )
        for example in controls
    )
