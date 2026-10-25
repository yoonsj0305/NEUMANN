"""Independent finite witness audit and algorithmic regression.
Full locally run source, receipts and complete exhaustive test in conversation ZIP.
"""
import pathlib,sys,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"memory_growth"))
from streaming_space_contract import (lower_bound_bits,shared_suffix_witness,
                                      future_bits,necessary_capacity,multiply_low)

def test_tighter_finite_width_state_lower_bound():
    # Existing RC6 only needed n>=2k+1; these witnesses work at n=2k.
    for n in range(2,21):
        k=lower_bound_bits(n)
        observed=set()
        for u in range(1<<k):
            prefix,suffix=shared_suffix_witness(n,u)
            assert len(prefix)+len(suffix)==n
            assert all(b==0 for _,b in prefix)
            bits=future_bits(n,u)
            assert bits[:k]==tuple((u>>i)&1 for i in range(k))
            observed.add(bits)
        assert len(observed)==1<<k

def test_all_low_products_to_eight_bits():
    evaluated=0
    for n in range(1,9):
        modulus=1<<n
        for a in range(modulus):
            for b in range(modulus):
                assert multiply_low(a,b,n)==(a*b)%modulus
                evaluated+=1
    assert evaluated==87380

def test_large_width_random_control():
    rng=random.Random(20261025)
    for n in (16,32,64,128,256,512):
        for _ in range(50):
            a,b=rng.getrandbits(n),rng.getrandbits(n)
            assert multiply_low(a,b,n)==(a*b)%(1<<n)

def test_capacity_gate_cannot_false_certify():
    for n in range(2,101):
        k=lower_bound_bits(n)
        assert necessary_capacity(n,k-1).status=="IMPOSSIBLE_UNDER_CONTRACT"
        assert necessary_capacity(n,k).status=="UNKNOWN_NOT_CERTIFIED"
        assert necessary_capacity(n,10*n).status=="UNKNOWN_NOT_CERTIFIED"
