"""Scoped Q34 RC8: exact active membership learning for 256 human-specified
two-gate polynomial convolution programs; NOT general neural primitive invention.
Only CONDITIONAL_CERTIFIED when target is independently PROMISED in this grammar.
No hidden gold in query selection. A separate proof auditor may use target after.
"""
from collections import Counter
from itertools import product

def run(n,a,b,g,h):
    out=0
    for i in range(n):
        acc=0
        for j in range(i+1):
            p=g[((a>>j)&1)+2*((b>>(i-j))&1)]
            acc=h[acc+2*p]
        out|=acc<<i
    return out

def candidates():
    return [(tuple((gi>>j)&1 for j in range(4)),
             tuple((hi>>j)&1 for j in range(4)))
            for gi in range(16) for hi in range(16)]

def query_pool():
    return [(n,a,b) for n in (1,2,3)
            for a in range(1<<n) for b in range(1<<n)]

def semantics(candidate):
    g,h=candidate
    return tuple(h[acc+2*g[a+2*b]] for acc,a,b in product((0,1),repeat=3))

class ActiveGateLearner:
    def __init__(self):
        self.programs=candidates()
        self.pool=query_pool()
        self.predictions=[tuple(run(*q,*c) for c in self.programs) for q in self.pool]

    def fit(self,membership,trusted_complete_grammar=False):
        remaining=list(range(256));used=set();trace=[]
        while True:
            signatures={semantics(self.programs[j]) for j in remaining}
            if len(signatures)<=1:break
            best=None
            for qi in range(len(self.pool)):
                if qi in used:continue
                counts=Counter(self.predictions[qi][j] for j in remaining)
                v=list(counts.values())
                score=(max(v),sum(x*x for x in v),-len(v),qi)
                if best is None or score<best[0]:best=(score,qi)
            if best is None:break
            qi=best[1]
            # Only here may the learner query the held-out target.
            result=membership(*self.pool[qi])
            used.add(qi)
            remaining=[j for j in remaining if self.predictions[qi][j]==result]
            trace.append((self.pool[qi],result,len(remaining)))
            if not remaining:
                return {'status':'GRAMMAR_MISMATCH_DETECTED','queries':trace,'remaining':[]}
        same=len({semantics(self.programs[j]) for j in remaining})==1
        status='CONDITIONAL_CERTIFIED' if same and trusted_complete_grammar else (
           'UNKNOWN_UNTRUSTED_GRAMMAR' if same else 'UNKNOWN_INSUFFICIENT_EVIDENCE')
        return {'status':status,'queries':trace,
                'remaining':[self.programs[j] for j in remaining]}

def independent_one_query_lower_bound(oracle):
    """POST-HOC auditor, NOT used by learner's candidate-only selection."""
    learner=ActiveGateLearner()
    min_count=256;min_distinct=256
    for qi,q in enumerate(learner.pool):
        answer=oracle(*q)
        left=[j for j in range(256) if learner.predictions[qi][j]==answer]
        min_count=min(min_count,len(left))
        min_distinct=min(min_distinct,len({semantics(learner.programs[j]) for j in left}))
    return min_count,min_distinct
