import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"discovery_policy"))
from source_input_identifiability_guard import (
    greedy_distinguishing_bits as solve, verify_guard_on_inputs as verify, guard_value)

def test_8bit_all_255_observed_except_one_always_has_guard():
    for target in (0,1,127,255):
        xs=[x for x in range(256) if x!=target]
        c=solve(xs,target,width=8)
        assert c["status"]=="INPUT_ONLY_DISTINGUISHING_GUARD_CONSTRUCTIBLE"
        assert len(c["selected_bits"])==8
        assert verify(c,xs)

def test_64bit_1000_unseen_inputs():
    t=0xabcdef0123456789
    xs=[(t+i*137949947 + 17)&((1<<64)-1) for i in range(1,1001)]
    xs=[x for x in xs if x!=t]
    c=solve(xs,t,width=64)
    assert verify(c,xs)
    assert c["count_bits"]<=64
    assert c["global_questions"]=="OPEN"

def test_observed_target_cannot_be_falsely_declared_unseen():
    assert solve([3,4,5],4,width=8)["status"]=="NO_DISTINGUISHABLE_GUARD_WITH_TARGET_IN_SOURCE"
    assert verify(solve([3,4,5],4,width=8),[3,4,5]) is False

def test_empty_observations_admit_every_input_as_separation():
    c=solve([],5,width=8)
    assert c["selected_bits"]==[]
    assert verify(c,[])
    assert guard_value(c["selected_bits"],0,5)==1

def test_invalid_inputs_hold_fail_closed():
    assert solve([-1],3,8)["status"]=="HOLD_BAD_INPUT"
    assert solve([256],3,8)["status"]=="HOLD_BAD_INPUT"
    assert solve([1],300,8)["status"]=="HOLD_BAD_INPUT"
    assert solve([1],3,0)["status"]=="HOLD_BAD_WIDTH"

def test_witness_is_not_claim_correct_future_gold():
    c=solve([0b0000,0b0010,0b1000],0b1011,width=4)
    assert verify(c,[0b0000,0b0010,0b1000])
    assert c["may_certify_unique_function"] is False
    # This certifies a *different source-consistent* program, not which
    # function's withheld original output is correct.
