"""Q3: synthesize causal TWO-OBJECT relational action from observed pixel changes.

The high-level program structure is NOT a hardcoded 'move-smallest-next-to-
largest' task. Source examples determine:
 - which object supplies the pixels,
 - which different object supplies the reference frame,
 - whether source is copied or moved,
 - whether paint comes from source or anchor,
 - two new executable coordinate expressions relating source and anchor.

The algorithm obtains inverse witnesses from output differences and intersects
their *entire executable program signatures* across source examples. A classical
component extractor is deliberately reused, not re-invented.

Bounded typed hypothesis language only. No arbitrary semantic/ASI guarantee.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter_ns
from collections import defaultdict

from .relational_grid_inventor import grid
from .scene_graph_inventor import extract, select_object

SELECTORS=tuple(
    (feature,rank)
    for feature in ("area","height","width","top","left","color","fill",
                    "center_distance","border","color_frequency")
    for rank in ("min","max","second_min","second_max")
)
OPERATIONS=("move","copy")
PAINTS=("source","anchor")
AXES={
    "r":("anchor_low","anchor_high","anchor_next","anchor_center",
         "anchor_low_minus_object","mover_low"),
    "c":("anchor_low","anchor_high","anchor_next","anchor_center",
         "anchor_low_minus_object","mover_low"),
}
OFFSETS=(-1,0,1)


def _shape(g):return len(g),len(g[0])


def _base(axis,expr,anchor,mover):
    a0,a1,b0,b1=anchor.bounds
    m0,m1,n0,n1=mover.bounds
    lo,hi,mlow,extent=(a0,a1,m0,mover.height) if axis=="r" else (
        b0,b1,n0,mover.width)
    if expr=="anchor_low":return lo
    if expr=="anchor_high":return hi
    if expr=="anchor_next":return hi+1
    if expr=="anchor_center":return (lo+hi)//2
    if expr=="anchor_low_minus_object":return lo-extent
    if expr=="mover_low":return mlow
    raise ValueError("unknown expression")


def _paint(g,mover,anchor,dest_r,dest_c,operation,paint):
    h,w=_shape(g)
    dr=dest_r-mover.bounds[0]
    dc=dest_c-mover.bounds[2]
    new_pixels=[(r+dr,c+dc) for r,c in mover.cells]
    if any(r<0 or r>=h or c<0 or c>=w for r,c in new_pixels):
        return None
    out=[list(row) for row in g]
    if operation=="move":
        for r,c in mover.cells:out[r][c]=0
    color=mover.color if paint=="source" else anchor.color
    for r,c in new_pixels:out[r][c]=color
    return tuple(tuple(row) for row in out)


def _objs(g):
    return extract(g,0,diagonal=False,mixed_colors=False)


def _selector_map(objects,shape):
    result=defaultdict(list)
    for feature,rank in SELECTORS:
        obj=select_object(objects,shape,feature,rank)
        if obj is not None:
            result[obj].append((feature,rank))
    return result


def _witnesses(g,y,objects,deadline):
    """Invert every observed pixel change; output constrains translations.

    For each source object and move/copy mode, erase source iff moving and
    compute changed target pixels. The destination of at least one changed
    cell must correspond to one cell of the moved component, so this
    generates a COMPLETE displacement set for a non-degenerate one-object
    action relative to the supplied DSL.
    """
    h,w=_shape(g)
    witnessed=set()
    for i,mover in enumerate(objects):
        if perf_counter_ns()>deadline:return
        for operation in OPERATIONS:
            base=[list(row) for row in g]
            if operation=="move":
                for r,c in mover.cells:base[r][c]=0
            changed=[(r,c,y[r][c]) for r in range(h) for c in range(w)
                     if base[r][c]!=y[r][c] and y[r][c]!=0]
            if not changed:continue
            for r,c,color in changed:
                if perf_counter_ns()>deadline:return
                for sy,sx in mover.cells:
                    dr,dc=r-sy,c-sx
                    dest_r=mover.bounds[0]+dr
                    dest_c=mover.bounds[2]+dc
                    key=(i,operation,dest_r,dest_c,color)
                    if key in witnessed:continue
                    witnessed.add(key)
                    # The newly discovered color may be any source/anchor
                    # color; the paint rule is inferred only in rule stage.
                    # Exhaustive cheap geometry-only equality check:
                    for a_idx,anchor in enumerate(objects):
                        if a_idx==i:continue
                        for paint in PAINTS:
                            if color != (mover.color if paint=="source"
                                         else anchor.color):
                                continue
                            if _paint(g,mover,anchor,dest_r,dest_c,
                                      operation,paint)==y:
                                yield (i,a_idx,operation,paint,dest_r,dest_c)


@dataclass(frozen=True)
class RelationalAction:
    mover_selector:tuple[str,str]
    anchor_selector:tuple[str,str]
    operation:str
    paint_rule:str
    row_expr:tuple[str,int]
    col_expr:tuple[str,int]

    @property
    def ast(self):
        return ("relational_action",
                ("classical_connected_components",),
                ("learned_entity_selector",self.mover_selector),
                ("learned_other_selector",self.anchor_selector),
                ("learned_row_relation",self.row_expr),
                ("learned_col_relation",self.col_expr),
                ("transfer_pixels",self.operation,self.paint_rule))

    def apply(self,source):
        g=grid(source)
        objects=_objs(g)
        if len(objects)<2:return None
        mover=select_object(objects,_shape(g),*self.mover_selector)
        anchor=select_object(objects,_shape(g),*self.anchor_selector)
        if mover is None or anchor is None or mover==anchor:return None
        dest_r=_base("r",self.row_expr[0],anchor,mover)+self.row_expr[1]
        dest_c=_base("c",self.col_expr[0],anchor,mover)+self.col_expr[1]
        return _paint(g,mover,anchor,dest_r,dest_c,
                      self.operation,self.paint_rule)


@dataclass(frozen=True)
class RelationalDiscovery:
    rules:tuple[RelationalAction,...]
    source_pairs:int
    independent_checks:int
    witness_signatures:int
    runtime_ms:float

    @property
    def source_fit(self):return bool(self.rules)


def _row_axis_signatures(axis,target,anchor,mover):
    result=[]
    for expr in AXES[axis]:
        delta=target-_base(axis,expr,anchor,mover)
        if delta in OFFSETS:result.append((expr,delta))
    return result


def _signature_for_pair(g,objects,selectors,w):
    mover_i,anchor_i,operation,paint,dest_r,dest_c=w
    mover,anchor=objects[mover_i],objects[anchor_i]
    row=_row_axis_signatures("r",dest_r,anchor,mover)
    col=_row_axis_signatures("c",dest_c,anchor,mover)
    for m_selector in selectors[mover]:
        for a_selector in selectors[anchor]:
            for rexpr in row:
                for cexpr in col:
                    yield (m_selector,a_selector,operation,paint,rexpr,cexpr)


def _signature_set(g,y,max_witnesses,deadline):
    objects=_objs(g)
    if not 2<=len(objects)<=14:return set()
    selectors=_selector_map(objects,_shape(g))
    rules=set()
    for k,w in enumerate(_witnesses(g,y,objects,deadline)):
        if k>=max_witnesses or perf_counter_ns()>deadline:break
        rules.update(_signature_for_pair(g,objects,selectors,w))
    return rules


class RelationalActionInventor:
    """Construct non-predefined pairwise causal rule from source I/O."""

    def __init__(self,*,max_source_ms=500,max_witnesses=256):
        if not 1<=max_source_ms<=120000 or not 1<=max_witnesses<=10000:
            raise ValueError("finite hypothesis search caps required")
        self.max_source_ms=max_source_ms
        self.max_witnesses=max_witnesses

    def invent(self,examples,*,verification,max_rules=2):
        start=perf_counter_ns()
        train=tuple((grid(x),grid(y)) for x,y in examples)
        checks=tuple((grid(x),grid(y)) for x,y in verification)
        if len(train)<2 or not checks or max_rules not in (1,2):
            raise ValueError("2 source I/O and independent source checks required")
        if any(_shape(x)!=_shape(y) for x,y in train+checks):
            return RelationalDiscovery((),len(train),len(checks),0,
                                       (perf_counter_ns()-start)/1e6)
        deadline=start+int(self.max_source_ms*1e6)
        current=None
        for x,y in train:
            if (perf_counter_ns()-start)/1e6>self.max_source_ms:
                return RelationalDiscovery((),len(train),len(checks),0,
                                           (perf_counter_ns()-start)/1e6)
            candidates=_signature_set(x,y,self.max_witnesses,deadline)
            current=(candidates if current is None else current & candidates)
            if not current:break
        remaining=len(current or ())
        if not current:
            return RelationalDiscovery((),len(train),len(checks),remaining,
                                       (perf_counter_ns()-start)/1e6)
        # No target gold. Every admitted rule must explain the additional
        # source verification examples, including unseen color/layout changes.
        candidates=[]
        for signature in sorted(current,
                key=lambda k:(
                    abs(k[4][1])+abs(k[5][1]),
                    k[2]!="move",k[3]!="source",repr(k))):
            if (perf_counter_ns()-start)/1e6>self.max_source_ms:
                break
            rule=RelationalAction(*signature)
            if all(rule.apply(x)==y for x,y in checks):
                candidates.append(rule)
                if len(candidates)>=max_rules:break
        return RelationalDiscovery(
            tuple(candidates),len(train),len(checks),remaining,
            (perf_counter_ns()-start)/1e6)
