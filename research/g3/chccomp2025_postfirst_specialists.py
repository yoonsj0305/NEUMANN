"""G3 second native specialists, AFTER untouched Z3-original FIRST freeze.

Exact cohorts: eight 2025 CHC-COMP arrays previously UNLABELED by competition,
seven integer multi-phase sources Z3 failed to decide in original 15s budget.
Syntactic semantics and SAT/UNSAT must be validated by source-free controls
before original source reruns; binaries are SHA256 release-pinned by CI.
NOT NEUMANN weights and NOT Q3 learned invention.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
ERRATUM=ROOT/"docs/experiments/G3_SOURCEFREE_PREOPEN_ONE_GIT_BLOB_ERRATUM_2026_11_06.json"
CONTRACT=ROOT/"docs/experiments/G3_POSTFIRST_STRONG_2025_CHC_2_NEW_NATIVE_SPECIALISTS_CONTRACT_2026_11_06.json"
SHA_FIRST={
    "LIA_MULTIPHASE":"c4529472973dc7e102e3b755ff866ccac5f285a9d7206488d65dd054f5b41535",
    "ARRAY_CHC":"47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8",
}
def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def blob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def run_expert(name:str,exe:Path,original:bytes,cap:int=20):
    cmd=([str(exe),"-l","QF_LIA"] if name=="Golem" else [str(exe)])
    with tempfile.NamedTemporaryFile("wb",suffix=".smt2") as f:
        f.write(original);f.flush()
        started=time.perf_counter_ns()
        try:
            p=subprocess.run(cmd+[f.name],capture_output=True,text=True,
                    timeout=cap+2,check=False)
        except subprocess.TimeoutExpired:
            return {"engine":name,"status":"TIMEOUT",
                "wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
                "budget_s":cap}
    elapsed=round((time.perf_counter_ns()-started)/1e6,3)
    stdout=p.stdout.strip()
    lines=[x.strip().lower() for x in stdout.splitlines() if x.strip()]
    ground=[x for x in lines if x in ("sat","unsat")]
    if p.returncode!=0 or "exception" in p.stderr.lower() or "error" in p.stderr.lower():
        status="SOURCE_OR_RUNTIME_ERROR"
    elif len(ground)!=1 or any(x not in ("sat","unsat") for x in lines[:1]):
        status=("UNKNOWN_OR_NO_GROUNDED_CLAIM" if "unknown" in stdout.lower()
          else "NOT_GROUNDED")
    else:
        status=("SAT_CLAIM_ONLY_NOT_INDEPENDENTLY_PROVED" if ground[0]=="sat"
          else "UNSAT_CLAIM_ONLY_NOT_INDEPENDENTLY_PROVED")
    return {"engine":name,"status":status,
       "wall_ms":elapsed,"process_exit":p.returncode,"budget_s":cap,
       "stdout_sha256":sha(p.stdout.encode()),
       "stdout_head":p.stdout[:900],"stderr_tail":p.stderr[-450:]}

def register_first(paths:dict[str,Path]):
    first={}
    for cohort,file in paths.items():
        data=file.read_bytes()
        if sha(data)!=SHA_FIRST[cohort]:
            raise ValueError("G3_FIRST_SOURCE_RECEIPT_IMMUTABLE_SHA_DRIFT")
        x=json.loads(data)
        if x.get("cohort")!=cohort or len(x.get("rows",[]))!=8:
            raise ValueError("G3_FIRST_EIGHT_CHANGED")
        first[cohort]=x["rows"]
    if sum(r["status"]=="NO_NATIVE_GROUNDED_VERDICT_WITHIN_BUDGET"
           for r in first["LIA_MULTIPHASE"])!=7:
        raise ValueError("G3_FIRST_LIA_EXACT_SEVEN_NOT_PRESERVED")
    if sum(r["status"]=="NO_NATIVE_GROUNDED_VERDICT_WITHIN_BUDGET"
           for r in first["ARRAY_CHC"])!=8:
        raise ValueError("G3_FIRST_ARRAY_EIGHT_NOT_PRESERVED")
    return first

def original_source(folder:str,file:str,sha_git:str,commit:str):
    url="https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/"+commit+"/"+folder+"/"+file
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-postfirst-new-natives"}),timeout=50) as r:
        raw=r.read(50000)
    if blob(raw)!=sha_git:raise ValueError("CHC_ORIGINAL_PUBLISHER_BLOB_CHANGED_"+file)
    return raw

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cohort",required=True,choices=["ARRAY_CHC","LIA_MULTIPHASE"])
    ap.add_argument("--eld",type=Path,required=True)
    ap.add_argument("--golem",type=Path)
    ap.add_argument("--first-array",type=Path,required=True)
    ap.add_argument("--first-lia",type=Path,required=True)
    args=ap.parse_args()
    first=register_first({"ARRAY_CHC":args.first_array,"LIA_MULTIPHASE":args.first_lia})
    doc=json.loads(MANIFEST.read_text())
    spec=json.loads(CONTRACT.read_text())
    err=json.loads(ERRATUM.read_text())["exact_single_metadata_transcription_error"]
    if spec["postfirst_scope"]["original_repo"]!="chc-comp/chc-comp25-benchmarks":
        raise ValueError("WRONG_OFFICIAL_PRECOMMIT")
    coh=next(c for c in doc["cohorts"] if c["id"]==args.cohort)
    firstrows=first[args.cohort]
    if not all(e["file"]==r["file"] for e,r in zip(coh["targets"],firstrows)):
        raise ValueError("FIRST_ORIGINAL_TASK_IDS_ORDER_CHANGED")
    entries=[
      (entry,first_result) for entry,first_result in zip(coh["targets"],firstrows)
      if first_result["status"]=="NO_NATIVE_GROUNDED_VERDICT_WITHIN_BUDGET"]
    if len(entries)!=(8 if args.cohort=="ARRAY_CHC" else 7):
        raise ValueError("POSTFIRST_REGISTERED_ORIGINAL_DENOMINATOR_CHANGED")
    if args.cohort=="LIA_MULTIPHASE" and args.golem is None:
        raise ValueError("G3_GOLEM_0_9_REQUIRED_FOR_PRECOMMITTED_LIA")
    rows=[]
    for t,fr in entries:
        expected=t["git_blob"]
        if (coh["folder"],t["file"])==(err["folder"],err["file"]):
            if expected!=err["original_38hex"]:
                raise ValueError("UNAUTHORIZED_G3_ERRATUM")
            expected=err["publisher_verified_40hex"]
        raw=original_source(coh["folder"],t["file"],expected,doc["upstream"]["commit"])
        row={"cohort":args.cohort,"original_file":t["file"],
             "original_git_blob":expected,
             "original_sha256":sha(raw),
             "first_Z3_status":fr["native"][0]["status"],
             "original_first_receipt_SHA256":SHA_FIRST[args.cohort],
             "natives":[]}
        row["natives"].append(run_expert("Eldarica",args.eld,raw,20))
        if args.cohort=="LIA_MULTIPHASE":
            row["natives"].append(run_expert("Golem",args.golem,raw,20))
        grounded=[n for n in row["natives"]
                  if n["status"] in ("SAT_CLAIM_ONLY_NOT_INDEPENDENTLY_PROVED",
                                     "UNSAT_CLAIM_ONLY_NOT_INDEPENDENTLY_PROVED")]
        row["postfirst_status"]=(
          "TWO_NATIVE_CLAIMS_DISAGREE_NEEDS_ARBITRATION"
             if len(grounded)==2 and grounded[0]["status"]!=grounded[1]["status"]
          else "NEW_NATIVE_CLAIM_UNCERTIFIED" if grounded
          else "NO_NEW_NATIVE_VERDICT_WITHIN_PREDECLARED_LIMIT")
        row["not_an_autonomous_NEUMANN_learned_discovery"]=True
        rows.append(row)
    result={
      "schema":"neumann.g3.2025-CHC-postfirst-two-specialist-original.v1",
      "postfirst_original_scope":args.cohort,
      "science_status":"STRONGER_NATIVE_CLASSICAL_ORIGINAL_COMPLETED_NOT_Q3",
      "original_Z3_FIRST_SHA256":SHA_FIRST[args.cohort],
      "postfirst_original_denominator":len(entries),
      "extra_training_and_neural_model_calls":0,
      "not_a_blind_original_benchmark":True,
      "stats":{
         "originals_checked":len(rows),
         "Eldarica_gave_grounded_claim":sum(any(n["engine"]=="Eldarica" and n["status"].startswith(("SAT_CLAIM","UNSAT_CLAIM")) for n in r["natives"]) for r in rows),
         "Golem_gave_grounded_claim":sum(any(n["engine"]=="Golem" and n["status"].startswith(("SAT_CLAIM","UNSAT_CLAIM")) for n in r["natives"]) for r in rows),
         "no_new_native_claims":sum(r["postfirst_status"]=="NO_NEW_NATIVE_VERDICT_WITHIN_PREDECLARED_LIMIT" for r in rows),
         "originals_unproved_by_any_algorithm":0,
         "ARC_public_eval_new_IDs":0},
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "rows":rows
    }
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":
    try:main()
    except Exception as e:
        print(json.dumps({"science_status":"POSTFIRST_EXPERT_INFRASTRUCTURE_FAIL_CLOSED",
          "error":type(e).__name__+":"+str(e)[:300]}))
        raise SystemExit(2)
