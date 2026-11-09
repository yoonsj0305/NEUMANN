"""Q3: invent an executable positional representation directly from SOURCE I/O.

This is a GENERIC algebraic program synthesizer. It is not dispatched on ARC
task IDs, visual object types, particular strings, or known transformation
names. Raw source examples are normalized into finite arrays, then the solver
constructs a program for:
  - how the output shape depends on the input's dimensions;
  - how output coordinate variables refer to source coordinates;
  - how nested coordinate expressions compose via arithmetic and if-then-else.

Crucially: a source *solution AST* is NOT required to begin invention. The
solver produces one from observed input/output pairs, overcoming the bootstrap
deadlock of StructuralMetaInventor (which required two certified programs).

All operations in the interpreter are total, bounded and typed. The arithmetic
bytecode itself IS human designed. Thus this is source-born compositional
program construction, NOT evidence of unrestricted autonomous invention.
No target answer, task name, or hidden source program enters the interface.

SOURCE candidates are first learned on training pairs, then filtered by
independent held-out SOURCE pairs. TARGET input may only be applied after
learning. Recorded macros can be reused only after new SOURCE certification.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns
from typing import Any

Expr = tuple[Any, ...]


class InexpressibleSource(ValueError):
    pass


def _normalise(value):
    if type(value) is str:
        if not value:
            raise InexpressibleSource("nonempty symbolic sequence required")
        return "string", (len(value),), tuple(value)
    if not isinstance(value, (tuple, list)) or not value:
        raise InexpressibleSource("nonempty finite sequence required")
    if all(not isinstance(v, (tuple, list)) for v in value):
        if len(value)>900 or any(type(x) not in (int,str) for x in value):
            raise InexpressibleSource("bounded scalar sequences only")
        return "sequence", (len(value),), tuple(value)
    if not all(isinstance(v, (tuple,list)) and v for v in value):
        raise InexpressibleSource("rectangular arrays required")
    rows=tuple(tuple(v) for v in value)
    if (len(rows)*len(rows[0])>900 or
            any(len(row)!=len(rows[0]) for row in rows) or
            any(type(v) not in (int,str) for row in rows for v in row)):
        raise InexpressibleSource("bounded rectangular scalar array required")
    return "matrix",(len(rows),len(rows[0])),rows


def _out(kind,rows):
    if kind=="string":
        return "".join(rows)
    return tuple(rows)


def _cost(expr):
    if expr[0] in ("o","d","k"):
        return 1+(expr[0]=="k")
    return 1+sum(_cost(x) for x in expr[1:] if isinstance(x,tuple))


def _eval(expr, dims, indices):
    op=expr[0]
    if op=="o":return indices[expr[1]]
    if op=="d":return dims[expr[1]]
    if op=="k":return expr[1]
    if op=="add":return _eval(expr[1],dims,indices)+_eval(expr[2],dims,indices)
    if op=="sub":return _eval(expr[1],dims,indices)-_eval(expr[2],dims,indices)
    if op=="mul":return _eval(expr[1],dims,indices)*_eval(expr[2],dims,indices)
    if op=="mod":
        den=_eval(expr[2],dims,indices)
        return None if den==0 else _eval(expr[1],dims,indices)%den
    if op=="div":
        den=_eval(expr[2],dims,indices)
        return None if den==0 else _eval(expr[1],dims,indices)//den
    if op=="odd":return _eval(expr[1],dims,indices)%2==1
    if op=="if":
        return _eval(expr[2] if _eval(expr[1],dims,indices)
                     else expr[3],dims,indices)
    raise ValueError("unknown bytecode operator")


def _shape_programs(source, output, axis):
    """Source-derived output shape relation, not a task-family classifier."""
    candidates=[]
    for src_dim in range(len(source[0])):
        d=("d",src_dim)
        candidates.append(d)
        for factor in range(2,9):
            candidates.append(("mul",d,("k",factor)))
        for delta in (-4,-3,-2,-1,1,2,3,4):
            candidates.append(("add",d,("k",delta)))
    for dim in range(1,21):
        candidates.append(("k",dim))
    if len(source[0])==2:
        candidates.append(("add",("d",0),("d",1)))
        for factor in (2,3,4):
            candidates.append(("mul",("add",("d",0),("d",1)),("k",factor)))
    candidates=[e for e in candidates
                if all(_eval(e,a,())==b[axis] for a,b in zip(source,output))]
    # A constant discovered from only same-sized demos must not override a
    # dimension-derived law; source-independent unseen sizes test this.
    candidates.sort(key=lambda e:(
        e[0]=="k",
        _cost(e),
        abs(e[2][1]) if e[0] in ("mul","add")
        and e[2][0]=="k" else 0,
        repr(e)))
    return tuple(dict.fromkeys(candidates))[:10]


def _coordinate_programs(rank):
    """Enumerate an algebra, not a menu of known tiling/rotation patterns.

    The same dimension/index/composition bytecode covers integers/characters,
    1D sequences, and 2D matrices with no category-specific solver.
    """
    expressions=[]
    def add(e):
        if e not in expressions:expressions.append(e)
    cond=[]
    for out_axis in range(rank):
        index=("o",out_axis)
        add(index)
        for dim_axis in range(rank):
            dim=("d",dim_axis)
            base=("mod",index,dim)
            inv=("sub",("sub",dim,("k",1)),base)
            whole=("div",index,dim)
            add(base)
            add(inv)
            add(whole)
            cond.append(("odd",whole))
            cond.append(("odd",base))
        cond.append(("odd",index))
    if rank==2:
        r,c=("o",0),("o",1)
        for axis in range(rank):
            d=("d",axis)
            add(("mod",("add",r,c),d))
            add(("mod",("sub",r,c),d))
            add(("mod",("sub",c,r),d))
            cond.append(("odd",("add",("div",r,("d",0)),
                                      ("div",c,("d",1)))))
    # Constructor growth: expressions built from other expressions.
    # Source observations, not a preselected named transform, choose the AST.
    for i in range(rank):
        d=("d",i)
        for j in range(rank):
            o=("o",j)
            base=("mod",o,d)
            inv=("sub",("sub",d,("k",1)),base)
            for test in cond:
                add(("if",test,inv,base))
                add(("if",test,base,inv))
    return tuple(sorted(expressions,key=lambda a:(_cost(a),repr(a))))


@dataclass(frozen=True)
class IndexProgram:
    rank: int
    kind: str
    shapes: tuple[Expr, ...]
    coordinates: tuple[Expr, ...]
    source_count: int
    independent_source_count: int

    @property
    def ast(self):
        return ("learned_generic_index_algebra",
                ("learned_output_shape",self.shapes),
                ("learned_output_coordinate_programs",self.coordinates),
                ("source_value_fetch",),
                ("source_certified",self.source_count,
                 self.independent_source_count))

    @property
    def cost(self):
        return sum(_cost(a) for a in self.shapes+self.coordinates)

    def apply(self,raw):
        kind,dims,values=_normalise(raw)
        if kind!=self.kind or len(dims)!=self.rank:return None
        shape=tuple(_eval(e,dims,()) for e in self.shapes)
        if (any(type(d) is not int or d<=0 for d in shape) or
                (shape[0] if len(shape)==1
                 else shape[0]*shape[1])>900):
            return None
        def val(index):
            coord=tuple(_eval(e,dims,index) for e in self.coordinates)
            if any(type(x) is not int or not 0<=x<dims[i]
                   for i,x in enumerate(coord)):
                return None
            return values[coord[0]] if self.rank==1 else values[coord[0]][coord[1]]
        if self.rank==1:
            out=[val((i,)) for i in range(shape[0])]
            if any(x is None for x in out):return None
            return _out(self.kind,out)
        rows=[]
        for r in range(shape[0]):
            row=[val((r,c)) for c in range(shape[1])]
            if any(x is None for x in row):return None
            rows.append(tuple(row))
        return _out(self.kind,rows)


@dataclass(frozen=True)
class InventionResult:
    status: str
    programs: tuple[IndexProgram, ...]
    source_candidates_examined: int
    source_counterexamples: int
    elapsed_ms: float
    reason: str

    def apply(self,raw):
        return self.programs[0].apply(raw) if self.programs else None


class SourceBornRepresentationInventor:
    """SOURCE-only raw-I/O -> new algebraic program -> certified macro inventory."""

    def __init__(self,*,max_ms=2500,max_source_checks=1500000):
        if (not 1<=max_ms<=120000 or
                not 1<=max_source_checks<=20000000):
            raise ValueError("bounded source invention budgets")
        self.max_ms=max_ms
        self.max_source_checks=max_source_checks
        self.library=[]

    def invent(self,source_pairs,*,independent_source_checks,
               classical_solvers=(),max_programs=2):
        t=perf_counter_ns()
        train=tuple(source_pairs)
        verifier=tuple(independent_source_checks)
        if not train or not verifier or not 1<=max_programs<=4:
            raise ValueError("SOURCE examples and disjoint verifier required")
        all_pairs=train+verifier
        try:
            norms=[(_normalise(a),_normalise(b)) for a,b in all_pairs]
        except InexpressibleSource as err:
            return InventionResult(
                "ABSTAIN_TYPED_INPUT",(),0,0,
                (perf_counter_ns()-t)/1e6,str(err))
        kind,shape,_=norms[0][0]
        rank=len(shape)
        if any(a[0]!=kind or b[0]!=kind or
               len(a[1])!=rank or len(b[1])!=rank for a,b in norms):
            return InventionResult(
                "ABSTAIN_CROSS_RANK",(),0,0,
                (perf_counter_ns()-t)/1e6,
                "no human per-task rank coercion")
        observations=tuple((a,b) for a,b in all_pairs)
        if any(all(solver(a)==_normalise(b)[2]
                   if _normalise(b)[0]=="matrix"
                   else solver(a)==b
                   for a,b in all_pairs)
               for solver in classical_solvers):
            return InventionResult(
                "CLASSICAL_FIRST",(),0,0,
                (perf_counter_ns()-t)/1e6,
                "source-verified existing solver already sufficient")
        verified=[]
        for p in self.library:
            if p.kind==kind and p.rank==rank and all(
                    p.apply(a)==b for a,b in all_pairs):
                verified.append(p)
                if len(verified)==max_programs:
                    return InventionResult(
                        "SOURCE_VERIFIED_REUSED_INVENTED_MACRO",
                        tuple(verified),0,0,
                        (perf_counter_ns()-t)/1e6,
                        "reused prior source-invented executable program")
        shapes_in=[a[1] for a,b in norms[:len(train)]]
        shapes_out=[b[1] for a,b in norms[:len(train)]]
        dimensions=[_shape_programs(shapes_in,shapes_out,axis)
                    for axis in range(rank)]
        if any(not d for d in dimensions):
            return InventionResult(
                "ABSTAIN_NO_SHAPE_PROGRAM",(),0,0,
                (perf_counter_ns()-t)/1e6,
                "none of the source-derived output shape expressions fits")

        # Filter coordinate expressions by SOURCE I/O membership only.
        # Required output color must occur in the proposed source row/column.
        # Thus all solutions of the direct source-copy language survive.
        expressions=_coordinate_programs(rank)
        arrays=[(a[1],a[2],b[1],b[2]) for a,b in norms[:len(train)]]
        samples=[]
        for dims,inp,shape,out in arrays:
            indices=(range(shape[0]) if rank==1 else
                     product(range(shape[0]),range(shape[1])))
            idx=list((i,) if rank==1 else i for i in indices)
            stride=max(1,len(idx)//48)
            for index in idx[::stride][:48]:
                expected=(out[index[0]] if rank==1
                          else out[index[0]][index[1]])
                samples.append((dims,inp,index,expected))
        # Duplicate expression ASTs are not merged on their short training
        # traces: that would erase extrapolation-distinct hypotheses.
        viable=[]
        for srcaxis in range(rank):
            surviving=[]
            for e in expressions:
                plausible=True
                for dims,inp,index,y in samples:
                    ix=_eval(e,dims,index)
                    if type(ix) is not int or not 0<=ix<dims[srcaxis]:
                        plausible=False;break
                    if rank==1:
                        if inp[ix]!=y:plausible=False;break
                    elif srcaxis==0:
                        if y not in inp[ix]:plausible=False;break
                    elif not any(row[ix]==y for row in inp):
                        plausible=False;break
                if plausible:surviving.append(e)
            viable.append(surviving)
        if any(not x for x in viable):
            return InventionResult(
                "ABSTAIN_NO_SOURCE_CORRESPONDENCE",(),0,0,
                (perf_counter_ns()-t)/1e6,
                "no generic coordinate expression fits SOURCE causal pixels")
        checked=0
        counterexamples=0
        seen={p.ast for p in verified}
        for dims in product(*dimensions):
            # Full original source checks are required; samples are *only*
            # safe sound pruning and never count as heldout verification.
            for coords in product(*viable):
                checked+=1
                if checked>self.max_source_checks or (
                        perf_counter_ns()-t)/1e6>self.max_ms:
                    return InventionResult(
                        "ABSTAIN_SOURCE_BUDGET" if not verified
                        else "SOURCE_VERIFIED_NEW_PROGRAM",
                        tuple(verified),checked,counterexamples,
                        (perf_counter_ns()-t)/1e6,
                        "source search capped, never guessed on target gold")
                p=IndexProgram(rank,kind,tuple(dims),tuple(coords),
                               len(train),len(verifier))
                if p.ast in seen:continue
                if any(p.apply(a)!=b for a,b in train):
                    continue
                if any(p.apply(a)!=b for a,b in verifier):
                    counterexamples+=1
                    continue
                verified.append(p)
                seen.add(p.ast)
                self.library.append(p)
                if len(verified)>=max_programs:
                    return InventionResult(
                        "SOURCE_VERIFIED_NEW_PROGRAM",
                        tuple(verified),checked,counterexamples,
                        (perf_counter_ns()-t)/1e6,
                        "new shape and address AST assembled from raw SOURCE")
        return InventionResult(
            "SOURCE_VERIFIED_NEW_PROGRAM" if verified
            else "ABSTAIN_OUTSIDE_INDEX_ALGEBRA",
            tuple(verified),checked,counterexamples,
            (perf_counter_ns()-t)/1e6,
            "bounded algebra, no unverified target guesses")
