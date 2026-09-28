from __future__ import annotations

from dataclasses import replace

from neumann1.block_discovery import (
    DISCOVERY_METHOD_ORDER,
    aggregate_discovery,
    discover,
    observe_discovery,
    select_discovery_method,
)
from neumann1.block_discovery_dataset import (
    V040_FINAL_EXAMPLES_PER_CELL,
    prior_v040_signatures,
    v040_final_examples,
)
from neumann1.mixed_coupled_dataset import (
    mixed_scale_grid,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def test_v040_final_cardinality_and_prior_disjointness():
    examples = v040_final_examples()

    assert len(examples) == (
        8 * V040_FINAL_EXAMPLES_PER_CELL
    )
    assert _signatures(
        examples
    ).isdisjoint(
        prior_v040_signatures()
    )

    for k, n in mixed_scale_grid():
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


def test_v040_discovery_does_not_depend_on_generator_metadata():
    example = next(
        example
        for example in v040_final_examples()
        if example.oracle_blocks
    )
    shadow = replace(
        example,
        oracle_easy_leaves=(),
        oracle_blocks=(),
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

    for method in DISCOVERY_METHOD_ORDER:
        original = discover(
            example.full_system,
            method,
        )
        changed = discover(
            shadow.full_system,
            method,
        )
        assert original == changed


def test_v040_incidence_router_recovers_visible_motifs_on_sample():
    examples = [
        example
        for example in v040_final_examples()
        if example.oracle_elimination_count > 0
    ][:8]

    for example in examples:
        plan = discover(
            example.full_system,
            "incidence_signature",
        )

        assert {
            (
                leaf.row_index,
                leaf.target,
            )
            for leaf in plan.easy_leaves
        } == {
            (
                leaf.row_index,
                leaf.target,
            )
            for leaf in example.oracle_easy_leaves
        }

        assert {
            (
                block.row_indices,
                block.targets,
            )
            for block in plan.blocks
        } == {
            (
                block.row_indices,
                block.targets,
            )
            for block in example.oracle_blocks
        }


def test_v040_all_methods_execute_safely_on_sample():
    frozen = fit_frozen_v033_scorer()
    examples = v040_final_examples()[:8]

    for method in DISCOVERY_METHOD_ORDER:
        rows = tuple(
            observe_discovery(
                example,
                method,
                frozen_scorer=frozen,
            )
            for example in examples
        )
        assert all(
            row.verified
            for row in rows
        )
        assert all(
            row.unsafe_accepted_reductions
            == 0
            for row in rows
        )


def test_v040_method_cost_order_on_nontrivial_sample():
    example = next(
        example
        for example in v040_final_examples()
        if example.apparent_dimension == 32
        and example.core_dimension == 2
    )

    m1 = discover(
        example.full_system,
        "incidence_signature",
    )
    m2 = discover(
        example.full_system,
        "row_pair_shared_target",
    )
    m3 = discover(
        example.full_system,
        "exact_visible_pair",
    )

    assert (
        m1.work.proxy_total
        < m2.work.proxy_total
    )
    assert (
        m2.work.proxy_total
        <= m3.work.proxy_total
    )


def test_v040_selection_prefers_first_adequate_method():
    adequate = {
        "verified_retention": 1.0,
        "unsafe_accepted_reductions": 0,
        "mean_active_solver_savings_recovery": 1.0,
        "mean_active_retained_dimension_error": 0.0,
        "easy_leaf_recall": 1.0,
        "block_recall": 1.0,
        "adequate": True,
    }
    aggregates = {
        method: dict(
            adequate,
            method=method,
        )
        for method in DISCOVERY_METHOD_ORDER
    }

    selected = select_discovery_method(
        aggregates
    )
    assert (
        selected["selected_method"]
        == "incidence_signature"
    )
    assert (
        selected["decision"]
        == "DELETE_LEARNED_BLOCK_SCORER"
    )


def test_v040_aggregate_contract_is_well_formed():
    frozen = fit_frozen_v033_scorer()
    examples = v040_final_examples()[:4]
    rows = tuple(
        observe_discovery(
            example,
            "incidence_signature",
            frozen_scorer=frozen,
        )
        for example in examples
    )
    result = aggregate_discovery(rows)

    assert result[
        "verified_retention"
    ] == 1.0
    assert result[
        "unsafe_accepted_reductions"
    ] == 0
