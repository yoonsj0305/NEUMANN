"""Q3 source-residual program COMPOSITION, not task-specific answer routing.

A partial SOURCE program is not useless. The previous learner accumulated
107 partly-correct independently SOURCE-checked hypotheses, but had no
program algebra for combining independently useful causal submethods.

This generator discovers a new *executable* method from multiple distinct
SOURCE changes. Two general forms:
 (i) parallel typed atomic relations applied at once (no destructive chain);
(ii) sequential composition of two verified-format Python method candidates.

Input is only the current training SOURCE, NEVER independent SOURCE checks
or original test gold. All generated programs must pass the exact same
pre-existing independent Docker SOURCE and original-author gates as A/B/C.
Uniform A and trained C receive the same compositional language and caps.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .open_program_inventor import source_same_value,validate_code
from .q3_structure_factorization import _all_leaves,StructuralFactor
from .q3_source_residual_probes import (
    induce_source_residual_probes,source_edit_f1)


def _parallel_code(pairs):
    if len(pairs)<2 or len(pairs)>8:
        return None
    dictionary="{"+",".join(
        repr(src)+":"+repr(dst) for src,dst in pairs)+"}"
    code=(
        "def transform(x):\n"
        "    mapping="+dictionary+"\n"
        "    def rewrite(v):\n"
        "        if isinstance(v,list):\n"
        "            return [rewrite(t) for t in v]\n"
        "        if isinstance(v,str):\n"
        "            return ''.join(mapping.get(t,t) for t in v)\n"
        "        return mapping.get(v,v)\n"
        "    return rewrite(x)")
    return validate_code(code)


def _apply_parallel(v,mapping):
    if type(v) is list:
        return [_apply_parallel(x,mapping) for x in v]
    if type(v) is str:
        return "".join(mapping.get(c,c) for c in v)
    return mapping.get(v,v)


def _sequential_code(first,second):
    """Compose methods with lexical isolation; no code evaluation at build."""
    first=validate_code(first)
    second=validate_code(second)
    def nested(src,name):
        lines=src.splitlines()
        if lines[0]!="def transform(x):":
            raise ValueError("noncanonical SOURCE transform cannot compose")
        return ("    def "+name+"(x):\n"
                +"\n".join("    "+line for line in lines[1:]))
    code=("def transform(x):\n"
          +nested(first,"stage1")+"\n"
          +nested(second,"stage2")+"\n"
          +"    return stage2(stage1(x))")
    return validate_code(code)


def induce_source_compositions(train,*,max_candidates=6):
    """Generate bounded new source-dependent methods, no domain dispatch."""
    if not 2<=len(train)<=32 or not 1<=max_candidates<=16:
        raise ValueError("bounded original SOURCE input required")
    observations=Counter()
    for x,y in train:
        pairs=_all_leaves([(x,y)])
        if pairs is None:continue
        observations.update(
            (v,w) for v,w in pairs
            if type(v) in (int,str) and type(w) in (int,str)
            and not source_same_value(v,w))
    grouped={}
    for (src,dst),n in observations.items():
        grouped.setdefault(src,[]).append((dst,n))
    best={}
    for src,changes in grouped.items():
        dst,n=sorted(changes,key=lambda p:(-p[1],repr(p[0])))[0]
        best[src]=dst
    candidates=[]
    if len(best)>=2:
        mapping=sorted(best.items(),key=lambda a:repr(a[0]))[:8]
        code=_parallel_code(mapping)
        if code is not None:
            exact=all(source_same_value(
                _apply_parallel(x,dict(mapping)),y) for x,y in train)
            candidates.append(StructuralFactor(
                code,"source-composition/parallel-atomic-relation",
                2 if exact else 18+len(mapping),len(train)))
    probes=induce_source_residual_probes(train,max_probes=4)
    for i,first in enumerate(probes):
        for j,second in enumerate(probes):
            if i==j:continue
            try:
                code=_sequential_code(first.program,second.program)
            except (ValueError,TypeError):
                continue
            if len(code)>6000:continue
            candidates.append(StructuralFactor(
                code,"source-composition/sequential-program",
                17+i+j,len(train)))
    seen=set()
    sorted_candidates=[]
    for candidate in sorted(candidates,key=lambda x:(
            x.description_length,x.representation,x.program)):
        if candidate.program in seen:continue
        seen.add(candidate.program)
        sorted_candidates.append(candidate)
        if len(sorted_candidates)>=max_candidates:
            break
    return tuple(sorted_candidates)
