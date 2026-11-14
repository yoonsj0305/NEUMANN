"""Independent no-neural-dependency scoped regression controls for RC17."""
import pathlib,sys,random,itertools,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc17_param_language"))
from learned_macro import *

def test_parametric_macro_all_new_params():
    assert proof_gated_registration(FROZEN_SOURCE_PROGRAM)=={"status":"SCOPED_CERTIFIED","token":"AUTO_a4f32841906f"}
    assert proof_gated_registration((0,0,0,0,0,0,0))["status"]=="UNKNOWN_NOT_PROVEN"
    for k in (2,3,4,5,6,7,8,9,11,16,31,64):
        for n in range(1,10):
            for v in range(1<<n):
                w=tuple((v>>i)&1 for i in range(n))
                assert run_compiled_learned_macro(k,w)==reference_degraded_fallback(k,w)

def test_long_strings_unknown_is_fail_closed():
    rng=random.Random(20261025)
    for k in (2,5,7,17,127):
        for n in (16,128,1024):
            word=tuple(rng.getrandbits(1) for _ in range(n))
            assert run_compiled_learned_macro(k,word)==reference_degraded_fallback(k,word)
    for k,word in ((0,(0,1)),(1,(1,)),(3,(2,))):
        try:run_compiled_learned_macro(k,word)
        except ValueError:pass
        else:raise AssertionError("invalid input accepted")

def test_k_states_pairwise_distinguishable():
    for k in range(2,40):
        assert minimal_state_bound(k)==k
        for a,b in itertools.combinations(range(k),2):
            # Extend both prefixes by the SAME positive suffix that makes
            # prefix a divisible by k but prefix b not divisible by k.
            length=(k-a)%k or k
            suffix=(1,)*length
            outa=run_compiled_learned_macro(k,(1,)*a+suffix)[-1]
            outb=run_compiled_learned_macro(k,(1,)*b+suffix)[-1]
            assert (outa,outb)==(1,0)


def test_new_nested_macro_language_task_without_retraining():
    # Frozen learned macro is used as a proper compositional language primitive.
    rng=random.Random(2026102505)
    count=0
    for first_k,second_k in ((5,7),(7,5),(11,13),(17,31),(3,29),(64,2)):
        for n in (8,31,127,1024):
            for _ in range(8):
                word=tuple(rng.getrandbits(1) for _ in range(n))
                inner=run_compiled_learned_macro(first_k,word)
                predicted=run_compiled_learned_macro(second_k,inner)
                c1=c2=0;expected=[]
                for b in word:
                    c1+=b
                    c2+=int(c1%first_k==0)
                    expected.append(int(c2%second_k==0))
                assert predicted==tuple(expected)
                count+=1
    assert count==192
