"""First CPU typed-contract diagnostic; no neural/capability gate is opened."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from time import perf_counter_ns
import traceback
import zipfile

from neumann1.control_plane_v1 import canonical, digest, finite
from neumann1.control_plane_p13 import contract, route
from neumann1.control_plane_p12_validation import opened_development_rows, structural_key

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "docs/experiments/control_plane_p13.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p13_public.json"
REFERENCES = ROOT / "docs/experiments/control_plane_p13_references.json"
IDS = tuple("p13v_%02d" % i for i in range(1,25))
GATE = {"exact_contract_matches": 24, "single_typed_neural_forwards": 0,
        "all_diagnostic_neural_forwards": 0, "per_item_wall_ms": 500.0, "whole_study_wall_ms": 30000.0,
        "scope": "authored typed contract and stopped-state diagnostic only; semantic fallback not run"}


def write_new(path, value):
    with path.open("xb") as f: f.write((canonical(value)+"\n").encode())


def registration():
    reg = json.loads(REGISTRATION.read_bytes())
    if reg["architecture"] != contract() or reg["gate"] != GATE or reg["task_ids"] != list(IDS):
        raise ValueError("P1.3 frozen contract/gate drift")
    for name, expected in reg["source_sha256"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError("registered source drift: "+name)
    rows = json.loads(PUBLIC.read_bytes())["rows"]
    refs = json.loads(REFERENCES.read_bytes())["rows"]
    if tuple(r["task_id"] for r in rows) != IDS or tuple(r["task_id"] for r in refs) != IDS:
        raise ValueError("exact fresh ordered coverage required")
    if any(set(r) != {"task_id","view"} for r in rows): raise ValueError("metadata outside public view required")
    if digest(rows) != reg["public_sha256"] or digest(refs) != reg["references_sha256"]:
        raise ValueError("frozen dataset drift")
    return reg, rows


def check_construction():
    """Only authored reference/checker and dedup controls, not routing scores."""
    from neumann1.general_runtime_v106 import _rational, verify_original
    reg, rows = registration(); refs = json.loads(REFERENCES.read_bytes())["rows"]
    old = opened_development_rows()+json.loads((ROOT/"docs/experiments/control_plane_p12_validation_public.json").read_bytes())["rows"]
    keys = [structural_key(r["view"]) for r in rows[:12]]
    if len(set(keys)) != 12 or set(keys)&{structural_key(r["view"]) for r in old}:
        raise ValueError("fresh positive structural duplicate")
    for row,ref in zip(rows[:12], refs[:12]):
        task = {"family":ref["family"], **row["view"]}
        if not verify_original(task,ref["witness"],ref["private"],2000): raise ValueError("construction witness rejected")
        if ref["family"] == "math_logic":
            if _rational(task["public"]["expression"],task["public"]["bindings"]) != ref["private"]["exact"]:
                raise ValueError("literal arithmetic reference disagreement")
            bad = "987654321"
        elif ref["family"] == "coding": bad = "def solve(items):\n    return None\n"
        else: bad = {k:987654321 for k in task["public"]["domains"]}
        if verify_original(task,bad,ref["private"],2000): raise ValueError("checker negative control accepted")
    return {"registration_valid":True, "new_rows":24, "compared_prior_rows":len(old),
            "positive_construction_controls":12, "negative_checker_controls":12,
            "scope":"finite coding tests, arithmetic references and original complete CSP checker; no candidate solutions",
            "routing_diagnostic_run":False,"model_inference":False}


def decision(records, references, complete, wall_ms):
    boundary = {"p2_registration_admitted":False,"p2_admitted":False,"decision3_admitted":False,
                "global_questions_closed":[],"semantic_fallback_validated":False,"answer_capability_validated":False}
    reason = "FRESH_TYPED_CONTRACT_DIAGNOSTIC_ONLY"; verdict = "PASS"
    if complete is not True or tuple(r.get("task_id") for r in records) != IDS or tuple(r.get("task_id") for r in references) != IDS:
        verdict,reason = "NOT_EVALUATED","INCOMPLETE_OR_COVERAGE_DRIFT"
    elif finite(wall_ms,True) > GATE["whole_study_wall_ms"]:
        verdict,reason = "FAIL","COMPLETE_COST_WALL_CAP"
    else:
        for r,ref in zip(records,references):
            if r["status"] != ref["status"] or r["selected_route"] != ref["selected_route"] or r["admissible_routes"] != ref["admissible_routes"]:
                verdict,reason = "FAIL","PUBLIC_CONTRACT_MISMATCH"; break
            if any(type(r[k]) is not int or r[k] != 0 for k in ("neural_forward_calls","fallback_calls","generated_calls","tool_calls")):
                verdict,reason = "FAIL","UNNECESSARY_NEURAL_OR_EXECUTOR_WORK"; break
            if r["accounting_complete"] is not True or finite(r["complete_ms"],True) > GATE["per_item_wall_ms"]:
                verdict,reason = "FAIL","INCOMPLETE_OR_TASK_WALL_CAP"; break
    return {**boundary,"verdict":verdict,"reason":reason}


def run(directory, frozen_head):
    if not re.fullmatch(r"[0-9a-f]{40}",frozen_head): raise ValueError("exact frozen source head required")
    if os.environ.get("GITHUB_RUN_ATTEMPT","1") != "1": raise ValueError("replacement CI attempts forbidden")
    directory = Path(directory); directory.mkdir(parents=True,exist_ok=False)
    began=perf_counter_ns(); elapsed=lambda:(perf_counter_ns()-began)/1e6
    records=[]; error=None; git_verified=False; reg=None; rows=[]
    write_new(directory/"started.json",{"schema":contract()["schema"],"frozen_head":frozen_head,"first_only":True})
    try:
        reg,rows=registration()
        if subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()!=frozen_head:
            raise ValueError("frozen Git source mismatch")
        subprocess.run(["git","diff","--exit-code","HEAD","--"],cwd=ROOT,check=True,capture_output=True)
        git_verified=True
        write_new(directory/"manifest.json",{"registration":reg,"public_rows":rows,"frozen_head":frozen_head})
        for i,row in enumerate(rows):
            write_new(directory/("task_%02d_started.json"%i),{"task_id":row["task_id"],"view_sha256":digest(row["view"])})
            record=route(row["view"]); record["task_id"]=row["task_id"]; records.append(record)
            write_new(directory/("task_%02d.json"%i),record)
            if elapsed()>GATE["whole_study_wall_ms"]: raise TimeoutError("complete CPU diagnostic deadline")
    except Exception as exc:
        error={"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
    refs=json.loads(REFERENCES.read_bytes())["rows"] if error is None else []
    wall=elapsed(); complete=error is None and len(records)==24
    d=decision(records,refs,complete,wall)
    report={"schema":contract()["schema"],"status":"COMPLETE" if complete else "INCOMPLETE","decision":d,
            "source_head":frozen_head,"git_commit_verified":git_verified,"observations":len(records),
            "whole_study_ms":wall,"route_wall_sum_ms":sum(r["complete_ms"] for r in records),
            "neural_forward_calls":sum(r["neural_forward_calls"] for r in records),"fallback_calls":0,
            "generated_calls":0,"tool_calls":0,"frontier_calls":0,"weights_loaded":False,
            "new_training":False,"sealed_data_opened":False,"fresh_opened":True,
            "accounting_complete":complete,"error":error,"energy_j":None,"flops":None,"cost_money":None,
            "cost_scope":"routing plus input/source checks and receipts; no solving or model startup"}
    write_new(directory/"report.json",report)
    write_new(directory/"terminal.json",{"files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.json"))},
              "complete":complete,"no_replacement":True,"decision":d["verdict"]})
    return report


def replay(directory):
    directory=Path(directory); reg,rows=registration()
    terminal=json.loads((directory/"terminal.json").read_bytes())
    names={p.name for p in directory.glob("*.json") if p.name!="terminal.json"}
    if names!=set(terminal["files"]) or any(hashlib.sha256((directory/n).read_bytes()).hexdigest()!=s for n,s in terminal["files"].items()):
        raise ValueError("receipt/member pin mismatch")
    report=json.loads((directory/"report.json").read_bytes())
    complete=report["status"]=="COMPLETE"
    records=[]
    for i,row in enumerate(rows):
        p=directory/("task_%02d.json"%i)
        if not p.exists():
            if complete: raise ValueError("complete diagnostic missing row")
            continue
        r=json.loads(p.read_bytes()); expected=route(row["view"])
        if r["task_id"]!=row["task_id"]: raise ValueError("task coverage mismatch")
        for key in expected:
            if key!="complete_ms" and r.get(key)!=expected[key]: raise ValueError("public type replay mismatch: "+key)
        records.append(r)
    refs=json.loads(REFERENCES.read_bytes())["rows"]
    d=decision(records,refs,complete,report["whole_study_ms"])
    if d!=report["decision"] or terminal["decision"]!=d["verdict"] or terminal["complete"]!=complete or terminal["no_replacement"] is not True:
        raise ValueError("decision/terminal drift")
    if complete:
        m=json.loads((directory/"manifest.json").read_bytes())
        if m["registration"]!=reg or m["public_rows"]!=rows or m["frozen_head"]!=report["source_head"]:
            raise ValueError("source/public manifest drift")
        if report["git_commit_verified"] is not True or report["observations"]!=24 or report["accounting_complete"] is not True:
            raise ValueError("source/accounting incomplete")
        if report["error"] is not None or terminal["complete"] is not True: raise ValueError("complete diagnostic error")
    if not re.fullmatch(r"[0-9a-f]{40}",report["source_head"]): raise ValueError("source head drift")
    for key in ("neural_forward_calls","fallback_calls","generated_calls","tool_calls","frontier_calls"):
        if report[key]!=0: raise ValueError("diagnostic work counter drift")
    for key in ("weights_loaded","new_training","sealed_data_opened"):
        if report[key] is not False: raise ValueError("forbidden study work")
    if abs(report["route_wall_sum_ms"]-sum(r["complete_ms"] for r in records))>1e-9:
        raise ValueError("complete measured route cost drift")
    return {"integrity_valid":True,"model_inference":False,"decision":d,"complete":complete}


def package(directory):
    directory=Path(directory); stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(directory.glob("*.json")): z.write(p,directory.name+"/"+p.name)
        for name in json.loads(REGISTRATION.read_bytes())["source_sha256"]:
            z.write(ROOT/name,"source/"+name)
        z.write(REGISTRATION,"source/"+str(REGISTRATION.relative_to(ROOT)))
    data=stream.getvalue()
    return data,{"archive":"NEUMANN_P13_FIRST_CONTRACT_EVIDENCE.zip","archive_bytes":len(data),"archive_sha256":hashlib.sha256(data).hexdigest()}


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--check-registration",action="store_true")
    parser.add_argument("--directory"); parser.add_argument("--frozen-head"); parser.add_argument("--archive-stdout",action="store_true"); args=parser.parse_args()
    if args.check_registration: print(canonical(check_construction()))
    else:
        if not args.directory or not args.frozen_head: parser.error("first run requires directory/frozen-head")
        report=run(args.directory,args.frozen_head); print("P13_REPORT "+canonical(report))
        try: print("P13_REPLAY "+canonical(replay(args.directory)))
        finally:
            data,identity=package(args.directory)
            with (Path(args.directory).parent/identity["archive"]).open("xb") as f: f.write(data)
            print("P13_ARCHIVE "+canonical(identity))
            if args.archive_stdout: print("P13_ARCHIVE_BASE64 "+base64.b64encode(data).decode())
        raise SystemExit(0 if report["decision"]["verdict"]=="PASS" else 2)
