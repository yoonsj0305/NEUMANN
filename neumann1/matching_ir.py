from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable

from .types import Problem, Representation, IRKind, CostLedger, VerificationResult


_IDENTIFIER = re.compile(r"^[A-Za-z0-9_\-]+$")
_EDGE_PATTERNS = [
    re.compile(r"^\s*(?P<left>[A-Za-z0-9_\-]+)\s+can\s+(?:use|take|connect\s+to|be\s+assigned\s+to)\s+(?P<rights>.+?)\s*$", re.I),
    re.compile(r"^\s*(?P<left>[A-Za-z0-9_\-]+)\s+may\s+be\s+assigned\s+to\s+(?P<rights>.+?)\s*$", re.I),
    re.compile(r"^\s*allowed\s+for\s+(?P<left>[A-Za-z0-9_\-]+)\s*:\s*(?P<rights>.+?)\s*$", re.I),
]
_UNSUPPORTED_SEMANTIC_MARKERS = re.compile(
    r"\b(?:not|except|unless|only if|at least|at most|exactly|prefer|cost|weight|capacity)\b",
    re.I,
)


@dataclass(frozen=True)
class MatchingParseDiagnostics:
    statements_seen: int
    statements_parsed: int
    duplicate_lefts: tuple[str, ...] = ()
    rejected_reason: str | None = None


def _split_rights(text: str) -> list[str]:
    text = re.sub(r"\band\b", ",", text, flags=re.I)
    text = re.sub(r"\bor\b", ",", text, flags=re.I)
    values = [x.strip(" .") for x in text.split(",")]
    return [x for x in values if x]


def _validate_rights(rights: Iterable[str]) -> list[str]:
    out: list[str] = []
    for value in rights:
        if not _IDENTIFIER.match(value):
            raise ValueError(f"unsupported right-side token: {value!r}")
        if value not in out:
            out.append(value)
    if not out:
        raise ValueError("matching statement has no usable right-side identifiers")
    return out


def parse_controlled_matching_with_diagnostics(text: str) -> tuple[dict[str, list[str]], MatchingParseDiagnostics]:
    edges: dict[str, list[str]] = {}
    duplicate_lefts: list[str] = []
    statements = [chunk.strip() for chunk in re.split(r"[;\n]+", text) if chunk.strip()]

    if not statements:
        raise ValueError("empty controlled matching input")

    for statement in statements:
        if _UNSUPPORTED_SEMANTIC_MARKERS.search(statement):
            raise ValueError("unsupported matching semantics detected; fail closed")

        matched = False
        for pattern in _EDGE_PATTERNS:
            m = pattern.match(statement)
            if not m:
                continue
            matched = True
            left = m.group("left")
            rights = _validate_rights(_split_rights(m.group("rights")))

            if left in edges:
                duplicate_lefts.append(left)
                if sorted(edges[left]) != sorted(rights):
                    raise ValueError(f"conflicting repeated statement for {left}; fail closed")
            else:
                edges[left] = rights
            break

        if not matched:
            raise ValueError(f"unparsed nonempty statement: {statement!r}")

    if len(edges) < 2 or not any(edges.values()):
        raise ValueError("controlled matching grammar not recognized")

    diagnostics = MatchingParseDiagnostics(
        statements_seen=len(statements),
        statements_parsed=len(statements),
        duplicate_lefts=tuple(sorted(set(duplicate_lefts))),
        rejected_reason=None,
    )
    return edges, diagnostics


def parse_controlled_matching(text: str) -> dict[str, list[str]]:
    edges, _ = parse_controlled_matching_with_diagnostics(text)
    return edges


class ControlledMatchingStructureFormer:
    """Compile a narrow matching text grammar into complete solver-ready IR.

    v0.0.8 fails closed when any nonempty statement is unparsed, when repeated
    left-side statements conflict, or when unsupported semantics such as
    negation/cost/capacity appear. This is still a compiler scaffold, not a
    general natural-language model.
    """

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        try:
            edges, diagnostics = parse_controlled_matching_with_diagnostics(problem.raw_text)
        except ValueError as exc:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale=str(exc),
            )
        right = sorted({v for values in edges.values() for v in values})
        return Representation(
            kind=IRKind.BIPARTITE_MATCHING,
            payload={
                "left": list(edges),
                "right": right,
                "edges": edges,
                "diagnostics": {
                    "statements_seen": diagnostics.statements_seen,
                    "statements_parsed": diagnostics.statements_parsed,
                    "duplicate_lefts": list(diagnostics.duplicate_lefts),
                },
            },
            confidence=1.0,
            rationale="controlled matching grammar compiled to solver-ready IR with fail-closed diagnostics",
        )


@dataclass(frozen=True)
class MatchingSemanticContract:
    expected_edges: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class MatchingEdgeMetrics:
    true_positive: int
    false_positive: int
    false_negative: int

    @property
    def precision(self) -> float:
        denom = self.true_positive + self.false_positive
        return self.true_positive / denom if denom else 1.0

    @property
    def recall(self) -> float:
        denom = self.true_positive + self.false_negative
        return self.true_positive / denom if denom else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def edge_metrics(expected_edges: dict[str, Iterable[str]], actual_edges: dict[str, Iterable[str]]) -> MatchingEdgeMetrics:
    expected = {(left, right) for left, rights in expected_edges.items() for right in rights}
    actual = {(left, right) for left, rights in actual_edges.items() for right in rights}
    return MatchingEdgeMetrics(
        true_positive=len(expected & actual),
        false_positive=len(actual - expected),
        false_negative=len(expected - actual),
    )


class MatchingSemanticVerifier:
    """Independent benchmark-side semantic checker for controlled matching fixtures."""

    def verify_representation(self, problem: Problem, representation: Representation, ledger: CostLedger) -> VerificationResult:
        contract = problem.metadata.get("matching_semantic_contract")
        ledger.verification_steps += 1
        if not contract:
            return VerificationResult(False, "missing matching semantic contract")
        if representation.kind != IRKind.BIPARTITE_MATCHING:
            return VerificationResult(False, "wrong representation kind")

        expected = {k: sorted(v) for k, v in contract["expected_edges"].items()}
        actual = {k: sorted(v) for k, v in representation.payload.get("edges", {}).items()}
        ledger.verification_steps += sum(len(v) for v in expected.values())
        if actual != expected:
            metrics = edge_metrics(expected, actual)
            return VerificationResult(
                False,
                f"edge semantics differ: precision={metrics.precision:.3f}, recall={metrics.recall:.3f}",
            )
        return VerificationResult(True, "matching representation faithful to contract")
