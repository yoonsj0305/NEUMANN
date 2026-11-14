"""RC7: neural-learned local gates, human-provided dynamic convolution topology.
Task is GF(2) polynomial carry-less multiplication, NOT integer multiplication.
GATE1 and GATE2 were frozen from actual 8-logit own PyTorch training using
only 84 end-to-end width1..3 I/O examples. Weights and training in sealed ZIP.
Model did not invent the convolution memory/dataflow/loop topology.
"""
GATE1=(1,1,1,0)  # frozen learned NAND representation, seed0
GATE2=(1,0,0,1)  # frozen learned XNOR representation, seed0

def local_invariant(g=GATE1,h=GATE2):
    """For every a,b,acc: h(acc,g(a,b)) = acc XOR (a AND b)."""
    return all(
       h[acc + 2*g[a+2*b]]==(acc^(a&b))
       for acc in (0,1) for a in (0,1) for b in (0,1)
    )

def learned_gf2_poly_multiply_low(a:int,b:int,n:int)->int:
    if not isinstance(n,int) or n<1 or not isinstance(a,int) or not isinstance(b,int) or not (0<=a<(1<<n) and 0<=b<(1<<n)):
        raise ValueError("expected n-bit nonnegative polynomial coefficients")
    aa=[(a>>i)&1 for i in range(n)]
    bb=[(b>>i)&1 for i in range(n)]
    out=0
    for i in range(n):
        acc=0
        for j in range(i+1):
            local=GATE1[aa[j]+2*bb[i-j]]
            acc=GATE2[acc+2*local]
        out|=acc<<i
    return out
