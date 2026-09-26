from __future__ import annotations
from .types import Problem, Representation, IRKind, CostLedger


class ExplicitStructureFormer:
    """Research scaffold.

    v0.0.1 intentionally does NOT pretend to understand arbitrary natural language.
    It accepts a candidate IR supplied in problem.metadata['candidate_ir'] and turns
    the execution/runtime side of NEUMANN into a testable system. The learned or LLM
    Structure Former is a later research component.
    """

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        ir = problem.metadata.get("candidate_ir")
        if not ir:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="No candidate IR supplied; fail closed.",
            )
        kind = IRKind(ir["kind"])
        return Representation(
            kind=kind,
            payload=ir.get("payload", {}),
            confidence=float(ir.get("confidence", 1.0)),
            rationale=ir.get("rationale", "explicit research scaffold"),
        )
