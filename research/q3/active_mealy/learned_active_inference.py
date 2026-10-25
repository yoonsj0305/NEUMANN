"""Research-only active Mealy observation table.

Membership oracle: word -> emitted output stream; no state or transition labels.
Equivalence oracle: separately privileged complete candidate->counterexample/None.
The scorer's 3 own-weight constants were extracted from frozen prior PyTorch
checkpoint. Learned scorer only tests equality of precomputed future outputs.
Without complete EQ, the result is never CERTIFIED.
"""
W_MAX=-4.431497573852539
W_MEAN=-4.19536828994751
BIAS=2.5596377849578857

def learned_equal(a,b):
    x=tuple(z for suffix in a for z in suffix)
    y=tuple(z for suffix in b for z in suffix)
    if len(x)!=len(y):raise ValueError("signature mismatch")
    miss=sum(u!=v for u,v in zip(x,y))
    return W_MAX*bool(miss)+W_MEAN*miss/max(1,len(x))+BIAS>=0

def execute(program,word):
    state=0;result=[]
    for a in word:
        result.append(program["output"][state][a])
        state=program["transition"][state][a]
    return tuple(result)

class Learner:
    def __init__(self,oracle,alphabet=(0,1)):
        self.oracle=oracle;self.A=tuple(alphabet)
        self.S=[()];self.E=[(a,) for a in self.A]
        self.cache={};self.refinements=[]
    def ask(self,word):
        word=tuple(word)
        if word not in self.cache:
            out=tuple(self.oracle(word))
            if len(out)!=len(word):raise ValueError("oracle length")
            self.cache[word]=out
        return self.cache[word]
    def row(self,p):
        return tuple(self.ask(p+e)[len(p):] for e in self.E)
    def hypothesis(self):
        for _ in range(2000):
            rows={self.row(p) for p in self.S}
            add=None
            for p in self.S:
                for a in self.A:
                    q=p+(a,)
                    if not any(learned_equal(self.row(q),r) for r in rows):
                        add=q;break
                if add is not None:break
            if add is not None:
                self.S.append(add);self.refinements.append(("split",add));continue
            suffix=None
            for i,p in enumerate(self.S):
                for q in self.S[i+1:]:
                    if not learned_equal(self.row(p),self.row(q)):continue
                    for a in self.A:
                        if not learned_equal(self.row(p+(a,)),self.row(q+(a,))):
                            for e in self.E:
                                if self.ask(p+(a,)+e)[len(p):]!=self.ask(q+(a,)+e)[len(q):]:
                                    suffix=(a,)+e;break
                            if suffix is None:raise AssertionError("no distinguishing suffix")
                            break
                    if suffix is not None:break
                if suffix is not None:break
            if suffix is not None:
                if suffix in self.E:raise AssertionError("duplicate suffix")
                self.E.append(suffix);self.refinements.append(("suffix",suffix));continue
            order=[];known={}
            for p in [()]+self.S:
                r=self.row(p)
                if r not in known:known[r]=len(order);order.append(p)
            transitions=[];output=[]
            for p in order:
                transitions.append([known[self.row(p+(a,))] for a in self.A])
                output.append([self.ask(p+(a,))[-1] for a in self.A])
            return {"transition":transitions,"output":output,
                    "states":len(order),"source_queries":len(self.cache)}
        raise RuntimeError("table did not close")
    def add_counterexample(self,word):
        word=tuple(word)
        for i in range(1,len(word)+1):
            p=word[:i]
            if p not in self.S:self.S.append(p)
        for i in range(len(word)):
            e=word[i:]
            if e not in self.E:self.E.append(e)
        self.refinements.append(("counterexample",word))

def learn(oracle,equivalence_oracle=None,alphabet=(0,1),max_rounds=30):
    learner=Learner(oracle,alphabet)
    for i in range(max_rounds):
        p=learner.hypothesis()
        if equivalence_oracle is None:
            p["status"]="PROVISIONAL_NO_EQ_OR_CLASS_PROOF";p["EQ_calls"]=0
            return p
        witness=equivalence_oracle(p)
        if witness is None:
            p["status"]="CONDITIONAL_CERTIFIED_BY_EXTERNAL_COMPLETE_EQ"
            p["EQ_calls"]=i+1;p["refinements"]=len(learner.refinements)
            return p
        learner.add_counterexample(witness)
    raise RuntimeError("equivalence rounds exhausted")
