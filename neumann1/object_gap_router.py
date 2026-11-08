"""Q3/Q4 source-only causal invention at a measured classical capability GAP.

Classical/previous strong composed ARC program grammar gets the same source
demonstrations and separate independent SOURCE verifier first. Only if
that prior method fails to pass source verification do we construct a
NEW object selection and rendering program. No original target outputs
can enter the interface. This hot path is conservative: a source-fitting
prior can still be wrong on test, but that is NOT justification to invoke
every inventor on every task.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from .composed_grid_inventor import ComposedGridInventor
from .relational_grid_inventor import grid
from .scene_graph_inventor import ObjectGrammarInventor, ObjectProgram


@dataclass(frozen=True)
class ObjectGapResult:
    origin: str
    candidates: tuple[tuple, ...]
    invented_programs: tuple[ObjectProgram, ...]
    object_inventor_invocations: int
    source_checks: int
    classical_source_verified: bool
    elapsed_ms: float

    @property
    def solved_source(self):
        return bool(self.candidates)


class ObjectGapRouter:
    def __init__(self,*,max_relational_ms=120,max_object_ms=350):
        if not 1<=max_relational_ms<=5000 or not 1<=max_object_ms<=120000:
            raise ValueError("finite execution caps required")
        self.max_relational_ms=max_relational_ms
        self.max_object_ms=max_object_ms

    def solve(self,source_examples,independent_source_checks,target_inputs):
        start=perf_counter_ns()
        demonstrations=tuple((grid(x),grid(y)) for x,y in source_examples)
        verified=tuple((grid(x),grid(y)) for x,y in independent_source_checks)
        targets=tuple(grid(x) for x in target_inputs)
        if len(demonstrations)<2 or not verified or not targets:
            raise ValueError("classical-first needs two source, independent verifier, target")
        # The prior source solver is its own classical/relational full grammar
        # comparator. It gets the same source input information, never test gold.
        verification_inputs=tuple(x for x,y in verified)
        prior=ComposedGridInventor(
            max_geometries=12,
            max_relational_ms=self.max_relational_ms).solve(
                demonstrations, verification_inputs+targets)
        certified=[]
        for prediction in prior.candidates:
            if any(prediction[i]!=answer
                   for i,(x,answer) in enumerate(verified)):
                continue
            attempt=tuple(prediction[len(verified):])
            if attempt not in certified:
                certified.append(attempt)
            if len(certified)==2:break
        if certified:
            return ObjectGapResult(
                "SOURCE_VERIFIED_PRIOR",tuple(certified),
                (),0,0,True,(perf_counter_ns()-start)/1e6)
        # The old language is insufficient on fresh source verification.
        # Only now spend computation on new object predicates and actions.
        invented=ObjectGrammarInventor(
            max_source_ms=self.max_object_ms).invent(
                demonstrations,verification=verified,max_programs=2)
        predictions=[]
        accepted=[]
        for p in invented.programs:
            trial=tuple(p.apply(x) for x in targets)
            if any(y is None for y in trial):continue
            if trial not in predictions:
                predictions.append(trial)
                accepted.append(p)
            if len(predictions)==2:break
        return ObjectGapResult(
            "SOURCE_VERIFIED_NEW_OBJECT_RULE" if predictions
            else "ABSTAIN_UNSUPPORTED",
            tuple(predictions),tuple(accepted),
            1,invented.source_checks,False,
            (perf_counter_ns()-start)/1e6)
