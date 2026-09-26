from __future__ import annotations
import re
from dataclasses import dataclass

from .types import Problem, Representation, IRKind, CostLedger, VerificationResult


_EDGE_PATTERNS = [
    re.compile(r"^\s*(?P<left>[A-Za-z0-9_\-]+)\s+can\s+(?:use|take|connect\s+to|be\s+assigned\s+to)\s+(?P<rights>.+?)\s*$", re.I),
    re.compile(r"^\s*(?P<left>[A-Za-z0-9_\-]+)\s+may\s+be\s+assigned\s+to\s+(?P<rights>.+?)\s*$", re.I),
    re.compile(r"^\s*allowed\s+for\s+(?P<left>[A-Za-z0-9_\-]+)\s*:\s*(?P<rights>.+?)\s*$", re.I),
]


def _split_rights(text: str) -> list[str]:
    text = re.sub(r"\band\b", ",", text, flags=re.I)
    text = re.sub(r"\bor\b", ",", text, flags=re.I)
    values = [x.strip(" .") for x in text.split(",")]
    return [x for x in values if x]


def parse_controlled_matching(text: str) -> dict[str, list[str]]:
    edges: dict[str, list[str]] = {}
    for chunk in re.split(r"[;\n]+", text):
        statement = chunk.strip()
        if not statement:
            continue
        for pattern in _EDGE_PATTERNS:
            m = pattern.match(statement)
            if not m:
                continue
            left = m.group("left")
            rights = _split_rights(m.group("rights"))
            if rights:
                edges[left] = rights
            break
    if len(edges) < 2 or not any(edges.values()):
        raise ValueError("controlled matching grammar not recognized")
    return edges


class ControlledMatchingStructureFormer:
    """Compile a narrow matching text grammar into complete solver-ready IR.

    This is a compiler scaffold, not a general natural-language model.
    """

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        try:
            edges = parse_controlled_matching(problem.raw_text)
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
            payload={"left": list(edges), "right": right, "edges": edges},
            confidence=1.0,
            rationale="controlled matching grammar compiled to solver-ready IR",
        )


@dataclass(frozen=True)
class MatchingSemanticContract:
    expected_edges: dict[str, tuple[str, ...]]


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
            return VerificationResult(False, "edge semantics differ from independent contract")
        return VerificationResult(True, "matching representation faithful to contract")