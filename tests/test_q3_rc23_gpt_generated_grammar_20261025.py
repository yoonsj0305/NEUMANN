"""A small CI smoke. Full 348912 and third-family 143366 tests live in ZIP."""
import pathlib,sys,itertools,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc23"))
from generated_language import Packed,recognize,nested_prefix,NEW_LANGUAGE_SYNTAX

def test_new_primitives_and_both_independent_language_specs():
    for k,n in ((2,6),(3,4)):
        for prefix in itertools.product(range(k),repeat=n):
            q=Packed.make(k)
            for x in prefix:q=q.write(x)
            a=q
            for x in prefix:
                got,q=q.take_front()
                assert got==x
            for x in prefix[::-1]:
                got,a=a.take_back()
                assert got==x
            for mode in ("COPY","REVERSE"):
                good=prefix+(None,)+(prefix if mode=="COPY" else prefix[::-1])
                assert recognize(good,k,mode)
                changed=list(good)
                changed[n+1]=(changed[n+1]+1)%k
                assert not recognize(changed,k,mode)

def test_third_language_and_error_propagation():
    for n in range(1,7):
        for w in itertools.product(tuple(itertools.product((0,1),range(2))),repeat=n):
            stack=[];bad=False;expected=[]
            for phase,t in w:
                if not bad:
                    if phase==0:stack.append(t)
                    elif not stack or stack.pop()!=t:bad=True
                expected.append(int(not bad and not stack))
            assert nested_prefix(w,2)==tuple(expected)

def test_explicit_scientific_scope_and_rejected_inputs():
    assert "READ_FRONT(trace)" in NEW_LANGUAGE_SYNTAX["TraceExpr"]
    assert "READ_BACK(trace)" in NEW_LANGUAGE_SYNTAX["TraceExpr"]
    assert not recognize((0,None,None,0),2,"COPY")
    assert not recognize((0,None,True),2,"COPY")
    try:Packed.make(1)
    except ValueError:pass
    else:raise AssertionError("invalid alphabet accepted")
