"""Q3 RC6.1: exact online n-bit product requires Omega(n) state bits.
This is classical proof code, NOT neural-authored semantic discovery.
Model: Mealy reads simultaneous LSB bit pairs, emits product bit immediately.
Only low n product bits are required. No input re-reading or external state.
"""
from dataclasses import dataclass

def lower_bound_bits(n: int) -> int:
    if not isinstance(n,int) or n<2: raise ValueError("n>=2")
    return n//2

def shared_suffix_witness(n: int, u: int):
    k=lower_bound_bits(n)
    if not (0<=u<(1<<k)): raise ValueError("invalid prefix")
    prefix=tuple(((u>>i)&1,0) for i in range(k))
    common=tuple((0,int(i==k)) for i in range(k,n))
    return prefix,common

def future_bits(n: int, u: int):
    prefix,suffix=shared_suffix_witness(n,u)
    pairs=prefix+suffix
    a=sum(x<<i for i,(x,_) in enumerate(pairs))
    b=sum(y<<i for i,(_,y) in enumerate(pairs))
    k=n//2
    return tuple(((a*b)>>i)&1 for i in range(k,n))

@dataclass(frozen=True)
class CapacityVerdict:
    status:str
    required_min_bits:int

def necessary_capacity(n:int, state_bits:int)->CapacityVerdict:
    k=lower_bound_bits(n)
    if not isinstance(state_bits,int) or state_bits<0:raise ValueError("bad capacity")
    if state_bits<k:return CapacityVerdict("IMPOSSIBLE_UNDER_CONTRACT",k)
    return CapacityVerdict("UNKNOWN_NOT_CERTIFIED",k)

class LowProductStream:
    """Human-authored O(n)-bit memory, O(n^2) bit work."""
    def __init__(self):
        self.a=[];self.b=[];self.carry=0
    def step(self,bit_a:int,bit_b:int)->int:
        if bit_a not in (0,1) or bit_b not in (0,1):
            raise ValueError("binary symbols only")
        i=len(self.a)
        self.a.append(bit_a);self.b.append(bit_b)
        diagonal=sum(self.a[j]*self.b[i-j] for j in range(i+1))
        total=diagonal+self.carry
        self.carry=total//2
        return total%2

def multiply_low(a:int,b:int,n:int)->int:
    if n<1 or not (0<=a<(1<<n) and 0<=b<(1<<n)):
        raise ValueError("bad operands")
    stream=LowProductStream()
    return sum(stream.step((a>>i)&1,(b>>i)&1)<<i for i in range(n))
