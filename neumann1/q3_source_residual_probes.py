"""Q3 source-residual *probes* for learning what remains unexplained.

The previous representation learner emitted ZERO probes on 50 genuine
independently authored ARC2 SOURCE tasks: no program perfectly fit train
examples, so ZERO actual SOURCE-check evaluations updated the policy.

This interface admits *partially explanatory*, executable hypotheses instead
of requiring full training fit before the learner is even allowed to test it.
SOURCE test gold remains inaccessible. Candidate operations use the SAME
pre-existing generic nested-value/relative-coordinate executable substrate
for learned C and unlearned classical A, without benchmark/name dispatch.

Probe gains mean improvement on a heldout SOURCE edit, NEVER a completely
solved original or independently invented operator grammar.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Any

from .open_program_inventor import source_same_value,validate_code
from .q3_structure_factorization import (
    _all_leaves,_move_label,_move_label_program,_symbol_mode)


@dataclass(frozen=True)
class SourceProbe:
    program: str
    representation: str
    description_length: int
    source_train_edit_f1: float
    # This pure interpretation is owned only by SOURCE candidate synthesis.
    # Independent SOURCE correctness is still established using the
    # compiled program in no-network Docker, not this helper.
    execute: Callable[[Any],Any] = field(
        default=lambda value:value,compare=False,repr=False)


def _aligned_triplets(inp,goal,proposal):
    if (type(inp) is list and type(goal) is list
            and type(proposal) is list):
        if len(inp)!=len(goal) or len(inp)!=len(proposal):
            return None
        triplets=[]
        for a,b,c in zip(inp,goal,proposal):
            child=_aligned_triplets(a,b,c)
            if child is None:return None
            triplets.extend(child)
        return triplets
    if any(type(x) is list for x in (inp,goal,proposal)):
        return None
    return [(inp,goal,proposal)]


def source_edit_f1(inp,expected,proposed):
    """Typed SOURCE delta F1, not background-dominated pixel accuracy."""
    triples=_aligned_triplets(inp,expected,proposed)
    if triples is None or not triples:
        return 0.0
    tp=fp=fn=0
    for old,true,pred in triples:
        need_change=not source_same_value(old,true)
        proposed_change=not source_same_value(old,pred)
        if need_change and source_same_value(pred,true):
            tp+=1
        elif proposed_change:
            fp+=1
        if need_change and not source_same_value(pred,true):
            fn+=1
    denom=2*tp+fp+fn
    return 2*tp/denom if denom else 0.0


def _replace_program(src,dst):
    if type(src) not in (int,str) or type(dst) not in (int,str):
        return None
    # Typed, recursively lifted atomic rewrite. No source position, benchmark
    # name or output target identity enters the learned method.
    code=(
        "def transform(x):\n"
        f"    src={repr(src)}\n"
        f"    dst={repr(dst)}\n"
        "    def rewrite(v):\n"
        "        if isinstance(v,list):\n"
        "            return [rewrite(t) for t in v]\n"
        "        if isinstance(v,str):\n"
        "            return ''.join(dst if c==src else c for c in v)\n"
        "        return dst if v==src else v\n"
        "    return rewrite(x)")
    return validate_code(code)


def induce_source_residual_probes(train,*,max_probes=8):
    """Bounded current SOURCE-only executable probes with partial credit."""
    if not 2<=len(train)<=32 or not 1<=max_probes<=32:
        raise ValueError("bounded disjoint SOURCE observations required")
    pairs=list(train)
    proposals=[]
    differences=Counter()
    for inp,out in pairs:
        vals=_all_leaves([(inp,out)])
        if vals:
            differences.update(
                (a,b) for a,b in vals if
                type(a) in (int,str) and type(b) in (int,str)
                and not source_same_value(a,b))
    for (src,dst),count in differences.most_common(8):
        code=_replace_program(src,dst)
        if code is None:continue
        proposals.append((code,"probe/atomic-relation",
                          5+len(repr(src))+len(repr(dst)),
                          lambda inp,a=src,b=dst:_rewrite(inp,a,b)))
    # Generic relative displacement of one recurring source token over
    # indexed nested sequences. No special ARC/scene/category handler.
    if all(
        type(x) is list and x and type(x[0]) is list and
        type(y) is list and len(x)==len(y) and len(x[0])==len(y[0])
        for x,y in pairs):
        bg=_symbol_mode(pairs[0][0])
        if bg is not None:
            freq=Counter(v for row in pairs[0][0] for v in row)
            for token,_ in freq.most_common(4):
                if source_same_value(token,bg):
                    continue
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    try:
                        code=_move_label_program(token,dr,dc,bg)
                    except (ValueError,TypeError):
                        continue
                    proposals.append((
                        code,"probe/relative-motion",12,
                        lambda inp,c=token,r=dr,d=dc,b=bg:
                            _move_label(inp,c,r,d,b)))
    filtered=[]
    seen=set()
    for program,label,cost,fn in proposals:
        if program in seen:continue
        seen.add(program)
        try:
            fit=sum(source_edit_f1(x,y,fn(x)) for x,y in pairs)/len(pairs)
        except (TypeError,ValueError,IndexError,KeyError):
            continue
        if fit>0.0:
            filtered.append(SourceProbe(
                program,label,cost,round(fit,6),fn))
    filtered.sort(key=lambda p:(
        -p.source_train_edit_f1,p.description_length,
        p.representation,p.program))
    return tuple(filtered[:max_probes])


def _rewrite(value,src,dst):
    if type(value) is list:
        return [_rewrite(v,src,dst) for v in value]
    if type(value) is str:
        return "".join(dst if c==src else c for c in value)
    return dst if value==src else value
