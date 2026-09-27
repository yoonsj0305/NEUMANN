from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from experiments.v031_sequence_challenger import (
    OUTPUT_CLASSES,
    SequenceExperimentConfig,
    SequenceTokenizer,
    TinySequenceTransformer,
    fit_sequence_pair,
    model_footprint,
    predict_classes,
)
from neumann1.direct_frontier import solution_pair_to_class
from neumann1.paired_linear_dataset import (
    direct_frontier_final_examples,
    direct_frontier_training_pool,
    direct_frontier_validation_examples,
    paired_linear_final_examples,
    paired_linear_training_examples,
    paired_linear_validation_examples,
    sequence_challenger_final_examples,
    sequence_challenger_training_pool,
    sequence_challenger_validation_examples,
)


def test_v031_corpora_are_disjoint_and_cover_all_solution_classes():
    training = sequence_challenger_training_pool()
    validation = sequence_challenger_validation_examples()
    final = sequence_challenger_final_examples()

    assert len(training) == 8192
    assert len(validation) == 243
    assert len(final) == 243

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

    assert training_texts.isdisjoint(validation_texts)
    assert training_texts.isdisjoint(final_texts)
    assert validation_texts.isdisjoint(final_texts)
    assert training_texts.isdisjoint(previous_texts)
    assert validation_texts.isdisjoint(previous_texts)
    assert final_texts.isdisjoint(previous_texts)

    classes = {
        solution_pair_to_class(example.solution)
        for example in training
    }
    assert classes == set(range(81))


def test_v031_tokenizer_preserves_sequence_and_numeric_channel():
    tokenizer = SequenceTokenizer()
    first = tokenizer.encode(
        "2*x + 3*y = 7; x - y = 1"
    )
    second = tokenizer.encode(
        "3*x + 2*y = 7; x - y = 1"
    )

    assert first.length <= 32
    assert second.length <= 32
    assert first.token_ids != second.token_ids or (
        first.numeric_values != second.numeric_values
    )
    assert any(value != 0.0 for value in first.numeric_values)


def test_v031_direct_and_structural_architectures_match_exactly():
    config = SequenceExperimentConfig()
    tokenizer = SequenceTokenizer(
        max_tokens=config.max_tokens,
        numeric_scale=config.numeric_scale,
    )

    torch.manual_seed(config.seed)
    direct = TinySequenceTransformer(tokenizer, config)
    torch.manual_seed(config.seed)
    structural = TinySequenceTransformer(tokenizer, config)

    direct_footprint = model_footprint(
        direct,
        token_length=25,
    )
    structural_footprint = model_footprint(
        structural,
        token_length=25,
    )

    assert OUTPUT_CLASSES == 82
    assert (
        direct_footprint.parameter_count
        == structural_footprint.parameter_count
    )
    assert (
        direct_footprint.parameter_bytes
        == structural_footprint.parameter_bytes
    )
    assert (
        direct_footprint.architecture_weighted_sum_terms_proxy
        == structural_footprint.architecture_weighted_sum_terms_proxy
    )


def test_v031_mini_training_path_is_executable():
    config = SequenceExperimentConfig(
        embedding_dim=16,
        d_model=16,
        heads=4,
        layers=1,
        feedforward_dim=32,
        direct_training_examples=162,
        structural_positive_examples=81,
        structural_negative_examples=81,
        epochs=1,
        batch_size=81,
        cpu_threads=2,
    )
    training = sequence_challenger_training_pool()
    models = fit_sequence_pair(
        training,
        config=config,
    )

    texts = [
        example.text
        for example in sequence_challenger_validation_examples()[:8]
    ]
    direct, _ = predict_classes(
        models.direct_model,
        models.tokenizer,
        texts,
    )
    structural, _ = predict_classes(
        models.structural_model,
        models.tokenizer,
        texts,
    )

    assert len(direct) == len(texts)
    assert len(structural) == len(texts)
    assert all(0 <= value < OUTPUT_CLASSES for value in direct)
    assert all(0 <= value < OUTPUT_CLASSES for value in structural)
