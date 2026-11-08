from __future__ import annotations
from typing import Iterable
from .types import Problem, SolveResult, CostLedger, IRKind
from .interfaces import StructureFormer, Solver, Verifier
from .structural_meta_invention import StructuralMetaInventor, CertifiedProgram


class NeumannEngine:
    def __init__(self, structure_former: StructureFormer, solvers: Iterable[Solver], verifier: Verifier, min_confidence: float = 0.8, *, meta_inventor: StructuralMetaInventor | None = None):
        self.structure_former = structure_former
        self.solvers = list(solvers)
        self.verifier = verifier
        self.min_confidence = min_confidence
        # Persist learned executable method-constructors across solve calls.
        self.meta_inventor = meta_inventor if meta_inventor is not None else StructuralMetaInventor()

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

    def observe_program(self, evidence: CertifiedProgram, *, verify):
        """Improve the live discovery METHOD INVENTORY from original-certified code."""
        return self.meta_inventor.observe(evidence, verify=verify)

    def invent_program(self, family: str, arity: int, *, params=(), verify=None, promote=True):
        """Generate a program using learned methods; never bypass original checking.

        A verified solution can become new training evidence and automatically
        induce another constructor method, not just grow a program cache.
        """
        return self.meta_inventor.solve(
            family, arity, params=params, verify=verify, promote=promote)
