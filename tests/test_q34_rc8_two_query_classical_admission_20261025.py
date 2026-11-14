"""Independent black-box membership checker for 256-program supplied grammar."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"learned_polymul"))
from active_two_query_certifier import ActiveGateLearner,independent_one_query_lower_bound,semantics

def reference(n,a,b):
    out=0
    for i in range(n):
        if (a>>i)&1:out^=b<<i
    return out&((1<<n)-1)

def test_two_query_optimal_for_true_gf2_target():
    calls=[]
    def membership(n,a,b):
        calls.append((n,a,b))
        return reference(n,a,b)
    r=ActiveGateLearner().fit(membership,trusted_complete_grammar=True)
    assert r["status"]=="CONDITIONAL_CERTIFIED"
    assert calls==[(3,1,1),(3,3,6)]
    assert len(r["remaining"])==2
    assert len({semantics(p) for p in r["remaining"]})==1

def test_no_unqualified_universal_certificate():
    r=ActiveGateLearner().fit(reference,trusted_complete_grammar=False)
    assert r["status"]=="UNKNOWN_UNTRUSTED_GRAMMAR"
    assert len(r["queries"])==2

def test_exhaustive_one_query_lower_bound():
    minimum,semantics_count=independent_one_query_lower_bound(reference)
    assert minimum==4
    assert semantics_count==2
