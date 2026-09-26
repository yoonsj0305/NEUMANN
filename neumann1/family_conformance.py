from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .types import Problem, CostLedger, is_unknown_kind, kind_id
from .family_registry import FamilyAdapter


@dataclass(frozen=True)
class ConformanceResult:
    family_id: str
    valid_total: int
    valid_compiled: int
    valid_solved_verified: int
    reject_total: int
    reject_fail_closed: int

    @property
    def valid_compile_rate(self) -> float:
        return self.valid_compiled / self.valid_total if self.valid_total else 1.0

    @property
    def valid_verified_rate(self) -> float:
        return (
            self.valid_solved_verified / self.valid_total if self.valid_total else 1.0
        )

    @property
    def reject_fail_closed_rate(self) -> float:
        return (
            self.reject_fail_closed / self.reject_total if self.reject_total else 1.0
        )


def run_family_conformance(
    adapter: FamilyAdapter,
    valid_texts: Sequence[str],
    reject_texts: Sequence[str],
) -> ConformanceResult:
    valid_compiled = 0
    valid_verified = 0

    for text in valid_texts:
        problem = Problem(text)
        ledger = CostLedger()
        rep = adapter.compiler.form(problem, ledger)
        try:
            same_kind = kind_id(rep.kind) == adapter.canonical_kind_id
        except (TypeError, ValueError):
            same_kind = False
        if not same_kind:
            continue
        valid_compiled += 1

        if not adapter.solver.supports(rep):
            continue
        answer = adapter.solver.solve(rep, ledger)
        vr = adapter.answer_verifier.verify(problem, rep, answer, ledger)
        if vr.ok:
            valid_verified += 1

    reject_fail_closed = 0
    for text in reject_texts:
        rep = adapter.compiler.form(Problem(text), CostLedger())
        if is_unknown_kind(rep.kind):
            reject_fail_closed += 1

    return ConformanceResult(
        family_id=adapter.family_id,
        valid_total=len(valid_texts),
        valid_compiled=valid_compiled,
        valid_solved_verified=valid_verified,
        reject_total=len(reject_texts),
        reject_fail_closed=reject_fail_closed,
    )
