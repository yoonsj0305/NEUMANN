from __future__ import annotations
from typing import Iterable
from .types import Problem, SolveResult, CostLedger, IRKind
from .interfaces import StructureFormer, Solver, Verifier


class NeumannEngine:
    def __init__(self, structure_former: StructureFormer, solvers: Iterable[Solver], verifier: Verifier, min_confidence: float = 0.8):
        self.structure_former = structure_former
        self.solvers = list(solvers)
        self.verifier = verifier
        self.min_confidence = min_confidence

    def solve(self, problem: Problem) -> SolveResult:
        ledger = CostLedger()
        trace = []
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

        solver = next((s for s in self.solvers if s.supports(rep)), None)
        if solver is None:
            ledger.fallback_steps += 1
            return SolveResult(
                answer=None,
                representation=rep,
                solver_name="fallback_required",
                verified=False,
                verification_reason="No compatible deterministic solver",
                ledger=ledger,
                trace=trace + ["no_solver_fail_closed"],
            )

        trace.append(f"solver={solver.name}")
        answer = solver.solve(rep, ledger)
        vr = self.verifier.verify(problem, rep, answer, ledger)
        trace.append(f"verified={vr.ok}")
        return SolveResult(
            answer=answer,
            representation=rep,
            solver_name=solver.name,
            verified=vr.ok,
            verification_reason=vr.reason,
            ledger=ledger,
            trace=trace,
        )
