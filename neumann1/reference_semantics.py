from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from .types import Problem, Representation, VerificationResult, CostLedger
from .verifier import DeterministicVerifier


@dataclass(frozen=True)
class SemanticContract:
    """Benchmark-only oracle contract.

    This is NOT a production semantic parser. It exists so research fixtures can
    independently state what semantic structure the raw problem is expected to have.
    """
    expected_kind: str
    required_payload_keys: tuple[str, ...] = ()


class ReferenceSemanticVerifier:
    """Combines an oracle semantic contract with deterministic answer verification.

    The semantic contract must be supplied independently in benchmark metadata.
    This prevents v0.0.2 from pretending that answer-vs-IR verification proves that
    the IR faithfully represents the original natural-language problem.
    """

    def __init__(self):
        self.answer_verifier = DeterministicVerifier()

    def verify(self, problem: Problem, representation: Representation, answer: Any, ledger: CostLedger) -> VerificationResult:
        contract_data: Dict[str, Any] | None = problem.metadata.get("semantic_contract")
        if contract_data is None:
            return VerificationResult(False, "No independent semantic contract for benchmark fixture")

        ledger.verification_steps += 1
        expected_kind = contract_data["expected_kind"]
        if representation.kind.value != expected_kind:
            return VerificationResult(
                False,
                f"semantic kind mismatch: expected {expected_kind}, got {representation.kind.value}",
            )

        for key in contract_data.get("required_payload_keys", []):
            ledger.verification_steps += 1
            if key not in representation.payload:
                return VerificationResult(False, f"semantic contract missing payload key: {key}")

        return self.answer_verifier.verify(problem, representation, answer, ledger)
