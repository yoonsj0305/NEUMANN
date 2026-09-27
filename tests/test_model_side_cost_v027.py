import pytest

from neumann1 import IRKind
from neumann1.compiler_gate_dataset import (
    compiler_gate_final_examples,
    compiler_gate_training_examples,
    compiler_gate_validation_examples,
)
from neumann1.model_side_cost import (
    inspect_two_stage_model,
    measure_repeated_proposal_reuse,
    measure_two_stage_proposal,
)
from neumann1.open_set import TwoStageOpenSetStructureFormer


def proposer():
    model = TwoStageOpenSetStructureFormer().fit(compiler_gate_training_examples())
    model.tune_threshold(compiler_gate_validation_examples())
    return model


def test_model_footprint_separates_linear_parameters_from_tfidf_state():
    model = proposer()
    footprint = inspect_two_stage_model(model)

    assert footprint.known_feature_count == model.known_detector.coef_.shape[1]
    assert footprint.kind_feature_count == model.kind_classifier.coef_.shape[1]
    assert footprint.linear_parameter_count > 0
    assert footprint.vectorizer_idf_state_count == (
        footprint.known_feature_count + footprint.kind_feature_count
    )


def test_cost_instrumentation_matches_public_predictor_on_final_corpus():
    model = proposer()
    for text, _, _ in compiler_gate_final_examples():
        observed = measure_two_stage_proposal(model, text)
        kind, confidence = model.predict_kind(text)
        assert observed.predicted_kind == kind
        assert observed.confidence == pytest.approx(confidence, abs=1e-12)
        assert observed.score_dot_product_terms_proxy > 0


def test_open_set_abstention_skips_second_classifier_stage():
    model = proposer()
    observed = measure_two_stage_proposal(
        model,
        "Find an Eulerian circuit in this graph.",
    )
    assert observed.predicted_kind == IRKind.UNKNOWN
    assert observed.stages_executed == 1
    assert observed.kind_active_features == 0


def test_known_item_executes_both_classifier_stages():
    model = proposer()
    observed = measure_two_stage_proposal(
        model,
        "L1 can use X1 or X2; L2 can use X2 or X3",
    )
    assert observed.predicted_kind == IRKind.BIPARTITE_MATCHING
    assert observed.stages_executed == 2
    assert observed.known_active_features > 0
    assert observed.kind_active_features > 0


def test_exact_proposal_reuse_amortizes_learned_scoring_proxy():
    model = proposer()
    observed = measure_repeated_proposal_reuse(
        model,
        "a + c = 9; a - c = 3",
        repeats=6,
    )
    assert observed.prediction_stable
    assert observed.score_terms_once_reuse > 0
    assert observed.score_terms_every_time == 6 * observed.score_terms_once_reuse
    assert observed.score_term_reduction_factor == 6.0


def test_repeated_proposal_reuse_requires_multiple_uses():
    model = proposer()
    with pytest.raises(ValueError, match="repeats must be >= 2"):
        measure_repeated_proposal_reuse(model, "x + y = 5; x - y = 1", repeats=1)
