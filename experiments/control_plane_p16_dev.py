"""Exclusive first P1.6 opened sketch diagnostic; never a P2 admission."""
import argparse
import hashlib
from importlib.metadata import version
from pathlib import Path
import re
import subprocess
from time import perf_counter_ns
import traceback

from neumann1.control_plane_v1 import canonical, finite, snapshot, digest
from neumann1.control_plane_p1_contract import manifest as p1_manifest, validate_identity
from neumann1.control_plane_p16 import FrozenHypothesisCompiler, contract, interpret_and_execute, validate_receipt
from experiments.control_plane_p1_first import write_new
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p16_registration import registration, GATE, BOUNDARY, ROOT

IDS = tuple("p16d_%02d" % i for i in range(1,9))


def totals(records):
    def charged(key):
        values=[r.get(key) for r in records]
        return sum(values) if all(type(v) is int and v>=0 for v in values) else None
    return {"model_calls":charged("model_calls"),"input_tokens":charged("input_tokens"),
            "output_tokens":charged("output_tokens"),"tool_calls":charged("tool_calls"),
            "verifier_calls":charged("verifier_calls")}


def evaluate(records, references, core_unchanged, complete, whole_ms):
    def verdict(value, reason, **extra):
        return {**BOUNDARY,"verdict":value,"reason":reason,**extra}
    if complete is not True or tuple(r.get("task_id") for r in records)!=IDS:
        return verdict("NOT_EVALUATED","INCOMPLETE_OR_COVERAGE_DRIFT")
    if tuple(r.get("task_id") for r in references)!=IDS or core_unchanged is not True:
        return verdict("NOT_EVALUATED","REFERENCE_OR_CORE_IDENTITY_DRIFT")
    if finite(whole_ms,True)>GATE["whole_study_wall_ms"]:
        return verdict("FAIL","COMPLETE_COST_WALL_CAP")
    if any(finite(r["complete_ms"],True)>GATE["per_item_wall_ms"] for r in records):
        return verdict("FAIL","TASK_WALL_CAP")
    try:
        for r in records:
            validate_receipt(r.get("semantic_receipt",{}))
            finite(r.get("normalization_ms"),True)
            if r.get("accounting_complete") is not True or r.get("semantic_budget_valid") is not True:
                raise ValueError("incomplete semantic accounting")
            if r.get("input_tokens")!=r["semantic_receipt"]["input_tokens"] or r.get("output_tokens")!=r["semantic_receipt"]["output_tokens"]:
                raise ValueError("copied token drift")
            if r.get("model_calls")!=1 or type(r.get("accepted")) is not bool:
                raise ValueError("semantic call/acceptance drift")
    except Exception:
        return verdict("FAIL","SEMANTIC_ACCOUNTING_OR_BUDGET_FAILURE")
    counts={"raw_semantic_accepted":sum(r["accepted"] for r in records),
            "raw_math_accepted":sum(r["accepted"] for r in records[:4]),
            "raw_csp_accepted":sum(r["accepted"] for r in records[4:]),
            "cost_totals":totals(records)}
    okay=all(counts[k]>=GATE[k+"_min"] for k in ("raw_semantic_accepted","raw_math_accepted","raw_csp_accepted"))
    return verdict("PASS" if okay else "FAIL",
                   "OPENED_HYPOTHESIS_DIAGNOSTIC_ONLY" if okay else "SEMANTIC_PATH_CAPABILITY_FAILURE",
                   **counts,next="FREEZE_P15_THEN_REGISTER_NEW_FRESH_SEMANTIC_VALIDATION" if okay else "RETAIN_FIRST_P15_FAILURE_AND_DIAGNOSE")


def run(directory, frozen_head):
    if not re.fullmatch(r"[0-9a-f]{40}",frozen_head): raise ValueError("exact frozen P1.6 source required")
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
    began=perf_counter_ns(); elapsed=lambda:(perf_counter_ns()-began)/1e6
    records=[]; core=None; audit={}; error=None; refs=[]; reg=None
    write_new(directory/"study_started.json",{"schema":contract()["schema"],"frozen_head":frozen_head,"first_only":True,**BOUNDARY})
    try:
        reg,rows,refs=registration()
        write_new(directory/"manifest.json",{"registration":reg,"public_rows":rows,"frozen_head":frozen_head})
        if subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()!=frozen_head:
            raise ValueError("exact frozen P1.6 source commit required")
        subprocess.run(["git","diff","--exit-code","HEAD","--"],cwd=ROOT,check=True,capture_output=True)
        for package,expected in p1_manifest()["runtime"].items():
            if version(package)!=expected: raise ValueError("original runtime mismatch: "+package)
        from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
        core=FrozenAcceleratorCore(); validate_identity(core.identity)
        identity=snapshot(core.identity); write_new(directory/"core.json",identity)
        compiler=FrozenHypothesisCompiler(core)
        for i,(row,ref) in enumerate(zip(rows,refs)):
            write_new(directory/("task_%02d_started.json"%i),{"task_id":row["task_id"],"view_sha256":digest(row["view"])})
            record=interpret_and_execute(row["view"],compiler,_executor,_hidden_verifier(ref))
            record.update(task_id=row["task_id"],kind=ref["kind"]); records.append(record)
            write_new(directory/("task_%02d.json"%i),record)
            print(canonical({k:record.get(k) for k in ("task_id","status","accepted","selected_route","accounting_complete")}),flush=True)
            if elapsed()>GATE["whole_study_wall_ms"]: raise TimeoutError("P1.6 study wall deadline")
        audit=core.audit()
        if core.identity!=identity: audit["unchanged"]=False
    except Exception as exc:
        error={"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
    if core is not None and not audit:
        try: audit=core.audit()
        except Exception as exc: audit={"unchanged":False,"error":str(exc)}
    complete=error is None and len(records)==8; whole=elapsed()
    decision=evaluate(records,refs,audit.get("unchanged"),complete,whole)
    report={"schema":contract()["schema"],"status":"COMPLETE" if complete else "INCOMPLETE",
            "decision":decision,"source_head":frozen_head,"observations":len(records),
            "whole_study_ms":whole,"startup_ms":getattr(core,"startup_ms",None),"core_audit":audit,
            "accounting_complete":complete and all(r["accounting_complete"] for r in records),
            "cost_totals":totals(records),"fallback_calls":0,"frontier_calls":0,"new_training":False,
            "sealed_data_opened":False,"historical_score_reuse":False,**BOUNDARY,"error":error,
            "energy_j":None,"flops":None,"cost_money":None,
            "timing_scope":"study includes source/registration/runtime checks, core startup, all items and final audit; excludes Python imports/bootstrap/setup/final serialization/packaging/replay"}
    write_new(directory/"report.json",report)
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.json"))}
    write_new(directory/"terminal.json",{"files":pins,"complete":complete,"no_replacement":True,
                                         "decision":decision["verdict"],**BOUNDARY})
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--directory",required=True); parser.add_argument("--frozen-head",required=True)
    args=parser.parse_args(); result=run(args.directory,args.frozen_head); print(canonical(result))
    raise SystemExit(0 if result["decision"]["verdict"]=="PASS" else 2)
