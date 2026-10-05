"""Exclusive first P1.10 opened-development runner."""
import argparse, hashlib, re, subprocess, traceback
from importlib.metadata import version
from pathlib import Path
from time import perf_counter_ns
from neumann1.control_plane_v1 import canonical, snapshot
from neumann1.control_plane_p1_contract import manifest as p1_manifest, validate_identity
from neumann1.control_plane_p110 import FrozenMinimalPairwiseSelector
from experiments.control_plane_p1_first import write_new
from experiments.control_plane_p110_registration import registration, GATE, BOUNDARY, ROOT
from experiments.control_plane_p110_runtime import run_item, evaluate, totals

def run(directory,frozen_head):
    if not re.fullmatch(r"[0-9a-f]{40}",frozen_head): raise ValueError("exact frozen P1.10 source required")
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
    began=perf_counter_ns(); elapsed=lambda:(perf_counter_ns()-began)/1e6
    records=[]; refs=[]; error=None; audit={}; core=None; startup_ms=None
    write_new(directory/"study_started.json",{"schema":"neumann.control-plane-p1.10-development.v1","frozen_head":frozen_head,"first_only":True,**BOUNDARY})
    try:
        reg,rows,refs=registration(); write_new(directory/"manifest.json",{"registration":reg,"public_rows":rows,"frozen_head":frozen_head})
        if subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()!=frozen_head: raise ValueError("exact frozen P1.10 source commit required")
        subprocess.run(["git","diff","--exit-code","HEAD","--"],cwd=ROOT,check=True,capture_output=True)
        for package,expected in p1_manifest()["runtime"].items():
            if version(package)!=expected: raise ValueError("original runtime mismatch: "+package)
        start=perf_counter_ns()
        from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
        core=FrozenAcceleratorCore(); validate_identity(core.identity); selector=FrozenMinimalPairwiseSelector(core)
        startup_ms=(perf_counter_ns()-start)/1e6; write_new(directory/"core.json",snapshot(core.identity))
        for i,(row,ref) in enumerate(zip(rows,refs)):
            write_new(directory/("task_%02d_started.json"%i),{"task_id":row["task_id"]})
            rec=run_item(row,ref,selector); records.append(rec); write_new(directory/("task_%02d.json"%i),rec)
            print(canonical({k:rec.get(k) for k in ("task_id","status","accepted","selected_candidate","selection_error","model_calls","neural_forward_calls","accounting_complete")}),flush=True)
            if elapsed()>GATE["whole_study_wall_ms"]: raise TimeoutError("P1.10 study wall deadline")
        audit=core.audit()
    except Exception as exc:
        error={"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
        if core is not None:
            try:audit=core.audit()
            except Exception as e:audit={"unchanged":False,"error":str(e)}
    complete=error is None and len(records)==8; whole=elapsed(); decision=evaluate(records,refs,audit.get("unchanged"),complete,whole)
    report={"schema":"neumann.control-plane-p1.10-development.v1","status":"COMPLETE" if complete else "INCOMPLETE",
            "decision":decision,"source_head":frozen_head,"observations":len(records),"whole_study_ms":whole,
            "selector_startup_ms":startup_ms,"core_audit":audit,
            "accounting_complete":complete and all(r.get("accounting_complete") is True for r in records),
            "cost_totals":totals(records),"fallback_calls":0,"frontier_calls":0,"new_training":False,
            "sealed_data_opened":False,"historical_score_reuse":False,"p19_opened_task_score_reuse":False,
            **BOUNDARY,"error":error,"energy_j":None,"flops":None,"cost_money":None,
            "timing_scope":"whole study includes registration/source/runtime checks, one frozen-core startup, feasibility, P1.10 minimal pairwise scoring, admitted execution, original verification and final audit; excludes bootstrap/setup/final serialization/packaging/replay"}
    write_new(directory/"report.json",report)
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.json"))}
    write_new(directory/"terminal.json",{"files":pins,"complete":complete,"no_replacement":True,"decision":decision["verdict"],**BOUNDARY})
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--directory",required=True); p.add_argument("--frozen-head",required=True)
    a=p.parse_args(); result=run(a.directory,a.frozen_head); print(canonical(result)); raise SystemExit(0 if result["decision"]["verdict"]=="PASS" else 2)
