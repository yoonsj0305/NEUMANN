"""CI smoke from RC7 sealed PyTorch study; full weights, pregrade receipts
and raw neural outputs are in the independent ZIP, not this thin CI test."""
import pathlib,sys,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"learned_polymul"))
from learned_gf2_polymul import GATE1,GATE2,local_invariant,learned_gf2_poly_multiply_low

def independent_reference(a,b,n):
    out=0
    for j in range(n):
        if (a>>j)&1: out^=b<<j
    return out&((1<<n)-1)

def test_exact_all_length_local_gate_invariant():
    assert local_invariant()
    # Eight possible single-entry mutations must all break the identity.
    for name in ("GATE1","GATE2"):
        for j in range(4):
            g=list(GATE1);h=list(GATE2)
            if name=="GATE1":g[j]^=1
            else:h[j]^=1
            assert not local_invariant(g,h)

def test_new_input_lengths_exhaustive_n4_to_8():
    total=0
    for n in range(4,9):
        for a in range(1<<n):
            for b in range(1<<n):
                assert learned_gf2_poly_multiply_low(a,b,n)==independent_reference(a,b,n)
                total+=1
    assert total==87296

def test_long_width_source_only_controls():
    r=random.Random(730211)
    for n in (16,32,64,128,256,512,1024):
        for _ in range(40):
            a=r.getrandbits(n);b=r.getrandbits(n)
            assert learned_gf2_poly_multiply_low(a,b,n)==independent_reference(a,b,n)
