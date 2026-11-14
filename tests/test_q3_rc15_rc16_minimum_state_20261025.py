"""Q3 RC15/RC16 extracted own-weight formal controls."""
import pathlib,sys,itertools,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc15_rc16"))
from learned_state_operators import *

def test_exhaustive_new_family_behaviors():
    cases=0
    for n in range(1,11):
        for v in range(1<<n):
            bits=tuple((v>>i)&1 for i in range(n))
            pp=[];seen=[];p=0;s=0
            for x in bits:
                p^=x;s|=x;pp.append(p);seen.append(s)
            assert prefix_parity(bits)==tuple(pp)
            assert prefix_seen_one(bits)==tuple(seen)
            cases+=1
    assert cases==2046

def test_minimal_three_state_all_length_bisimulation():
    assert machine_bisimulation(MOD3_TRANSITION,MOD3_EMIT)
    for a,b in itertools.combinations(range(3),2):
        assert any(int((a+d)%3==0)!=int((b+d)%3==0) for d in (0,1))
    # Each of 6 outputs / 6 next-state entries is indispensable.
    for k in range(6):
        changed=list(MOD3_EMIT);changed[k]^=1
        assert not machine_bisimulation(MOD3_TRANSITION,changed)
        changed=list(MOD3_TRANSITION);changed[k]=(changed[k]+1)%3
        assert not machine_bisimulation(changed,MOD3_EMIT)

def test_unseen_streams_and_degraded_fallback():
    r=random.Random(20261025)
    reg=ProofGatedStateRegistry()
    assert reg.register("LEARNED_MOD3",MOD3_TRANSITION,MOD3_EMIT,"signed")=="SCOPED_CERTIFIED"
    assert reg.register("LEARNED_BROKEN",MOD3_TRANSITION,(0,)*6,"signed")=="UNKNOWN_UNPROVED"
    for n in (2,3,6,12,16,64,256,1024):
        for _ in range(16):
            seq=tuple(r.getrandbits(1) for _ in range(n))
            assert prefix_multiple_of_three(seq)==reg.fallback(seq)==reg.run("LEARNED_MOD3",seq)
