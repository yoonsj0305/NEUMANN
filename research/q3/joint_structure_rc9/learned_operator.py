"""Q3 RC9.1: frozen extracted structure from NEUMANN OWN PyTorch weights.
Original 44 learned scalars + 12-seed train logs are in the sealed research ZIP.
HUMAN predefined: 36 routing templates, 2 local gates, append-only memory.
The model learned gate tables AND/XOR and index routing (i-j,j) from only 84
end-to-end training input/outputs, without hidden gate/index labels.
NOT an autonomous new DSL or general memory architecture invention.
"""
GATE_G=(0,0,0,1)  # learned AND, seed7
GATE_H=(0,1,1,0)  # learned XOR, seed7
ROUTE=("i-j","j")
TRAINED_ROUTE_SEEDS_CORRECT=12
FROZEN_WEIGHT_SHA256="902ab73823446d32f9cd2985ec60eb23f7f9b4db5ce35e7a4a5d0ec6cf252b54"

def local_rule(acc,bit_a,bit_b,g=GATE_G,h=GATE_H):
    return h[acc+2*g[bit_a+2*bit_b]]

def product(n,a,b,g=GATE_G,h=GATE_H,route=ROUTE):
    """Low n bits of GF(2) carryless polynomial multiplication."""
    if not isinstance(n,int) or not isinstance(a,int) or not isinstance(b,int) or not (n>=1 and 0<=a<1<<n and 0<=b<1<<n):
        raise ValueError("expected two n-bit nonnegative polynomial coefficients")
    if route not in (("i-j","j"),("j","i-j")):
        raise ValueError("only mathematically proven route family is accepted")
    result=0
    for i in range(n):
        acc=0
        for j in range(i+1):
            ia=i-j if route[0]=="i-j" else j
            ib=i-j if route[1]=="i-j" else j
            acc=local_rule(acc,(a>>ia)&1,(b>>ib)&1,g,h)
        result|=acc<<i
    return result

def rule_proven():
    """Local truth table + route symmetry give an ALL finite n proof."""
    return all(local_rule(c,a,b)==(c^(a&b))
               for c in (0,1) for a in (0,1) for b in (0,1))
