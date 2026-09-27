from __future__ import annotations

from functools import lru_cache
import math

import numpy as np

from neumann1.linear_ir import (
    ControlledLinearSystemStructureFormer,
)
from neumann1.paired_linear_dataset import (
    make_near_negative,
    paired_linear_final_examples,
    paired_linear_training_examples,
    paired_linear_validation_examples,
)
from neumann1.paired_token_baseline import (
    FixedPositionTokenEncoder,
    direct_solution,
    fit_matched_token_models,
    inspect_matched_token_models,
    measure_token_model,
    structural_accepts_linear,
)
from neumann1.solvers import LinearSystemSolver
from neumann1.types import CostLedger, IRKind, Problem
from neumann1.verifier import DeterministicVerifier


@lru_cache(maxsize=1)
def _models():
    return fit_matched_token_models(
        paired_linear_training_examples(),
        paired_linear_validation_examples(),
        hidden_units=8,
        validation_negative_margin=0.10,
    )


def test_v029_corpora_are_deterministic_and_disjoint():
    training = paired_linear_training_examples()
    validation = paired_linear_validation_examples()
    final = paired_linear_final_examples()

    assert len(training) == 128
    assert len(validation) == 32
    assert len(final) == 64
    assert training == paired_linear_training_examples()

    training_texts = {example.text for example in training}
    validation_texts = {example.text for example in validation}
    final_texts = {example.text for example in final}
    assert training_texts.isdisjoint(validation_texts)
    assert training_texts.isdisjoint(final_texts)
    assert validation_texts.isdisjoint(final_texts)


def test_v029_generated_solutions_match_deterministic_semantics():
    compiler = ControlledLinearSystemStructureFormer()
    solver = LinearSystemSolver()
    verifier = DeterministicVerifier()

    for example in paired_linear_final_examples():
        ledger = CostLedger()
        representation = compiler.form(
            Problem(example.text),
            ledger,
        )
        assert representation.kind == IRKind.LINEAR_SYSTEM

        stored_answer = dict(
            zip(
                representation.payload["variables"],
                example.solution,
            )
        )
        stored_verification = verifier.verify(
            Problem(example.text),
            representation,
            stored_answer,
            CostLedger(),
        )
        assert stored_verification.ok

        solved = solver.solve(representation, ledger)
        solved_verification = verifier.verify(
            Problem(example.text),
            representation,
            solved,
            ledger,
        )
        assert solved_verification.ok


def test_v029_encoder_is_sequence_sensitive_and_bounded():
    encoder = FixedPositionTokenEncoder()
    examples = paired_linear_training_examples()
    first = encoder.encode(examples[0].text)
    second = encoder.encode(examples[1].text)

    assert first.shape == (encoder.input_dimension,)
    assert second.shape == first.shape
    assert not np.array_equal(first, second)

    for dataset in (
        paired_linear_training_examples(),
        paired_linear_validation_examples(),
        paired_linear_final_examples(),
    ):
        for example in dataset:
            assert encoder.observe(example.text).token_count <= 32


def test_v029_models_have_matched_inference_capacity():
    models = _models()
    footprint = inspect_matched_token_models(models)

    assert (
        footprint.structural_parameter_count
        == footprint.direct_parameter_count
    )
    assert (
        footprint.structural_layer_shapes
        == footprint.direct_layer_shapes
    )
    assert (
        footprint.structural_dense_weighted_sum_terms_proxy
        == footprint.direct_dense_weighted_sum_terms_proxy
    )
    assert footprint.structural_parameter_count > 0


def test_v029_structural_validation_contract_is_separated():
    models = _models()
    validation = paired_linear_validation_examples()

    for index, example in enumerate(validation):
        positive = measure_token_model(
            models.structural_model,
            models.encoder,
            example.text,
        )
        negative = measure_token_model(
            models.structural_model,
            models.encoder,
            make_near_negative(example, index),
        )
        assert structural_accepts_linear(models, positive)
        assert not structural_accepts_linear(models, negative)


def test_v029_structural_path_verifies_final_positives_and_fails_closed():
    models = _models()
    compiler = ControlledLinearSystemStructureFormer()
    solver = LinearSystemSolver()
    verifier = DeterministicVerifier()

    for index, example in enumerate(paired_linear_final_examples()):
        observation = measure_token_model(
            models.structural_model,
            models.encoder,
            example.text,
        )
        assert structural_accepts_linear(models, observation)

        ledger = CostLedger()
        representation = compiler.form(
            Problem(example.text),
            ledger,
        )
        assert representation.kind == IRKind.LINEAR_SYSTEM
        answer = solver.solve(representation, ledger)
        assert verifier.verify(
            Problem(example.text),
            representation,
            answer,
            ledger,
        ).ok

        negative_text = make_near_negative(example, index)
        negative_observation = measure_token_model(
            models.structural_model,
            models.encoder,
            negative_text,
        )
        if structural_accepts_linear(models, negative_observation):
            rejected = compiler.form(
                Problem(negative_text),
                CostLedger(),
            )
            assert rejected.kind == IRKind.UNKNOWN


def test_v029_direct_outputs_are_finite_and_cost_matched():
    models = _models()
    example = paired_linear_final_examples()[0]

    direct_observation = measure_token_model(
        models.direct_model,
        models.encoder,
        example.text,
    )
    structural_observation = measure_token_model(
        models.structural_model,
        models.encoder,
        example.text,
    )
    predicted = direct_solution(models, direct_observation)

    assert all(math.isfinite(value) for value in predicted)
    assert (
        direct_observation.dense_weighted_sum_terms_proxy
        == structural_observation.dense_weighted_sum_terms_proxy
    )
    assert (
        direct_observation.active_input_scalars
        == structural_observation.active_input_scalars
    )
