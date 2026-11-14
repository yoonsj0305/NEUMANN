"""G3 frozen one-index-quantified array invariant hypothesis, all original 8.

This is a classical domain-specific CHC solver hypothesis, never a trained
NEUMANN proposer. One fixed array quantifier per argument; no per-target
tuning. -verifySolutions enables solver-internal witness checking, but this
is still NOT an independent source certificate.
"""
from __future__ import annotations

import argparse,hashlib,json,subprocess,tempfile,time,re
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
CONTRACT=ROOT/"docs/experiments/G3_ONE_SHARED_ARRAY_INDEX_QUANTIFIED_INVARIANT_8_POSTFIRST_2026_11_06.json"
SHA_ORIGINAL="47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8"
SHA_DEFAULT="28b1131382f42fef480223d648ef48d4823a979d63ad3e016996628c9a8d58e0"

def sha(x:bytes):return hashlib.sha256(x).hexdigest()
def blob(x:bytes):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def baseline(original:Path, default:Path)->list:
    a=original.read_bytes();b=default.read_bytes()
    if sha(a)!=SHA_ORIGINAL or sha(b)!=SHA_DEFAULT:
        raise ValueError("G3_ORIGINAL_OR_DEFAULT_POSTFIRST_SHA_CHANGED")
    o=json.loads(a);d=json.loads(b)
    if o["cohort"]!="ARRAY_CHC" or len(o["rows"])!=8 or len(d["rows"])!=8:
        raise ValueError("ORIGINAL_EIGHT_CHANGED")
    for r,s in zip(o["rows"],d["rows"]):
        if r["file"]!=s["original_file"] or s["postfirst_status"]!="NO_NEW_NATIVE_VERDICT_WITHIN_PREDECLARED_LIMIT":
            raise ValueError("NOT_PREVIOUSLY_OPENED_DEFAULT_UNRESOLVED")
    return o["rows"]

def run(eld:Path, original:Path, default:Path):
    rows=baseline(original,default)
    contract=json.loads(CONTRACT.read_text())
    manifest=json.loads(MANIFEST.read_text())
    grp=next(g for g in manifest["cohorts"] if g["id"]=="ARRAY_CHC")
    if len(grp["targets"])!=8 or contract["method"]["per_source_solver_wall_budget_seconds"]!=30:
        raise ValueError("SOURCE_PRECOMMIT_OR_BUDGET_CHANGED")
    out=[]
    for entry,r in zip(grp["targets"],rows):
        if r["file"]!=entry["file"] or entry["git_blob"]!=r["git_blob"]:
            raise ValueError("REGISTERED_SOURCE_FILE_ORDER_CHANGED")
        url="https://raw.githubusercontent.com/"+manifest["upstream"]["repo"]+"/"+manifest["upstream"]["commit"]+"/"+grp["folder"]+"/"+entry["file"]
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-one-shared-array-quantifier"}),timeout=50) as f:
            data=f.read(50000)
        if blob(data)!=entry["git_blob"]:
            raise ValueError("OFFICIAL_G3_2025_SOURCE_CHANGED")
        with tempfile.NamedTemporaryFile("wb",suffix=".smt2") as original_file:
            original_file.write(data);original_file.flush()
            started=time.perf_counter_ns()
            try:
                p=subprocess.run([str(eld),"-arrayQuans:1","-verifySolutions",original_file.name],
                      capture_output=True,text=True,timeout=32)
                wall=round((time.perf_counter_ns()-started)/1e6,3)
                lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
                verdict=lines[-1].lower() if lines else ""
                if p.returncode!=0 or "error" in p.stderr.lower() or "exception" in p.stderr.lower():
                    status="EXPERT_OR_SOURCE_ERROR"
                elif verdict=="sat":status="NATIVE_SAT_CLAIM_VERIFIED_ONLY_IN_SOLVER"
                elif verdict=="unsat":status="NATIVE_UNSAT_CLAIM_VERIFIED_ONLY_IN_SOLVER"
                else:status="NO_GROUNDED_RESULT"
                result={"file":entry["file"],"original_git_blob":entry["git_blob"],
                  "status":status,"process_exit":p.returncode,"wall_ms":wall,
                  "stdout_head":p.stdout[:600],"stderr_tail":p.stderr[-350:],
                  "binary_source_exact":True,"independent_cross_tool_original_certificate":False,
                  "original_source_sha256":sha(data)}
            except subprocess.TimeoutExpired:
                result={"file":entry["file"],"original_git_blob":entry["git_blob"],
                  "status":"TIMEOUT","wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
                  "original_source_sha256":sha(data),
                  "independent_cross_tool_original_certificate":False}
        out.append(result)
    stats={
       "original_count":8,
       "grounded_native_syntax_claims":sum(x["status"].startswith(("NATIVE_SAT","NATIVE_UNSAT")) for x in out),
       "native_timeouts":sum(x["status"]=="TIMEOUT" for x in out),
       "native_infra_errors":sum(x["status"]=="EXPERT_OR_SOURCE_ERROR" for x in out),
       "genuine_independent_original_certificates":0,
       "learned_model_training_or_inference_calls":0,
       "ARC_public_eval_new_IDs":0,
    }
    return {"schema":"neumann.g3.2025-array8-one-index-quantified-postfirst.v1",
      "science_status":"FIXED_REUSABLE_CLASSICAL_QUANTIFIED_ARRAY_INVARIANT_TEST_NOT_NEUMANN_Q3",
      "exact_binary_version":"Eldarica v2.3 SHA pinned at workflow",
      "original_first_sha256":SHA_ORIGINAL,
      "unchanged_default_elderica_first_sha256":SHA_DEFAULT,
      "all_8_registered":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "stats":stats,"rows":out}

if __name__=="__main__":
    try:
        ap=argparse.ArgumentParser()
        ap.add_argument("--eld",type=Path,required=True)
        ap.add_argument("--first",type=Path,required=True)
        ap.add_argument("--default",type=Path,required=True)
        a=ap.parse_args()
        print(json.dumps(run(a.eld,a.first,a.default),indent=2,sort_keys=True))
    except Exception as e:
        print(json.dumps({"science_status":"G3_ONE_QUANTIFIER_INFRA_FAIL_CLOSED",
           "error":type(e).__name__+":"+str(e)[:250]}))
        raise SystemExit(2)
