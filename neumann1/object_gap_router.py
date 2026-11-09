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
from .scene_graph_inventor import ObjectGrammarInventor
from .relational_action_inventor import RelationalActionInventor, RelationalAction
from .parallel_object_edit_inventor import ParallelObjectEditInventor, BulkEditProgram
from .topological_region_inventor import TopologicalRegionInventor


@dataclass(frozen=True)
class ObjectGapResult:
    origin: str
    candidates: tuple[tuple, ...]
    invented_programs: tuple[object, ...]
    object_inventor_invocations: int
    source_checks: int
    classical_source_verified: bool
    elapsed_ms: float

    @property
    def solved_source(self):
        return bool(self.candidates)


class ObjectGapRouter:
    def __init__(self,*,max_relational_ms=120,max_object_ms=350,
                 max_causal_ms=350,max_bulk_ms=350,
                 known_causal_rules=(),known_bulk_rules=()):
        if (not 1<=max_relational_ms<=5000 or
                not 1<=max_object_ms<=120000 or
                not 1<=max_causal_ms<=120000 or
                not 1<=max_bulk_ms<=120000):
            raise ValueError("finite execution caps required")
        self.max_relational_ms=max_relational_ms
        self.max_object_ms=max_object_ms
        self.max_causal_ms=max_causal_ms
        self.max_bulk_ms=max_bulk_ms
        self.known_bulk_rules=tuple(known_bulk_rules)
        if any(not isinstance(p,BulkEditProgram) for p in self.known_bulk_rules):
            raise TypeError('remembered bulk programs must be typed')
        self.known_causal_rules=tuple(known_causal_rules)
        if any(not isinstance(p,RelationalAction)
               for p in self.known_causal_rules):
            raise TypeError('known causal programs must be typed and verifiable')

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
        # A previously SOURCE-VERIFIED invented operator may be reused as an
        # executable law, but only after the classical source-verifier fails.
        # Recheck the learned law on the NEW task's original source data:
        # source-driven transfer, not answer caching or unverified imitation.
        for remembered in self.known_causal_rules:
            try:
                if not all(remembered.apply(x)==y
                           for x,y in demonstrations+verified):
                    continue
                predicted=tuple(remembered.apply(x) for x in targets)
                if any(x is None for x in predicted):
                    continue
                return ObjectGapResult(
                    "SOURCE_VERIFIED_REUSED_CAUSAL_RELATION",
                    (predicted,), (remembered,),
                    0,0,False,(perf_counter_ns()-start)/1e6)
            except (ValueError,TypeError):
                continue
        for remembered in self.known_bulk_rules:
            try:
                if not all(remembered.apply(x)==y
                           for x,y in demonstrations+verified):
                    continue
                predicted=tuple(remembered.apply(x) for x in targets)
                if any(x is None for x in predicted):continue
                return ObjectGapResult(
                    "SOURCE_VERIFIED_REUSED_BULK_RULE",
                    (predicted,),(remembered,),0,0,False,
                    (perf_counter_ns()-start)/1e6)
            except (ValueError,TypeError):
                continue
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
        if predictions:
            return ObjectGapResult(
                "SOURCE_VERIFIED_NEW_OBJECT_RULE",tuple(predictions),
                tuple(accepted),1,invented.source_checks,False,
                (perf_counter_ns()-start)/1e6)
        # Discover an entirely different executable grammar: transfer one
        # entity's pixels under a causal positional relation to another.
        # This is only activated after two stronger original source
        # grammars failed; it cannot contaminate a solved classical case.
        causal=RelationalActionInventor(
            max_source_ms=self.max_causal_ms).invent(
                demonstrations,verification=verified,max_rules=2)
        for p in causal.rules:
            try:
                trial=tuple(p.apply(x) for x in targets)
            except (ValueError,TypeError):
                continue
            if any(y is None for y in trial):continue
            if trial not in predictions:
                predictions.append(trial)
                accepted.append(p)
            if len(predictions)==2:break
        if predictions:
            return ObjectGapResult(
                "SOURCE_VERIFIED_NEW_CAUSAL_RELATION",
                tuple(predictions),tuple(accepted),2,
                invented.source_checks+causal.witness_signatures,False,
                (perf_counter_ns()-start)/1e6)
        # A new language for mapping a learned predicate over MANY objects.
        # Unlike a one-object source action, this may recolor or delete
        # an arbitrary number of objects in a single learned program.
        bulk=ParallelObjectEditInventor(
            max_source_ms=self.max_bulk_ms).invent(
                demonstrations,verification=verified,max_programs=2)
        for p in bulk.programs:
            try:
                trial=tuple(p.apply(x) for x in targets)
            except (ValueError,TypeError):
                continue
            if any(x is None for x in trial):continue
            if trial not in predictions:
                predictions.append(trial)
                accepted.append(p)
            if len(predictions)==2:break
        # Q3 capability gap: if all foreground-object grammars fail, seek
        # a new DUAL ontology whose entities are connected EMPTY REGIONS.
        # Do not pay this cost or override successful older algorithms.
        new_topology=False
        if not predictions:
            try:
                face=TopologicalRegionInventor(
                    max_source_ms=self.max_bulk_ms).invent(
                    demonstrations,independent_source_checks=verified)
                if face.operator is not None:
                    trial=tuple(face.operator.apply(x) for x in targets)
                    if all(x is not None for x in trial):
                        predictions.append(trial)
                        accepted.append(face.operator)
                        new_topology=True
            except (ValueError,TypeError,ArithmeticError):
                pass
        return ObjectGapResult(
            ("SOURCE_VERIFIED_NEW_FACE_GRAPH" if new_topology
             else "SOURCE_VERIFIED_NEW_BULK_RULE" if predictions
             else "ABSTAIN_UNSUPPORTED"),
            tuple(predictions),tuple(accepted),
            4 if new_topology else 3,
            invented.source_checks+causal.witness_signatures+
              bulk.evaluated_clauses,False,
            (perf_counter_ns()-start)/1e6)
