"""Independent model-free replay for first P1.10 development receipts."""
import argparse, hashlib, json, re
from pathlib import Path
from neumann1.control_plane_v1 import finite, snapshot
from experiments.control_plane_p110_registration import registration, BOUNDARY
from experiments.control_plane_p110_runtime import run_item, evaluate, totals

class RecordedSelector:
    def __init__(self,receipt): self.receipt=snapshot(receipt)
    def score(self,*_args): return snapshot(self.receipt)

def replay_record(row,ref,record):
    receipt=record.get("selector_receipt")
    if type(receipt) is not dict:
        if record.get("accounting_complete") is False:
            for k in ("extraction_ms","feasibility_ms","selection_ms","complete_ms"): finite(record.get(k),True)
            return
        raise ValueError("P1.10 item missing selector receipt")
    expected=run_item(row,ref,RecordedSelector(receipt))
    keys=("task_id","stratum","status","accepted","executed","original_view_sha256","selected_candidate","selected_route",
          "model_calls","neural_forward_calls","generated_calls","evaluated_tokens","padded_tokens","tool_calls","verifier_calls",
          "feasibility_calls","feasibility_nodes","feasibility_constraint_checks","witness_cache_hits","accounting_complete",
          "selector_complete","selection_error","eligible_indexes","selection","proposal","selector_decision")
    for k in keys:
        if record.get(k)!=expected.get(k): raise ValueError("P1.10 semantic replay drift: "+k)
    if bool(record.get("error"))!=bool(expected.get("error")): raise ValueError("P1.10 error coverage drift")
    observed=record.get("execution"); replayed=expected.get("execution")
    if (observed is None)!=(replayed is None): raise ValueError("P1.10 execution coverage drift")
    if observed is not None:
        for k in ("accepted","executed","answer","error"):
            if observed.get(k)!=replayed.get(k): raise ValueError("P1.10 execution semantic drift: "+k)
    for k in ("extraction_ms","feasibility_ms","selection_ms","compile_ms","routing_ms","execution_ms","verification_ms","complete_ms"):
        finite(record.get(k),True)

def replay(directory):
    directory=Path(directory); read=lambda n:json.loads((directory/n).read_bytes()); terminal=read("terminal.json")
    names={p.name for p in directory.glob("*.json") if p.name!="terminal.json"}
    if names!=set(terminal["files"]): raise ValueError("P1.10 terminal coverage drift")
    allowed={"study_started.json","manifest.json","core.json","report.json"}
    allowed.update("task_%02d%s.json"%(i,s) for i in range(8) for s in ("","_started"))
    if names-allowed: raise ValueError("unexpected P1.10 study member")
    for name,expected in terminal["files"].items():
        p=directory/name
        if Path(name).name!=name or p.is_symlink(): raise ValueError("unsafe terminal member")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise ValueError("P1.10 receipt byte drift: "+name)
    reg,rows,refs=registration(); report=read("report.json"); started=read("study_started.json"); head=report["source_head"]
    if not re.fullmatch(r"[0-9a-f]{40}",head) or started.get("frozen_head")!=head or started.get("first_only") is not True:
        raise ValueError("P1.10 first source identity drift")
    complete=report["status"]=="COMPLETE"
    records=[]; gap=False
    for i,(row,ref) in enumerate(zip(rows,refs)):
        name="task_%02d.json"%i
        if name not in names:
            if complete: raise ValueError("complete P1.10 result missing task")
            gap=True; continue
        if gap: raise ValueError("noncontiguous P1.10 partial receipts")
        record=read(name); marker=read("task_%02d_started.json"%i)
        if record.get("task_id")!=row["task_id"] or marker!={"task_id":row["task_id"]}: raise ValueError("P1.10 task identity drift")
        replay_record(row,ref,record); records.append(record)
    if complete and "core.json" not in names: raise ValueError("complete P1.10 result missing core identity")
    decision=evaluate(records,refs,report["core_audit"].get("unchanged"),complete,report["whole_study_ms"])
    if decision!=report["decision"] or terminal["decision"]!=decision["verdict"] or terminal["complete"]!=complete: raise ValueError("P1.10 decision drift")
    if report["observations"]!=len(records) or report["cost_totals"]!=totals(records): raise ValueError("P1.10 aggregate cost drift")
    if report.get("accounting_complete")!=(complete and all(r.get("accounting_complete") is True for r in records)): raise ValueError("P1.10 aggregate accounting drift")
    if terminal.get("no_replacement") is not True: raise ValueError("replacement evidence forbidden")
    for obj in (report,terminal,started):
        for k,v in BOUNDARY.items():
            if obj.get(k)!=v: raise ValueError("P1.10 boundary drift: "+k)
    for k,v in {"frontier_calls":0,"fallback_calls":0,"new_training":False,"sealed_data_opened":False,
                "historical_score_reuse":False,"p19_opened_task_score_reuse":False}.items():
        if report.get(k)!=v: raise ValueError("forbidden P1.10 study drift: "+k)
    if complete and report.get("error") is not None: raise ValueError("complete P1.10 report hides error")
    if read("manifest.json")!={"registration":reg,"public_rows":rows,"frozen_head":head}: raise ValueError("P1.10 manifest drift")
    return {"integrity_valid":True,"complete":complete,"decision":decision,"model_inference":False,"cost_replayed":True,**BOUNDARY}

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--directory",required=True); a=p.parse_args(); print(json.dumps(replay(a.directory),sort_keys=True))
