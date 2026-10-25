"""RC34 proof boundaries: new alphabets, EPS, no prelisted rhs max, UNKNOWN."""
import itertools,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc34"))
from generic_grammar import discover,admit,emit,parse,apply
def case(g):
    alphabet="".join(g)
    return {"alphabet":alphabet,
            "sources":tuple(alphabet[i:]+alphabet[:i] for i in range(len(alphabet))),
            "io":tuple(apply(alphabet[i:]+alphabet[:i],g) for i in range(len(alphabet)))}
def test_new_language_alphabet_and_erasure():
    for g in ({"A":"AB","B":"","C":"CCCA"},
              {"A":"ABCDE","B":"","C":"EEE","D":"BC","E":"A"},
              {"A":"ABCD","B":"B","C":"","D":"DAAAAAA"}):
        d=discover(case(g))
        assert d["status"] in ("UNIQUE_CONDITIONAL","AMBIGUOUS")
        q=[]
        def member(s):q.append(s);return apply(s,g)
        result=admit(d,member)
        assert result["status"]=="CONDITIONAL_CLASS_CERTIFIED"
        assert result["queries"]==len(q)
        assert result["grammar"]==g
        assert parse(emit(g))==g
def test_empty_and_malformed_never_pass():
    g={"A":"A","B":"","C":"B"}
    d=discover(case(g),max_splits=1)
    assert d["status"]=="UNKNOWN_BUDGET"
    for bad in ("import os","A ::= D","A ::= A\nA ::= B","A ::= B\nB ::= C"):
        try:parse(bad)
        except ValueError:pass
        else:raise AssertionError("untrusted syntax entered compiler")
def test_external_contract_is_logical_assumption_not_consequence():
    g={"A":"AB","B":"B","C":"C"};d=discover(case(g))
    assert d["status"]=="UNIQUE_CONDITIONAL"
    h=admit(d)
    assert h["status"]=="CONDITIONAL_CLASS_CERTIFIED"
    # An adversarial non-morphism matches every requested source observation.
    def outside(w):return "DEVIANT" if w=="AA" else apply(w,g)
    src=case(g)
    assert all(outside(x)==y for x,y in zip(src["sources"],src["io"]))
    assert outside("AA")!=apply("AA",h["grammar"])
