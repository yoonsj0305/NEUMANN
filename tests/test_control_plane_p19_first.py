"""P1.9 opened-development registration/gate contracts; CPU-only."""
from experiments.control_plane_p19_registration import (
    registration, check_construction, GATE, BOUNDARY, COUNTS, EXPECTED_FORWARDS,
)
from experiments.control_plane_p19_runtime import evaluate, totals

def synthetic_rows(accepted=None, abstained=None):
    accepted=[True]*8 if accepted is None else list(accepted)
    abstained=set() if abstained is None else set(abstained)
    rows=[]
    for i,(k,fw) in enumerate(zip(COUNTS,EXPECTED_FORWARDS)):
        is_abstain=i in abstained
        ok=accepted[i] and not is_abstain
        selected=None if is_abstain else 0
        status="SEMANTIC_ABSTAINED" if is_abstain else ("ACCEPTED" if ok else "REJECTED_BY_ORIGINAL_VERIFIER")
        rows.append({
          "task_id":"p19d_b%02d"%(i+1),"accepted":ok,"executed":not is_abstain,
          "selected_candidate":selected,"status":status,"accounting_complete":True,"selector_complete":True,
          "model_calls":1,"neural_forward_calls":fw,"generated_calls":0,
          "evaluated_tokens":1000,"padded_tokens":1000,
          "tool_calls":0 if is_abstain else 1,"verifier_calls":0 if is_abstain else 1,
          "feasibility_calls":k,"feasibility_nodes":k,"feasibility_constraint_checks":k,
          "witness_cache_hits":0 if is_abstain else 1,
          "extraction_ms":1.0,"feasibility_ms":1.0,"selection_ms":10.0,
          "compile_ms":0.0 if is_abstain else 1.0,"routing_ms":0.0 if is_abstain else 1.0,
          "execution_ms":0.0 if is_abstain else 1.0,"verification_ms":0.0 if is_abstain else 1.0,
          "complete_ms":20.0,
        })
    return rows

def test_registration_is_fresh_and_model_free():
    reg,rows,refs=registration()
    assert reg["scores_seen_at_registration"] is False
    assert reg["first_only"] is True
    assert reg["p18_opened_task_score_reuse"] is False
    assert len(rows)==len(refs)==8
    result=check_construction()
    assert result["candidate_counts"]==COUNTS
    assert result["expected_forward_calls"]==EXPECTED_FORWARDS
    assert result["total_expected_forward_calls"]==39
    assert result["multi_feasible_tasks"]==8
    assert result["out_of_grammar_stops"]==4
    assert result["model_inference"] is False
    assert result["weights_loaded"] is False

def test_all_accepts_pass_but_never_admit_p2():
    _,_,refs=registration()
    d=evaluate(synthetic_rows(),refs,True,True,1000.0)
    assert d["verdict"]=="PASS"
    assert d["accepted"]==8
    assert d["p2_registration_admitted"] is False
    assert d["decision3_admitted"] is False

def test_two_complete_abstentions_are_capability_not_accounting_failure():
    _,_,refs=registration()
    rows=synthetic_rows(abstained={1,6})
    d=evaluate(rows,refs,True,True,1000.0)
    assert d["verdict"]=="PASS"
    assert d["accepted"]==6
    assert d["semantic_abstained"]==2
    assert d["reason"]=="OPENED_P19_PROPOSITION_DIAGNOSTIC_ONLY"

def test_three_semantic_failures_miss_capability_floor():
    _,_,refs=registration()
    rows=synthetic_rows(abstained={0,1,2})
    d=evaluate(rows,refs,True,True,1000.0)
    assert d["verdict"]=="FAIL"
    assert d["reason"]=="P19_SEMANTIC_CAPABILITY_FAILURE"
    assert d["accepted"]==5

def test_partial_selector_is_accounting_failure():
    _,_,refs=registration()
    rows=synthetic_rows()
    rows[3]["accounting_complete"]=False
    rows[3]["selector_complete"]=False
    assert evaluate(rows,refs,True,True,1000.0)["reason"]=="CONTROL_WORK_ACCOUNTING_FAILURE"

def test_exact_prospective_path_cost_is_39_forwards():
    rows=synthetic_rows()
    t=totals(rows)
    assert t["model_calls"]==8
    assert t["neural_forward_calls"]==39
    assert t["feasibility_calls"]==23
    assert GATE["selector_wall_ms"]==60000.0
    assert GATE["per_item_wall_ms"]==90000.0
    assert GATE["whole_study_wall_ms"]==900000.0
    for key in ("p2_registration_admitted","p2_admitted","decision3_admitted"):
        assert BOUNDARY[key] is False

def test_per_item_cost_drift_fails_closed():
    _,_,refs=registration()
    rows=synthetic_rows()
    rows[0]["neural_forward_calls"]=3
    assert evaluate(rows,refs,True,True,1000.0)["reason"]=="CONTROL_WORK_ACCOUNTING_FAILURE"

def test_wall_and_core_identity_fail_closed():
    _,_,refs=registration()
    assert evaluate(synthetic_rows(),refs,False,True,1000.0)["verdict"]=="NOT_EVALUATED"
    rows=synthetic_rows(); rows[0]["complete_ms"]=GATE["per_item_wall_ms"]+1
    assert evaluate(rows,refs,True,True,1000.0)["reason"]=="TASK_WALL_CAP"
