"""Q3 task-agnostic *partial causal credit*, never a correctness certificate.

One universal typed JSON observer computes whether a proposed executable
transform moves SOURCE outputs closer to observed SOURCE labels than identity.
This is an update signal *for the model policy*, not a hidden new operator:
no ARC, image, graph, string, DFA, coordinate or task-family branches.
Independent SOURCE checks and original author TARGET gold are not consulted.

A positive advantage only says "less wrong than another failed program".
Only exact independent SOURCE and original TEST may produce a Q3 proof.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

from .open_program_inventor import source_same_value


def _size(v):
    if isinstance(v,list):
        return max(1,sum(_size(x) for x in v))
    if isinstance(v,dict):
        return max(1,sum(_size(x) for x in v.values()))
    return 1


def _raw_distance(a,b):
    """Generic nested JSON tree edit cost, no learned or coded domain solver."""
    if source_same_value(a,b):
        return 0
    if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):
        n=min(len(a),len(b))
        return (sum(_raw_distance(a[i],b[i]) for i in range(n))
                +sum(_size(x) for x in a[n:])
                +sum(_size(x) for x in b[n:]))
    if isinstance(a,dict) and isinstance(b,dict):
        common=set(a)&set(b)
        return (sum(_raw_distance(a[k],b[k]) for k in common)
                +sum(_size(a[k]) for k in set(a)-common)
                +sum(_size(b[k]) for k in set(b)-common))
    # Avoid rewarding numerical coincidence (e.g. 7 closer to 8 than 6);
    # these are ordinal identifiers in some problem families.
    return max(_size(a),_size(b))


@dataclass(frozen=True)
class SourceSemanticCredit:
    gain:float
    exact:int
    count:int
    identity_distance:int
    candidate_distance:int
    status:str


def source_semantic_credit(pairs,execution):
    """Source-only reward. An unexecuted/empty candidate has no preference."""
    pairs=tuple(pairs)
    if (not pairs or execution.status!="EXECUTED"
            or len(execution.outputs)!=len(pairs)):
        return SourceSemanticCredit(0.0,0,len(pairs),0,0,"ABSTAIN_EXECUTION")
    identity_distance=sum(
        _raw_distance(x,y) for x,y in pairs)
    candidate_distance=sum(
        _raw_distance(got,y)
        for got,(_,y) in zip(execution.outputs,pairs))
    exact=sum(source_same_value(got,y)
              for got,(_,y) in zip(execution.outputs,pairs))
    if identity_distance==0:
        return SourceSemanticCredit(
            0.0,exact,len(pairs),0,candidate_distance,
            "ABSTAIN_UNIDENTIFIABLE_IDENTITY")
    improvement=(identity_distance-candidate_distance)/max(
        1,identity_distance)
    if not math.isfinite(improvement):
        raise ValueError("invalid SOURCE credit")
    return SourceSemanticCredit(
        round(max(-1.0,min(1.0,improvement)),8),
        exact,len(pairs),identity_distance,candidate_distance,
        "SOURCE_PARTIAL_ONLY" if exact<len(pairs) else "SOURCE_TRAIN_FIT_ONLY")


def preference_from_source(pairs,runner,first,second,*,margin=0.02):
    """Admit two model-authored programs only after SOURCE execution.

    True credit is determined by their own SOURCE outputs, not code text or
    hidden original labels. A positive partial does not mean task solved.
    """
    if not 0<margin<=1:
        raise ValueError("pre-registered positive causal margin required")
    from .open_program_inventor import validate_code
    a=validate_code(first);b=validate_code(second)
    if a==b:
        return None
    src=list(pairs)
    checked=[]
    for code in (a,b):
        out=runner.evaluate(code,[x for x,y in src])
        checked.append(source_semantic_credit(src,out))
    ca,cb=checked
    if (ca.status.startswith("ABSTAIN") or cb.status.startswith("ABSTAIN")):
        return None
    high,low=(0,1) if (ca.exact,ca.gain)>(cb.exact,cb.gain) else (1,0)
    better=checked[high]
    worse=checked[low]
    # Never reward two equally wrong programs or a method worse than
    # the trivial identity. Require source-exact improvement or gain.
    if (better.gain<=0 or
        better.gain-worse.gain<margin and better.exact==worse.exact):
        return None
    return {
        "positive_program":(a,b)[high],
        "negative_program":(a,b)[low],
        "positive_credit":better.__dict__,
        "negative_credit":worse.__dict__,
        "independent_source_certified":False,
        "original_target_gold_read":False,
    }
