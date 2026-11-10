"""Q3 autonomous SOURCE factorization: periodic coordinate lattice + residual causal rule.

The existing structural solver can infer a separable index map when the
output is a direct reindexing of the input. That leaves an entire class
unrepresentable: input values are repeated into a periodic output whose
base cell has been *altered by a causal relation among source elements*.

This generator does NOT implement a named visual puzzle. For any rectangular
sequence of typed atomic values, it tests whether all SOURCE outputs are
periodic over the INPUT dimensions. If so, it extracts the shortest missing
residual and tries a bounded generic directed-neighbor relation from every
non-background input item to a previously background destination. The
offset and new symbol are *inferred from SOURCE*, not hardcoded. It compiles
one self-contained Python transform(x) for the SAME existing no-network
Docker SOURCE verifier. The reserved SOURCE checks and author TARGET output
are never passed into induction.

This is invention of an executable composition in a fixed human-provided
meta-grammar. It is not independent invention of that meta-grammar; Q3 OPEN.
"""
from __future__ import annotations

from collections import Counter

from .open_program_inventor import source_same_value,validate_code
from .q3_structure_factorization import StructuralFactor


def _rect(v):
    return bool(
        type(v) is list and 1<=len(v)<=30
        and type(v[0]) is list and 1<=len(v[0])<=30
        and all(type(row) is list and len(row)==len(v[0])
                and all(type(x) in (int,str,bool) for x in row)
                for row in v))


def _background(v):
    counts=Counter(item for row in v for item in row)
    return sorted(counts.items(),key=lambda kv:(-kv[1],repr(kv[0])))[0][0]


def _periodic_unit(source,output):
    """Discover the repeated quotient lattice rather than the target motif."""
    if not _rect(source) or not _rect(output):
        return None
    h,w=len(source),len(source[0])
    oh,ow=len(output),len(output[0])
    if oh%h or ow%w or not (2<=oh//h<=5 and 2<=ow//w<=5):
        return None
    unit=[row[:w] for row in output[:h]]
    if not all(source_same_value(
            output[r][c],unit[r%h][c%w])
            for r in range(oh) for c in range(ow)):
        return None
    return unit,oh//h,ow//w


def _apply(source,row_multiplier,col_multiplier,dr,dc,new_symbol):
    h,w=len(source),len(source[0])
    bg=_background(source)
    unit=[row[:] for row in source]
    for r,row in enumerate(source):
        for c,value in enumerate(row):
            if source_same_value(value,bg):
                continue
            rr=(r+dr)%h
            cc=(c+dc)%w
            if source_same_value(source[rr][cc],bg):
                unit[rr][cc]=new_symbol
    return [
        [unit[r%h][c%w] for c in range(w*col_multiplier)]
        for r in range(h*row_multiplier)
    ]


def _compile(rmul,cmul,dr,dc,new_symbol):
    return validate_code(
        "def transform(x):\n"
        f"    rmul={rmul}\n"
        f"    cmul={cmul}\n"
        f"    dr={dr}\n"
        f"    dc={dc}\n"
        f"    new_symbol={repr(new_symbol)}\n"
        "    h=len(x)\n"
        "    w=len(x[0])\n"
        "    counts={}\n"
        "    for row in x:\n"
        "        for v in row:\n"
        "            counts[v]=counts.get(v,0)+1\n"
        "    bg=sorted(counts,key=lambda v:(-counts[v],str(v)))[0]\n"
        "    unit=[row[:] for row in x]\n"
        "    for r in range(h):\n"
        "        for c in range(w):\n"
        "            if x[r][c]==bg:continue\n"
        "            rr=(r+dr)%h\n"
        "            cc=(c+dc)%w\n"
        "            if x[rr][cc]==bg:\n"
        "                unit[rr][cc]=new_symbol\n"
        "    return [[unit[r%h][c%w] for c in range(w*cmul)]\n"
        "            for r in range(h*rmul)]")


def induce_periodic_residual_rules(source_pairs,*,max_candidates=4):
    """Source-only low-description-length periodic + relational rewrite."""
    if not 2<=len(source_pairs)<=32 or not 1<=max_candidates<=16:
        raise ValueError("bounded original SOURCE required for causal invention")
    pairs=tuple(source_pairs)
    quotient=[]
    multipliers=set()
    for x,y in pairs:
        found=_periodic_unit(x,y)
        if found is None:
            return ()
        unit,rmul,cmul=found
        quotient.append((x,unit))
        multipliers.add((rmul,cmul))
    if len(multipliers)!=1:
        return ()
    rmul,cmul=next(iter(multipliers))
    # Residual symbols must have observable, repeatable causal support.
    symbols=set()
    for x,unit in quotient:
        bg=_background(x)
        differences=[
            unit[r][c] for r in range(len(x)) for c in range(len(x[0]))
            if not source_same_value(x[r][c],unit[r][c])
            and source_same_value(x[r][c],bg)
        ]
        if not differences:
            return ()
        symbols.update(differences)
        if len(symbols)>16:
            return ()
        # This grammar cannot hide unexpected deletions/mutations as additions.
        if any(not source_same_value(x[r][c],unit[r][c])
               for r in range(len(x)) for c in range(len(x[0]))
               if not source_same_value(x[r][c],bg)):
            return ()
    scored=[]
    for symbol in sorted(symbols,key=repr):
        for dr in range(-2,3):
            for dc in range(-2,3):
                if dr==0 and dc==0:continue
                if all(source_same_value(
                        _apply(x,rmul,cmul,dr,dc,symbol),y)
                       for x,y in pairs):
                    code=_compile(rmul,cmul,dr,dc,symbol)
                    complexity=(
                        10+abs(dr)+abs(dc)
                        +len(repr(symbol))
                        +int(dr<0)+int(dc<0))
                    scored.append((complexity,dr,dc,code))
    scored.sort(key=lambda row:(row[0],row[1],row[2],row[3]))
    return tuple(
        StructuralFactor(
            code,"source-inferred-residual-periodic-neighbor",
            complexity,len(pairs))
        for complexity,dr,dc,code in scored[:max_candidates]
    )
