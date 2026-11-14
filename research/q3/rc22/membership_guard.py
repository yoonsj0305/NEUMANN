"""RC22 W-method guard for learned DFA syntax. CLASSICAL, not neural.
Target hidden transitions are NEVER exposed. Membership calls and externally
TRUSTED target-state bound U are prerequisites for conditional certification.
"""
from collections import deque
from itertools import product
from hashlib import sha256
import json

def run(h,word):
    s=h["start"]
    for bit in word:s=h["transitions"][s][bit]
    return int(h["outputs"][s])

def suite(h,U,cap=500000):
    if not isinstance(U,int) or isinstance(U,bool) or U<1:
        return {"status":"UNKNOWN_NO_TRUSTED_BOUND"}
    states=tuple(h["states"]);m=len(states)
    if not states or m>U:return {"status":"UNKNOWN_EXCEEDS_BOUND"}
    access={h["start"]:""};queue=deque([h["start"]])
    try:
        while queue:
            s=queue.popleft()
            for a in "01":
                v=h["transitions"][s][a]
                if v not in access:access[v]=access[s]+a;queue.append(v)
        if len(access)!=m:return {"status":"UNKNOWN_UNREACHABLE"}
        W={""}
        for i in range(m):
            for j in range(i+1,m):
                q=deque([(states[i],states[j],"")]);seen={(states[i],states[j])}
                suffix=None
                while q:
                    a,b,w=q.popleft()
                    if h["outputs"][a]!=h["outputs"][b]:suffix=w;break
                    for char in "01":
                        v=(h["transitions"][a][char],h["transitions"][b][char])
                        if v not in seen:seen.add(v);q.append((v[0],v[1],w+char))
                if suffix is None:return {"status":"UNKNOWN_NONMINIMAL"}
                W.add(suffix)
        cover=set(access.values())|{p+a for p in access.values() for a in "01"}
        gap=U-m
        if gap>24 or len(cover)*len(W)*(2**(gap+1)-1)>cap:
            return {"status":"UNKNOWN_TEST_BUDGET"}
        q={p+mid+w for depth in range(gap+1)
           for mid_tuple in product("01",repeat=depth)
           for mid in ("".join(mid_tuple),)
           for p in cover for w in W}
    except (KeyError,TypeError):return {"status":"UNKNOWN_MALFORMED_DFA"}
    return {"status":"READY","words":sorted(q,key=lambda w:(len(w),w)),
            "U":U,"model_states":m}

class ProofCarryingAdmission:
    def __init__(self,membership,trusted_U=None):
        self.membership=membership;self.trusted_U=trusted_U
        self.cache={}
    def query(self,word):
        if word not in self.cache:self.cache[word]=int(self.membership(word))
        return self.cache[word]
    def check(self,h):
        result=suite(h,self.trusted_U)
        if result["status"]!="READY":return result
        for word in result["words"]:
            if self.query(word)!=run(h,word):
                return {"status":"COUNTEREXAMPLE","word":word}
        return {"status":"CONDITIONAL_W_METHOD_CERTIFIED",
                "hypothesis_sha256":sha256(json.dumps(h,sort_keys=True).encode()).hexdigest(),
                "trusted_U":self.trusted_U,"suite_words":len(result["words"]),
                "unique_membership_words":len(self.cache),
                "assumption":"unknown target is complete binary Moore DFA of at most U states"}

def block_bare_none(_result):
    # RC21's former `if ce is None: PASS` was UNSOUND with bounded callbacks.
    return {"status":"UNKNOWN_EQUIVALENCE_PROOF_MISSING"}
