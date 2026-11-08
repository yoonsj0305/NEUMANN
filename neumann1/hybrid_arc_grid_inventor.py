"""NEUMANN ARC grid: hybrid of discovered relational methods and prior DSL.

This is a production integration path, NOT an oracle selector. It selects
up to TWO candidate programs using only each original task's training
examples. Target gold cannot affect representation choice or routing.

The older 626-program baseline keeps its previous full-language search
rights. Complementary new methods are introduced without deleting the old
solver's correct solutions when the new representation has no demo fit.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter_ns
from .relational_grid_inventor import RelationalGridInventor,grid
from . import arc2_meta_grid_reasoner as old

@dataclass(frozen=True)
class GridCandidate:
    origin: str
    program_id: int|None
    outputs: tuple
    expression: dict|None

@dataclass(frozen=True)
class GridHybridResult:
    candidates: tuple[GridCandidate,...]
    new_source_fit: bool
    old_source_fit: bool
    old_candidate_checks: int
    new_search_ms: float
    old_search_ms: float
    total_search_ms: float
    source_examples: int
    max_attempts: int

    def chosen(self):
        return tuple(c.outputs for c in self.candidates)

class HybridArcGridInventor:
    def __init__(self,max_attempts=2):
        if type(max_attempts) is not int or max_attempts!=2:
            raise ValueError("ARC2 original scoring requires 2 output attempts")
        self.max_attempts=max_attempts
        self.relational=RelationalGridInventor()

    def solve(self,source_pairs,target_inputs):
        t0=perf_counter_ns()
        demo=[(grid(x),grid(y)) for x,y in source_pairs]
        target=[grid(x) for x in target_inputs]
        if not demo or not target:raise ValueError("source demonstrations and target inputs required")
        t=perf_counter_ns()
        result=self.relational.solve(demo)
        new_outputs=tuple(self.relational.apply(result,g) for g in target)
        elapsed_new=(perf_counter_ns()-t)/1e6
        t=perf_counter_ns()
        baseline,index_checks=old.fit_task(
            demo,range(len(old.PROGRAMS)),len(old.PROGRAMS),
            max_hits=len(old.PROGRAMS))
        # A recoloring adapter has up to 10 additional fitted variables.
        # If an exact geometric transformation exists, it is strictly
        # simpler and more likely to survive unseen input colors. The old
        # interpreter used first-two syntax enumeration and overfit such
        # examples (e.g. synthetic rotation with disjoint palettes).
        baseline=sorted(baseline,
            key=lambda item:(item[1]["kind"]!="exact",
                             len(old.PROGRAMS[item[0]]),item[0]))[:2]
        old_programs=[]
        for idx,adapter in baseline:
            pred=[]
            for g in target:
                obj=old.predict(g,old.PROGRAMS[idx])
                if obj is not None and adapter["kind"]=="recolor":
                    obj=old.recolor(obj,adapter["mapping"])
                pred.append(obj)
            old_programs.append(
                GridCandidate("prior_626_programs",int(idx),tuple(pred),None))
        elapsed_old=(perf_counter_ns()-t)/1e6
        candidate_pool=[]
        if result.source_fit and all(x is not None for x in new_outputs):
            candidate_pool.append(GridCandidate(
                "self_invented_relational_rule",None,new_outputs,result.method))
        candidate_pool.extend(old_programs)
        # Duplicate predictions are deleted before charging the limited
        # two-attempt interface. Both programs are still cost-accounted.
        distinct=[];seen=set()
        for cand in candidate_pool:
            key=cand.outputs
            if key in seen:continue
            seen.add(key);distinct.append(cand)
            if len(distinct)==self.max_attempts:break
        return GridHybridResult(
            candidates=tuple(distinct),
            new_source_fit=bool(result.source_fit),
            old_source_fit=bool(baseline),
            old_candidate_checks=index_checks,
            new_search_ms=round(elapsed_new,5),
            old_search_ms=round(elapsed_old,5),
            total_search_ms=round((perf_counter_ns()-t0)/1e6,5),
            source_examples=len(demo),
            max_attempts=self.max_attempts)
