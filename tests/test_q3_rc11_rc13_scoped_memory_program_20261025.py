"""Compact smoke only; full raw source-only first-grade and comparisons in ZIP."""
import pathlib,sys,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"program_synthesis"))
from learned_programs import learned_integer_low,learned_gf2_low,provable_emitted_programs

def test_full_width1_to7_and_independent_gf2():
    count=0
    for n in range(1,8):
        mask=(1<<n)-1
        for a in range(1<<n):
            for b in range(1<<n):
                gf2=0
                for j in range(n):
                    if (a>>j)&1: gf2 ^= b<<j
                assert learned_gf2_low(a,b,n)==(gf2&mask)
                assert learned_integer_low(a,b,n)==((a*b)&mask)
                count+=1
    assert count==21844

def test_long_inputs_and_scope():
    rng=random.Random(20261025)
    for n in (16,32,64,128,256,512):
        mask=(1<<n)-1
        for _ in range(12):
            a,b=rng.getrandbits(n),rng.getrandbits(n)
            assert learned_integer_low(a,b,n)==((a*b)&mask)
    assert provable_emitted_programs()["global_new_DSL"]=="OPEN"

def test_bounded_program_inputs_fail_closed():
    for a,b,n in ((-1,0,2),(8,0,3),(0,-1,3),(0,0,0)):
        for fn in (learned_integer_low,learned_gf2_low):
            try: fn(a,b,n)
            except ValueError:pass
            else:raise AssertionError("bad source must be rejected")
