from __future__ import annotations

import hashlib
import json
import math

from neumann1.learned_compression import (
    LearnedCompressionProposer,
    ScoredCandidate,
    aggregate_learned_observations,
    candidate_features,
    check_scored_proposals,
    enumerate_affine_candidates,
    inspect_learned_compressor,
    observe_learned_compression,
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


def _signatures(examples):
    return {
        example.signature
        for example in examples
    }


def _oracle_candidates_present(examples) -> bool:
    for example in examples:
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
        if not oracle_keys.issubset(candidate_keys):
            return False
    return True


def _generic_name_and_order_controls(examples) -> dict[str, bool]:
    generic_names = all(
        example.full_system.variables
        == tuple(
            f"v{i}"
            for i in range(example.apparent_dimension)
        )
        for example in examples
    )

    has_permuted_retained_set = any(
        set(example.oracle_retained_variables)
        != set(
            example.full_system.variables[
                : example.core_dimension
            ]
        )
        for example in examples
        if example.apparent_dimension > example.core_dimension
    )

    has_nonblock_oracle_rows = any(
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
        for example in examples
        if example.apparent_dimension > example.core_dimension
    )

    return {
        "generic_variable_names": generic_names,
        "retained_variables_not_fixed_prefix": has_permuted_retained_set,
        "oracle_rows_not_fixed_suffix": has_nonblock_oracle_rows,
    }




def _sort_scored(items):
    output = list(items)
    output.sort(
        key=lambda item: (
            -item.score,
            item.candidate.row_index,
            int(item.candidate.target[1:]),
        )
    )
    return tuple(output)


def _deterministic_random_scores(example):
    scored = []
    system_fingerprint = repr(
        (example.full_system.A, example.full_system.b)
    )
    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        payload = (
            "v033-random-control|"
            + system_fingerprint
            + f"|{candidate.row_index}|{candidate.target}"
        ).encode("utf-8")
        digest = hashlib.sha256(payload).digest()
        integer = int.from_bytes(digest[:8], "big")
        score = integer / float(2**64 - 1)
        scored.append(
            ScoredCandidate(
                candidate=candidate,
                score=score,
            )
        )
    return _sort_scored(scored)


def _simple_sparsity_scores(example):
    scored = []
    for candidate in enumerate_affine_candidates(
        example.full_system
    ):
        features = candidate_features(
            example.full_system,
            candidate,
        )
        row_density = features[1]
        target_incidence = features[4]
        score = -(row_density + target_incidence)
        scored.append(
            ScoredCandidate(
                candidate=candidate,
                score=score,
            )
        )
    return _sort_scored(scored)


def _control_metrics(examples, scorer):
    recoveries = []
    exact_recoveries = []
    verified = []
    rejected = 0
    opportunities = 0

    for example in examples:
        budget = example.oracle_elimination_count
        checked = check_scored_proposals(
            example,
            scorer(example),
            proposal_budget=budget,
        )
        verified.append(
            1.0
            if (
                checked.materialized.verified
                and checked.materialized.ground_truth_equivalent
            )
            else 0.0
        )
        rejected += len(checked.rejected_candidates)

        if budget <= 0:
            continue

        opportunities += 1
        oracle_keys = {
            (rule.row_index, rule.target)
            for rule in example.oracle_dependencies
        }
        accepted = len(checked.accepted_candidates)
        exact = sum(
            1
            for candidate in checked.accepted_candidates
            if candidate.key in oracle_keys
        )
        recoveries.append(accepted / budget)
        exact_recoveries.append(exact / budget)

    return {
        "compression_opportunity_count": opportunities,
        "verified_retention": sum(verified) / len(verified),
        "mean_elimination_count_recovery": (
            sum(recoveries) / len(recoveries)
        ),
        "mean_exact_oracle_rule_recovery": (
            sum(exact_recoveries) / len(exact_recoveries)
        ),
        "total_fail_closed_rejections": rejected,
    }


def run() -> dict[str, object]:
    training = learned_compression_training_examples()
    validation = learned_compression_validation_examples()
    final = learned_compression_final_examples()

    train_signatures = _signatures(training)
    validation_signatures = _signatures(validation)
    final_signatures = _signatures(final)

    split_disjoint = (
        train_signatures.isdisjoint(validation_signatures)
        and train_signatures.isdisjoint(final_signatures)
        and validation_signatures.isdisjoint(final_signatures)
    )

    proposer = LearnedCompressionProposer().fit(training)
    footprint = inspect_learned_compressor(proposer)

    validation_observations = tuple(
        observe_learned_compression(
            example,
            proposer,
            footprint,
        )
        for example in validation
    )
    final_observations = tuple(
        observe_learned_compression(
            example,
            proposer,
            footprint,
        )
        for example in final
    )

    validation_aggregate = aggregate_learned_observations(
        validation_observations
    )
    final_aggregate = aggregate_learned_observations(
        final_observations
    )

    random_control = _control_metrics(
        final,
        _deterministic_random_scores,
    )
    sparsity_control = _control_metrics(
        final,
        _simple_sparsity_scores,
    )

    all_examples = training + validation + final
    naming_controls = _generic_name_and_order_controls(
        all_examples
    )

    cell_counts = {
        (cell["core_dimension"], cell["apparent_dimension"]): (
            cell["count"]
        )
        for cell in final_aggregate["cells"]
    }
    final_cells_complete = (
        len(cell_counts) == len(learned_scale_grid())
        and all(
            cell_counts.get((k, n)) == FINAL_EXAMPLES_PER_CELL
            for k, n in learned_scale_grid()
        )
    )

    learned_cost_finite = (
        footprint.input_feature_dimension > 0
        and footprint.fitted_weight_bias_scalars > 0
        and footprint.weighted_sum_terms_per_candidate > 0
        and all(
            observation.learned_weighted_sum_proxy > 0
            for observation in final_observations
            if observation.candidates_scored > 0
        )
        and all(
            math.isfinite(
                float(observation.learned_weighted_sum_proxy)
            )
            for observation in final_observations
        )
    )

    oracle_candidates_present = _oracle_candidates_present(
        all_examples
    )

    keep = (
        split_disjoint
        and all(naming_controls.values())
        and oracle_candidates_present
        and final_cells_complete
        and final_aggregate["verified_retention"] == 1.0
        and final_aggregate["unsafe_accepted_reduction_count"] == 0
        and learned_cost_finite
    )

    return {
        "experiment": "v0.0.33 Learned Compression Proposal",
        "data_contract": {
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in learned_scale_grid()
            ],
            "training_examples_per_cell": TRAIN_EXAMPLES_PER_CELL,
            "validation_examples_per_cell": VALIDATION_EXAMPLES_PER_CELL,
            "final_examples_per_cell": FINAL_EXAMPLES_PER_CELL,
            "training_examples": len(training),
            "validation_examples": len(validation),
            "final_examples": len(final),
            "split_signatures_disjoint": split_disjoint,
            "oracle_candidates_present": oracle_candidates_present,
            **naming_controls,
        },
        "model": {
            "input_feature_dimension": (
                footprint.input_feature_dimension
            ),
            "hidden_units": footprint.hidden_units,
            "fitted_weight_bias_scalars": (
                footprint.fitted_weight_bias_scalars
            ),
            "scaler_state_scalars": (
                footprint.scaler_state_scalars
            ),
            "layer_shapes": [
                list(shape)
                for shape in footprint.layer_shapes
            ],
            "weighted_sum_terms_per_candidate": (
                footprint.weighted_sum_terms_per_candidate
            ),
        },
        "validation": validation_aggregate,
        "final": final_aggregate,
        "post_result_diagnostic_controls": {
            "status": (
                "Added after the first learned result was observed, "
                "before merge. These are diagnostic controls, not "
                "pre-registered primary endpoints."
            ),
            "deterministic_random_ranking": random_control,
            "simple_row_sparsity_plus_target_incidence": (
                sparsity_control
            ),
        },
        "contract_checks": {
            "final_cells_complete": final_cells_complete,
            "final_verified_retention_1": (
                final_aggregate["verified_retention"] == 1.0
            ),
            "unsafe_accepted_reduction_count_0": (
                final_aggregate[
                    "unsafe_accepted_reduction_count"
                ]
                == 0
            ),
            "learned_cost_finite": learned_cost_finite,
        },
        "keep_learned_compression_contract": keep,
        "boundary": (
            "v0.0.33 supplies the oracle elimination cardinality n-k "
            "as the proposal budget. The learned model predicts candidate "
            "identities only; it does not infer the retained dimension. "
            "Candidate features are fixed matrix statistics rather than raw "
            "natural language or a general sequence model. Every accepted "
            "reduction is checked deterministically and the reconstructed "
            "answer is verified on the original full system. Learned weighted-"
            "sum terms are an architecture proxy, not measured FLOPs, CPU "
            "instructions, memory traffic, latency, or energy."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
