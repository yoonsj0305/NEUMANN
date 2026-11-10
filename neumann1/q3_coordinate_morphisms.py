"""Q3 general SOURCE-inferred coordinate morphisms for nested sequences.

The previous Q3 semantic grammar could only preserve the dimensions of
simple nested data. On the frozen ARC2 AUTHOR SOURCE cohort, seven of twenty
disjoint tasks produced NO executable proposals at all. New hypothesis:
infer an executable coordinate *representation* directly from multiple
observed input/output arrays, using one identical axis law on rows and
columns. No task ID, target answer, benchmark or human-written solution is
ever input to this generator.

Operators are generic index transformations over any rectangular typed
sequence, not ARC-specific operations. The operator and its free integers
are chosen by exact SOURCE training constraints and a fixed description
length, not by seeing withheld SOURCE checks or original TARGET output.
The shared existing GenerativeProgramInventor must still independently
Docker-verify every emitted program. A/C receive identical method grammar;
learned discovery advantage must be evaluated separately.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .open_program_inventor import source_same_value, validate_code
from .q3_structure_factorization import StructuralFactor

_MODES=(
    "identity","reverse","periodic","reverse_periodic",
    "alternate_reverse_first","alternate_reverse_second",
    "expand","reverse_expand","prefix_crop","suffix_crop",
    "prefix_pad","suffix_pad")
_EXPAND=(
    "periodic","reverse_periodic","alternate_reverse_first",
    "alternate_reverse_second","expand","reverse_expand")


def _rect(x):
    return bool(
        type(x) is list and 1<=len(x)<=30
        and type(x[0]) is list and 1<=len(x[0])<=30
        and all(type(row) is list and len(row)==len(x[0])
                and all(type(v) in (int,str,bool) for v in row)
                for row in x))


def _size(n,mode,k):
    if mode in ("identity","reverse"):
        return n
    if mode in _EXPAND:
        return n*k
    if mode in ("prefix_crop","suffix_crop"):
        return n-k
    if mode in ("prefix_pad","suffix_pad"):
        return n+k
    raise ValueError("unknown coordinate representation")


def _index(i,n,mode,k):
    if mode=="identity":
        return i
    if mode=="reverse":
        return n-i-1
    if mode=="periodic":
        return i%n
    if mode=="reverse_periodic":
        return n-1-(i%n)
    if mode=="alternate_reverse_first":
        return n-1-(i%n) if (i//n)%2==0 else i%n
    if mode=="alternate_reverse_second":
        return i%n if (i//n)%2==0 else n-1-(i%n)
    if mode=="expand":
        return i//k
    if mode=="reverse_expand":
        return n-1-(i//k)
    if mode in ("prefix_crop","suffix_pad"):
        return i
    if mode in ("suffix_crop","prefix_pad"):
        return i+k
    raise ValueError("unknown coordinate representation")


def _background(grid):
    counts=Counter(v for row in grid for v in row)
    # The filler matters only where generated indexes leave source bounds.
    # A deterministic typed tie break gives reproducible SOURCE operations.
    return sorted(counts.items(),key=lambda p:(-p[1],repr(p[0])))[0][0]


def _apply(grid,row_mode,row_k,col_mode,col_k):
    if not _rect(grid):
        return None
    h,w=len(grid),len(grid[0])
    oh=_size(h,row_mode,row_k)
    ow=_size(w,col_mode,col_k)
    if not(1<=oh<=30 and 1<=ow<=30):
        return None
    bg=_background(grid)
    result=[]
    for r in range(oh):
        source_r=_index(r,h,row_mode,row_k)
        row=[]
        for c in range(ow):
            source_c=_index(c,w,col_mode,col_k)
            row.append(grid[source_r][source_c]
                       if 0<=source_r<h and 0<=source_c<w
                       else bg)
        result.append(row)
    return result


def _axis_candidates(train,axis):
    possibilities=[]
    for mode in _MODES:
        for k in range(1,6):
            if mode in ("identity","reverse") and k!=1:
                continue
            if mode in _EXPAND and k==1:
                continue
            if all(_size(len(x) if axis==0 else len(x[0]),mode,k)
                   ==(len(y) if axis==0 else len(y[0]))
                   for x,y in train):
                possibilities.append((mode,k))
    return possibilities


def _compiled_code(row_mode,row_k,col_mode,col_k):
    code=(
        "def transform(x):\n"
        f"    row_mode={repr(row_mode)}\n"
        f"    row_k={row_k}\n"
        f"    col_mode={repr(col_mode)}\n"
        f"    col_k={col_k}\n"
        "    def size(n,mode,k):\n"
        "        if mode=='identity' or mode=='reverse':return n\n"
        "        if mode=='periodic' or mode=='reverse_periodic' or mode=='alternate_reverse_first' or mode=='alternate_reverse_second' or mode=='expand' or mode=='reverse_expand':return n*k\n"
        "        if mode=='prefix_crop' or mode=='suffix_crop':return n-k\n"
        "        return n+k\n"
        "    def index(i,n,mode,k):\n"
        "        if mode=='identity':return i\n"
        "        if mode=='reverse':return n-i-1\n"
        "        if mode=='periodic':return i%n\n"
        "        if mode=='reverse_periodic':return n-1-(i%n)\n"
        "        if mode=='alternate_reverse_first':return n-1-(i%n) if (i//n)%2==0 else i%n\n"
        "        if mode=='alternate_reverse_second':return i%n if (i//n)%2==0 else n-1-(i%n)\n"
        "        if mode=='expand':return i//k\n"
        "        if mode=='reverse_expand':return n-1-(i//k)\n"
        "        if mode=='prefix_crop' or mode=='suffix_pad':return i\n"
        "        return i+k\n"
        "    h=len(x)\n"
        "    w=len(x[0])\n"
        "    oh=size(h,row_mode,row_k)\n"
        "    ow=size(w,col_mode,col_k)\n"
        "    if oh<1 or ow<1 or oh>30 or ow>30:return x\n"
        "    counts={}\n"
        "    for row in x:\n"
        "        for v in row:\n"
        "            counts[v]=counts.get(v,0)+1\n"
        "    bg=sorted(counts,key=lambda v:(-counts[v],str(v)))[0]\n"
        "    out=[]\n"
        "    for r in range(oh):\n"
        "        sr=index(r,h,row_mode,row_k)\n"
        "        row=[]\n"
        "        for c in range(ow):\n"
        "            sc=index(c,w,col_mode,col_k)\n"
        "            if 0<=sr<h and 0<=sc<w:\n"
        "                row.append(x[sr][sc])\n"
        "            else:row.append(bg)\n"
        "        out.append(row)\n"
        "    return out")
    return validate_code(code)


def induce_coordinate_morphisms(source_pairs,*,max_candidates=4):
    if not 2<=len(source_pairs)<=32 or not 1<=max_candidates<=16:
        raise ValueError("SOURCE-only bounded coordinate invention required")
    train=tuple(source_pairs)
    if not all(_rect(x) and _rect(y) for x,y in train):
        return ()
    # Preserve the original simple-expression/graph paths. Coordinate
    # invention is useful precisely when the required output has an altered
    # size or new index support unavailable to those paths.
    if all(len(x)==len(y) and len(x[0])==len(y[0])
           for x,y in train):
        return ()
    rows=_axis_candidates(train,0)
    columns=_axis_candidates(train,1)
    choices=[]
    for rm,rk in rows:
        for cm,ck in columns:
            if all(source_same_value(
                    _apply(x,rm,rk,cm,ck),y) for x,y in train):
                complexity=(
                    1+int(rm!="identity")+int(cm!="identity")
                    +int(rk!=1)+int(ck!=1)+
                    int(rm.startswith("alternate"))+
                    int(cm.startswith("alternate")))
                choices.append((complexity,rm,rk,cm,ck))
    choices.sort()
    result=[]
    for cost,rm,rk,cm,ck in choices:
        code=_compiled_code(rm,rk,cm,ck)
        if any(old.program==code for old in result):
            continue
        result.append(StructuralFactor(
            code,"source-inferred-coordinate/"+rm+"+"+cm,
            cost,len(train)))
        if len(result)>=max_candidates:
            break
    return tuple(result)
