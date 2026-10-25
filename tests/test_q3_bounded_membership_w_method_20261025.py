"""Q3 independent membership-only W-method soundness contract.

No model training; mathematical W-method theorem needs trusted external state cap.
These exhaustive two-state tests sanity-check the implementation, not global Q3.
"""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"bounded_membership"))
from w_method import bounded_membership_conformance as conformance,execute

def independent_equivalent(a,b):
    todo=[(0,0)];seen=set()
    while todo:
        p,q=todo.pop()
        if (p,q) in seen:continue
        seen.add((p,q))
        for x in (0,1):
            if a["output"][p][x]!=b["output"][q][x]:return False
            todo.append((a["transition"][p][x],b["transition"][q][x]))
    return True

def test_exhaustive_all_65536_two_state_targets_against_two_specs():
    specs=(
        {"transition":[[0,0]],"output":[[0,1]]},
        {"transition":[[1,0],[1,0]],"output":[[0,0],[1,0]]},
    )
    checked=0
    for spec in specs:
        for bits in range(65536):
            m={
                "transition":[[(bits>>(2*i+x))&1 for x in (0,1)] for i in (0,1)],
                "output":[[(bits>>(4+2*i+x))&1 for x in (0,1)] for i in (0,1)]
            }
            verdict=conformance(spec,lambda w:execute(m,w),2)
            predicted=verdict["status"]=="CONDITIONAL_CERTIFIED_UNDER_TRUSTED_BOUND"
            assert predicted==independent_equivalent(spec,m),(bits,len(spec["transition"]))
            checked+=1
    assert checked==131072

def test_no_trusted_bound_must_return_unknown():
    candidate={"transition":[[0,0]],"output":[[0,0]]}
    verdict=conformance(candidate,lambda w:(),None)
    assert verdict["status"]=="UNKNOWN_NO_TRUSTED_STATE_BOUND"

def test_delayed_ten_state_hidden_counterexample_refutes_false_bound():
    candidate={"transition":[[0,0]],"output":[[0,0]]}
    hidden={"transition":[[(i+1)%10,0] for i in range(10)],
            "output":[[int(i==9),0] for i in range(10)]}
    assert conformance(candidate,lambda w:execute(hidden,w),7)["status"]=="CONDITIONAL_CERTIFIED_UNDER_TRUSTED_BOUND"
    valid=conformance(candidate,lambda w:execute(hidden,w),10)
    assert valid["status"]=="COUNTEREXAMPLE"
    assert valid["witness"]==(0,)*10

def test_same_source_is_not_a_proof_without_class_or_bound():
    m={"transition":[[0,0]],"output":[[0,1]]}
    assert conformance(m,lambda w:execute(m,w),1)["status"]=="CONDITIONAL_CERTIFIED_UNDER_TRUSTED_BOUND"
    assert conformance(m,lambda w:execute(m,w),None)["status"]=="UNKNOWN_NO_TRUSTED_STATE_BOUND"
