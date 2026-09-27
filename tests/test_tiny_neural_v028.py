import pytest

from neumann1 import IRKind
from neumann1.compiler_gate_dataset import (
    compiler_gate_final_examples,
    compiler_gate_training_examples,
    compiler_gate_validation_examples,
)
from neumann1.neural_model_cost import (
    inspect_tiny_neural_model,
    measure_repeated_neural_proposal_reuse,
    measure_tiny_neural_proposal,
)
from neumann1.neural_open_set import TinyNeuralOpenSetStructureFormer


def proposer():
    model = TinyNeuralOpenSetStructureFormer(
        hidden_units=4,
        alpha=1e-3,
    ).fit(compiler_gate_training_examples())
    model.tune_threshold(compiler_gate_validation_examples())
    return model


def test_tiny_neural_footprint_is_explicit_and_nonzero():
    model = proposer()
    footprint = inspect_tiny_neural_model(model)

    assert footprint.known_feature_count == 1322
    assert footprint.kind_feature_count == 638
    assert footprint.neural_parameter_count > 0
    assert footprint.vectorizer_idf_state_count == (
        footprint.known_feature_count + footprint.kind_feature_count
    )
    assert footprint.known_layer_shapes == ((1322, 4), (4, 1))
    assert footprint.kind_layer_shapes == ((638, 4), (4, 1))


def test_neural_cost_measurement_matches_public_predictor():
    model = proposer()
    for text, _, _ in compiler_gate_final_examples():
        observed = measure_tiny_neural_proposal(model, text)
        kind, confidence = model.predict_kind(text)

        assert observed.predicted_kind == kind
        assert observed.confidence == pytest.approx(
            confidence,
            abs=1e-12,
        )
        assert observed.weighted_sum_terms_proxy > 0


def test_tiny_neural_final_corpus_preserves_known_family_routing():
    model = proposer()
    known = [
        (text, expected)
        for text, expected, _ in compiler_gate_final_examples()
        if expected != IRKind.UNKNOWN
    ]

    for text, expected in known:
        predicted, _ = model.predict_kind(text)
        assert predicted == expected


def test_tiny_neural_final_corpus_abstains_on_current_unknowns():
    model = proposer()
    unknown = [
        text
        for text, expected, _ in compiler_gate_final_examples()
        if expected == IRKind.UNKNOWN
    ]

    assert all(
        model.predict_kind(text)[0] == IRKind.UNKNOWN
        for text in unknown
    )


def test_neural_exact_reuse_amortizes_weighted_sum_proxy():
    model = proposer()
    observed = measure_repeated_neural_proposal_reuse(
        model,
        "a + c = 9; a - c = 3",
        repeats=6,
    )

    assert observed.prediction_stable
    assert observed.weighted_sum_terms_once_reuse > 0
    assert observed.weighted_sum_terms_every_time == (
        6 * observed.weighted_sum_terms_once_reuse
    )
    assert observed.weighted_sum_term_reduction_factor == 6.0


def test_neural_reuse_requires_multiple_uses():
    model = proposer()
    with pytest.raises(ValueError, match="repeats must be >= 2"):
        measure_repeated_neural_proposal_reuse(
            model,
            "x + y = 5; x - y = 1",
            repeats=1,
        )
