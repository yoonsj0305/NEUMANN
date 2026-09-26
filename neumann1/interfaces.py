from __future__ import annotations
from typing import Protocol, Any
from .types import Problem, Representation, VerificationResult, CostLedger


class StructureFormer(Protocol):
    def form(self, problem: Problem, ledger: CostLedger) -> Representation: ...


class Solver(Protocol):
    name: str
    def supports(self, representation: Representation) -> bool: ...
    def solve(self, representation: Representation, ledger: CostLedger) -> Any: ...


class Verifier(Protocol):
    def verify(
        self,
        problem: Problem,
        representation: Representation,
        answer: Any,
        ledger: CostLedger,
    ) -> VerificationResult: ...
