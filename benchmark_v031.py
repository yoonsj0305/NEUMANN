from __future__ import annotations

import json
from statistics import mean

import torch

from experiments.v031_sequence_challenger import (
    SequenceExperimentConfig,
    decode_direct_class,
    fit_sequence_pair,
    model_footprint,
    predict_classes,
    structural_accepts,
)
from neumann1.direct_frontier import solution_pair_to_class
from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.paired_linear_dataset import (
    direct_frontier_final_examples,
    direct_frontier_training_pool,
    direct_frontier_validation_examples,
    make_near_negative,
    paired_linear_final_examples,
    paired_linear_training_examples,
    paired_linear_validation_examples,
    sequence_challenger_final_examples,
    sequence_challenger_training_pool,
    sequence_challenger_validation_examples,
)
from neumann1.paired_token_baseline import (
    fit_matched_token_models,
    measure_token_model,
    structural_accepts_linear,
)
from neumann1.solvers import LinearSystemSolver
from neumann1.types import CostLedger, IRKind, Problem
from neumann1.verifier import DeterministicVerifier


def _reference_representation(compiler, text):
    representation = compiler.form(Problem(text), CostLedger())
    if representation.kind != IRKind.LINEAR_SYSTEM:
        raise RuntimeError("positive example failed reference compiler")
    return representation


def _verify_values(verifier, representation, values):
    if values is None:
        return False
    answer = dict(zip(representation.payload["variables"], values))
    result = verifier.verify(
        Problem("evaluation-only"),
        representation,
        answer,
        CostLedger(),
    )
    return bool(result.ok)


def _mean_proxy(model, tokenizer, examples):
    proxies = []
    for example in examples:
        length = tokenizer.encode(example.text).length
        proxies.append(
            model_footprint(
                model,
                token_length=length,
            ).architecture_weighted_sum_terms_proxy
        )
    return mean(proxies)


def _evaluate_direct(models, examples, compiler, verifier):
    texts = [example.text for example in examples]
    classes, wall_seconds = predict_classes(
        models.direct_model,
        models.tokenizer,
        texts,
    )
    verified = 0
    exact_class = 0
    abstain_or_invalid = 0

    for class_id, example in zip(classes, examples):
        if class_id == solution_pair_to_class(example.solution):
            exact_class += 1

        values = decode_direct_class(class_id)
        if values is None:
            abstain_or_invalid += 1
            continue

        representation = _reference_representation(
            compiler,
            example.text,
        )
        if _verify_values(
            verifier,
            representation,
            values,
        ):
            verified += 1

    count = len(examples)
    return {
        "strict_verified_coverage": verified / count,
        "exact_solution_class_accuracy": exact_class / count,
        "abstain_or_invalid_rate": abstain_or_invalid / count,
        "batch_inference_wall_seconds": wall_seconds,
        "mean_weighted_sum_terms_proxy": _mean_proxy(
            models.direct_model,
            models.tokenizer,
            examples,
        ),
    }


def _evaluate_sequence_structural(
    models,
    examples,
    compiler,
    solver,
    verifier,
):
    texts = [example.text for example in examples]
    classes, wall_seconds = predict_classes(
        models.structural_model,
        models.tokenizer,
        texts,
    )

    proposed = 0
    verified = 0
    solver_steps = []

    for class_id, example in zip(classes, examples):
        if not structural_accepts(class_id):
            solver_steps.append(0)
            continue

        proposed += 1
        ledger = CostLedger()
        representation = compiler.form(
            Problem(example.text),
            ledger,
        )
        if representation.kind != IRKind.LINEAR_SYSTEM:
            solver_steps.append(0)
            continue

        answer = solver.solve(representation, ledger)
        verification = verifier.verify(
            Problem(example.text),
            representation,
            answer,
            ledger,
        )
        solver_steps.append(ledger.solver_steps)
        if verification.ok:
            verified += 1

    count = len(examples)
    return {
        "proposal_coverage": proposed / count,
        "strict_verified_coverage": verified / count,
        "batch_inference_wall_seconds": wall_seconds,
        "mean_solver_steps": mean(solver_steps),
        "mean_weighted_sum_terms_proxy": _mean_proxy(
            models.structural_model,
            models.tokenizer,
            examples,
        ),
    }


def _evaluate_sequence_negatives(
    models,
    examples,
    compiler,
):
    texts = [
        make_near_negative(example, index)
        for index, example in enumerate(examples)
    ]
    classes, wall_seconds = predict_classes(
        models.structural_model,
        models.tokenizer,
        texts,
    )

    proposal_false = 0
    final_false = 0
    for class_id, text in zip(classes, texts):
        if not structural_accepts(class_id):
            continue

        proposal_false += 1
        representation = compiler.form(
            Problem(text),
            CostLedger(),
        )
        if representation.kind == IRKind.LINEAR_SYSTEM:
            final_false += 1

    count = len(examples)
    return {
        "proposal_false_route_rate": proposal_false / count,
        "compiler_gated_false_route_rate": final_false / count,
        "batch_inference_wall_seconds": wall_seconds,
    }


def _evaluate_fixed_mlp_structural(
    examples,
    compiler,
    solver,
    verifier,
):
    models = fit_matched_token_models(
        paired_linear_training_examples(),
        paired_linear_validation_examples(),
        hidden_units=8,
        validation_negative_margin=0.10,
    )

    proposed = 0
    verified = 0

    for example in examples:
        observation = measure_token_model(
            models.structural_model,
            models.encoder,
            example.text,
        )
        if not structural_accepts_linear(models, observation):
            continue
        proposed += 1

        ledger = CostLedger()
        representation = compiler.form(
            Problem(example.text),
            ledger,
        )
        if representation.kind != IRKind.LINEAR_SYSTEM:
            continue
        answer = solver.solve(representation, ledger)
        if verifier.verify(
            Problem(example.text),
            representation,
            answer,
            ledger,
        ).ok:
            verified += 1

    count = len(examples)
    return {
        "proposal_coverage": proposed / count,
        "strict_verified_coverage": verified / count,
    }


def run():
    config = SequenceExperimentConfig()
    training = sequence_challenger_training_pool()
    validation = sequence_challenger_validation_examples()
    final = sequence_challenger_final_examples()

    compiler = ControlledLinearSystemStructureFormer()
    solver = LinearSystemSolver()
    verifier = DeterministicVerifier()

    models = fit_sequence_pair(
        training,
        config=config,
    )

    direct_footprint = model_footprint(
        models.direct_model,
        token_length=config.max_tokens,
    )
    structural_footprint = model_footprint(
        models.structural_model,
        token_length=config.max_tokens,
    )

    direct_validation = _evaluate_direct(
        models,
        validation,
        compiler,
        verifier,
    )
    direct_final = _evaluate_direct(
        models,
        final,
        compiler,
        verifier,
    )
    structural_validation = _evaluate_sequence_structural(
        models,
        validation,
        compiler,
        solver,
        verifier,
    )
    structural_final = _evaluate_sequence_structural(
        models,
        final,
        compiler,
        solver,
        verifier,
    )
    structural_validation_negatives = _evaluate_sequence_negatives(
        models,
        validation,
        compiler,
    )
    structural_final_negatives = _evaluate_sequence_negatives(
        models,
        final,
        compiler,
    )

    fixed_mlp_validation = _evaluate_fixed_mlp_structural(
        validation,
        compiler,
        solver,
        verifier,
    )
    fixed_mlp_final = _evaluate_fixed_mlp_structural(
        final,
        compiler,
        solver,
        verifier,
    )

    training_texts = {example.text for example in training}
    validation_texts = {example.text for example in validation}
    final_texts = {example.text for example in final}

    previous_texts = {
        example.text
        for dataset in (
            paired_linear_training_examples(),
            paired_linear_validation_examples(),
            paired_linear_final_examples(),
            direct_frontier_training_pool(),
            direct_frontier_validation_examples(),
            direct_frontier_final_examples(),
        )
        for example in dataset
    }

    split_disjoint = (
        training_texts.isdisjoint(validation_texts)
        and training_texts.isdisjoint(final_texts)
        and validation_texts.isdisjoint(final_texts)
    )
    disjoint_from_previous = (
        training_texts.isdisjoint(previous_texts)
        and validation_texts.isdisjoint(previous_texts)
        and final_texts.isdisjoint(previous_texts)
    )

    direct_classes = {
        solution_pair_to_class(example.solution)
        for example in training[: config.direct_training_examples]
    }

    parity = {
        "parameter_count_equal": (
            direct_footprint.parameter_count
            == structural_footprint.parameter_count
        ),
        "parameter_bytes_equal": (
            direct_footprint.parameter_bytes
            == structural_footprint.parameter_bytes
        ),
        "validation_learned_proxy_equal": (
            direct_validation["mean_weighted_sum_terms_proxy"]
            == structural_validation["mean_weighted_sum_terms_proxy"]
        ),
        "final_learned_proxy_equal": (
            direct_final["mean_weighted_sum_terms_proxy"]
            == structural_final["mean_weighted_sum_terms_proxy"]
        ),
        "total_training_examples_equal": (
            config.direct_training_examples
            == config.structural_positive_examples
            + config.structural_negative_examples
        ),
    }

    keep = (
        all(parity.values())
        and split_disjoint
        and disjoint_from_previous
        and len(direct_classes) == 81
        and structural_validation_negatives[
            "compiler_gated_false_route_rate"
        ]
        == 0.0
        and structural_final_negatives[
            "compiler_gated_false_route_rate"
        ]
        == 0.0
    )

    return {
        "experiment": (
            "v0.0.31 matched tiny-Transformer direct-vs-structure challenger"
        ),
        "runtime": {
            "torch_version": torch.__version__,
            "device": "cpu",
        },
        "pre_registered_config": {
            "max_tokens": config.max_tokens,
            "vocabulary_size": models.tokenizer.vocabulary_size,
            "d_model": config.d_model,
            "heads": config.heads,
            "layers": config.layers,
            "feedforward_dim": config.feedforward_dim,
            "output_classes": config.output_classes,
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "weight_decay": config.weight_decay,
            "seed": config.seed,
            "direct_training_examples": (
                config.direct_training_examples
            ),
            "structural_positive_examples": (
                config.structural_positive_examples
            ),
            "structural_negative_examples": (
                config.structural_negative_examples
            ),
            "validation_examples": len(validation),
            "final_examples": len(final),
            "splits_text_disjoint": split_disjoint,
            "disjoint_from_v029_v030": disjoint_from_previous,
            "direct_training_solution_classes": len(direct_classes),
        },
        "matched_model_footprint": {
            "direct_parameter_count": (
                direct_footprint.parameter_count
            ),
            "structural_parameter_count": (
                structural_footprint.parameter_count
            ),
            "direct_parameter_bytes": (
                direct_footprint.parameter_bytes
            ),
            "structural_parameter_bytes": (
                structural_footprint.parameter_bytes
            ),
            "parity": parity,
        },
        "training_diagnostics": {
            "direct_training_seconds": (
                models.direct_training_seconds
            ),
            "structural_training_seconds": (
                models.structural_training_seconds
            ),
        },
        "direct_sequence_path": {
            "validation": direct_validation,
            "final": direct_final,
        },
        "matched_sequence_structural_path": {
            "validation": structural_validation,
            "validation_near_negatives": (
                structural_validation_negatives
            ),
            "final": structural_final,
            "final_near_negatives": structural_final_negatives,
        },
        "fixed_v029_mlp_structural_reference": {
            "validation": fixed_mlp_validation,
            "final": fixed_mlp_final,
        },
        "keep_sequence_challenger_contract": keep,
        "boundary": (
            "Direct and Structural use identical two-layer Transformer "
            "architectures, identical 82-way heads, identical total training "
            "cardinality, fixed epochs, and the same tokenizer. Direct is "
            "favored with 8192 unique positive solution examples, while "
            "Structural receives 4096 positives plus 4096 near-negatives. "
            "Direct compiler use is evaluation-only. Structural actually "
            "executes compiler -> deterministic solver -> verifier. The "
            "weighted-sum proxy excludes embeddings, layer norm, softmax, "
            "activations, bias additions, memory traffic, and hardware energy. "
            "This remains a tiny controlled Transformer experiment, not an "
            "LLM or total-compute efficiency result."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
