"""NEUMANN source-trained, lazy representation-routing in the core.

Discover a SEARCH STRATEGY (which representation to run), not a magic
task oracle. One selected strategy is frozen from disjoint source originals
per public concept family, and applied on untouched target originals.
Classical-only does not instantiate the costly relational generator;
relational-only does not enumerate 626 classical programs.

No target output is available to the routing code. The learned routing
strategy is purely metadata/source-calibrated and has the same 2-attempt cap.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter_ns
from .relational_grid_inventor import RelationalGridInventor,grid
from .hybrid_arc_grid_inventor import GridCandidate,GridHybridResult,HybridArcGridInventor
from . import arc2_meta_grid_reasoner as previous

STRATEGIES=("classical_only","relational_only","hybrid")
@dataclass(frozen=True)
class RoutedGridResult:
    strategy:str
    candidates:tuple[GridCandidate,...]
    search_ms:float
    classical_program_checks:int
    relational_source_fit:bool
    classical_source_fit:bool
    max_attempts:int=2

def _classical(demo,inputs,limit=2):
    # Output-identical exact elimination of redundant classical work.
    from .classical_grid_fast import fit_all
    matches,checks=fit_all(demo)
    # Exact source symmetries take precedence over unconstrained palette
    # mappings; prevent overfitting otherwise indistinguishable demos.
    ordered=sorted(matches,key=lambda item:(
        item[1]["kind"]!="exact",
        len(previous.PROGRAMS[item[0]]),item[0]))
    proposed=[]
    seen=set()
    for i,adapter in ordered:
        outputs=[]
        for inp in inputs:
            out=previous.predict(inp,previous.PROGRAMS[i])
            if out is not None and adapter["kind"]=="recolor":
                out=previous.recolor(out,adapter["mapping"])
            outputs.append(out)
        key=tuple(outputs)
        if key in seen:continue
        seen.add(key)
        proposed.append(GridCandidate(
            origin="source_classical_grid_grammar",
            program_id=int(i),
            outputs=key,
            expression=None))
        if len(proposed)==limit:break
    return tuple(proposed),checks,bool(matches)

class SourceLearnedGridRouter:
    def __init__(self,source_policy,*,max_attempts=2):
        if type(source_policy) is not dict or not source_policy:
            raise ValueError("nonempty source learned strategy dictionary required")
        if max_attempts!=2:raise ValueError("fixed original two-attempt interface")
        if any(not isinstance(k,str) or not k or v not in STRATEGIES
               for k,v in source_policy.items()):
            raise ValueError("unsupported source strategy")
        self.source_policy=dict(source_policy)
        self.max_attempts=max_attempts

    def solve(self,category,source_pairs,target_inputs):
        if category not in self.source_policy:
            raise ValueError("unregistered category, do not guess strategy")
        strategy=self.source_policy[category]
        start=perf_counter_ns()
        if strategy=="hybrid":
            core=HybridArcGridInventor(max_attempts=2).solve(
                source_pairs,target_inputs)
            return RoutedGridResult(
                strategy=strategy,candidates=core.candidates,
                search_ms=core.total_search_ms,
                classical_program_checks=core.old_candidate_checks,
                relational_source_fit=core.new_source_fit,
                classical_source_fit=core.old_source_fit)
        demo=[(grid(a),grid(b)) for a,b in source_pairs]
        inputs=[grid(a) for a in target_inputs]
        if not demo or not inputs:raise ValueError("nonempty original task required")
        if strategy=="classical_only":
            candidates,checks,fit=_classical(demo,inputs,2)
            return RoutedGridResult(
                strategy=strategy,candidates=candidates,
                search_ms=round((perf_counter_ns()-start)/1e6,5),
                classical_program_checks=checks,
                relational_source_fit=False,
                classical_source_fit=fit)
        method=RelationalGridInventor().solve(demo)
        outputs=tuple(RelationalGridInventor().apply(method,x) for x in inputs)
        candidates=(GridCandidate(
            "self_invented_relational_rule",None,outputs,
            method.method),) if (method.source_fit and
              all(y is not None for y in outputs)) else ()
        return RoutedGridResult(
            strategy=strategy,candidates=candidates,
            search_ms=round((perf_counter_ns()-start)/1e6,5),
            classical_program_checks=0,
            relational_source_fit=method.source_fit,
            classical_source_fit=False)
