from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion

from .types import Problem, Representation, IRKind, CostLedger
from .learned_representation import KindTrainingExample


def _features():
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)),
    ])


@dataclass
class PrototypeMetrics:
    similarity_threshold: float
    known_coverage: float
    unknown_false_route_rate: float


class PrototypeOpenSetStructureFormer:
    """Centroid-similarity open-set baseline.

    Each supported structural family is represented by a centroid in TF-IDF space.
    A query is routed only when its maximum cosine similarity to a class centroid is
    above a tuned threshold.
    """

    def __init__(self):
        self.vectorizer = _features()
        self.class_labels: list[str] = []
        self.centroids = None
        self.threshold = 0.0
        self.fitted = False

    def fit(self, examples: Iterable[KindTrainingExample]) -> "PrototypeOpenSetStructureFormer":
        known = [e for e in examples if e.kind != IRKind.UNKNOWN]
        texts = [e.text for e in known]
        labels = [e.kind.value for e in known]
        X = self.vectorizer.fit_transform(texts)
        self.class_labels = sorted(set(labels))
        centroids = []
        for label in self.class_labels:
            idx = [i for i, y in enumerate(labels) if y == label]
            centroids.append(np.asarray(X[idx].mean(axis=0)).ravel())
        self.centroids = np.vstack(centroids)
        self.fitted = True
        return self

    def score(self, text: str) -> tuple[IRKind, float, float]:
        if not self.fitted:
            raise RuntimeError("fit before score")
        X = self.vectorizer.transform([text])
        sims = cosine_similarity(X, self.centroids)[0]
        order = np.argsort(sims)[::-1]
        top = int(order[0])
        top_sim = float(sims[top])
        second = float(sims[order[1]]) if len(order) > 1 else 0.0
        margin = top_sim - second
        return IRKind(self.class_labels[top]), top_sim, margin

    def tune_threshold(self, validation: Sequence[tuple[str, IRKind, str]]) -> PrototypeMetrics:
        candidates = [i / 100 for i in range(5, 81)]
        known_n = sum(expected != IRKind.UNKNOWN for _, expected, _ in validation)
        unknown_n = sum(expected == IRKind.UNKNOWN for _, expected, _ in validation)
        best = None
        for th in candidates:
            known_accept = 0
            wrong_known = 0
            false_unknown = 0
            for text, expected, _ in validation:
                raw_kind, sim, _ = self.score(text)
                if expected != IRKind.UNKNOWN and sim >= th:
                    known_accept += 1
                    if raw_kind != expected:
                        wrong_known += 1
                if expected == IRKind.UNKNOWN and sim >= th:
                    false_unknown += 1
            coverage = known_accept / known_n if known_n else 0.0
            false_rate = false_unknown / unknown_n if unknown_n else 0.0
            if false_unknown == 0 and wrong_known == 0:
                cand = PrototypeMetrics(th, coverage, false_rate)
                if best is None or cand.known_coverage > best.known_coverage or (
                    cand.known_coverage == best.known_coverage and cand.similarity_threshold < best.similarity_threshold
                ):
                    best = cand
        if best is None:
            best = PrototypeMetrics(0.80, 0.0, 0.0)
        self.threshold = best.similarity_threshold
        return best

    def predict_kind(self, text: str) -> tuple[IRKind, float]:
        kind, sim, _ = self.score(text)
        if sim < self.threshold:
            return IRKind.UNKNOWN, 1.0 - sim
        return kind, sim

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        kind, confidence = self.predict_kind(problem.raw_text)
        if kind == IRKind.UNKNOWN:
            return Representation(kind=kind, payload={}, confidence=confidence, rationale="prototype-distance rejection")
        payloads = problem.metadata.get("payload_by_kind", {})
        payload = payloads.get(kind.value, {})
        if not payload:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=confidence,
                rationale=f"prototype predicted {kind.value} but no independent payload supplied",
            )
        return Representation(
            kind=kind,
            payload=payload,
            confidence=confidence,
            rationale=f"prototype centroid threshold={self.threshold:.2f}",
        )
