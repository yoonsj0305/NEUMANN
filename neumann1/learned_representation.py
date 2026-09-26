from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

from .types import Problem, Representation, IRKind, CostLedger


@dataclass
class KindTrainingExample:
    text: str
    kind: IRKind


class LearnedKindStructureFormer:
    """Small learned classifier for structure *kind* only.

    It intentionally does NOT parse arbitrary natural language into a complete IR.
    For controlled research fixtures, solver payloads are supplied independently in
    problem.metadata['payload_by_kind']. This isolates one research question:
    can a small learned model recognize the structural family under surface change?
    """

    def __init__(self, min_payload_confidence: float = 0.0):
        word = TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True, sublinear_tf=True)
        char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, lowercase=True, sublinear_tf=True)
        self.vectorizer = FeatureUnion([("word", word), ("char", char)])
        self.model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
        self.fitted = False
        self.min_payload_confidence = min_payload_confidence

    def fit(self, examples: Iterable[KindTrainingExample]) -> "LearnedKindStructureFormer":
        examples = list(examples)
        X = [e.text for e in examples]
        y = [e.kind.value for e in examples]
        Z = self.vectorizer.fit_transform(X)
        self.model.fit(Z, y)
        self.fitted = True
        return self

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        if not self.fitted:
            raise RuntimeError("LearnedKindStructureFormer must be fit before use")
        ledger.representation_steps += 1
        Z = self.vectorizer.transform([problem.raw_text])
        probs = self.model.predict_proba(Z)[0]
        idx = int(probs.argmax())
        label = str(self.model.classes_[idx])
        confidence = float(probs[idx])
        kind = IRKind(label)
        payloads = problem.metadata.get("payload_by_kind", {})
        payload = payloads.get(label, {})

        if kind != IRKind.UNKNOWN and not payload:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=confidence,
                rationale=f"learned_kind={label}, but no independent payload supplied",
            )

        return Representation(
            kind=kind,
            payload=payload,
            confidence=confidence,
            rationale=f"learned TF-IDF logistic classifier; predicted={label}",
        )


class KeywordKindBaseline:
    """Deliberately simple non-learned baseline for surface-shift comparison."""

    def predict(self, text: str) -> IRKind:
        t = text.lower()
        if any(k in t for k in ("shortest", "route", "path", "distance")):
            return IRKind.SHORTEST_PATH
        if any(k in t for k in ("assign", "assignment", "slot", "job", "worker", "matching")):
            return IRKind.BIPARTITE_MATCHING
        if any(k in t for k in ("equation", "solve x", "solve for x", "simultaneous", "linear system")):
            return IRKind.LINEAR_SYSTEM
        return IRKind.UNKNOWN
