"""Q3 RC36 independently confirm compiled own-weight runtime boundary."""
import itertools,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc36"))
from relative_access import FROZEN_COMPILED,ABC,READS,compiled_text,parse,run,token,Gate

SPEC={"A":(-2,"B","A","C"),"B":(2,"B","C","A"),"C":(-3,"A","C","B")}
def oracle(p,task):
    offset,curr,neighbor,replacement=SPEC[task]
    if p["relative_access_offset"]!=offset:return False
    for i,x in enumerate(ABC):
        for j,n in enumerate(READS):
            expected=replacement if x==curr and n==neighbor else x
            if ABC[p["symbol_table"][i][j]]!=expected:return False
    return True
def ref(word,task):
    d,c,n,r=SPEC[task]
    return "".join(r if ch==c and 0<=i+d<len(word) and word[i+d]==n
                   else ch for i,ch in enumerate(word))
def test_self_proposed_language_exact_and_all_length_verifier():
    assert [token(FROZEN_COMPILED[t]) for t in "ABC"]==[
        "AUTO_REL_5d9635c33125","AUTO_REL_8cce50ad4cc1",
        "AUTO_REL_c4bb29549439"]
    g=Gate()
    for t,p in FROZEN_COMPILED.items():
        syntax=compiled_text(p)
        assert parse(syntax)==p and oracle(p,t)
        status=g.admit(syntax,t,oracle)
        assert status["status"]=="SCOPED_VERIFIED"
        for n in range(1,9):
            for tup in itertools.product(ABC,repeat=n):
                w="".join(tup)
                assert g.execute(status["token"],w)==ref(w,t)
def test_old_immediate_context_expressivity_impossible():
    for task,(delta,current,neighbor,replacement) in SPEC.items():
        i=8;word=list("C"*20);word[i]=current;word[i+delta]=neighbor
        w1="".join(word)
        word[i+delta]="B" if neighbor!="B" else "A"
        w2="".join(word)
        assert w1[i-1:i+2]==w2[i-1:i+2]
        assert ref(w1,task)[i]!=ref(w2,task)[i]
def test_bad_semantics_and_host_code_are_fail_closed():
    gate=Gate()
    source=compiled_text(FROZEN_COMPILED["A"])
    for bad in ("import os",source.replace("ACCESS READ_REL","EXEC PYTHON"),
                source.replace("CASE CUR=A","CASE CUR=D"),
                source+"import os"):
        assert gate.admit(bad,"A",oracle)["status"]=="UNKNOWN_BAD_GRAMMAR"
    p={**FROZEN_COMPILED["A"],"relative_access_offset":-1}
    assert gate.admit(compiled_text(p),"A",oracle)["status"]=="UNKNOWN_NO_PROOF"
    try:gate.execute("FAKE","AB")
    except ValueError:pass
    else:raise AssertionError("unauthorized code executed")
