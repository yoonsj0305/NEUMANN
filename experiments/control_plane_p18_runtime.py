"""P1.8 opened-development runtime helpers; no import-time model work."""
from time import perf_counter_ns

from neumann1.control_plane_v1 import digest, finite, snapshot
from neumann1.control_plane_p13 import execute_selected
from neumann1.control_plane_p14 import _routing_from_proposal
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import Budget as P0Budget, prune_candidates
from neumann1.control_plane_p18_semantic import build_semantic_bundle, validate_selection
from experiments.control_plane_p14_dev import _hidden_verifier
from experiments.control_plane_p18_registration import GATE, BOUNDARY

IDS=tuple(["p18d_a0%d"%i for i in range(1,5)]+["p18d_b0%d"%i for i in range(1,5)])

def known_sum(rows,key):
    v=[r.get(key) for r in rows]
    return sum(v) if all(type(x) is int and x>=0 for x in v) else None

def totals(rows):
    keys=("model_calls","neural_forward_calls","generated_calls","evaluated_tokens","padded_tokens",
          "tool_calls","verifier_calls","feasibility_calls","feasibility_nodes",
          "feasibility_constraint_checks","witness_cache_hits")
    return {k:known_sum(rows,k) for k in keys}

def evaluate(rows,refs,core_unchanged,complete,whole_ms):
    out=lambda v,reason,**extra:{**BOUNDARY,"verdict":v,"reason":reason,**extra}
    if complete is not True or tuple(r.get("task_id") for r in rows)!=IDS:
        return out("NOT_EVALUATED","INCOMPLETE_OR_COVERAGE_DRIFT")
    if tuple(r.get("task_id") for r in refs)!=IDS or core_unchanged is not True:
        return out("NOT_EVALUATED","REFERENCE_OR_CORE_IDENTITY_DRIFT")
    if finite(whole_ms,True)>GATE["whole_study_wall_ms"]: return out("FAIL","COMPLETE_COST_WALL_CAP")
    if any(finite(r.get("complete_ms"),True)>GATE["per_item_wall_ms"] for r in rows): return out("FAIL","TASK_WALL_CAP")
    try:
        for r in rows:
            if r.get("accounting_complete") is not True or type(r.get("accepted")) is not bool: raise ValueError
            for k in ("model_calls","neural_forward_calls","generated_calls","evaluated_tokens","padded_tokens",
                      "tool_calls","verifier_calls","feasibility_calls","feasibility_nodes",
                      "feasibility_constraint_checks","witness_cache_hits"):
                if type(r.get(k)) is not int or r[k]<0: raise ValueError
            for k in ("extraction_ms","feasibility_ms","selection_ms","compile_ms","routing_ms","execution_ms","verification_ms","complete_ms"):
                finite(r.get(k),True)
    except Exception:
        return out("FAIL","CONTROL_WORK_ACCOUNTING_FAILURE",cost_totals=totals(rows))
    a,b=rows[:4],rows[4:]
    path={
      "a_model_calls":known_sum(a,"model_calls"),"a_neural_forward_calls":known_sum(a,"neural_forward_calls"),
      "b_model_calls":known_sum(b,"model_calls"),"b_neural_forward_calls":known_sum(b,"neural_forward_calls"),
      "generated_calls":known_sum(rows,"generated_calls"),"feasibility_calls":known_sum(rows,"feasibility_calls"),
      "tool_calls":known_sum(rows,"tool_calls"),"verifier_calls":known_sum(rows,"verifier_calls")}
    expected={k:GATE[x] for k,x in (
      ("a_model_calls","a_model_calls_exact"),("a_neural_forward_calls","a_neural_forward_calls_exact"),
      ("b_model_calls","b_model_calls_exact"),("b_neural_forward_calls","b_neural_forward_calls_exact"),
      ("generated_calls","generated_calls_exact"),("feasibility_calls","feasibility_calls_exact"),
      ("tool_calls","tool_calls_exact"),("verifier_calls","verifier_calls_exact"))}
    if path!=expected:return out("FAIL","CONTROL_PATH_COST_DRIFT",path_cost=path,cost_totals=totals(rows))
    if any(r.get("selection")!="UNIQUE_PROVEN_FEASIBLE_ZERO_NEURAL" for r in a):
        return out("FAIL","A_FEASIBILITY_PATH_DRIFT",path_cost=path)
    if any(r.get("selection")!="FEASIBLE_MASKED_SEMANTIC_FULL_S4" for r in b):
        return out("FAIL","B_SEMANTIC_PATH_DRIFT",path_cost=path)
    counts={"accepted":sum(r["accepted"] for r in rows),"a_accepted":sum(r["accepted"] for r in a),
            "b_accepted":sum(r["accepted"] for r in b),"path_cost":path,"cost_totals":totals(rows)}
    counts["a_gate_pass"]=counts["a_accepted"]==GATE["a_accepted_exact"]
    counts["b_gate_pass"]=counts["b_accepted"]>=GATE["b_accepted_min"]
    ok=counts["accepted"]>=GATE["overall_accepted_min"] and counts["a_gate_pass"] and counts["b_gate_pass"]
    return out("PASS" if ok else "FAIL","OPENED_P18_A_B_DIAGNOSTIC_ONLY" if ok else "P18_A_OR_B_CAPABILITY_FAILURE",
               **counts,next="FREEZE_P18_THEN_REGISTER_NEW_FRESH_VALIDATION" if ok else "RETAIN_FIRST_P18_FAILURE_AND_DIAGNOSE")

def run_item(row,ref,selector=None):
    began=perf_counter_ns(); elapsed=lambda:(perf_counter_ns()-began)/1e6
    r={"task_id":row["task_id"],"stratum":row["stratum"],"accepted":False,"executed":False,
       "original_view_sha256":digest(row["view"]),"selected_candidate":None,"selected_route":None,
       "model_calls":0,"neural_forward_calls":0,"generated_calls":0,"evaluated_tokens":0,"padded_tokens":0,
       "tool_calls":0,"verifier_calls":0,"feasibility_calls":0,"feasibility_nodes":0,
       "feasibility_constraint_checks":0,"witness_cache_hits":0,"accounting_complete":True,"error":None,
       "extraction_ms":0.0,"feasibility_ms":0.0,"selection_ms":0.0,"compile_ms":0.0,
       "routing_ms":0.0,"execution_ms":0.0,"verification_ms":0.0,"proposal":None}
    try:
        t=perf_counter_ns(); parsed,bundle=build_semantic_bundle(row["view"]); r["extraction_ms"]=(perf_counter_ns()-t)/1e6
        r["parser_view"]=snapshot(parsed); r["bundle"]=snapshot(bundle)
        t=perf_counter_ns(); p=prune_candidates(parsed,bundle,P0Budget()); r["feasibility_ms"]=(perf_counter_ns()-t)/1e6
        r["pruning_receipt"]=snapshot(p); r.update(feasibility_calls=p["probe_calls"],feasibility_nodes=p["nodes"],feasibility_constraint_checks=p["constraint_checks"])
        if p["unknown_indexes"]: raise ValueError("feasibility UNKNOWN")
        eligible=p["sat_indexes"]; r["eligible_indexes"]=snapshot(eligible)
        if row["stratum"]=="A_FEASIBILITY_REDUCIBLE":
            if len(eligible)!=1: raise ValueError("A did not reduce to one feasible candidate")
            chosen=eligible[0]; r["selection"]="UNIQUE_PROVEN_FEASIBLE_ZERO_NEURAL"
        else:
            if len(eligible)<2 or selector is None: raise ValueError("B requires multi-feasible selector")
            t=perf_counter_ns(); r.update(model_calls=1,accounting_complete=False,neural_forward_calls=None,generated_calls=None,evaluated_tokens=None,padded_tokens=None)
            receipt=selector.score(row["view"],parsed,bundle,GATE["per_item_wall_ms"]-elapsed()); r["selector_receipt"]=snapshot(receipt)
            for target,key in (("neural_forward_calls","forward_calls"),("evaluated_tokens","evaluated_tokens"),("padded_tokens","padded_tokens")):
                v=receipt.get("ledger",{}).get(key)
                if type(v) is int and v>=0:r[target]=v
            v=receipt.get("generated_calls")
            if type(v) is int and v>=0:r["generated_calls"]=v
            chosen=validate_selection(row["view"],parsed,bundle,eligible,receipt); r["selection_ms"]=(perf_counter_ns()-t)/1e6
            r.update(accounting_complete=True,selection="FEASIBLE_MASKED_SEMANTIC_FULL_S4")
        r["selected_candidate"]=chosen; cached=p["candidates"][chosen]
        t=perf_counter_ns(); proposal=compile_references(parsed,bundle,chosen); r["proposal"]=snapshot(proposal); r["compile_ms"]=(perf_counter_ns()-t)/1e6
        t=perf_counter_ns(); typed,routing=_routing_from_proposal(parsed,proposal); r["routing_ms"]=(perf_counter_ns()-t)/1e6; r["selected_route"]=routing["selected_route"]
        checker=_hidden_verifier(ref)
        def execute(route,project):
            r["tool_calls"]+=1; s=perf_counter_ns()
            try:
                if route!="CSP" or cached["status"]!="SAT" or cached["project_sha256"]!=digest(project): raise ValueError("cached witness/project drift")
                r["witness_cache_hits"]+=1; return snapshot(cached["witness"])
            finally:r["execution_ms"]+=(perf_counter_ns()-s)/1e6
        def verify(_typed,answer):
            r["verifier_calls"]+=1; s=perf_counter_ns()
            try:return checker(snapshot(row["view"]),answer)
            finally:r["verification_ms"]+=(perf_counter_ns()-s)/1e6
        execution=execute_selected(typed,routing,execute,verify); r["execution"]=snapshot(execution)
        r.update(accepted=execution["accepted"],executed=execution["executed"],status="ACCEPTED" if execution["accepted"] else "REJECTED_BY_ORIGINAL_VERIFIER")
        if elapsed()>=GATE["per_item_wall_ms"]: r.update(accepted=False,status="FAILED"); raise TimeoutError("complete item deadline")
    except Exception as exc:
        r["status"]="FAILED"; r["error"]=type(exc).__name__+": "+str(exc)
    finally:r["complete_ms"]=elapsed()
    return r
