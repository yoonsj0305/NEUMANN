from __future__ import annotations

from dataclasses import replace

from neumann1.anti_shortcut_dataset import v041_contract_examples
from neumann1.mixed_coupled_dataset import generate_mixed_cell
from neumann1.block_discovery import (
    DISCOVERY_METHODS, discover_exact_candidate_overlap,
    materialize_generic_mixed, observe_discovery_method,
)
from neumann1.learned_compression import enumerate_affine_candidates
from neumann1.mixed_coupled import (
    materialize_mixed_reference, oracle_block_candidates,
    oracle_easy_leaf_candidates,
)
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def test_causal_arms_preserve_exact_oracle_and_distinct_shortcuts():
    for arm, example in v041_contract_examples():
        full = example.full_system
        assert tuple(
            sum(a * x for a, x in zip(row, full.ground_truth))
            for row in full.A
        ) == full.b
        assert materialize_mixed_reference(example) is not None
        assert materialize_generic_mixed(
            example, oracle_easy_leaf_candidates(example),
            oracle_block_candidates(example),
        ) is not None

        visible = {candidate.key for candidate in enumerate_affine_candidates(full)}
        declared = {
            (row, target)
            for block in example.oracle_blocks
            for row in block.row_indices
            for target in block.targets
        }
        if arm == "coefficient":
            assert visible.isdisjoint(declared)
        if arm == "overlap":
            assert declared.issubset(visible)


def test_methods_stay_metadata_blind_and_verify_on_contract_examples():
    frozen = fit_frozen_v033_scorer()
    for _, example in v041_contract_examples():
        shadow = replace(example, oracle_easy_leaves=(), oracle_blocks=(),
                         core_dimension=1)
        assert discover_exact_candidate_overlap(example, ()) == (
            discover_exact_candidate_overlap(shadow, ())
        )
        for method in DISCOVERY_METHODS:
            observation = observe_discovery_method(
                example, method, frozen_scorer=frozen,
            )
            assert observation.final_verified
            assert observation.unsafe_accepted_reductions == 0
            if observation.rejected_materialization_count:
                assert observation.final_solver_ops == observation.baseline_solver_ops
                assert observation.total_eliminated_variables == 0


def test_two_by_two_control_is_scoped_to_v041_control_split():
    example = generate_mixed_cell(2, 2, count=1, split="v041_control",
                                  seed=912_002)[0]
    assert example.oracle_elimination_count == 0
    assert materialize_mixed_reference(example) is not None
    try:
        generate_mixed_cell(2, 2, count=1, split="legacy", seed=912_002)
    except ValueError:
        pass
    else:
        raise AssertionError("legacy grid unexpectedly changed")
