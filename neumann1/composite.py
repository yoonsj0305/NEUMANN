from __future__ import annotations
from typing import Iterable

from .types import Problem, Representation, IRKind, CostLedger


class CompositeStructureFormer:
    """Try multiple fail-closed family compilers and accept exactly one recognized IR.

    If zero families recognize the input, return UNKNOWN.
    If more than one family recognizes it, return UNKNOWN rather than guessing.
    """

    def __init__(self, formers: Iterable[object]):
        self.formers = list(formers)

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        recognized: list[Representation] = []
        rationales: list[str] = []

        for former in self.formers:
            local = CostLedger()
            rep = former.form(problem, local)
            ledger.representation_steps += local.representation_steps
            rationales.append(f"{former.__class__.__name__}: {rep.rationale}")
            if rep.kind != IRKind.UNKNOWN:
                recognized.append(rep)

        if len(recognized) == 1:
            return recognized[0]
        if len(recognized) == 0:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="no controlled family recognized input | " + " | ".join(rationales),
            )
        return Representation(
            kind=IRKind.UNKNOWN,
            payload={},
            confidence=0.0,
            rationale="ambiguous multi-family recognition; fail closed",
        )
