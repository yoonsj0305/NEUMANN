"""Model-free reconstruction from raw sketch text; cached proposals are not trusted."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from neumann1.control_plane_v1 import digest, finite, snapshot
from neumann1.control_plane_p15 import interpret_and_execute, validate_receipt, SketchProposalFailure
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p15_dev import evaluate, totals
from experiments.control_plane_p15_registration import registration, BOUNDARY, GATE


class RecordedCompiler:
    def __init__(self,record): self.record=record
    def propose(self,view,remaining_ms):
        receipt=self.record.get("semantic_receipt")
        if receipt is None:
            raise RuntimeError("retained backend exception; generated work UNKNOWN")
        try: validate_receipt(receipt)
        except Exception as exc: raise SketchProposalFailure(type(exc).__name__+": "+str(exc),receipt) from exc
        return snapshot(receipt)


def replay_record(row,ref,record):
    expected=interpret_and_execute(row["view"],RecordedCompiler(record),_executor,_hidden_verifier(ref))
    keys=("schema","status","accepted","executed","selected_route","sketch","proposal",
          "original_view_sha256","typed_view_sha256","model_calls","input_tokens","output_tokens",
          "tool_calls","verifier_calls","accounting_complete","semantic_budget_valid","semantic_receipt")
    # A real observed item timeout is retained as budget failure, never replayed
    # into an admission, even when the deterministic path is now fast.
    timed_out=record.get("semantic_budget_valid") is False and "deadline" in (record.get("error") or "") and record.get("accounting_complete") is True
    stopped_before_execution=timed_out and record.get("executed") is False
    if timed_out and finite(record.get("complete_ms"),True)<=GATE["per_item_wall_ms"]:
        raise ValueError("item timeout lacks observed wall cap")
    for key in keys:
        if timed_out and key in ("status","accepted","semantic_budget_valid"): continue
        if stopped_before_execution and key in ("executed","tool_calls","verifier_calls"): continue
        if record.get(key)!=expected.get(key): raise ValueError("raw sketch replay drift: "+key)
    if timed_out and (record.get("status")!="FAILED" or record.get("accepted") is not False):
        raise ValueError("item timeout cannot be accepted")
    if bool(record.get("error"))!=bool(expected.get("error")) and not timed_out:
        raise ValueError("retained failure explanation drift")
    a,b=record.get("execution"),expected.get("execution")
    if stopped_before_execution:
        if a is not None or record.get("tool_calls")!=0 or record.get("verifier_calls")!=0:
            raise ValueError("pre-execution deadline cannot conceal tool work")
        b=None
    if (a is None)!=(b is None): raise ValueError("execution receipt coverage drift")
    if a is not None:
        for key in ("accepted","executed","answer","error"):
            if a.get(key)!=b.get(key): raise ValueError("execution answer/checker drift: "+key)
    for key in ("complete_ms","execution_ms","verification_ms"):
        finite(record.get(key),True)
    for key in ("compile_ms","routing_ms"):
        if record.get(key) is not None: finite(record[key],True)


def replay(directory):
    directory=Path(directory); read=lambda name:json.loads((directory/name).read_bytes())
    terminal=read("terminal.json")
    names={p.name for p in directory.glob("*.json") if p.name!="terminal.json"}
    if names!=set(terminal["files"]): raise ValueError("terminal coverage drift")
    allowed={"study_started.json","manifest.json","core.json","report.json"}
    allowed.update("task_%02d%s.json"%(i,suffix) for i in range(8) for suffix in ("","_started"))
    if names-allowed: raise ValueError("unexpected study member")
    for name,expected in terminal["files"].items():
        if Path(name).name!=name or (directory/name).is_symlink(): raise ValueError("unsafe terminal member")
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=expected: raise ValueError("receipt byte drift: "+name)
    reg,rows,refs=registration(); report=read("report.json"); started=read("study_started.json")
    head=report["source_head"]
    if not re.fullmatch(r"[0-9a-f]{40}",head) or started.get("frozen_head")!=head or started.get("first_only") is not True:
        raise ValueError("first source identity drift")
    if report["status"] not in ("COMPLETE","INCOMPLETE"): raise ValueError("unknown terminal status")
    complete=report["status"]=="COMPLETE"; records=[]; gap=False
    for i,(row,ref) in enumerate(zip(rows,refs)):
        name="task_%02d.json"%i
        if name not in names:
            if complete: raise ValueError("complete result missing record")
            gap=True
            continue
        if gap: raise ValueError("noncontiguous partial receipt coverage")
        record=read(name); marker=read("task_%02d_started.json"%i)
        if record.get("task_id")!=row["task_id"] or record.get("kind")!=ref["kind"] or marker!={"task_id":row["task_id"],"view_sha256":digest(row["view"])}:
            raise ValueError("task/started identity drift")
        replay_record(row,ref,record); records.append(record)
        if record.get("semantic_receipt") and "core.json" in names and record["semantic_receipt"].get("identity")!=read("core.json"):
            # Core drift is legitimate retained nonpass, but cannot be falsely
            # declared unchanged in the study audit or in a valid receipt.
            if report["core_audit"].get("unchanged") is True or record.get("semantic_budget_valid") is True:
                raise ValueError("generation/core identity drift")
    decision=evaluate(records,refs,report["core_audit"].get("unchanged"),complete,report["whole_study_ms"])
    if decision!=report["decision"] or terminal["decision"]!=decision["verdict"] or terminal["complete"]!=complete:
        raise ValueError("decision/terminal drift")
    if report["observations"]!=len(records) or report["cost_totals"]!=totals(records): raise ValueError("aggregate cost drift")
    if report.get("accounting_complete")!=(complete and all(r["accounting_complete"] for r in records)):
        raise ValueError("aggregate accounting drift")
    if terminal.get("no_replacement") is not True: raise ValueError("replacement evidence forbidden")
    for obj in (report,terminal,started):
        for key,value in BOUNDARY.items():
            if obj.get(key)!=value: raise ValueError("study boundary drift: "+key)
    for key,value in {"frontier_calls":0,"fallback_calls":0,"new_training":False,"sealed_data_opened":False,"historical_score_reuse":False}.items():
        if report.get(key)!=value: raise ValueError("forbidden study drift: "+key)
    if complete and report.get("error") is not None: raise ValueError("completed report cannot hide run error")
    if "manifest.json" in names:
        manifest=read("manifest.json")
        if manifest!={"registration":reg,"public_rows":rows,"frozen_head":head}: raise ValueError("frozen manifest drift")
    elif complete: raise ValueError("complete result missing manifest")
    return {"integrity_valid":True,"complete":complete,"decision":decision,"model_inference":False,**BOUNDARY}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--directory",required=True); args=parser.parse_args()
    print(json.dumps(replay(args.directory),sort_keys=True))
