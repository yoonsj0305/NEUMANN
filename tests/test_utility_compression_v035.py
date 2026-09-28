from __future__ import annotations

from dataclasses import replace

from neumann1.frozen_v035_checkpoints import (
    V035_REFERENCE_STATE_SHA256,
    V035_UTILITY_STATE_SHA256,
    FrozenV035ReferenceClassifier,
    FrozenV035UtilityRegressor,
    checkpoint_fingerprints,
)
from neumann1.learned_compression import (
    check_scored_proposals,
    enumerate_affine_candidates,
)
from neumann1.learned_compression_dataset import (
    learned_compression_final_examples,
    learned_compression_training_examples,
    learned_compression_validation_examples,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)
from neumann1.utility_compression_dataset import (
    V035_CALIBRATION_EXAMPLES_PER_CELL,
    V035_FINAL_EXAMPLES_PER_CELL,
    V035_TRAIN_EXAMPLES_PER_CELL,
    v035_calibration_examples,
    v035_final_examples,
    v035_training_examples,
)
from neumann1.utility_gauntlet import (
    build_prefix_trace,
    calibrate_utility_threshold,
    make_v035_scorers,
    observe_utility_policy,
    score_v035_candidates,
)
from neumann1.utility_training import (
    certified_one_step_solver_utility,
)


def _signatures(examples):
    return {example.signature for example in examples}


def test_v035_checkpoint_identity_and_matched_capacity():
    fingerprints = checkpoint_fingerprints()
    reference = FrozenV035ReferenceClassifier()
    utility = FrozenV035UtilityRegressor()

    assert fingerprints["reference"] == V035_REFERENCE_STATE_SHA256
    assert fingerprints["utility"] == V035_UTILITY_STATE_SHA256
    assert reference.state_sha256 == V035_REFERENCE_STATE_SHA256
    assert utility.state_sha256 == V035_UTILITY_STATE_SHA256


def test_v035_split_sizes_and_disjointness():
    training = v035_training_examples()
    calibration = v035_calibration_examples()
    final = v035_final_examples()

    assert len(training) == 8 * V035_TRAIN_EXAMPLES_PER_CELL
    assert len(calibration) == 8 * V035_CALIBRATION_EXAMPLES_PER_CELL
    assert len(final) == 8 * V035_FINAL_EXAMPLES_PER_CELL

    prior = _signatures(learned_compression_training_examples())
    prior.update(_signatures(learned_compression_validation_examples()))
    prior.update(_signatures(learned_compression_final_examples()))
    prior.update(_signatures(v034_calibration_examples()))
    prior.update(_signatures(v034_final_examples()))

    train_sigs = _signatures(training)
    calibration_sigs = _signatures(calibration)
    final_sigs = _signatures(final)

    assert train_sigs.isdisjoint(prior)
    assert calibration_sigs.isdisjoint(prior)
    assert final_sigs.isdisjoint(prior)
    assert train_sigs.isdisjoint(calibration_sigs)
    assert train_sigs.isdisjoint(final_sigs)
    assert calibration_sigs.isdisjoint(final_sigs)


def test_v035_one_step_utility_is_certified_and_bounded():
    examples = v035_training_examples()[:8]

    saw_positive = False
    for example in examples:
        for candidate in enumerate_affine_candidates(
            example.full_system
        )[:8]:
            utility = certified_one_step_solver_utility(
                example,
                candidate,
            )
            assert 0.0 <= utility <= 1.0
            saw_positive = saw_positive or utility > 0.0

    assert saw_positive


def test_v035_matched_scores_do_not_use_core_dimension_metadata():
    example = v035_calibration_examples()[0]
    shadow_dimension = (
        example.core_dimension + 1
        if example.core_dimension + 1 < example.apparent_dimension
        else max(1, example.core_dimension - 1)
    )
    shadow = replace(
        example,
        core_dimension=shadow_dimension,
    )

    reference = FrozenV035ReferenceClassifier()
    utility = FrozenV035UtilityRegressor()

    assert reference.score(example) == reference.score(shadow)
    assert utility.score(example) == utility.score(shadow)


def test_v035_prefix_trace_matches_existing_checker_on_sample():
    scorers = make_v035_scorers()
    example = v035_calibration_examples()[10]
    scored = score_v035_candidates(
        example,
        "matched_utility",
        scorers=scorers,
    )
    trace = build_prefix_trace(example, scored)

    prefix = min(5, len(scored))
    checked = check_scored_proposals(
        example,
        scored,
        proposal_budget=prefix,
    )
    state = trace[prefix]

    assert state.accepted_candidates == checked.accepted_candidates
    assert state.rejected_count == len(checked.rejected_candidates)
    assert (
        state.materialized.solver_counts
        == checked.materialized.solver_counts
    )
    assert state.materialized.full_answer == checked.materialized.full_answer
    assert state.materialized.verified == checked.materialized.verified


def test_v035_calibration_and_final_sample_preserve_authority():
    scorers = make_v035_scorers()
    calibration_examples = v035_calibration_examples()[:16]
    final_examples = v035_final_examples()[:4]

    for method in (
        "matched_reference",
        "matched_utility",
        "target_leaf",
        "markowitz",
    ):
        calibration = calibrate_utility_threshold(
            calibration_examples,
            method,
            scorers=scorers,
        )
        for example in final_examples:
            observation = observe_utility_policy(
                example,
                method,
                calibration,
                scorers=scorers,
            )
            assert observation.final_verified
            assert observation.unsafe_accepted_reductions == 0
