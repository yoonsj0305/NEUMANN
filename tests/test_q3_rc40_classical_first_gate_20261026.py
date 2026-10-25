"""Classical-first safety contract, no neural engine invoked."""
import pathlib,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc40"))
from classical_first_gate import *

def test_classically_exact_read_address_has_no_neural_path():
    words=["ABCD","BCDA","CABD","ABCDE","ABCDAB"]
    for contract,code,method in [
        ("FIRST",[0,0],lambda s:s[0]*len(s)),
        ("LAST",[0,1],lambda s:s[-1]*len(s)),
        ("REVERSE",[-1,1],lambda s:s[::-1])
    ]:
        rows=[{"input":w,"output":method(w)} for w in words]
        fit=classical_affine(rows)
        assert fit["status"]=="SOURCE_UNIQUE" and fit["codes"]==[code]
        result=independent_affine_proof(fit,contract)
        assert result["status"]=="CLASSICAL_CERTIFIED"
        assert classical_first_route(result)=={"decision":"EXECUTE_CLASSICAL","neural":False}

def test_relative_one_head_minimum_source_fit_is_not_universal_certificate():
    rows=[]
    for n in range(1,6):
        for xs in itertools.product("ABC",repeat=n):
            w="".join(xs);out=[]
            for i,c in enumerate(w):
                out.append("C" if c=="B" and i>0 and w[i-1]=="A" else c)
            rows.append({"input":w,"output":"".join(out)})
    r=classical_min_reads(rows,max_heads=2)
    assert r["status"]=="SOURCE_MIN_HEADS" and r["heads"]==[-1]
    assert not r["all_length_proof"]
    assert classical_first_route(r)["neural"] is False

def test_classical_representation_failed_does_not_prove_all_classical_impossible():
    r=classical_affine([{"input":"ABCD","output":"CDAB"},
                        {"input":"ABCDEFGH","output":"EFGHABCD"}])
    assert r["status"]=="REPRESENTATION_EXHAUSTED"
    assert not classical_first_route(r)["neural"]
    assert not classical_first_route(r,bounded_class_exhausted=True)["neural"]
    z=classical_first_route(r,bounded_class_exhausted=True,
                             external_verifier_ready=True,cost_case_documented=True)
    assert z["decision"]=="NEURAL_RESEARCH_ELIGIBLE" and z["deploy_authorized"] is False

def test_underconstrained_source_and_small_budget_do_not_trigger_neural():
    ambiguous=classical_affine([{"input":"AAAA","output":"AAAA"}])
    assert ambiguous["status"]=="SOURCE_AMBIGUOUS"
    assert classical_first_route(ambiguous)["decision"]=="GET_MORE_DISTINGUISHING_IO"
    b=classical_min_reads([{"input":"AB","output":"CC"}],max_heads=4,max_candidates=1)
    assert b["status"]=="UNKNOWN_BUDGET"
    assert classical_first_route(b)["neural"] is False
