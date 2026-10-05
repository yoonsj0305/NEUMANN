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


def _selector_receipt(row, preferred, strength=2.0):
    from neumann1.control_plane_p19_semantic import build_bundle
    from neumann1.control_plane_p19 import proposition_prompt
    from neumann1.control_plane_p11 import CodePlan, plan_cost
    from neumann1.control_plane_p12 import CODE_TOKEN_IDS
    from neumann1.control_plane_p1_contract import MODEL
    from neumann1.control_plane_v1 import digest

    parsed,bundle=build_bundle(row["view"])
    eligible=list(range(len(bundle["candidates"])))
    prompts=[proposition_prompt(row["view"],parsed,bundle,i) for i in eligible]
    prefixes=[tuple(range(1,5+i)) for i in range(len(eligible))]
    matrix=[]
    for i in range(len(eligible)):
        if i==preferred: matrix.append([-0.1,-0.1-strength,-5.0,-5.0])
        else: matrix.append([-0.1-strength,-0.1,-5.0,-5.0])
    passes=[]
    k=len(eligible)
    for mode,size,order in (
        ("batch_all",k,list(range(k))),
        ("unbatched1",1,list(range(k))),
        ("reverse_batch_all",k,list(reversed(range(k)))),
    ):
        ordered=[prefixes[i] for i in order]
        plan=CodePlan(tuple(ordered),CODE_TOKEN_IDS); cost=plan_cost(plan,size)
        passes.append({
          "mode":mode,"batch_size":size,"order":order,"prefixes":ordered,
          "code_ids":list(CODE_TOKEN_IDS),"planned":cost,"actual":cost,"status":"COMPLETE",
          "matrix":[list(x) for x in matrix],"peak_accelerator_memory_bytes":1,
        })
    ledger={k:0 for k in passes[0]["actual"]}
    for p in passes:
        for key,value in p["actual"].items(): ledger[key]+=value
    return {
      "status":"COMPLETE","bundle_sha256":bundle["bundle_sha256"],
      "original_view_sha256":digest(row["view"]),"parser_view_sha256":digest(parsed),
      "eligible_indexes":eligible,"prompt_sha256":[digest(p) for p in prompts],
      "identity":{**MODEL,"device_type":"cuda","device_name":"Tesla T4","evidence_kind":"actual_frozen_model",
                  "framework":"torch-2.11.0+cu128/transformers-5.16.1","torchvision":"0.26.0+cu128"},
      "unchanged":True,"generated_calls":0,"passes":passes,"ledger":ledger,
    }

class _RecordedSelector:
    def __init__(self,receipt): self.receipt=receipt
    def score(self,*_args):
        from neumann1.control_plane_v1 import snapshot
        return snapshot(self.receipt)

def test_run_item_complete_selector_reaches_original_verifier():
    from experiments.control_plane_p19_runtime import run_item
    _,rows,refs=registration()
    row,ref=rows[0],refs[0]
    receipt=_selector_receipt(row,ref["expected_candidate"],strength=2.0)
    got=run_item(row,ref,_RecordedSelector(receipt))
    assert got["status"]=="ACCEPTED"
    assert got["accepted"] is True and got["executed"] is True
    assert got["selected_candidate"]==ref["expected_candidate"]
    assert got["model_calls"]==1 and got["neural_forward_calls"]==4
    assert got["tool_calls"]==got["verifier_calls"]==1
    assert got["accounting_complete"] is True and got["selector_complete"] is True

def test_run_item_low_margin_is_complete_semantic_abstention():
    from experiments.control_plane_p19_runtime import run_item
    _,rows,refs=registration()
    row,ref=rows[0],refs[0]
    receipt=_selector_receipt(row,ref["expected_candidate"],strength=0.2)
    got=run_item(row,ref,_RecordedSelector(receipt))
    assert got["status"]=="SEMANTIC_ABSTAINED"
    assert got["accepted"] is False and got["executed"] is False
    assert got["selected_candidate"] is None
    assert got["tool_calls"]==got["verifier_calls"]==0
    assert got["accounting_complete"] is True and got["selector_complete"] is True
    assert "candidate margin failure" in got["selection_error"]
