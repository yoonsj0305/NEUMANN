from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

from .types import Problem, Representation, IRKind, CostLedger
from .learned_representation import KindTrainingExample


def _features():
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)),
    ])


@dataclass
class OpenSetMetrics:
    threshold: float
    known_coverage: float
    unknown_false_route_rate: float


class TwoStageOpenSetStructureFormer:
    """Exploratory two-stage structure recognizer.

    Stage 1 asks whether a text belongs to any currently-supported structural family.
    Stage 2 classifies among the supported families only.

    The threshold is selected on a separate validation set. This remains a small,
    synthetic research scaffold, not a calibrated production OOD detector.
    """

    def __init__(self):
        self.known_vectorizer = _features()
        self.known_detector = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
        self.kind_vectorizer = _features()
        self.kind_classifier = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
        self.threshold = 0.5
        self.fitted = False

    def fit(self, examples: Iterable[KindTrainingExample]) -> "TwoStageOpenSetStructureFormer":
        examples = list(examples)
        texts = [e.text for e in examples]
        is_known = [0 if e.kind == IRKind.UNKNOWN else 1 for e in examples]
        X = self.known_vectorizer.fit_transform(texts)
        self.known_detector.fit(X, is_known)

        known = [e for e in examples if e.kind != IRKind.UNKNOWN]
        Xk = self.kind_vectorizer.fit_transform([e.text for e in known])
        yk = [e.kind.value for e in known]
        self.kind_classifier.fit(Xk, yk)
        self.fitted = True
        return self

    def tune_threshold(self, validation: Sequence[tuple[str, IRKind, str]]) -> OpenSetMetrics:
        """Select useful coverage subject to zero observed routing errors.

        A routed validation item counts as an error if it is an unsupported structure
        or if the within-known classifier predicts the wrong supported family. This is
        still an exploratory finite-validation rule, not a statistical guarantee.
        """
        if not self.fitted:
            raise RuntimeError("fit before tune_threshold")
        candidates = [i / 100 for i in range(25, 81)]
        best = None
        known_n = sum(expected != IRKind.UNKNOWN for _, expected, _ in validation)
        unknown_n = sum(expected == IRKind.UNKNOWN for _, expected, _ in validation)
        for th in candidates:
            known_accept = 0
            wrong_known = 0
            false_unknown = 0
            for text, expected, _ in validation:
                p = self.known_probability(text)
                if expected != IRKind.UNKNOWN and p >= th:
                    known_accept += 1
                    if self.predict_supported_kind(text) != expected:
                        wrong_known += 1
                if expected == IRKind.UNKNOWN and p >= th:
                    false_unknown += 1
            coverage = known_accept / known_n if known_n else 0.0
            false_rate = false_unknown / unknown_n if unknown_n else 0.0
            if false_unknown == 0 and wrong_known == 0:
                cand = OpenSetMetrics(th, coverage, false_rate)
                if best is None or cand.known_coverage > best.known_coverage or (
                    cand.known_coverage == best.known_coverage and cand.threshold < best.threshold
                ):
                    best = cand
        if best is None:
            best = OpenSetMetrics(0.80, 0.0, 0.0)
        self.threshold = best.threshold
        return best

    def known_probability(self, text: str) -> float:
        X = self.known_vectorizer.transform([text])
        classes = list(self.known_detector.classes_)
        known_idx = classes.index(1)
        return float(self.known_detector.predict_proba(X)[0][known_idx])

    def predict_supported_kind(self, text: str) -> IRKind:
        Xk = self.kind_vectorizer.transform([text])
        probs = self.kind_classifier.predict_proba(Xk)[0]
        idx = int(probs.argmax())
        return IRKind(str(self.kind_classifier.classes_[idx]))

    def predict_kind(self, text: str) -> tuple[IRKind, float]:
        p_known = self.known_probability(text)
        if p_known < self.threshold:
            return IRKind.UNKNOWN, 1.0 - p_known
        Xk = self.kind_vectorizer.transform([text])
        probs = self.kind_classifier.predict_proba(Xk)[0]
        idx = int(probs.argmax())
        kind = IRKind(str(self.kind_classifier.classes_[idx]))
        return kind, min(p_known, float(probs[idx]))

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        if not self.fitted:
            raise RuntimeError("fit before form")
        ledger.representation_steps += 1
        kind, confidence = self.predict_kind(problem.raw_text)
        if kind == IRKind.UNKNOWN:
            return Representation(kind=kind, payload={}, confidence=confidence, rationale="two-stage open-set rejection")
        payloads = problem.metadata.get("payload_by_kind", {})
        payload = payloads.get(kind.value, {})
        if not payload:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=confidence,
                rationale=f"predicted {kind.value} but no independent payload supplied",
            )
        return Representation(
            kind=kind,
            payload=payload,
            confidence=confidence,
            rationale=f"two-stage open-set model threshold={self.threshold:.2f}",
        )
