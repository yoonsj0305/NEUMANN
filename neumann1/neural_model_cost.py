from __future__ import annotations

from dataclasses import dataclass
import time

from .types import IRKind


@dataclass(frozen=True)
class TinyNeuralModelFootprint:
    known_feature_count: int
    kind_feature_count: int
    neural_parameter_count: int
    vectorizer_idf_state_count: int
    known_layer_shapes: tuple[tuple[int, int], ...]
    kind_layer_shapes: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class NeuralProposalCostObservation:
    predicted_kind: IRKind
    confidence: float
    known_probability: float
    stages_executed: int
    known_active_features: int
    kind_active_features: int
    weighted_sum_terms_proxy: int
    wall_seconds: float

    @property
    def total_active_features(self) -> int:
        return self.known_active_features + self.kind_active_features


@dataclass(frozen=True)
class RepeatedNeuralProposalReuseObservation:
    repeats: int
    prediction_stable: bool
    weighted_sum_terms_every_time: int
    weighted_sum_terms_once_reuse: int
    measured_model_wall_seconds_every_time: float
    measured_model_wall_seconds_once: float

    @property
    def weighted_sum_term_reduction_factor(self) -> float:
        if self.weighted_sum_terms_once_reuse <= 0:
            return float("inf")
        return (
            self.weighted_sum_terms_every_time
            / self.weighted_sum_terms_once_reuse
        )


def _require_fitted(proposer: object) -> None:
    if not bool(getattr(proposer, "fitted", False)):
        raise RuntimeError("tiny neural proposer must be fit before measurement")
    required = (
        "known_vectorizer",
        "known_detector",
        "kind_vectorizer",
        "kind_classifier",
        "threshold",
    )
    missing = [name for name in required if not hasattr(proposer, name)]
    if missing:
        raise TypeError(
            "unsupported neural proposer for measurement; missing "
            + ", ".join(missing)
        )


def _parameter_count(model: object) -> int:
    weights = getattr(model, "coefs_", None)
    biases = getattr(model, "intercepts_", None)
    if weights is None or biases is None:
        raise RuntimeError("MLP model is not fit")
    return int(
        sum(matrix.size for matrix in weights)
        + sum(vector.size for vector in biases)
    )


def _layer_shapes(model: object) -> tuple[tuple[int, int], ...]:
    weights = getattr(model, "coefs_", None)
    if weights is None:
        raise RuntimeError("MLP model is not fit")
    return tuple(
        (int(matrix.shape[0]), int(matrix.shape[1]))
        for matrix in weights
    )


def _idf_state_count(feature_union: object) -> int:
    count = 0
    for _, transformer in getattr(feature_union, "transformer_list", ()):
        idf = getattr(transformer, "idf_", None)
        if idf is not None:
            count += int(idf.size)
    return count


def _weighted_sum_terms(model: object, input_nnz: int) -> int:
    """Count weighted-sum terms under a sparse-first-layer proxy.

    The first layer counts only nonzero TF-IDF inputs times output units.
    Later layers are treated as dense. Bias additions, activations,
    vectorization, probability conversion, memory traffic, and hardware effects
    are deliberately excluded.
    """
    weights = getattr(model, "coefs_", None)
    if not weights:
        raise RuntimeError("MLP model is not fit")

    total = int(input_nnz) * int(weights[0].shape[1])
    for matrix in weights[1:]:
        total += int(matrix.size)
    return total


def inspect_tiny_neural_model(proposer: object) -> TinyNeuralModelFootprint:
    _require_fitted(proposer)
    known_model = proposer.known_detector
    kind_model = proposer.kind_classifier

    return TinyNeuralModelFootprint(
        known_feature_count=int(known_model.coefs_[0].shape[0]),
        kind_feature_count=int(kind_model.coefs_[0].shape[0]),
        neural_parameter_count=(
            _parameter_count(known_model)
            + _parameter_count(kind_model)
        ),
        vectorizer_idf_state_count=(
            _idf_state_count(proposer.known_vectorizer)
            + _idf_state_count(proposer.kind_vectorizer)
        ),
        known_layer_shapes=_layer_shapes(known_model),
        kind_layer_shapes=_layer_shapes(kind_model),
    )


def measure_tiny_neural_proposal(
    proposer: object,
    text: str,
) -> NeuralProposalCostObservation:
    """Measure one tiny-neural family proposal.

    weighted_sum_terms_proxy is an architecture-aware arithmetic proxy, not a
    FLOP, instruction, memory-traffic, latency, or energy count.
    """
    _require_fitted(proposer)

    start = time.perf_counter()
    known_features = proposer.known_vectorizer.transform([text])
    known_probabilities = proposer.known_detector.predict_proba(
        known_features
    )[0]
    known_classes = list(proposer.known_detector.classes_)
    known_probability = float(
        known_probabilities[known_classes.index(1)]
    )

    known_active = int(known_features.nnz)
    weighted_terms = _weighted_sum_terms(
        proposer.known_detector,
        known_active,
    )

    if known_probability < float(proposer.threshold):
        predicted = IRKind.UNKNOWN
        confidence = 1.0 - known_probability
        kind_active = 0
        stages = 1
    else:
        kind_features = proposer.kind_vectorizer.transform([text])
        kind_probabilities = proposer.kind_classifier.predict_proba(
            kind_features
        )[0]
        index = int(kind_probabilities.argmax())
        predicted = IRKind(
            str(proposer.kind_classifier.classes_[index])
        )
        confidence = min(
            known_probability,
            float(kind_probabilities[index]),
        )
        kind_active = int(kind_features.nnz)
        weighted_terms += _weighted_sum_terms(
            proposer.kind_classifier,
            kind_active,
        )
        stages = 2

    wall_seconds = time.perf_counter() - start
    return NeuralProposalCostObservation(
        predicted_kind=predicted,
        confidence=confidence,
        known_probability=known_probability,
        stages_executed=stages,
        known_active_features=known_active,
        kind_active_features=kind_active,
        weighted_sum_terms_proxy=weighted_terms,
        wall_seconds=wall_seconds,
    )


def measure_repeated_neural_proposal_reuse(
    proposer: object,
    text: str,
    *,
    repeats: int = 8,
) -> RepeatedNeuralProposalReuseObservation:
    if repeats < 2:
        raise ValueError("repeats must be >= 2")

    every = [
        measure_tiny_neural_proposal(proposer, text)
        for _ in range(repeats)
    ]
    once = measure_tiny_neural_proposal(proposer, text)

    stable = all(
        observation.predicted_kind == once.predicted_kind
        and abs(observation.confidence - once.confidence) <= 1e-12
        and observation.weighted_sum_terms_proxy
        == once.weighted_sum_terms_proxy
        for observation in every
    )

    return RepeatedNeuralProposalReuseObservation(
        repeats=repeats,
        prediction_stable=stable,
        weighted_sum_terms_every_time=sum(
            observation.weighted_sum_terms_proxy
            for observation in every
        ),
        weighted_sum_terms_once_reuse=(
            once.weighted_sum_terms_proxy
        ),
        measured_model_wall_seconds_every_time=sum(
            observation.wall_seconds for observation in every
        ),
        measured_model_wall_seconds_once=once.wall_seconds,
    )
