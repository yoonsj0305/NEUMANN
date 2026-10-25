"""RC21 compact CLASSICAL observation-table state-grammar generator.
Never call this a neural learner or oracle-free: equivalence checker is external.
"""
from collections import OrderedDict
from hashlib import sha256

class ConditionalStateGrammar:
    def __init__(self,membership,equivalence):
        self.membership=membership;self.equivalence=equivalence
        self.prefixes=[''];self.suffixes=[''];self.cache={};self.eq_queries=0

    def f(self,w):
        if w not in self.cache:self.cache[w]=int(self.membership(w))
        return self.cache[w]

    def row(self,w):return tuple(self.f(w+e) for e in self.suffixes)

    def synthesize(self,iterations=200):
        for _ in range(iterations):
            while True:
                known={self.row(s) for s in self.prefixes}
                missing=next((s+a for s in self.prefixes for a in '01'
                              if self.row(s+a) not in known),None)
                if missing is not None:self.prefixes.append(missing);continue
                witness=None
                for i,s in enumerate(self.prefixes):
                    for t in self.prefixes[i+1:]:
                        if self.row(s)!=self.row(t):continue
                        for a in '01':
                            rs,rt=self.row(s+a),self.row(t+a)
                            if rs!=rt:
                                e=next(e for j,e in enumerate(self.suffixes) if rs[j]!=rt[j])
                                witness=a+e;break
                        if witness is not None:break
                    if witness is not None:break
                if witness is not None:self.suffixes.append(witness);continue
                break
            reps=OrderedDict()
            for s in self.prefixes:reps.setdefault(self.row(s),s)
            names={r:'STATE_'+sha256(str(r).encode()).hexdigest()[:10] for r in reps}
            machine={'initial':names[self.row('')],
                     'transitions':{names[r]:{a:names[self.row(s+a)] for a in '01'} for r,s in reps.items()},
                     'output':{names[r]:self.f(s) for r,s in reps.items()},
                     'new_productions':tuple(names.values())}
            ce=self.equivalence(machine);self.eq_queries+=1
            if ce is None:
                return {'status':'CONDITIONAL_EQ_CERTIFIED','machine':machine,
                        'states':len(reps),'membership_queries':len(self.cache),
                        'equivalence_queries':self.eq_queries}
            if not isinstance(ce,str) or any(c not in '01' for c in ce):
                return {'status':'UNKNOWN_BAD_VERIFIER'}
            for i in range(len(ce)+1):
                if ce[:i] not in self.prefixes:self.prefixes.append(ce[:i])
        return {'status':'UNKNOWN_BUDGET'}
