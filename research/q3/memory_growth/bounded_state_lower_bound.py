"""Q3 classical theorem counterexample: fixed-state online multiplication impossible.

Inputs (a_i,b_i) are binary and supplied LSB first, one output bit each step.
After k zero-b prefixes, a low prefix u has 2^k distinguishable histories:
continue with b_k=1 and all remaining inputs zero, and output suffix equals u.
Every deterministic one-pass Mealy transducer must use >=2^k states.
Not a claim about normal RAM arithmetic or NEUMANN neural discovery.
"""
def witness(k,u):
    if not (k>=1 and 0<=u<2**k):raise ValueError("invalid witness")
    n=2*k+1
    prefix=tuple(((u>>i)&1,0) for i in range(k))
    suffix=((0,1),)+((0,0),)*(n-k-1)
    return prefix,suffix

def future_output(k,u):
    prefix,suffix=witness(k,u)
    sequence=prefix+suffix
    a=sum(v[0]<<i for i,v in enumerate(sequence))
    b=sum(v[1]<<i for i,v in enumerate(sequence))
    output=a*b
    return tuple((output>>j)&1 for j in range(k,2*k))

def assert_lower_bound(k):
    observed={future_output(k,u) for u in range(2**k)}
    assert len(observed)==2**k
    return 2**k

class GrowingMemoryMultiply:
    """Human-authored online binary convolution, NOT learned weights."""
    def __init__(self):
        self.a=[];self.b=[];self.carry=0;self.bits=[]
    def step(self,a,b):
        if a not in (0,1) or b not in (0,1):raise ValueError("not binary")
        i=len(self.a)
        self.a.append(a);self.b.append(b)
        diagonal=sum(self.a[j]*self.b[i-j] for j in range(i+1))
        total=diagonal+self.carry
        self.bits.append(total%2);self.carry=total//2
        return self.bits[-1]
    def finish(self,n):
        while len(self.bits)<2*n:self.step(0,0)
        return sum(bit<<i for i,bit in enumerate(self.bits))

def multiply(a,b,n):
    if not (n>=1 and 0<=a<2**n and 0<=b<2**n):
        raise ValueError("bad operands")
    m=GrowingMemoryMultiply()
    for i in range(n):
        m.step((a>>i)&1,(b>>i)&1)
    return m.finish(n)
