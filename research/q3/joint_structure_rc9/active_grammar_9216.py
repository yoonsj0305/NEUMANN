"""RC10: source-only active observer for human-supplied complete 9216 grammar.
CLASSICAL prior art technique. No model new-DSL, no global Q3/Q4 PASS.
Strictly separate candidate-only query choice from oracle membership answers.
"""
from itertools import product
from collections import Counter

ROUTES=("j","i-j","i","0","prev-diag","prev-j")
POOL=tuple((n,a,b) for n in (1,2,3) for a in range(1<<n) for b in range(1<<n))
PROGRAMS=tuple((r,tuple((g>>i)&1 for i in range(4)),
    tuple((h>>i)&1 for i in range(4)))
    for r in product(ROUTES,repeat=2) for g in range(16) for h in range(16))

def idx(name,i,j):
    if name=="j":return j
    if name=="i-j":return i-j
    if name=="i":return i
    if name=="0":return 0
    if name=="prev-diag":return max(0,i-j-1)
    if name=="prev-j":return max(0,j-1)
    raise ValueError(name)

def execute(candidate,n,a,b):
    (ra,rb),g,h=candidate;out=0
    for i in range(n):
        c=0
        for j in range(i+1):
            x=(a>>idx(ra,i,j))&1;y=(b>>idx(rb,i,j))&1
            c=h[c+2*g[x+2*y]]
        out|=c<<i
    return out

def proved_gf2(candidate):
    route,g,h=candidate
    return (route in (("j","i-j"),("i-j","j")) and
      all(h[c+2*g[a+2*b]]==(c^(a&b))
      for a,b,c in product((0,1),repeat=3)))

class ActiveObserver:
    def __init__(self):
        self.responses=tuple(bytes(execute(c,*q) for c in PROGRAMS) for q in POOL)
    def identify(self,membership,trusted_complete_grammar=False):
        remaining=list(range(9216));used=set();trace=[]
        while remaining and not all(proved_gf2(PROGRAMS[j]) for j in remaining):
            best=None
            for qi in range(84):
                if qi in used:continue
                counts=Counter(self.responses[qi][j] for j in remaining)
                values=list(counts.values())
                key=(max(values),sum(v*v for v in values),-len(values),qi)
                if best is None or key<best[0]:best=(key,qi)
            if best is None:break
            qi=best[1];answer=membership(*POOL[qi]);used.add(qi)
            remaining=[j for j in remaining if self.responses[qi][j]==answer]
            trace.append((POOL[qi],answer,len(remaining)))
            if not remaining:
                return {"status":"GRAMMAR_MISMATCH_DETECTED","queries":trace,"remaining":0}
        proven=bool(remaining) and all(proved_gf2(PROGRAMS[j]) for j in remaining)
        return {"status":"CONDITIONAL_CERTIFIED_GF2" if proven and trusted_complete_grammar
                else ("UNKNOWN_UNTRUSTED_GRAMMAR" if proven
                else "UNKNOWN_INSUFFICIENT_INFORMATION"),
                "queries":trace,"remaining":len(remaining),"symbolic_proof":proven}
