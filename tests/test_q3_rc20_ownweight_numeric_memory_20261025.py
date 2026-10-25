"""Q3 RC20 scope CI: compact learned arithmetic-code semantics only."""
import itertools,pathlib,random,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc20"))
from numeric_macro import (FROZEN_LEARNED_CODE,universal_radix_proof,
       learned_radix_execute,VerifiedNumericMacro,info_bits_bounds,reuse_reverse)

def test_correct_and_incorrect_candidates_are_distinguished():
    model=VerifiedNumericMacro()
    r=model.register(FROZEN_LEARNED_CODE,"a"*64)
    assert r["status"]=="SCOPED_CERTIFIED"
    assert r["token"]=="LEARNED_NUMMEM_dac6ad97831b"
    variants=[(base,dm,0,1,0,0,0,0,0)
             for base in (1,2,3) for dm in (1,2)]
    assert all(universal_radix_proof(x) for x in variants)
    for i in range(2,9):
        c=list(FROZEN_LEARNED_CODE)
        c[i]=(c[i]+1)%([4,3,4,4,4,4,2,2,3][i])
        assert not universal_radix_proof(c)
        assert model.register(c,"a"*64)["status"]=="UNKNOWN_NO_UNIVERSAL_PROOF"
    assert model.register(FROZEN_LEARNED_CODE,"short")["status"]=="REJECT_UNSEALED"

def test_fresh_k_exhaustive_and_degraded_fallback():
    reg=VerifiedNumericMacro()
    token=reg.register(FROZEN_LEARNED_CODE,"a"*64)["token"]
    for k in (2,3,4,5):
        for n in range(1,5):
            for w in itertools.product(itertools.product((0,1),range(k)),repeat=n):
                assert reg.run(token,k,w)==reg.degraded_fallback(k,w)
    rng=random.Random(20262020)
    for k in (3,5,16):
        for depth in (8,32,128):
            for _ in range(8):
                types=tuple(rng.randrange(k) for _ in range(depth))
                good=tuple((0,t) for t in types)+tuple((1,t) for t in types[::-1])
                wrong=good[:-1]+((1,(good[-1][1]+1)%k),)
                assert reg.run(token,k,good)[-1]==1
                assert reg.run(token,k,wrong)[-1]==0
                assert reuse_reverse(FROZEN_LEARNED_CODE,k,types)==types[::-1]

def test_bit_lower_bound_and_fail_closed():
    assert info_bits_bounds(16,512)==(2048,2093)
    reg=VerifiedNumericMacro()
    try:reg.run("unregistered",3,((0,1),))
    except ValueError:pass
    else:raise AssertionError("invalid authorization")
