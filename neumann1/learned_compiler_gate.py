from __future__ import annotations
from typing import Mapping

from .types import Problem, Representation, IRKind, CostLedger


class LearnedProposalCompilerGate:
    """Use a learned model only to propose a structural family.

    The proposal never becomes solver-ready authority by itself. A deterministic
    family compiler must independently accept the raw text and emit an IR whose
    kind agrees with the proposal. Otherwise the system fails closed to UNKNOWN.
    """

    def __init__(self, proposer: object, compilers: Mapping[IRKind, object]):
        self.proposer = proposer
        self.compilers = dict(compilers)

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        proposed_kind, proposal_confidence = self.proposer.predict_kind(problem.raw_text)

        if proposed_kind == IRKind.UNKNOWN:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=proposal_confidence,
                rationale="learned proposer abstained; fail closed",
            )

        compiler = self.compilers.get(proposed_kind)
        if compiler is None:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale=f"proposed family {proposed_kind.value} has no authorized compiler",
            )

        local = CostLedger()
        compiled = compiler.form(problem, local)
        ledger.representation_steps += local.representation_steps

        if compiled.kind == IRKind.UNKNOWN:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale=(
                    f"proposal={proposed_kind.value} rejected by deterministic compiler: "
                    f"{compiled.rationale}"
                ),
            )

        if compiled.kind != proposed_kind:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale=(
                    f"proposal/compiler disagreement: proposed={proposed_kind.value}, "
                    f"compiled={compiled.kind.value}"
                ),
            )

        return Representation(
            kind=compiled.kind,
            payload=compiled.payload,
            confidence=min(float(proposal_confidence), float(compiled.confidence)),
            rationale=(
                f"learned proposal={proposed_kind.value} accepted by "
                f"{compiler.__class__.__name__}"
            ),
        )
