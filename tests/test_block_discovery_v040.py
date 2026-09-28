from __future__ import annotations

from dataclasses import replace

from neumann1.block_discovery import (
    DISCOVERY_METHODS,
    discover_component_graph,
    discover_exact_candidate_overlap,
    discover_sparse_unit_pair,
    materialize_generic_mixed,
    observe_discovery_method,
    route_incidence_one_locals,
)
from neumann1.block_discovery_dataset import (
    V040_FINAL_EXAMPLES_PER_CELL,
    prior_v040_signatures,
    v040_contract_examples,
    v040_final_examples,
)
from neumann1.mixed_coupled import (
    oracle_block_candidates,
    oracle_easy_leaf_candidates,
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


def test_v040_final_cardinality_and_disjointness():
    examples = v040_final_examples()

    assert len(examples) == (
        8 * V040_FINAL_EXAMPLES_PER_CELL
    )
    assert _signatures(
        examples
    ).isdisjoint(
        prior_v040_signatures()
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
        ) == V040_FINAL_EXAMPLES_PER_CELL


def test_v040_generic_materializer_reproduces_oracle_on_contract_fixture():
    for example in v040_contract_examples():
        materialized = materialize_generic_mixed(
            example,
            oracle_easy_leaf_candidates(
                example
            ),
            oracle_block_candidates(
                example
            ),
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


def test_v040_incidence_router_recovers_contract_easy_leaves():
    frozen = fit_frozen_v033_scorer()

    for example in v040_contract_examples():
        routed = route_incidence_one_locals(
            example,
            frozen_scorer=frozen,
        )
        expected = {
            (
                leaf.row_index,
                leaf.target,
            )
            for leaf
            in example.oracle_easy_leaves
        }
        actual = {
            candidate.key
            for candidate in routed
        }
        assert actual == expected


def test_v040_discovery_methods_are_generator_metadata_blind():
    frozen = fit_frozen_v033_scorer()
    example = v040_contract_examples()[0]

    local = route_incidence_one_locals(
        example,
        frozen_scorer=frozen,
    )

    shadow = replace(
        example,
        oracle_easy_leaves=(),
        oracle_blocks=(),
        core_dimension=max(
            1,
            example.core_dimension - 1,
        ),
    )

    assert discover_exact_candidate_overlap(
        example,
        local,
    ) == discover_exact_candidate_overlap(
        shadow,
        local,
    )

    assert discover_sparse_unit_pair(
        example,
        local,
    ) == discover_sparse_unit_pair(
        shadow,
        local,
    )

    assert discover_component_graph(
        example,
        local,
    ) == discover_component_graph(
        shadow,
        local,
    )


def test_v040_pre_registered_discovery_methods_find_contract_blocks():
    frozen = fit_frozen_v033_scorer()

    for example in v040_contract_examples():
        local = route_incidence_one_locals(
            example,
            frozen_scorer=frozen,
        )
        expected = {
            (
                tuple(
                    sorted(
                        block.row_indices
                    )
                ),
                tuple(
                    sorted(
                        block.targets,
                        key=lambda name: int(
                            name[1:]
                        ),
                    )
                ),
            )
            for block
            in example.oracle_blocks
        }

        for result in (
            discover_exact_candidate_overlap(
                example,
                local,
            ),
            discover_sparse_unit_pair(
                example,
                local,
            ),
            discover_component_graph(
                example,
                local,
            ),
        ):
            actual = {
                (
                    candidate.row_indices,
                    candidate.targets,
                )
                for candidate
                in result.block_candidates
            }
            assert actual == expected


def test_v040_all_methods_verify_on_nonfinal_contract_fixtures():
    frozen = fit_frozen_v033_scorer()

    for example in v040_contract_examples():
        for method in DISCOVERY_METHODS:
            observation = observe_discovery_method(
                example,
                method,
                frozen_scorer=frozen,
            )
            assert observation.final_verified
            assert (
                observation.unsafe_accepted_reductions
                == 0
            )
