"""Q3 compositional grammar growth: known geometry + SOURCE-induced relation.

A new executable program may combine a classical geometry operation
with a causally learned pixel predicate AFTER the shape transformation.
The frozen 626-program vocabulary is reused rather than reimplemented.
Source training outputs only; heldout target outputs never accepted.

This is a bounded new language construction, NOT unrestricted Q3/Q6
or a discovery of an unknown primitive's semantics from no examples.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns
from . import arc2_meta_grid_reasoner as known
from .relational_grid_inventor import RelationalGridInventor, grid


@dataclass(frozen=True)
class ComposedGridRule:
    geometric_preprogram: tuple[str, ...]
    relational_method: dict

    def apply(self, source_grid):
        x=grid(source_grid)
        intermediate=known.predict(x,self.geometric_preprogram)
        if intermediate is None:
            return None
        from .relational_grid_inventor import predict
        return predict(intermediate,self.relational_method)


@dataclass(frozen=True)
class ComposedGridResult:
    candidates: tuple[tuple, ...]
    invented_program: ComposedGridRule | None
    invented_source_fit: bool
    fixed_626_source_fit: bool
    fixed_program_checks: int
    relational_invention_attempts: int
    search_ms: float
    source_examples: int

    def predict(self, input_grid):
        if self.invented_program is None:
            return None
        return self.invented_program.apply(input_grid)


def _shape(g):
    return len(g),len(g[0])


def _coincidence(a,b):
    """Cheap, SOURCE-only geometry ranking; no target answers accessed."""
    h,w=_shape(a)
    if _shape(b)!=(h,w):
        return -100000
    exact=sum(x==y for row_a,row_b in zip(a,b)
              for x,y in zip(row_a,row_b))
    mask=sum((x!=0)==(y!=0) for row_a,row_b in zip(a,b)
             for x,y in zip(row_a,row_b))
    return 3*mask+exact


def _old_program_output(program,adapter,inputs):
    outputs=[]
    for x in inputs:
        out=known.predict(x,program)
        if out is not None and adapter["kind"]=="recolor":
            out=known.recolor(out,adapter["mapping"])
        outputs.append(out)
    return tuple(outputs)


class ComposedGridInventor:
    """Expand a program language only when source classical fit is insufficient.

    The candidate language consists of a provided old geometric primitive,
    followed by one newly induced relational rewrite. It is a new *composition
    rule*, but the individual interpreter primitives remain human supplied.
    """

    def __init__(self, *, max_geometries=12, max_relational_ms=120):
        if type(max_geometries) is not int or not 1<=max_geometries<=26:
            raise ValueError("positive finite geometry search cap")
        if type(max_relational_ms) not in (int,float) or not 1<=max_relational_ms<=5000:
            raise ValueError("positive finite relational search deadline")
        self.max_geometries=max_geometries
        self.max_relational_ms=max_relational_ms

    def solve(self, source_pairs, target_inputs):
        start=perf_counter_ns()
        demo=tuple((grid(a),grid(b)) for a,b in source_pairs)
        inputs=tuple(grid(x) for x in target_inputs)
        if len(demo)<2 or not inputs:
            raise ValueError("2 source demonstrations and test inputs required")
        # Strong fixed-vocabulary solver gets the exact same source I/O first.
        winners,checks=known.fit_task(demo,tuple(range(len(known.PROGRAMS))),
                                      len(known.PROGRAMS), max_hits=len(known.PROGRAMS))
        classical=[]
        seen=set()
        for index,adapter in sorted(
            winners,key=lambda z:(z[1]["kind"]!="exact",
                                  len(known.PROGRAMS[z[0]]),z[0])):
            result=_old_program_output(known.PROGRAMS[index],adapter,inputs)
            if result not in seen and all(x is not None for x in result):
                classical.append(result);seen.add(result)
                if len(classical)>=2:
                    break
        # If old geometry alone already exactly explains the original,
        # do NOT spend time learning a needlessly re-invented relation.
        if any(adapter["kind"]=="exact" for _,adapter in winners):
            return ComposedGridResult(
                tuple(classical[:2]),None,False,bool(winners),
                checks,0,round((perf_counter_ns()-start)/1e6,5),len(demo))

        # A relational edit by itself preserves shape. Only consider this
        # language expansion where SOURCE requires a shape change.
        if all(_shape(x)==_shape(y) for x,y in demo):
            return ComposedGridResult(
                tuple(classical[:2]),None,False,bool(winners),
                checks,0,round((perf_counter_ns()-start)/1e6,5),len(demo))
        if not all(_shape(x)!=_shape(y) for x,y in demo):
            return ComposedGridResult(
                tuple(classical[:2]),None,False,bool(winners),
                checks,0,round((perf_counter_ns()-start)/1e6,5),len(demo))

        # Rank feasible classical geometric transformers WITHOUT fitting a
        # relational rule for every impossible shape mapping.
        transforms=[]
        for op in known.OPERATORS:
            pre=(op,)
            transformed=[known.predict(x,pre) for x,y in demo]
            if any(z is None or _shape(z)!=_shape(y)
                   for z,(_,y) in zip(transformed,demo)):
                continue
            score=sum(_coincidence(z,y)
                      for z,(_,y) in zip(transformed,demo))
            transforms.append((-score,pre,tuple(transformed)))
        transforms.sort(key=lambda item:(item[0],len(item[1]),item[1]))
        tries=0
        learned=None
        for _,pre,transformed in transforms[:self.max_geometries]:
            tries+=1
            pairs=tuple((z,y) for z,(_,y) in zip(transformed,demo))
            inventor=RelationalGridInventor(max_search_ms=self.max_relational_ms)
            fit=inventor.solve(pairs)
            if not fit.source_fit or fit.method is None:
                continue
            proposal=ComposedGridRule(pre,fit.method)
            if not all(proposal.apply(x)==y for x,y in demo):
                continue
            candidates=tuple(proposal.apply(x) for x in inputs)
            if all(x is not None for x in candidates):
                learned=proposal
                if candidates not in seen:
                    # The invented program is the first candidate when old
                    # classical source grammar fitted only via a fragile
                    # recolor adapter; retain at least one classical result.
                    classical.insert(0,candidates)
                break
        return ComposedGridResult(
            tuple(classical[:2]),learned,learned is not None,bool(winners),
            checks,tries,round((perf_counter_ns()-start)/1e6,5),len(demo))
