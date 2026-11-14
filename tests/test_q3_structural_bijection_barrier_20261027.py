import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"discovery_policy"))
from structural_bijection_barrier import test_structural_representation_barrier as certify

A_X_R=("A","X","R")

def test_rightshift_external_easy2_is_impossible_at_any_depth():
    x=certify(lambda a:a>>1,A_X_R)
    assert x["status"]=="PROVEN_UNREPRESENTABLE_IN_DECLARED_BIJECTIVE_DSL"
    assert x["distinct_input_witness"]==[0,1] and x["equal_output"]==0
    assert x["automatically_promote_Q"] is False

def test_negated_rightshift_external_easy3_is_impossible_at_any_depth():
    x=certify(lambda a:(~(a>>1))&255,A_X_R,witness=(0,1))
    assert x["status"]=="PROVEN_UNREPRESENTABLE_IN_DECLARED_BIJECTIVE_DSL"
    assert x["equal_output"]==255 and x["witness_evaluations"]==2

def test_original_easy1_identity_is_not_excluded():
    x=certify(lambda a:a,A_X_R)
    assert x["status"]=="NO_INJECTIVITY_EXCLUSION_FOUND"
    assert x["checked_all_256_inputs"] is True

def test_every_admitted_primitive_is_bijective():
    for c in (0,1,11,127,255):
        assert certify(lambda x:(x+c)&255,A_X_R)["status"]=="NO_INJECTIVITY_EXCLUSION_FOUND"
        assert certify(lambda x:x^c,A_X_R)["status"]=="NO_INJECTIVITY_EXCLUSION_FOUND"
    for r in range(1,8):
        f=lambda x:((x<<r)|(x>>(8-r)))&255
        assert certify(f,A_X_R)["status"]=="NO_INJECTIVITY_EXCLUSION_FOUND"

def test_extended_shift_grammar_must_abstain():
    x=certify(lambda a:a>>1,A_X_R+("SHR",))
    assert x["status"]=="UNKNOWN_GRAMMAR_HAS_UNPROVEN_OPERATOR"

def test_invalid_witness_and_bad_function_hold():
    assert certify(lambda a:a>>1,A_X_R,witness=(0,2))["status"]=="HOLD_INVALID_WITNESS"
    assert certify(lambda a:256,A_X_R)["status"]=="HOLD_INVALID_FUNCTION_OR_EXECUTION"
    assert certify(lambda a:"oops",A_X_R)["status"]=="HOLD_INVALID_FUNCTION_OR_EXECUTION"
