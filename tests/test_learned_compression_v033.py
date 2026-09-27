from __future__ import annotations

from dataclasses import replace

from neumann1.learned_compression import (
    AffineCandidate,
    LearnedCompressionProposer,
    check_scored_proposals,
    enumerate_affine_candidates,
    inspect_learned_compressor,
    materialize_reduction,
    observe_learned_compression,
    oracle_candidates,
    validate_candidate_against_system,
)
from neumann1.learned_compression_dataset import (
    FINAL_EXAMPLES_PER_CELL,
    TRAIN_EXAMPLES_PER_CELL,
    VALIDATION_EXAMPLES_PER_CELL,
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
    learned_scale_grid,
)


def test_v033_split_sizes_and_signatures_are_disjoint():
    training = learned_compression_training_examples()
    validation = learned_compression_validation_examples()
    final = learned_compression_final_examples()

    cells = len(learned_scale_grid())
    assert len(training) == cells * TRAIN_EXAMPLES_PER_CELL
    assert len(validation) == cells * VALIDATION_EXAMPLES_PER_CELL
    assert len(final) == cells * FINAL_EXAMPLES_PER_CELL

    train_signatures = {example.signature for example in training}
    validation_signatures = {
        example.signature
        for example in validation
    }
    final_signatures = {example.signature for example in final}

    assert train_signatures.isdisjoint(validation_signatures)
    assert train_signatures.isdisjoint(final_signatures)
    assert validation_signatures.isdisjoint(final_signatures)


def test_v033_variable_and_row_order_do_not_encode_oracle_roles():
    examples = learned_compression_validation_examples()

    assert all(
        example.full_system.variables
        == tuple(f"v{i}" for i in range(example.apparent_dimension))
        for example in examples
    )

    compressible = [
        example
        for example in examples
        if example.apparent_dimension > example.core_dimension
    ]
    assert any(
        set(example.oracle_retained_variables)
        != set(
            example.full_system.variables[: example.core_dimension]
        )
        for example in compressible
    )
    assert any(
        {
            rule.row_index
            for rule in example.oracle_dependencies
        }
        != set(
            range(
                example.core_dimension,
                example.apparent_dimension,
            )
        )
        for example in compressible
    )


def test_v033_candidate_universe_contains_every_oracle_rule():
    for example in learned_compression_validation_examples():
        candidate_keys = {
            candidate.key
            for candidate in enumerate_affine_candidates(
                example.full_system
            )
        }
        oracle_keys = {
            (rule.row_index, rule.target)
            for rule in example.oracle_dependencies
        }
        assert oracle_keys.issubset(candidate_keys)


def test_v033_oracle_reduction_materializes_exactly():
    for example in learned_compression_validation_examples()[:24]:
        reduction = materialize_reduction(
            example,
            oracle_candidates(example),
        )
        assert reduction is not None
        assert reduction.verified
        assert reduction.ground_truth_equivalent


def test_v033_tampered_candidate_fails_closed():
    example = next(
        item
        for item in learned_compression_validation_examples()
        if item.oracle_elimination_count > 0
    )
    candidate = oracle_candidates(example)[0]
    tampered = replace(
        candidate,
        constant=candidate.constant + 1,
    )

    ok, _ = validate_candidate_against_system(
        example.full_system,
        tampered,
    )
    assert not ok
    assert materialize_reduction(
        example,
        (tampered,),
    ) is None


def test_v033_small_learned_path_is_checked_and_verified():
    training = learned_compression_training_examples()[:48]
    proposer = LearnedCompressionProposer().fit(training)
    footprint = inspect_learned_compressor(proposer)

    assert footprint.input_feature_dimension == 16
    assert footprint.hidden_units == 16
    assert footprint.fitted_weight_bias_scalars > 0

    example = next(
        item
        for item in learned_compression_validation_examples()
        if item.oracle_elimination_count > 0
    )
    observation = observe_learned_compression(
        example,
        proposer,
        footprint,
    )

    assert observation.final_verified
    assert observation.ground_truth_equivalent
    assert observation.unsafe_accepted_reductions == 0
    assert observation.learned_weighted_sum_proxy > 0


def test_v033_no_compression_control_proposes_nothing():
    example = next(
        item
        for item in learned_compression_validation_examples()
        if item.apparent_dimension == item.core_dimension
    )
    proposer = LearnedCompressionProposer().fit(
        learned_compression_training_examples()[:48]
    )
    scored = proposer.score(example)
    checked = check_scored_proposals(
        example,
        scored,
        proposal_budget=0,
    )

    assert checked.proposed_candidates == ()
    assert checked.accepted_candidates == ()
    assert checked.materialized.verified
    assert checked.materialized.ground_truth_equivalent
