from __future__ import annotations

from dataclasses import dataclass
import time

from .types import IRKind


@dataclass(frozen=True)
class TwoStageModelFootprint:
    """Inspectable model-state footprint for the current two-stage proposer.

    \`\`linear_parameter_count\`\` counts fitted logistic-regression coefficient and
    intercept scalars only. TF-IDF vocabulary and IDF state are reported
    separately because they are learned preprocessing state, not trainable linear
    classifier parameters.
    """

    known_feature_count: int
    kind_feature_count: int
    linear_parameter_count: int
    vectorizer_idf_state_count: int


@dataclass(frozen=True)
class ProposalCostObservation:
    predicted_kind: IRKind
    confidence: float
    known_probability: float
    stages_executed: int
    known_active_features: int
    kind_active_features: int
    score_dot_product_terms_proxy: int
    wall_seconds: float

    @property
    def total_active_features(self) -> int:
        return self.known_active_features + self.kind_active_features


@dataclass(frozen=True)
class RepeatedProposalReuseObservation:
    repeats: int
    prediction_stable: bool
    score_terms_every_time: int
    score_terms_once_reuse: int
    measured_model_wall_seconds_every_time: float
    measured_model_wall_seconds_once: float

    @property
    def score_term_reduction_factor(self) -> float:
        if self.score_terms_once_reuse <= 0:
            return float("inf")
        return self.score_terms_every_time / self.score_terms_once_reuse


def _require_fitted(proposer: object) -> None:
    if not bool(getattr(proposer, "fitted", False)):
        raise RuntimeError("two-stage proposer must be fit before cost measurement")
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
            "unsupported proposer for model-side measurement; missing "
            + ", ".join(missing)
        )


def _linear_parameter_count(model: object) -> int:
    coef = getattr(model, "coef_", None)
    intercept = getattr(model, "intercept_", None)
    if coef is None or intercept is None:
        raise RuntimeError("logistic model is not fit")
    return int(coef.size) + int(intercept.size)


def _idf_state_count(feature_union: object) -> int:
    count = 0
    for _, transformer in getattr(feature_union, "transformer_list", ()):
        idf = getattr(transformer, "idf_", None)
        if idf is not None:
            count += int(idf.size)
    return count


def inspect_two_stage_model(proposer: object) -> TwoStageModelFootprint:
    """Report fitted model state without pretending it is an LLM parameter count."""
    _require_fitted(proposer)
    known_model = proposer.known_detector
    kind_model = proposer.kind_classifier
    return TwoStageModelFootprint(
        known_feature_count=int(known_model.coef_.shape[1]),
        kind_feature_count=int(kind_model.coef_.shape[1]),
        linear_parameter_count=(
            _linear_parameter_count(known_model)
            + _linear_parameter_count(kind_model)
        ),
        vectorizer_idf_state_count=(
            _idf_state_count(proposer.known_vectorizer)
            + _idf_state_count(proposer.kind_vectorizer)
        ),
    )


def measure_two_stage_proposal(
    proposer: object,
    text: str,
) -> ProposalCostObservation:
    """Measure one learned proposal using the same decision rule as predict_kind().

    The score-term metric is deliberately a proxy: sparse non-zero input features
    multiplied by the number of fitted logistic coefficient rows actually scored.
    It is not a FLOP, CPU-instruction, memory-traffic, or energy measurement.
    """
    _require_fitted(proposer)

    start = time.perf_counter()
    known_x = proposer.known_vectorizer.transform([text])
    known_probs = proposer.known_detector.predict_proba(known_x)[0]
    known_classes = list(proposer.known_detector.classes_)
    known_idx = known_classes.index(1)
    p_known = float(known_probs[known_idx])

    known_active = int(known_x.nnz)
    known_rows = int(proposer.known_detector.coef_.shape[0])
    score_terms = known_active * known_rows

    if p_known < float(proposer.threshold):
        predicted = IRKind.UNKNOWN
        confidence = 1.0 - p_known
        kind_active = 0
        stages = 1
    else:
        kind_x = proposer.kind_vectorizer.transform([text])
        kind_probs = proposer.kind_classifier.predict_proba(kind_x)[0]
        idx = int(kind_probs.argmax())
        predicted = IRKind(str(proposer.kind_classifier.classes_[idx]))
        confidence = min(p_known, float(kind_probs[idx]))
        kind_active = int(kind_x.nnz)
        kind_rows = int(proposer.kind_classifier.coef_.shape[0])
        score_terms += kind_active * kind_rows
        stages = 2

    wall = time.perf_counter() - start
    return ProposalCostObservation(
        predicted_kind=predicted,
        confidence=confidence,
        known_probability=p_known,
        stages_executed=stages,
        known_active_features=known_active,
        kind_active_features=kind_active,
        score_dot_product_terms_proxy=score_terms,
        wall_seconds=wall,
    )


def measure_repeated_proposal_reuse(
    proposer: object,
    text: str,
    *,
    repeats: int = 8,
) -> RepeatedProposalReuseObservation:
    """Compare repeated learned proposal inference with exact proposal reuse.

    This isolates learned proposal work only. It does not remove the downstream
    deterministic compiler, solver, or verifier work required by NEUMANN.
    """
    if repeats < 2:
        raise ValueError("repeats must be >= 2")

    every = [measure_two_stage_proposal(proposer, text) for _ in range(repeats)]
    once = measure_two_stage_proposal(proposer, text)
    prediction_stable = all(
        obs.predicted_kind == once.predicted_kind
        and abs(obs.confidence - once.confidence) <= 1e-12
        and obs.score_dot_product_terms_proxy == once.score_dot_product_terms_proxy
        for obs in every
    )

    return RepeatedProposalReuseObservation(
        repeats=repeats,
        prediction_stable=prediction_stable,
        score_terms_every_time=sum(
            obs.score_dot_product_terms_proxy for obs in every
        ),
        score_terms_once_reuse=once.score_dot_product_terms_proxy,
        measured_model_wall_seconds_every_time=sum(obs.wall_seconds for obs in every),
        measured_model_wall_seconds_once=once.wall_seconds,
    )
