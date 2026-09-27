from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import FeatureUnion

from .learned_representation import KindTrainingExample
from .types import IRKind


def _features() -> FeatureUnion:
    return FeatureUnion([
        (
            "word",
            TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                lowercase=True,
            ),
        ),
        (
            "char",
            TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                sublinear_tf=True,
                lowercase=True,
            ),
        ),
    ])


@dataclass(frozen=True)
class NeuralOpenSetMetrics:
    threshold: float
    known_coverage: float
    unknown_false_route_rate: float


class TinyNeuralOpenSetStructureFormer:
    """Small nonlinear structural-family proposer.

    The model keeps the v0.0.27 two-stage open-set architecture but replaces
    logistic heads with one-hidden-layer MLP classifiers. It proposes only a
    family. Deterministic compilers remain the authority for solver-ready IR.
    """

    def __init__(
        self,
        *,
        hidden_units: int = 4,
        alpha: float = 1e-3,
    ):
        if hidden_units < 1:
            raise ValueError("hidden_units must be >= 1")
        self.hidden_units = int(hidden_units)
        self.alpha = float(alpha)

        self.known_vectorizer = _features()
        self.known_detector = MLPClassifier(
            hidden_layer_sizes=(self.hidden_units,),
            activation="relu",
            solver="lbfgs",
            alpha=self.alpha,
            max_iter=4000,
            random_state=0,
        )
        self.kind_vectorizer = _features()
        self.kind_classifier = MLPClassifier(
            hidden_layer_sizes=(self.hidden_units,),
            activation="relu",
            solver="lbfgs",
            alpha=self.alpha,
            max_iter=4000,
            random_state=0,
        )
        self.threshold = 0.5
        self.fitted = False

    def fit(
        self,
        examples: Iterable[KindTrainingExample],
    ) -> "TinyNeuralOpenSetStructureFormer":
        examples = list(examples)
        texts = [e.text for e in examples]
        is_known = [0 if e.kind == IRKind.UNKNOWN else 1 for e in examples]

        known_features = self.known_vectorizer.fit_transform(texts)
        self.known_detector.fit(known_features, is_known)

        supported = [e for e in examples if e.kind != IRKind.UNKNOWN]
        kind_features = self.kind_vectorizer.fit_transform(
            [e.text for e in supported]
        )
        self.kind_classifier.fit(
            kind_features,
            [e.kind.value for e in supported],
        )
        self.fitted = True
        return self

    def _require_fitted(self) -> None:
        if not self.fitted:
            raise RuntimeError("fit before neural proposal inference")

    def known_probability(self, text: str) -> float:
        self._require_fitted()
        features = self.known_vectorizer.transform([text])
        probabilities = self.known_detector.predict_proba(features)[0]
        classes = list(self.known_detector.classes_)
        return float(probabilities[classes.index(1)])

    def predict_supported_kind(self, text: str) -> IRKind:
        self._require_fitted()
        features = self.kind_vectorizer.transform([text])
        probabilities = self.kind_classifier.predict_proba(features)[0]
        index = int(probabilities.argmax())
        return IRKind(str(self.kind_classifier.classes_[index]))

    def predict_kind(self, text: str) -> tuple[IRKind, float]:
        self._require_fitted()
        known_probability = self.known_probability(text)
        if known_probability < self.threshold:
            return IRKind.UNKNOWN, 1.0 - known_probability

        features = self.kind_vectorizer.transform([text])
        probabilities = self.kind_classifier.predict_proba(features)[0]
        index = int(probabilities.argmax())
        kind = IRKind(str(self.kind_classifier.classes_[index]))
        confidence = min(known_probability, float(probabilities[index]))
        return kind, confidence

    def tune_threshold(
        self,
        validation: Sequence[tuple[str, IRKind, str]],
    ) -> NeuralOpenSetMetrics:
        """Choose maximum observed known coverage with zero validation routes.

        This is a finite validation rule for the controlled research corpus. It is
        not a calibrated statistical guarantee for open-world deployment.
        """
        self._require_fitted()
        candidates = [index / 100 for index in range(25, 81)]
        best: NeuralOpenSetMetrics | None = None
        known_count = sum(
            expected != IRKind.UNKNOWN for _, expected, _ in validation
        )
        unknown_count = sum(
            expected == IRKind.UNKNOWN for _, expected, _ in validation
        )

        for threshold in candidates:
            known_accept = 0
            wrong_known = 0
            false_unknown = 0

            for text, expected, _ in validation:
                probability = self.known_probability(text)
                if expected != IRKind.UNKNOWN and probability >= threshold:
                    known_accept += 1
                    if self.predict_supported_kind(text) != expected:
                        wrong_known += 1
                if expected == IRKind.UNKNOWN and probability >= threshold:
                    false_unknown += 1

            coverage = (
                known_accept / known_count if known_count else 0.0
            )
            false_rate = (
                false_unknown / unknown_count if unknown_count else 0.0
            )

            if false_unknown == 0 and wrong_known == 0:
                candidate = NeuralOpenSetMetrics(
                    threshold=threshold,
                    known_coverage=coverage,
                    unknown_false_route_rate=false_rate,
                )
                if (
                    best is None
                    or candidate.known_coverage > best.known_coverage
                    or (
                        candidate.known_coverage == best.known_coverage
                        and candidate.threshold < best.threshold
                    )
                ):
                    best = candidate

        if best is None:
            best = NeuralOpenSetMetrics(
                threshold=0.80,
                known_coverage=0.0,
                unknown_false_route_rate=0.0,
            )

        self.threshold = best.threshold
        return best
