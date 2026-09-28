from __future__ import annotations

from neumann1.block_compression import (
    materialize_block_reduction,
    oracle_block_candidates,
    validate_block_candidate,
)
from neumann1.block_compression_dataset import (
    BLOCK_FINAL_EXAMPLES_PER_CELL,
    block_scale_grid,
    v038_final_examples,
)
from neumann1.block_compression_experiment import (
    observe_block_compression,
)
from neumann1.learned_compression import (
    enumerate_affine_candidates,
)


def test_v038_dataset_cardinality_and_cells():
    examples = v038_final_examples()
    assert len(examples) == (
        8 * BLOCK_FINAL_EXAMPLES_PER_CELL
    )

    for k, n in block_scale_grid():
        cell = [
            example
            for example in examples
            if (
                example.core_dimension,
                example.apparent_dimension,
            )
            == (k, n)
        ]
        assert len(cell) == (
            BLOCK_FINAL_EXAMPLES_PER_CELL
        )


def test_v038_generator_has_no_unit_coefficients():
    for example in v038_final_examples():
        assert all(
            value == 0 or abs(value) >= 2
            for row in example.full_system.A
            for value in row
        )


def test_v038_scalar_affine_operator_is_blind_everywhere():
    for example in v038_final_examples():
        assert (
            enumerate_affine_candidates(
                example.full_system
            )
            == ()
        )


def test_v038_oracle_block_count_matches_dimension_contract():
    for example in v038_final_examples():
        assert len(example.oracle_blocks) == (
            (
                example.apparent_dimension
                - example.core_dimension
            )
            // 2
        )


def test_v038_oracle_blocks_validate_independently():
    for example in v038_final_examples()[:16]:
        for candidate in oracle_block_candidates(
            example
        ):
            ok, message, validated = (
                validate_block_candidate(
                    example.full_system,
                    candidate,
                )
            )
            assert ok, message
            assert validated is not None
            assert abs(
                validated.determinant
            ) == 1


def test_v038_block_oracle_reconstructs_original_problem():
    examples = v038_final_examples()
    seen = set()

    for example in examples:
        key = (
            example.core_dimension,
            example.apparent_dimension,
        )
        if key in seen:
            continue
        seen.add(key)

        materialized = (
            materialize_block_reduction(
                example,
                oracle_block_candidates(
                    example
                ),
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


def test_v038_no_compression_control_is_safe():
    example = next(
        example
        for example in v038_final_examples()
        if (
            example.core_dimension,
            example.apparent_dimension,
        )
        == (4, 4)
    )
    observation = observe_block_compression(
        example
    )

    assert observation.expected_block_count == 0
    assert observation.accepted_block_count == 0
    assert observation.retained_dimension == 4
    assert observation.oracle_solver_savings == 0
    assert observation.final_verified
    assert observation.ground_truth_equivalent
