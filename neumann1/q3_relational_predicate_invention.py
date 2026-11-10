"""Q3 data-derived relational set comprehension, no task-name routing.

Invent a new executable Boolean formula defining a set of changed output
coordinates. Source examples select anchor roles, output symbol, and a
low-description-length DNF predicate *from observed causal differences*.
No fixed named puzzle transformer is selected or retrieved. The abstract
lattice of equality/order/between constraints is human-provided: this is
program synthesis within a compositional grammar, not proof of autonomous
metagrammar invention or Q3 global PASS.

Candidate programs must go to the independent no-network SOURCE oracle.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from .open_program_inventor import source_same_value,validate_code
from .q3_structure_factorization import StructuralFactor


_FEATURES=(
    "r_eq_a","r_eq_b","c_eq_a","c_eq_b",
    "r_between","c_between","r_lt_a","r_gt_a",
    "r_lt_b","r_gt_b","c_lt_a","c_gt_a",
    "c_lt_b","c_gt_b",
)


def _rect(x):
    return (type(x) is list and bool(x) and len(x)<=30
            and type(x[0]) is list and bool(x[0]) and len(x[0])<=30
            and all(type(row) is list and len(row)==len(x[0])
                    and all(type(v) in (int,str,bool) for v in row)
                    for row in x))


def _bg(x):
    counts=Counter(v for row in x for v in row)
    return sorted(counts.items(),key=lambda p:(-p[1],repr(p[0])))[0][0]


def _locations(x,color):
    return [(r,c) for r,row in enumerate(x) for c,v in enumerate(row)
            if source_same_value(v,color)]


def _feature(name,r,c,ra,ca,rb,cb):
    if name=="r_eq_a":return r==ra
    if name=="r_eq_b":return r==rb
    if name=="c_eq_a":return c==ca
    if name=="c_eq_b":return c==cb
    if name=="r_between":return min(ra,rb)<=r<=max(ra,rb)
    if name=="c_between":return min(ca,cb)<=c<=max(ca,cb)
    if name=="r_lt_a":return r<ra
    if name=="r_gt_a":return r>ra
    if name=="r_lt_b":return r<rb
    if name=="r_gt_b":return r>rb
    if name=="c_lt_a":return c<ca
    if name=="c_gt_a":return c>ca
    if name=="c_lt_b":return c<cb
    if name=="c_gt_b":return c>cb
    raise ValueError("invalid relation")


def _source_cells(pairs,a,b):
    """Return only causal additions, never count unchanged background."""
    rows=[]
    symbol=None
    for x,y in pairs:
        if not _rect(x) or not _rect(y) or (
                len(x)!=len(y) or len(x[0])!=len(y[0])):
            return None
        bg=_bg(x)
        aa=_locations(x,a)
        bb=_locations(x,b)
        if len(aa)!=1 or len(bb)!=1 or source_same_value(a,b):
            return None
        ra,ca=aa[0];rb,cb=bb[0]
        count_changed=0
        for r in range(len(x)):
            for c in range(len(x[0])):
                original=x[r][c]
                target=y[r][c]
                changed=not source_same_value(original,target)
                if changed:
                    count_changed+=1
                    if not source_same_value(original,bg):return None
                    if symbol is None:
                        symbol=target
                    elif not source_same_value(symbol,target):
                        return None
                if source_same_value(original,bg):
                    rows.append((r,c,ra,ca,rb,cb,changed))
        if not count_changed:return None
    if symbol is None:return None
    return rows,symbol


def _learn_dnf(rows,*,max_terms=3,max_clause=3):
    """Exact minimum-bias mask cover from coordinate relation algebra."""
    positives=sum(1 for z in rows if z[-1])
    if not positives:return None
    target=sum(1<<i for i,z in enumerate(rows) if z[-1])
    universe=(1<<len(rows))-1
    primitive={}
    for name in _FEATURES:
        mask=0
        for i,(r,c,ra,ca,rb,cb,_) in enumerate(rows):
            if _feature(name,r,c,ra,ca,rb,cb):
                mask|=1<<i
        if mask and mask!=universe:
            primitive[name]=mask
    names=tuple(primitive)
    pure={}
    for n in range(1,max_clause+1):
        for clause in combinations(names,n):
            intersection=universe
            for name in clause:
                intersection&=primitive[name]
            if intersection and not intersection&~target:
                old=pure.get(intersection)
                if old is None or (len(clause),clause)<(len(old),old):
                    pure[intersection]=clause
    if not pure:return None
    candidates=tuple(sorted(
        ((mask,terms) for mask,terms in pure.items()),
        key=lambda x:(len(x[1]),x[1])))
    remaining=target
    chosen=[]
    while remaining and len(chosen)<max_terms:
        available=[(mask,clause) for mask,clause in candidates
                   if (mask&remaining)]
        if not available:return None
        # Maximize newly explained causal locations. Tie: simplest law.
        mask,clause=max(available,key=lambda x:(
            (x[0]&remaining).bit_count()/(len(x[1])+0.5),
            -len(x[1]),tuple(-ord(ch) for ch in ",".join(x[1]))))
        chosen.append(clause)
        remaining &=~mask
    if remaining:return None
    return tuple(chosen)


_EXPRESSIONS={
    "r_eq_a":"r==ra","r_eq_b":"r==rb",
    "c_eq_a":"c==ca","c_eq_b":"c==cb",
    "r_between":"min(ra,rb)<=r<=max(ra,rb)",
    "c_between":"min(ca,cb)<=c<=max(ca,cb)",
    "r_lt_a":"r<ra","r_gt_a":"r>ra",
    "r_lt_b":"r<rb","r_gt_b":"r>rb",
    "c_lt_a":"c<ca","c_gt_a":"c>ca",
    "c_lt_b":"c<cb","c_gt_b":"c>cb",
}


def _compile(a,b,symbol,clauses):
    predicate=" or ".join(
        "("+" and ".join(_EXPRESSIONS[n] for n in clause)+")"
        for clause in clauses)
    code=(
        "def transform(x):\n"
        f"    a={repr(a)}\n"
        f"    b={repr(b)}\n"
        f"    symbol={repr(symbol)}\n"
        "    if not x or not x[0]:return x\n"
        "    counts={}\n"
        "    for row in x:\n"
        "        for v in row:counts[v]=counts.get(v,0)+1\n"
        "    bg=sorted(counts,key=lambda v:(-counts[v],repr(v)))[0]\n"
        "    loc_a=[]\n"
        "    loc_b=[]\n"
        "    for r in range(len(x)):\n"
        "        for c in range(len(x[0])):\n"
        "            if x[r][c]==a:loc_a.append((r,c))\n"
        "            if x[r][c]==b:loc_b.append((r,c))\n"
        "    if len(loc_a)!=1 or len(loc_b)!=1:return x\n"
        "    ra,ca=loc_a[0]\n"
        "    rb,cb=loc_b[0]\n"
        "    out=[row[:] for row in x]\n"
        "    for r in range(len(x)):\n"
        "        for c in range(len(x[0])):\n"
        f"            if x[r][c]==bg and ({predicate}):\n"
        "                out[r][c]=symbol\n"
        "    return out")
    return validate_code(code)


def induce_relational_comprehensions(source_pairs,*,max_candidates=4):
    """Synthesize relational programs by abducting predicates from SOURCE."""
    if not 2<=len(source_pairs)<=32 or not 1<=max_candidates<=12:
        raise ValueError("bounded SOURCE-only relational invention required")
    pairs=tuple((x,y) for x,y in source_pairs)
    if not all(_rect(x) and _rect(y) for x,y in pairs):return ()
    first=pairs[0][0]
    first_bg=_bg(first)
    singles=[
        color for color,n in Counter(v for row in first for v in row).items()
        if n==1 and not source_same_value(color,first_bg)
    ]
    if len(singles)<2 or len(singles)>8:return ()
    solutions=[]
    for a,b in combinations(sorted(singles,key=repr),2):
        evidence=_source_cells(pairs,a,b)
        if evidence is None:continue
        cells,symbol=evidence
        clauses=_learn_dnf(cells)
        if not clauses:continue
        program=_compile(a,b,symbol,clauses)
        complexity=sum(len(c) for c in clauses)+2*len(clauses)
        solutions.append(StructuralFactor(
            program,"source-invented-relational-set-comprehension",
            complexity,len(pairs)))
    solutions.sort(key=lambda p:(p.description_length,p.program))
    return tuple(solutions[:max_candidates])
