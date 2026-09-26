from __future__ import annotations

from .types import Problem, SolveResult, CostLedger, IRKind
from .family_registry import FamilyRegistry


class RegistryEngine:
    """Execute a solver-ready IR through the adapter registered for its family."""

    def __init__(
        self,
        structure_former: object,
        registry: FamilyRegistry,
        min_confidence: float = 0.8,
    ):
        self.structure_former = structure_former
        self.registry = registry
        self.min_confidence = min_confidence

    def solve(self, problem: Problem) -> SolveResult:
        ledger = CostLedger()
        trace: list[str] = []

        rep = self.structure_former.form(problem, ledger)
        trace.append(f"representation={rep.kind.value} confidence={rep.confidence:.3f}")

        if rep.kind == IRKind.UNKNOWN or rep.confidence < self.min_confidence:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason="Representation unknown or below confidence threshold",
                ledger=ledger,
                trace=trace + ["fail_closed"],
            )

        adapter = self.registry.get(rep.kind)
        if adapter is None:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason=f"No registered family adapter for {rep.kind.value}",
                ledger=ledger,
                trace=trace + ["unregistered_family_fail_closed"],
            )

        if not adapter.solver.supports(rep):
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason="Registered family solver rejected its representation",
                ledger=ledger,
                trace=trace + ["solver_contract_fail_closed"],
            )

        trace.append(f"family={adapter.family_id}")
        trace.append(f"solver={adapter.solver.name}")
        answer = adapter.solver.solve(rep, ledger)
        vr = adapter.answer_verifier.verify(problem, rep, answer, ledger)
        trace.append(f"verified={vr.ok}")

        return SolveResult(
            answer=answer,
            representation=rep,
            solver_name=adapter.solver.name,
            verified=vr.ok,
            verification_reason=vr.reason,
            ledger=ledger,
            trace=trace,
        )
