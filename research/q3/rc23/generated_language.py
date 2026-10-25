"""RC23 compact port of GPT-6-authored instructions. Original SHA-frozen
proposal and reference grader are in downloadable 9-file archive, not here.
GPT-6 proposer != NEUMANN own-weight model. Python is provided metalanguage.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Packed:
    b:int
    s:int=0
    n:int=0

    @classmethod
    def make(cls,k):
        if type(k)!=int or k<2: raise ValueError("alphabet")
        return cls(k+1)

    def write(self,x):
        if type(x)!=int or x<0 or x>=self.b-1: raise ValueError("symbol")
        return Packed(self.b,self.b*self.s+x+1,self.n+1)

    def take_front(self):
        if self.n==0:return None,self
        p=self.b**(self.n-1)
        return self.s//p-1,Packed(self.b,self.s%p,self.n-1)

    def take_back(self):
        if self.n==0:return None,self
        return self.s%self.b-1,Packed(self.b,self.s//self.b,self.n-1)

NEW_LANGUAGE_SYNTAX={
    "TraceExpr":["MAKE(k)","WRITE(trace,symbol)","READ_FRONT(trace)",
                 "READ_BACK(trace)"],
    "PredicateExpr":["MATCH(x,y)","EXHAUSTED(trace)"]
}

def recognize(word,k,mode):
    if mode not in ("COPY","REVERSE"):raise ValueError("mode")
    trace=Packed.make(k);second=False
    for x in word:
        if x is None:
            if second:return False
            second=True
        elif type(x)!=int or x<0 or x>=k:return False
        elif not second:trace=trace.write(x)
        else:
            got,trace=(trace.take_front() if mode=="COPY" else trace.take_back())
            if got!=x:return False
    return second and trace.n==0

def nested_prefix(stream,k):
    trace=Packed.make(k);bad=False;out=[]
    for phase,x in stream:
        if phase not in (0,1) or type(x)!=int or not 0<=x<k:raise ValueError("typed delimiter")
        if not bad:
            if phase==0:trace=trace.write(x)
            else:
                got,trace=trace.take_back()
                if got!=x:bad=True
        out.append(int(not bad and trace.n==0))
    return tuple(out)
