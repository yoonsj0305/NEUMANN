"""Classical Q34 RC10 9216 candidate first results. No gold in query chooser."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"joint_structure_rc9"))
from active_grammar_9216 import ActiveObserver,POOL

def oracle(n,a,b):
    out=0
    for j in range(n):
        if (a>>j)&1:out^=b<<j
    return out&((1<<n)-1)

def test_four_source_only_queries_symbolic_conditional_proof():
    membership_calls=[]
    def answer(n,a,b):
        membership_calls.append((n,a,b))
        return oracle(n,a,b)
    r=ActiveObserver().identify(answer,trusted_complete_grammar=True)
    assert r["status"]=="CONDITIONAL_CERTIFIED_GF2"
    assert r["remaining"]==4
    assert r["symbolic_proof"]
    assert r["queries"]==[
        ((3,1,2),2,274),((3,2,6),4,32),
        ((3,4,3),4,8),((2,3,3),1,4)]
    assert membership_calls==[q for q,a,k in r["queries"]]

def test_unknown_without_independent_grammar_bound():
    r=ActiveObserver().identify(oracle,trusted_complete_grammar=False)
    assert r["status"]=="UNKNOWN_UNTRUSTED_GRAMMAR"
    assert len(r["queries"])==4

def test_unseen_length_adversary_same_84_sources():
    def delayed(n,a,b):
        return oracle(n,a,b) if n<=3 else (oracle(n,a,b)^(((a&1)&((b>>3)&1))<<3))
    assert all(delayed(*q)==oracle(*q) for q in POOL)
    assert delayed(4,1,8)!=oracle(4,1,8)
