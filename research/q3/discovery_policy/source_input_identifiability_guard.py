"""Finite-input source identifiability certificate, classical and fail-closed.

For a language with bit extraction, boolean AND, conditional selection, and
output complement, any target input t outside a finite observed set S admits
an executable guard M with M(s)=0 (all s in S), M(t)=1. Thus for any existing
source-fitting program F, the program IF M THEN NOT F ELSE F also source-fits
and disagrees at t. This proves underdetermination relative to THAT grammar;
it is not a generator of correct heldout labels or any neural invention.
"""
from typing import Iterable

def greedy_distinguishing_bits(source_inputs: Iterable[int], target: int,
                              width: int = 64) -> dict:
    if type(width) is not int or not 1 <= width <= 256:
        return {"status":"HOLD_BAD_WIDTH","global_questions":"OPEN"}
    limit=1<<width
    samples=list(source_inputs)
    if type(target) is not int or not 0<=target<limit or any(
        type(x) is not int or not 0<=x<limit for x in samples):
        return {"status":"HOLD_BAD_INPUT","global_questions":"OPEN"}
    if target in samples:
        return {"status":"NO_DISTINGUISHABLE_GUARD_WITH_TARGET_IN_SOURCE",
                "global_questions":"OPEN","may_certify_unique_function":False}
    pending=set(samples)
    bits=[]
    while pending:
        choices=[]
        for j in range(width):
            if j in bits:continue
            eliminated=sum(((x>>j)&1)!=((target>>j)&1) for x in pending)
            choices.append((eliminated,-j,j))
        eliminated,_,j=max(choices)
        if eliminated==0:
            return {"status":"HOLD_CANNOT_COVER",
                    "global_questions":"OPEN","may_certify_unique_function":False}
        bits.append(j)
        pending={x for x in pending if ((x>>j)&1)==((target>>j)&1)}
    return {"status":"INPUT_ONLY_DISTINGUISHING_GUARD_CONSTRUCTIBLE",
            "width":width,"target":target,"source_count":len(samples),
            "selected_bits":bits,"count_bits":len(bits),
            "proof":"all observed x differ from target in at least one selected bit",
            "may_certify_unique_function":False,"global_questions":"OPEN"}

def guard_value(selected_bits: list[int], x: int, t: int) -> int:
    return int(all(((x>>j)&1)==((t>>j)&1) for j in selected_bits))

def verify_guard_on_inputs(certificate: dict, source_inputs: Iterable[int]) -> bool:
    if certificate.get("status")!="INPUT_ONLY_DISTINGUISHING_GUARD_CONSTRUCTIBLE":
        return False
    bits=certificate["selected_bits"]
    t=certificate["target"]
    return (guard_value(bits,t,t)==1
            and all(guard_value(bits,x,t)==0 for x in source_inputs))
