"""A strict proof/admission and provenance guard for RC26/27.

Read-only typed result; this file itself does not prove correctness: it
checks independent frozen verifier receipts. Full proof/grader and Torch
checkpoints live in the SHA-audited conversation ZIP.
"""
from dataclasses import dataclass
@dataclass(frozen=True)
class FrozenEvidence:
    seed:int
    kind:str
    source:str
    formal:str
    minimal:str
    neural_horizon_errors:int
    symbolic_horizon_errors:int
    horizon_bits:int=262144

def admit(e:FrozenEvidence):
    if e.kind!="trained_gru":
        return "UNKNOWN_NOT_OWN_WEIGHT_SOURCE"
    if e.source!="SCOPED_COMPILED":
        return "UNKNOWN_NOT_COMPILABLE"
    if e.formal!="PROVED_EQUIVALENT_FINITE_PROGRAM":
        return "UNKNOWN_NO_ALL_LENGTH_PROOF"
    if e.minimal!="PROVED_MINIMAL":
        return "UNKNOWN_MINIMALITY"
    if e.symbolic_horizon_errors!=0:
        return "UNKNOWN_LONG_HORIZON_CONTRADICTION"
    return "SCOPED_CERTIFIED"

def runtime_choice(symbolic_cpu,direct_cpu,direct_proved=True):
    if direct_proved and direct_cpu<=symbolic_cpu:
        return "CLASSICAL_EXACT_FIRST"
    return "NO_EFFICIENCY_AUTHORITY"

FROZEN_LONG_HORIZON={
 402:{"k":3,"neural":0,"symbolic":0,"cert":True},
 403:{"k":3,"neural":5066,"symbolic":0,"cert":True},
 404:{"k":3,"neural":0,"symbolic":0,"cert":True},
 405:{"k":3,"neural":1,"symbolic":0,"cert":True},
 502:{"k":5,"neural":190,"symbolic":0,"cert":True},
 503:{"k":5,"neural":45400,"symbolic":0,"cert":True},
 504:{"k":5,"neural":50729,"symbolic":50729,"cert":False},
 505:{"k":5,"neural":74596,"symbolic":0,"cert":True},
}
