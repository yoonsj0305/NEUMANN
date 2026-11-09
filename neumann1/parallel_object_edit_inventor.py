"""Q3: synthesize a new PARALLEL object-editing program from source I/O.

Unlike one-object transformations, a learned Boolean selector is mapped
over EVERY connected component; the selected objects receive an independently
inferred color function. Source I/O induces predicate clauses and color role;
no original target gold or task IDs are used in invention.

Only a bounded typed primitive/feature basis is human-supplied. This is
NOT unrestricted autonomous grammar invention or a new general theorem.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from time import perf_counter_ns

from .relational_grid_inventor import grid
from .scene_graph_inventor import extract, attribute, select_object

FEATURES=("area","height","width","color","fill","top","left","border",
          "color_frequency","color_object_count")
RELATIONS=("min","max","lt_max","gt_min")


def feature(o,objects,shape,name):
    return attribute(o,name,objects,shape)


def atom_true(atom,o,objects,shape):
    kind,name,p=atom
    val=feature(o,objects,shape,name)
    if kind=="relative":
        vals=[feature(x,objects,shape,name) for x in objects]
        if p=="min":return val==min(vals)
        if p=="max":return val==max(vals)
        if p=="lt_max":return val<max(vals)
        if p=="gt_min":return val>min(vals)
        raise ValueError("unsupported source-derived relation")
    if kind=="exact":return val==p
    if kind=="upper":return val<=p
    if kind=="lower":return val>=p
    raise ValueError("unsupported learned Boolean clause")


def _all_objects(g):
    return extract(g,0,diagonal=False,mixed_colors=False)


def _color_expression(g,objects,expr):
    name=expr[0]
    if name=="constant":return expr[1]
    if name=="from_object":
        selector=expr[1]
        chosen=select_object(objects,(len(g),len(g[0])),*selector)
        return None if chosen is None else chosen.color
    if name=="most_common":
        freq=Counter(v for row in g for v in row if v!=0)
        return min(freq,key=lambda c:(-freq[c],c)) if freq else None
    if name=="least_common":
        freq=Counter(v for row in g for v in row if v!=0)
        return min(freq,key=lambda c:(freq[c],c)) if freq else None
    raise ValueError("unknown color generator")


@dataclass(frozen=True)
class BulkEditProgram:
    # DNF clauses: OR of AND(s) over newly synthesized object predicates.
    clauses:tuple[tuple[tuple,...],...]
    output_color_expr:tuple

    @property
    def ast(self):
        return ("parallel_map_objects",
                ("classical_connected_component_graph",),
                ("synthesized_boolean_dnf",self.clauses),
                ("synthesized_color_expression",self.output_color_expr))

    def apply(self,source):
        g=grid(source)
        objects=_all_objects(g)
        if not objects:return None
        color=_color_expression(g,objects,self.output_color_expr)
        if color is None or not isinstance(color,int) or not 0<=color<=9:
            return None
        shape=len(g),len(g[0])
        result=[list(row) for row in g]
        for o in objects:
            selected=any(all(atom_true(a,o,objects,shape) for a in term)
                         for term in self.clauses)
            if selected:
                for r,c in o.cells:
                    result[r][c]=color
        return tuple(tuple(row) for row in result)


@dataclass(frozen=True)
class BulkEditDiscovery:
    programs:tuple[BulkEditProgram,...]
    positive_objects:int
    negative_objects:int
    evaluated_clauses:int
    elapsed_ms:float
    source_examples:int
    verifier_examples:int

    @property
    def solved_source(self):
        return bool(self.programs)


def _labels(x,y):
    """Invert changed output into affected/unaffected SOURCE components.

    Fails closed unless every edit is a uniform full-object recoloring or
    deletion, and every background pixel remains unchanged.
    """
    if len(x)!=len(y) or len(x[0])!=len(y[0]):
        return None
    if any(x[r][c]==0 and y[r][c]!=0
           for r in range(len(x)) for c in range(len(x[0]))):
        return None
    objs=_all_objects(x)
    if not objs:return None
    rows=[]
    for o in objs:
        targets={y[r][c] for r,c in o.cells}
        if len(targets)!=1:return None
        target=next(iter(targets))
        rows.append((o,target!=o.color,target))
    return objs,rows


def _source_atoms(records):
    """Infer *candidate* predicate constants from the I/O data itself."""
    values={name:set() for name in FEATURES}
    for g,objs,labeled in records:
        shape=len(g),len(g[0])
        for obj,_,_ in labeled:
            for name in FEATURES:
                values[name].add(feature(obj,objs,shape,name))
    atoms=[]
    for name in FEATURES:
        atoms.extend(("relative",name,op) for op in RELATIONS)
        for value in sorted(values[name]):
            atoms.extend((("exact",name,value),
                          ("upper",name,value),
                          ("lower",name,value)))
    return tuple(atoms)


def _paint_candidates(records):
    observed=sorted({new for g,objs,labeled in records
                     for obj,changed,new in labeled if changed})
    if not observed:return []
    candidates=[("constant",c) for c in observed]
    candidates.extend((("from_object",(f,rank))
                       for f in ("area","height","width","color",
                                 "color_frequency")
                       for rank in ("min","max")))
    candidates.extend((("most_common",),("least_common",)))
    # Evaluate global role at each affected object. A role predicts
    # possibly different colors on each source example, whereas a
    # constant predicts only one fixed color.
    accepted=[]
    for expr in candidates:
        if all(_color_expression(g,objs,expr)==new
               for g,objs,labeled in records
               for obj,changed,new in labeled if changed):
            accepted.append(expr)
    return accepted


def _mask_for_atom(atom,records):
    yes=0;no=0;i=0
    for g,objs,labeled in records:
        shape=len(g),len(g[0])
        for o,changed,_ in labeled:
            if atom_true(atom,o,objs,shape):
                if changed:yes|=1<<i
                else:no|=1<<i
            i+=1
    return yes,no


class ParallelObjectEditInventor:
    """Generate a new boolean object-selection grammar from edit witnesses."""

    def __init__(self,*,max_source_ms=500,max_clauses=80000):
        if not 1<=max_source_ms<=120000 or not 1<=max_clauses<=1000000:
            raise ValueError("finite candidate and wall budget")
        self.max_source_ms=max_source_ms
        self.max_clauses=max_clauses

    def invent(self,demonstrations,*,verification,max_programs=2):
        t0=perf_counter_ns()
        train=tuple((grid(x),grid(y)) for x,y in demonstrations)
        checked=tuple((grid(x),grid(y)) for x,y in verification)
        if len(train)<2 or not checked or max_programs not in (1,2):
            raise ValueError("2 examples and independent source checks required")
        if set(x for x,y in train)&set(x for x,y in checked):
            raise ValueError("source verifier cannot reuse training input")
        records=[]
        npos=nneg=0
        for x,y in train:
            got=_labels(x,y)
            if got is None:
                return BulkEditDiscovery((),0,0,0,(perf_counter_ns()-t0)/1e6,
                                         len(train),len(checked))
            objects,labeled=got
            npos+=sum(changed for o,changed,t in labeled)
            nneg+=sum(not changed for o,changed,t in labeled)
            records.append((x,objects,labeled))
        if npos==0 or nneg==0:
            return BulkEditDiscovery((),npos,nneg,0,(perf_counter_ns()-t0)/1e6,
                                     len(train),len(checked))
        color_candidates=_paint_candidates(records)
        if not color_candidates:
            return BulkEditDiscovery((),npos,nneg,0,(perf_counter_ns()-t0)/1e6,
                                     len(train),len(checked))
        deadline=t0+int(self.max_source_ms*1e6)
        pos_mask=0;neg_mask=0;i=0
        for g,objs,labeled in records:
            for o,changed,t in labeled:
                if changed:pos_mask|=1<<i
                else:neg_mask|=1<<i
                i+=1
        atoms=_source_atoms(records)
        atom_rows=[]
        for a in atoms:
            yes,no=_mask_for_atom(a,records)
            if yes:atom_rows.append((a,yes,no))
        evaluated=0
        clauses=[]
        # Single source-invented predicate first; generalize to AND of
        # two clauses when source differences require causal conjunction.
        for atom,yes,no in atom_rows:
            evaluated+=1
            if no==0:clauses.append(((atom,),yes))
        for (a,ya,na),(b,yb,nb) in combinations(atom_rows,2):
            if perf_counter_ns()>deadline or evaluated>=self.max_clauses:
                break
            evaluated+=1
            both_yes=ya & yb
            if both_yes and not (na & nb):
                # True for positive examples but no negative examples.
                # For any atom, negative bit is its false-positive mask.
                # Both predicates true on a negative iff na & nb.
                clauses.append(((a,b),both_yes))
        if not clauses:
            return BulkEditDiscovery((),npos,nneg,evaluated,
                                     (perf_counter_ns()-t0)/1e6,
                                     len(train),len(checked))
        # Set-cover of ALL affected components with at most 2 disjuncts.
        candidate_dnfs=[]
        for clause,mask in clauses:
            if mask==pos_mask:
                candidate_dnfs.append((clause,))
        if not candidate_dnfs:
            for i,(left,mask_l) in enumerate(clauses):
                for right,mask_r in clauses[i+1:]:
                    if mask_l|mask_r==pos_mask:
                        candidate_dnfs.append((left,right))
                        if len(candidate_dnfs)>=400:break
                if len(candidate_dnfs)>=400:break
        programs=[]
        for dnf in candidate_dnfs:
            if perf_counter_ns()>deadline:break
            for color_expr in color_candidates:
                candidate=BulkEditProgram(tuple(dnf),color_expr)
                if all(candidate.apply(x)==y for x,y in checked):
                    if candidate not in programs:
                        programs.append(candidate)
                    if len(programs)>=max_programs:
                        return BulkEditDiscovery(tuple(programs),npos,nneg,
                                                 evaluated,(perf_counter_ns()-t0)/1e6,
                                                 len(train),len(checked))
        return BulkEditDiscovery(tuple(programs),npos,nneg,evaluated,
                                 (perf_counter_ns()-t0)/1e6,
                                 len(train),len(checked))
