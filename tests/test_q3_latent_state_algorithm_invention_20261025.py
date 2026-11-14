"""Exact logic regression of the model-extracted new named stateful operator.

The torch-training evaluation is independently reproducible in the chat's
24-file research ZIP; this stdlib-only CI tests the immutable learned truth
table, its mathematical all-length induction condition, negative controls
and already-frozen 2-state growth witness.
"""
import pathlib,sys,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"latent_state"))
from learned_operator import EMIT,NEXT,H_LEARNED_ADD
from state_growth_gate import propose_minimal_expansion

def test_all_eight_local_transitions_form_binary_addition_induction():
    assert len(EMIT)==len(NEXT)==8
    assert all(EMIT[4*s+(a+2*b)]==(a+b+s)%2 and
               NEXT[4*s+(a+2*b)]==(a+b+s)//2
               for s in (0,1) for a in (0,1) for b in (0,1))

def test_all_short_integer_pairs_including_overflow():
    for n in range(1,7):
        for a in range(1<<n):
            for b in range(1<<n):
                assert H_LEARNED_ADD(a,b,n)==a+b

def test_long_carry_and_cross_task_reuse():
    rng=random.Random(41592)
    for n in (8,64,256,4096):
        assert H_LEARNED_ADD((1<<n)-1,1,n)==1<<n
        for _ in range(20):
            a,b,c=(rng.getrandbits(n) for _ in range(3))
            assert H_LEARNED_ADD(a,b,n)==a+b
            assert H_LEARNED_ADD(a,1,n)==a+1
            assert H_LEARNED_ADD(H_LEARNED_ADD(a,b,n),c,n+1)==a+b+c

def test_missing_one_bit_rule_invalidates_induction():
    for name,original in (("emit",EMIT),("next",NEXT)):
        for k in range(8):
            changed=list(original);changed[k]^=1
            f=lambda s,a,b:4*s+a+2*b
            proven=all((changed[f(s,a,b)]==(a+b+s)%2 if name=="emit" else
                        changed[f(s,a,b)]==(a+b+s)//2)
                       for s in (0,1) for a in (0,1) for b in (0,1))
            assert not proven,(name,k)

def test_minimal_state_growth_follows_from_observation_only():
    result=propose_minimal_expansion()
    assert result["status"]=="NEED_ADDITIONAL_STATE"
    assert result["lower_bound"]==2
    assert result["upper_bound"]=="NOT_PROVEN_BY_THIS_GATE"
    witness=result["witness"]
    assert witness["same_symbol"]==(0,0)
    assert {witness["first_output"],witness["second_output"]}=={0,1}
