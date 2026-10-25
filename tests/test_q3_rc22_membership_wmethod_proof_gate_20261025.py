"""Exact RC22 regression plus adversarial false-bound witness."""
import pathlib,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc22"))
from membership_guard import run,suite,ProofCarryingAdmission,block_bare_none

def model_mod(k):
    states=[str(i) for i in range(k)]
    return {"start":"0","states":states,
            "outputs":{s:int(s=="0") for s in states},
            "transitions":{s:{"0":s,"1":str((int(s)+1)%k)} for s in states}}

def test_membership_only_trusted_bound_and_missing_bound():
    for k in (2,3,5,7):
        h=model_mod(k)
        f=lambda w: int(sum(x=="1" for x in w)%k==0)
        result=ProofCarryingAdmission(f,k).check(h)
        assert result["status"]=="CONDITIONAL_W_METHOD_CERTIFIED"
        assert result["trusted_U"]==k
        assert ProofCarryingAdmission(f,None).check(h)["status"]=="UNKNOWN_NO_TRUSTED_BOUND"
        assert block_bare_none(None)["status"]=="UNKNOWN_EQUIVALENCE_PROOF_MISSING"

def test_incorrect_hypothesis_returns_counterexample():
    target=lambda w:int(sum(x=="1" for x in w)%5==0)
    # 3-state modulo claimant under credible bound U=5 must be rejected
    result=ProofCarryingAdmission(target,5).check(model_mod(3))
    assert result["status"]=="COUNTEREXAMPLE"

def test_finite_length_cannot_certify_unbounded():
    one={"start":"0","states":["0"],"outputs":{"0":0},
         "transitions":{"0":{"0":"0","1":"0"}}}
    assert ProofCarryingAdmission(lambda w:int(w=="1"*17),None).check(one)["status"]=="UNKNOWN_NO_TRUSTED_BOUND"
    # A FALSE bound makes the W guarantee inapplicable; only conditional status
    result=ProofCarryingAdmission(lambda w:int(w=="1"*17),1).check(one)
    assert result["status"]=="CONDITIONAL_W_METHOD_CERTIFIED"
    assert run(one,"1"*17)!=1
    assert suite(model_mod(7),40)["status"]=="UNKNOWN_TEST_BUDGET"
