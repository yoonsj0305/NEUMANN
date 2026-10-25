"""Q3 research-only state-growth compiler driven by a learned equivalence scorer.

Own-weight 3-parameter classifier *only judges observed residual equality*.
State exploration, probe depth and compiler are HUMAN CODED and classical.
Never claim global Q3 PASS or universal CERTIFIED from bounded observations.
"""
from itertools import product

W_MAX=-4.431497573852539
W_MEAN=-4.19536828994751
BIAS=2.5596377849578857

def learned_equal_future(a,b):
    if len(a)!=len(b):raise ValueError("Different signature lengths")
    n=sum(x!=y for x,y in zip(a,b))
    return W_MAX*int(bool(n))+W_MEAN*n/max(len(a),1)+BIAS>=0

def invent(oracle, depth=5):
    # oracle: input word tuple -> output word tuple, reset per call
    suffixes=tuple(s for length in range(1,depth+1)
                   for s in product((0,1),repeat=length))
    prefix_states=[()]
    def signature(p):
        return tuple(bit for suf in suffixes
                     for bit in oracle(p+suf)[len(p):])
    observed_signatures=[signature(())]
    transition=[];output=[]
    i=0
    while i<len(prefix_states):
        prefix=prefix_states[i]
        nxt=[];emit=[]
        for symbol in (0,1):
            q=prefix+(symbol,)
            sig=signature(q)
            matches=[k for k,other in enumerate(observed_signatures)
                     if learned_equal_future(sig,other)]
            if len(matches)>1:raise ValueError("Ambiguous observed equivalence")
            if matches:target=matches[0]
            else:
                target=len(prefix_states)
                prefix_states.append(q)
                observed_signatures.append(sig)
            nxt.append(target);emit.append(int(oracle(q)[-1]))
        transition.append(nxt);output.append(emit)
        i+=1
        if i>64:raise RuntimeError("Incomplete evidence for bounded closure")
    return {"transition":transition,"output":output,"states":len(prefix_states),
            "status":"PROVISIONAL_NEEDS_INDEPENDENT_CLASS_OR_BISIMULATION_PROOF"}

def run(operator,input_word):
    state=0;out=[]
    for sym in input_word:
        out.append(operator["output"][state][sym])
        state=operator["transition"][state][sym]
    return tuple(out)
