"""Independent model-free replay for first P1.8 development receipts."""
import argparse, hashlib, json, re
from pathlib import Path

from neumann1.control_plane_v1 import digest, finite, snapshot
from experiments.control_plane_p18_registration import registration, BOUNDARY
from experiments.control_plane_p18_runtime import run_item, evaluate, totals

class RecordedSelector:
    def __init__(self,receipt): self.receipt=snapshot(receipt)
    def score(self,*_args): return snapshot(self.receipt)

def replay_record(row,ref,record):
    selector=None
    if row["stratum"]=="B_MULTI_FEASIBLE_SEMANTIC":
        receipt=record.get("selector_receipt")
        if type(receipt) is not dict:
            if record.get("accepted") is False and record.get("accounting_complete") is False and record.get("tool_calls")==0 and record.get("verifier_calls")==0:
                for k in ("extraction_ms","feasibility_ms","selection_ms","complete_ms"): finite(record.get(k),True)
                return
            raise ValueError("B item missing selector receipt")
        selector=RecordedSelector(receipt)
    expected=run_item(row,ref,selector)
    keys=("task_id","stratum","status","accepted","executed","original_view_sha256","selected_candidate","selected_route",
          "model_calls","neural_forward_calls","generated_calls","evaluated_tokens","padded_tokens","tool_calls","verifier_calls",
          "feasibility_calls","feasibility_nodes","feasibility_constraint_checks","witness_cache_hits","accounting_complete",
          "eligible_indexes","selection","proposal")
    for k in keys:
        if record.get(k)!=expected.get(k): raise ValueError("P1.8 semantic replay drift: "+k)
    if bool(record.get("error"))!=bool(expected.get("error")): raise ValueError("P1.8 error coverage drift")
    observed=record.get("execution"); replayed=expected.get("execution")
    if (observed is None)!=(replayed is None): raise ValueError("execution coverage drift")
    if observed is not None:
        for k in ("accepted","executed","answer","error"):
            if observed.get(k)!=replayed.get(k): raise ValueError("execution semantic drift: "+k)
        finite(observed.get("complete_ms"),True); finite(replayed.get("complete_ms"),True)
    for k in ("extraction_ms","feasibility_ms","selection_ms","compile_ms","routing_ms","execution_ms","verification_ms","complete_ms"):
        finite(record.get(k),True)

def replay(directory):
    directory=Path(directory); read=lambda n:json.loads((directory/n).read_bytes())
    terminal=read("terminal.json")
    names={p.name for p in directory.glob("*.json") if p.name!="terminal.json"}
    if names!=set(terminal["files"]): raise ValueError("P1.8 terminal coverage drift")
    allowed={"study_started.json","manifest.json","core.json","report.json"}
    allowed.update("task_%02d%s.json"%(i,s) for i in range(8) for s in ("","_started"))
    if names-allowed: raise ValueError("unexpected P1.8 study member")
    for name,expected in terminal["files"].items():
        p=directory/name
        if Path(name).name!=name or p.is_symlink(): raise ValueError("unsafe terminal member")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise ValueError("P1.8 receipt byte drift: "+name)

    reg,rows,refs=registration(); report=read("report.json"); started=read("study_started.json"); head=report["source_head"]
    if not re.fullmatch(r"[0-9a-f]{40}",head) or started.get("frozen_head")!=head or started.get("first_only") is not True:
        raise ValueError("P1.8 first source identity drift")
    complete=report["status"]=="COMPLETE"
    if report["status"] not in ("COMPLETE","INCOMPLETE"): raise ValueError("unknown report status")
    records=[]; gap=False
    for i,(row,ref) in enumerate(zip(rows,refs)):
        name="task_%02d.json"%i
        if name not in names:
            if complete: raise ValueError("complete result missing task")
            gap=True; continue
        if gap: raise ValueError("noncontiguous partial receipts")
        record=read(name); marker=read("task_%02d_started.json"%i)
        if record.get("task_id")!=row["task_id"] or marker!={"task_id":row["task_id"],"view_sha256":digest(row["view"])}:
            raise ValueError("P1.8 task identity drift")
        replay_record(row,ref,record); records.append(record)

    if complete and "core.json" not in names: raise ValueError("complete result missing core identity")
    decision=evaluate(records,refs,report["core_audit"].get("unchanged"),complete,report["whole_study_ms"])
    if decision!=report["decision"] or terminal["decision"]!=decision["verdict"] or terminal["complete"]!=complete:
        raise ValueError("P1.8 decision drift")
    if report["observations"]!=len(records) or report["cost_totals"]!=totals(records): raise ValueError("aggregate cost drift")
    if report.get("accounting_complete")!=(complete and all(r.get("accounting_complete") is True for r in records)):
        raise ValueError("aggregate accounting drift")
    if terminal.get("no_replacement") is not True: raise ValueError("replacement evidence forbidden")
    for obj in (report,terminal,started):
        for k,v in BOUNDARY.items():
            if obj.get(k)!=v: raise ValueError("P1.8 boundary drift: "+k)
    for k,v in {"frontier_calls":0,"fallback_calls":0,"new_training":False,"sealed_data_opened":False,"historical_score_reuse":False}.items():
        if report.get(k)!=v: raise ValueError("forbidden study drift: "+k)
    if complete and report.get("error") is not None: raise ValueError("complete report hides error")
    if "manifest.json" in names:
        if read("manifest.json")!={"registration":reg,"public_rows":rows,"frozen_head":head}: raise ValueError("manifest drift")
    elif complete: raise ValueError("complete result missing manifest")
    return {"integrity_valid":True,"complete":complete,"decision":decision,"model_inference":False,"cost_replayed":True,**BOUNDARY}

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--directory",required=True); a=p.parse_args()
    print(json.dumps(replay(a.directory),sort_keys=True))
