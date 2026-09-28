from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from neumann1.coupled_block import (
    derive_block_candidate,
    materialize_block_reduction,
    oracle_block_candidates,
    validate_block_candidate,
)
from neumann1.coupled_block_dataset import (
    V038_FINAL_EXAMPLES_PER_CELL,
    prior_v038_signatures,
    v038_final_examples,
)
from neumann1.learned_compression import (
    enumerate_affine_candidates,
)
from neumann1.structural_compression import (
    scale_grid,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v038_final_cardinality_and_prior_disjointness():
    examples = v038_final_examples()

    assert len(examples) == (
        8 * V038_FINAL_EXAMPLES_PER_CELL
    )
    assert _signatures(
        examples
    ).isdisjoint(
        prior_v038_signatures()
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
        ) == V038_FINAL_EXAMPLES_PER_CELL


def test_v038_active_examples_expose_real_one_row_candidates():
    for example in v038_final_examples():
        if (
            example.apparent_dimension
            == example.core_dimension
        ):
            continue

        candidates = enumerate_affine_candidates(
            example.full_system
        )
        assert candidates
        assert len(candidates) >= (
            4 * example.block_count
        )


def test_v038_oracle_blocks_materialize_to_exact_core():
    for example in v038_final_examples()[:16]:
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
        assert len(oracle) == (
            example.block_count
        )


def test_v038_block_checker_recomputes_original_algebra():
    example = next(
        example
        for example in v038_final_examples()
        if example.block_count > 0
    )
    candidate = oracle_block_candidates(
        example
    )[0]

    first_rule = candidate.rules[0]
    corrupted_rule = replace(
        first_rule,
        constant=(
            first_rule.constant
            + Fraction(1, 7)
        ),
    )
    corrupted = replace(
        candidate,
        rules=(
            corrupted_rule,
            candidate.rules[1],
        ),
    )

    ok, _ = validate_block_candidate(
        example.full_system,
        corrupted,
    )
    assert not ok
    assert materialize_block_reduction(
        example,
        (corrupted,),
    ) is None


def test_v038_derived_candidate_is_canonical_under_pair_order():
    example = next(
        example
        for example in v038_final_examples()
        if example.block_count > 0
    )
    block = example.oracle_blocks[0]

    forward = derive_block_candidate(
        example.full_system,
        block.row_indices,
        block.targets,
    )
    reverse = derive_block_candidate(
        example.full_system,
        tuple(
            reversed(
                block.row_indices
            )
        ),
        tuple(
            reversed(
                block.targets
            )
        ),
    )

    assert forward is not None
    assert forward == reverse


def test_v038_controls_have_no_oracle_blocks():
    controls = [
        example
        for example in v038_final_examples()
        if (
            example.apparent_dimension
            == example.core_dimension
        )
    ]
    assert controls
    assert all(
        example.block_count == 0
        for example in controls
    )
    assert all(
        example.oracle_elimination_count == 0
        for example in controls
    )
