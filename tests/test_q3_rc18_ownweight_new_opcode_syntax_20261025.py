"""RC18 scope regression; original PyTorch weights/predictions in sealed ZIP."""
import pathlib,random,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc18"))
from learned_language import *

def setup():
    p=ExtensibleBitLanguage()
    a=p.register_weight_generated((-8,8,8,-8),"sealed first source")
    b=p.register_weight_generated((-8,8,8,8),"sealed second source")
    assert a["name"]=="LEARNED_450720c79994"
    assert b["name"]=="LEARNED_073b9d9363d0"
    return p,a["name"],b["name"]

def test_dynamic_opcode_semantics_and_new_productions():
    reg,parity,seen=setup()
    assert len(reg.rules)==2
    assert reg.rules[parity]==(0,1,1,0)
    assert reg.rules[seen]==(0,1,1,1)
    assert generated_token((1,1,1,1)) not in (parity,seen)
    assert "BitExpr" in reg.register_weight_generated((8,8,8,8),"sha")["grammar_rule"]

def test_independent_unseen_all_lengths_finite():
    reg,parity,seen=setup()
    for n in range(1,10):
        for number in range(1<<n):
            bits=tuple((number>>i)&1 for i in range(n))
            pref=0;once=0;pa=[];se=[]
            for bit in bits:
                pref^=bit;once|=bit;pa.append(pref);se.append(once)
            assert reg.run(parity,bits)==tuple(pa)
            assert reg.run(seen,bits)==tuple(se)
            assert composition(reg,seen,parity,bits)==run_proven_three_state_reference(bits)

def test_strict_three_state_composite_and_unknown_unregistered():
    reg,parity,seen=setup()
    states=((0,0),(1,1),(1,0))
    def from_state(s,word):
        a,p=s;out=[]
        for b in word:
            a|=b;p^=a;out.append(p)
        return tuple(out)
    for a,b in itertools.combinations(states,2):
        assert any(from_state(a,w)!=from_state(b,w)
                   for n in range(1,4) for w in itertools.product((0,1),repeat=n))
    assert grammar_science_boundary()["global_Q3"]=="OPEN"
    try:reg.run("UNKNOWN",(0,1))
    except ValueError:pass
    else:raise AssertionError("invalid authorization")
