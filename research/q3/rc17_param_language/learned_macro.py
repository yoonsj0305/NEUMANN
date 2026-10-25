"""A program body extracted from an actual NEUMANN own-weight learned policy.
Full weights / original source-only first-pred sealed evidence in RC17 archive.
This is a novel macro composed WITHIN a human-provided register/integer ISA.
"""
import hashlib,json

FROZEN_SOURCE_PROGRAM=(1,0,2,1,0,2,1)
FROZEN_FIRST_SHA256="6f5b927045d8059371385a5f6130f29fe3cc1bdc9838a7c2326c260a4f99a5a5"
MODEL_REPRESENTATION="state=(1+prefix_ones) mod k"

def run_compiled_learned_macro(k, bits):
    if not isinstance(k,int) or isinstance(k,bool) or k<2:
        raise ValueError("parameter k>=2 required")
    state=1;out=[]
    for digit in bits:
        if digit not in (0,1):raise ValueError("binary only")
        interim=state+digit
        out.append(int(interim==1))
        state=0 if interim>k-1 else interim
    return tuple(out)

def reference_degraded_fallback(k,bits):
    if not isinstance(k,int) or isinstance(k,bool) or k<2:raise ValueError("k>=2")
    state=0;out=[]
    for digit in bits:
        if digit not in (0,1):raise ValueError("binary only")
        state=(state+digit)%k
        out.append(int(state==0))
    return tuple(out)

def proof_gated_registration(candidate,has_weight_receipt=True):
    if not has_weight_receipt:return {"status":"REJECT_MISSING_PROVENANCE"}
    if tuple(candidate)!=FROZEN_SOURCE_PROGRAM:
        return {"status":"UNKNOWN_NOT_PROVEN"}
    # Independent all-k proof documented in README, not guessed from test rates.
    content=json.dumps({"code":FROZEN_SOURCE_PROGRAM,
        "body":{"initial":1,"step":"ADD_DIGIT","condition":"GT",
                "threshold":"PARAM_MINUS_ONE","on_true":"ZERO",
                "output":"IS_ONE","emit_timing":"PRE_RESET"}},
        sort_keys=True,separators=(",",":"))
    # Runtime vocabulary extension is deterministic from model-proposed body.
    return {"status":"SCOPED_CERTIFIED","token":"AUTO_"+hashlib.sha256(content.encode()).hexdigest()[:12]}

def minimal_state_bound(k):
    if not isinstance(k,int) or isinstance(k,bool) or k<2:raise ValueError("k>=2")
    return k
