"""Q3 bounded membership-only W-method conformance. Classical Chow/Vasilevskii.
This is a CONDITIONAL complete test only with a separately justified bound
on the number of target states. Never infer that bound from observed outputs.
Target transitions must not be imported by the verification algorithm.
"""
from itertools import product
from collections import deque

def execute(program,word):
    s=0; out=[]
    for a in word:
        out.append(program["output"][s][a])
        s=program["transition"][s][a]
    return tuple(out)

def state_cover(candidate):
    nexts=candidate["transition"]; n=len(nexts)
    reach={0:()};q=deque([0])
    while q:
        s=q.popleft()
        for a,t in enumerate(nexts[s]):
            if t not in reach:
                reach[t]=reach[s]+(a,)
                q.append(t)
    if len(reach)!=n:raise ValueError("candidate must be reachable")
    return tuple(reach[i] for i in range(n))

def suffix_output(candidate,start,word):
    o=[];s=start
    for a in word:
        o.append(candidate["output"][s][a]);s=candidate["transition"][s][a]
    return tuple(o)

def pair_witness(candidate,a,b):
    alphabet=range(len(candidate["transition"][0]))
    q=deque([(a,b,())]);seen={(a,b)}
    while q:
        p,r,w=q.popleft()
        for x in alphabet:
            if candidate["output"][p][x]!=candidate["output"][r][x]:
                return w+(x,)
            p1=candidate["transition"][p][x]
            r1=candidate["transition"][r][x]
            if (p1,r1) not in seen:
                seen.add((p1,r1));q.append((p1,r1,w+(x,)))
    return None

def characterization(candidate):
    n=len(candidate["transition"])
    W=set()
    for i in range(n):
        for j in range(i+1,n):
            suffix=pair_witness(candidate,i,j)
            if suffix is None:raise ValueError("minimize candidate first")
            W.add(suffix)
    if not W:
        W.update((a,) for a in range(len(candidate["transition"][0])))
    return tuple(sorted(W,key=lambda x:(len(x),x)))

def bounded_membership_conformance(candidate,membership,trusted_upper_bound,
                                  max_queries=200000):
    """Use ONLY resettable input/output membership oracle.
    A certificate is CONDITIONAL on complete deterministic Mealy target with
    at most trusted_upper_bound states, identical finite alphabets and reset.
    """
    if trusted_upper_bound is None:
        return {"status":"UNKNOWN_NO_TRUSTED_STATE_BOUND","queries":0}
    if not isinstance(trusted_upper_bound,int) or trusted_upper_bound<1:
        raise ValueError("invalid bound")
    n=len(candidate["transition"])
    if n>trusted_upper_bound:raise ValueError("candidate exceeds trusted bound")
    A=tuple(range(len(candidate["transition"][0])))
    P=state_cover(candidate)
    W=characterization(candidate)
    seen=set();calls=0
    # Standard W-method: P * A^{<= U-n+1} * W
    for access in P:
        for depth in range(trusted_upper_bound-n+2):
            for middle in product(A,repeat=depth):
                for suffix in W:
                    word=access+middle+suffix
                    if word in seen:continue
                    seen.add(word)
                    calls+=1
                    if calls>max_queries:
                        return {"status":"UNKNOWN_BUDGET","queries":calls}
                    if tuple(membership(word))!=execute(candidate,word):
                        return {"status":"COUNTEREXAMPLE","witness":word,
                                "queries":calls}
    return {"status":"CONDITIONAL_CERTIFIED_UNDER_TRUSTED_BOUND",
            "bound":trusted_upper_bound,"candidate_states":n,"queries":calls}
