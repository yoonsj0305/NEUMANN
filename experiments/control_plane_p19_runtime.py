"""P1.9 opened-development runtime helpers; no import-time model work."""
from time import perf_counter_ns

from neumann1.control_plane_v1 import digest, finite, snapshot
from neumann1.control_plane_p13 import execute_selected
from neumann1.control_plane_p14 import _routing_from_proposal
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import prune_candidates
from neumann1.control_plane_p19 import validate_selection
from neumann1.control_plane_p19_semantic import build_bundle
from experiments.control_plane_p14_dev import _hidden_verifier
from experiments.control_plane_p19_registration import GATE, BOUNDARY, COUNTS, EXPECTED_FORWARDS

IDS=tuple("p19d_b%02d"%i for i in range(1,9))

def known_sum(rows,key):
    values=[r.get(key) for r in rows]
    return sum(values) if all(type(v) is int and v>=0 for v in values) else None

def totals(rows):
    keys=("model_calls","neural_forward_calls","generated_calls","evaluated_tokens","padded_tokens",
          "tool_calls","verifier_calls","feasibility_calls","feasibility_nodes",
          "feasibility_constraint_checks","witness_cache_hits")
    return {k:known_sum(rows,k) for k in keys}

def evaluate(rows,refs,core_unchanged,complete,whole_ms):
    out=lambda verdict,reason,**extra:{**BOUNDARY,"verdict":verdict,"reason":reason,**extra}
    if complete is not True or tuple(r.get("task_id") for r in rows)!=IDS:
        return out("NOT_EVALUATED","INCOMPLETE_OR_COVERAGE_DRIFT")
    if tuple(r.get("task_id") for r in refs)!=IDS or core_unchanged is not True:
        return out("NOT_EVALUATED","REFERENCE_OR_CORE_IDENTITY_DRIFT")
    if finite(whole_ms,True)>GATE["whole_study_wall_ms"]:
        return out("FAIL","COMPLETE_COST_WALL_CAP")
    if any(finite(r.get("complete_ms"),True)>GATE["per_item_wall_ms"] for r in rows):
        return out("FAIL","TASK_WALL_CAP")

    try:
        for i,r in enumerate(rows):
            if r.get("accounting_complete") is not True or type(r.get("accepted")) is not bool:
                raise ValueError
            if r.get("selector_complete") is not True:
                raise ValueError
            for k in ("model_calls","neural_forward_calls","generated_calls","evaluated_tokens","padded_tokens",
                      "tool_calls","verifier_calls","feasibility_calls","feasibility_nodes",
                      "feasibility_constraint_checks","witness_cache_hits"):
                if type(r.get(k)) is not int or r[k]<0: raise ValueError
            for k in ("extraction_ms","feasibility_ms","selection_ms","compile_ms","routing_ms",
                      "execution_ms","verification_ms","complete_ms"):
                finite(r.get(k),True)
            if r["model_calls"]!=1 or r["neural_forward_calls"]!=EXPECTED_FORWARDS[i] or r["feasibility_calls"]!=COUNTS[i]:
                raise ValueError
            selected=r.get("selected_candidate")
            if selected is None:
                if r["tool_calls"]!=0 or r["verifier_calls"]!=0 or r.get("executed") is not False or r.get("status")!="SEMANTIC_ABSTAINED":
                    raise ValueError
            else:
                if r["tool_calls"]!=1 or r["verifier_calls"]!=1 or r.get("executed") is not True:
                    raise ValueError
                if r.get("status") not in ("ACCEPTED","REJECTED_BY_ORIGINAL_VERIFIER"):
                    raise ValueError
    except Exception:
        return out("FAIL","CONTROL_WORK_ACCOUNTING_FAILURE",cost_totals=totals(rows))

    path={
      "model_calls":known_sum(rows,"model_calls"),
      "neural_forward_calls":known_sum(rows,"neural_forward_calls"),
      "generated_calls":known_sum(rows,"generated_calls"),
      "feasibility_calls":known_sum(rows,"feasibility_calls"),
      "selector_complete":sum(r["selector_complete"] is True for r in rows),
    }
    expected={
      "model_calls":GATE["model_calls_exact"],
      "neural_forward_calls":GATE["neural_forward_calls_exact"],
      "generated_calls":GATE["generated_calls_exact"],
      "feasibility_calls":GATE["feasibility_calls_exact"],
      "selector_complete":GATE["selector_complete_exact"],
    }
    if path!=expected:
        return out("FAIL","CONTROL_PATH_COST_DRIFT",path_cost=path,cost_totals=totals(rows))

    accepted=sum(r["accepted"] for r in rows)
    selected=sum(r.get("selected_candidate") is not None for r in rows)
    verifier_rejected=sum(r.get("status")=="REJECTED_BY_ORIGINAL_VERIFIER" for r in rows)
    abstained=sum(r.get("status")=="SEMANTIC_ABSTAINED" for r in rows)
    counts={
      "accepted":accepted,"selected":selected,"verifier_rejected":verifier_rejected,
      "semantic_abstained":abstained,"path_cost":path,"cost_totals":totals(rows),
    }
    passed=accepted>=GATE["accepted_min"]
    return out(
      "PASS" if passed else "FAIL",
      "OPENED_P19_PROPOSITION_DIAGNOSTIC_ONLY" if passed else "P19_SEMANTIC_CAPABILITY_FAILURE",
      **counts,
      next="FREEZE_P19_THEN_REGISTER_NEW_FRESH_VALIDATION" if passed else "RETAIN_FIRST_P19_FAILURE_AND_DIAGNOSE",
    )

def run_item(row,ref,selector):
    began=perf_counter_ns(); elapsed=lambda:(perf_counter_ns()-began)/1e6
    r={
      "task_id":row["task_id"],"stratum":row["stratum"],"accepted":False,"executed":False,
      "original_view_sha256":digest(row["view"]),"selected_candidate":None,"selected_route":None,
      "model_calls":0,"neural_forward_calls":0,"generated_calls":0,"evaluated_tokens":0,"padded_tokens":0,
      "tool_calls":0,"verifier_calls":0,"feasibility_calls":0,"feasibility_nodes":0,
      "feasibility_constraint_checks":0,"witness_cache_hits":0,"accounting_complete":True,
      "selector_complete":False,"selection_error":None,"error":None,
      "extraction_ms":0.0,"feasibility_ms":0.0,"selection_ms":0.0,"compile_ms":0.0,
      "routing_ms":0.0,"execution_ms":0.0,"verification_ms":0.0,"proposal":None,
    }
    try:
        t=perf_counter_ns(); parsed,bundle=build_bundle(row["view"]); r["extraction_ms"]=(perf_counter_ns()-t)/1e6
        r["parser_view"]=snapshot(parsed); r["bundle"]=snapshot(bundle)
        t=perf_counter_ns(); pruning=prune_candidates(parsed,bundle); r["feasibility_ms"]=(perf_counter_ns()-t)/1e6
        r["pruning_receipt"]=snapshot(pruning)
        r.update(
          feasibility_calls=pruning["probe_calls"],feasibility_nodes=pruning["nodes"],
          feasibility_constraint_checks=pruning["constraint_checks"],
        )
        if pruning["unknown_indexes"]: raise ValueError("feasibility UNKNOWN")
        eligible=pruning["sat_indexes"]; r["eligible_indexes"]=snapshot(eligible)
        if len(eligible)<2 or eligible!=list(range(len(bundle["candidates"]))):
            raise ValueError("P1.9 development requires fully multi-feasible candidates")
        if selector is None: raise ValueError("P1.9 frozen selector required")

        t=perf_counter_ns()
        r.update(model_calls=1,accounting_complete=False,neural_forward_calls=None,generated_calls=None,
                 evaluated_tokens=None,padded_tokens=None)
        left=min(GATE["selector_wall_ms"],GATE["per_item_wall_ms"]-elapsed())
        if left<=0: raise TimeoutError("P1.9 item deadline before semantic scoring")
        receipt=selector.score(row["view"],parsed,bundle,eligible,left); r["selector_receipt"]=snapshot(receipt)
        for target,key in (("neural_forward_calls","forward_calls"),("evaluated_tokens","evaluated_tokens"),
                           ("padded_tokens","padded_tokens")):
            value=receipt.get("ledger",{}).get(key)
            if type(value) is int and value>=0:r[target]=value
        value=receipt.get("generated_calls")
        if type(value) is int and value>=0:r["generated_calls"]=value
        if receipt.get("status")!="COMPLETE":
            raise ValueError("partial P1.9 selector receipt")
        r.update(accounting_complete=True,selector_complete=True)
        try:
            decision=validate_selection(row["view"],parsed,bundle,eligible,receipt)
        except ValueError as exc:
            r.update(
              status="SEMANTIC_ABSTAINED",selection="CANDIDATE_LOCAL_PROPOSITION_ABSTAIN",
              selection_error=type(exc).__name__+": "+str(exc),
              selection_ms=(perf_counter_ns()-t)/1e6,
            )
            return r
        r["selection_ms"]=(perf_counter_ns()-t)/1e6
        chosen=decision["selected_candidate"]; r["selector_decision"]=snapshot(decision)
        r.update(selected_candidate=chosen,selection="CANDIDATE_LOCAL_PROPOSITION")
        cached=pruning["candidates"][chosen]

        t=perf_counter_ns(); proposal=compile_references(parsed,bundle,chosen); r["proposal"]=snapshot(proposal); r["compile_ms"]=(perf_counter_ns()-t)/1e6
        t=perf_counter_ns(); typed,routing=_routing_from_proposal(parsed,proposal); r["routing_ms"]=(perf_counter_ns()-t)/1e6
        r["selected_route"]=routing["selected_route"]
        checker=_hidden_verifier(ref)
        def execute(route,project):
            r["tool_calls"]+=1; s=perf_counter_ns()
            try:
                if route!="CSP" or cached["status"]!="SAT" or cached["project_sha256"]!=digest(project):
                    raise ValueError("cached witness/project drift")
                r["witness_cache_hits"]+=1
                return snapshot(cached["witness"])
            finally:r["execution_ms"]+=(perf_counter_ns()-s)/1e6
        def verify(_typed,answer):
            r["verifier_calls"]+=1; s=perf_counter_ns()
            try:return checker(snapshot(row["view"]),answer)
            finally:r["verification_ms"]+=(perf_counter_ns()-s)/1e6
        execution=execute_selected(typed,routing,execute,verify); r["execution"]=snapshot(execution)
        r.update(
          accepted=execution["accepted"],executed=execution["executed"],
          status="ACCEPTED" if execution["accepted"] else "REJECTED_BY_ORIGINAL_VERIFIER",
        )
        if elapsed()>=GATE["per_item_wall_ms"]:
            r.update(accepted=False,status="FAILED"); raise TimeoutError("complete P1.9 item deadline")
    except Exception as exc:
        r["status"]="FAILED"; r["error"]=type(exc).__name__+": "+str(exc)
    finally:
        r["complete_ms"]=elapsed()
    return r
