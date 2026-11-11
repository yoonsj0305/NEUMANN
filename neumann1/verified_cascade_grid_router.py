"""NEUMANN verification-gated lazy cascade (zero-investment routing).

Q4 root cause of the 2026-11-08 source-learned lazy router: a family ->
strategy table was LEARNED from 180 opened originals (24.77 s source cost),
which exceeded the inference it saved on 360 new originals, and the table
REFUSES every concept family it has not seen (no open-set route at all).

North Star: "Do not learn what can be derived more cheaply."  Whether an
engine has found a usable program is already DERIVABLE at test time, without
any oracle: its candidate either reproduces every TRAIN demonstration or not.
This router therefore spends zero source/training compute and needs no
family metadata:

    run the first engine in a fixed order
      - TRAIN-consistent candidate exists -> stop, never instantiate the rest
      - otherwise                         -> escalate to the next engine

Only TRAIN demonstrations and target INPUTS are visible.  Target outputs are
never passed in.  The same two-attempt cap as the hybrid applies.

Scope: the engines, their languages and the order are human designed.  This
is a cost-elimination mechanism, not autonomous representation invention.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter_ns
from .relational_grid_inventor import RelationalGridInventor, grid
from .hybrid_arc_grid_inventor import GridCandidate
from .classical_grid_fast import classical_candidates as _classical

ENGINES = ("relational", "classical")
# Classical first: on the opened 1D-ARC development corpus it is the cheaper
# engine after exact redundancy elimination, and a TRAIN-consistent classical
# program (short, low description length) was never wrong where the
# relational rule was right (0 lost vs hybrid); relational-first lost 16.
DEFAULT_ORDER = ("classical", "relational")


@dataclass(frozen=True)
class CascadeGridResult:
    order: tuple[str, ...]
    engines_run: tuple[str, ...]
    stopped_by: str | None
    candidates: tuple[GridCandidate, ...]
    engine_ms: tuple[tuple[str, float], ...]
    search_ms: float
    classical_program_checks: int
    relational_source_fit: bool
    classical_source_fit: bool
    max_attempts: int = 2


def _relational(demo, inputs):
    inventor = RelationalGridInventor()
    method = inventor.solve(demo)
    if not method.source_fit:
        return (), False
    outputs = tuple(inventor.apply(method, x) for x in inputs)
    if any(y is None for y in outputs):
        return (), True
    return (GridCandidate("self_invented_relational_rule", None, outputs,
                          method.method),), True


class VerifiedCascadeGridRouter:
    """Stop at the first engine whose program reproduces all TRAIN pairs."""

    def __init__(self, order=DEFAULT_ORDER, *, max_attempts=2):
        order = tuple(order)
        if (not order or len(set(order)) != len(order)
                or any(e not in ENGINES for e in order)):
            raise ValueError("order must be a non-empty permutation of engines")
        if max_attempts != 2:
            raise ValueError("fixed original two-attempt interface")
        self.order = order
        self.max_attempts = max_attempts

    def solve(self, source_pairs, target_inputs):
        start = perf_counter_ns()
        demo = [(grid(a), grid(b)) for a, b in source_pairs]
        inputs = [grid(a) for a in target_inputs]
        if not demo or not inputs:
            raise ValueError("nonempty original task required")
        pool, ran, timing = [], [], []
        checks, rel_fit, cls_fit, stopped = 0, False, False, None
        for engine in self.order:
            t = perf_counter_ns()
            if engine == "relational":
                found, rel_fit = _relational(demo, inputs)
            else:
                found, checks, cls_fit = _classical(demo, inputs,
                                                    self.max_attempts)
            ran.append(engine)
            timing.append((engine, round((perf_counter_ns() - t) / 1e6, 5)))
            pool.extend(found)
            if found:
                stopped = engine
                break
        distinct, seen = [], set()
        for cand in pool:
            if cand.outputs in seen:
                continue
            seen.add(cand.outputs)
            distinct.append(cand)
            if len(distinct) == self.max_attempts:
                break
        return CascadeGridResult(
            order=self.order, engines_run=tuple(ran), stopped_by=stopped,
            candidates=tuple(distinct), engine_ms=tuple(timing),
            search_ms=round((perf_counter_ns() - start) / 1e6, 5),
            classical_program_checks=checks,
            relational_source_fit=rel_fit, classical_source_fit=cls_fit,
            max_attempts=self.max_attempts)
