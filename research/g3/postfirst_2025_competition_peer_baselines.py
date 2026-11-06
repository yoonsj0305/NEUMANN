"""G3 post-FIRST 2025 CHC-COMP real peer specialists, exact 15 Z3-budget failures.

Original source identities and first receipts are immutable. Source is never
rewritten. This is stronger classical benchmarking, NOT neural Q3. Golem
v0.7.1 for LIA, Eldarica v2.2 for array Horn, source-rights identical.
The official competition YAML audit is used ONLY after raw peer outcomes.
Positive verdict requires standalone sat/unsat, process success and explicit
match with published expectation whenever one exists. Others are claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
import sys
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
FIX=ROOT/"docs/experiments/G3_SOURCEFREE_PREOPEN_ONE_GIT_BLOB_ERRATUM_2026_11_06.json"
CON=ROOT/"docs/experiments/G3_POSTFIRST_2025_GOLEM_AND_ELDARICA_PEER_SPECIALISTS_CONTRACT_2026_11_06.json"
FIRST_SHA={
"LIA_MULTIPHASE":"c4529472973dc7e102e3b755ff866ccac5f285a9d7206488d65dd054f5b41535",
"ARRAY_CHC":"47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8"
}
OFFICIAL_SHA="8e05b0a75ad63883daa6bc1fda5d6853c62a08b5b869b9d6c43b1946f55af3df"

def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def gitblob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def check_first(cohort:str,original_first:Path,official_path:Path):
    first_data=original_first.read_bytes()
    official_data=official_path.read_bytes()
    if sha(first_data)!=FIRST_SHA[cohort]:
        raise ValueError("G3_NATIVE_FIRST_IMMUTABLE_SHA_MISMATCH")
    if sha(official_data)!=OFFICIAL_SHA:
        raise ValueError("G3_OFFICIAL_COMPETITION_READONLY_AUDIT_SHA_MISMATCH")
    original=json.loads(first_data)
    labels=json.loads(official_data)
    if original["cohort"]!=cohort or len(original["rows"])!=8:
        raise ValueError("G3_ORIGINAL_DENOMINATOR_OR_COHORT_CHANGED")
    if labels["audit_pass"] is not True or labels["totals"]["original_total"]!=24:
        raise ValueError("G3_INDEPENDENT_OFFICIAL_AUDIT_NOT_PASSED")
    if original["stats"].get("student_training_runs")!=0:
        raise ValueError("G3_NEURAL_ALREADY_TRAINED_IN_FIRST")
    return original,labels

def single_peer(binary:Path,cohort:str,source:bytes,cap_s:float=15.0):
    if not binary.is_file():
        raise ValueError("PINNED_2025_NATIVE_BINARY_NOT_INSTALLED")
    with tempfile.NamedTemporaryFile(suffix=".smt2") as f:
        f.write(source)
        f.flush()
        command=(
            [str(binary),"-l","QF_LIA","--input",f.name]
            if cohort=="LIA_MULTIPHASE" else [str(binary),f.name]
        )
        start=time.perf_counter_ns()
        try:
            out=subprocess.run(command,capture_output=True,text=True,
                timeout=cap_s,check=False)
        except subprocess.TimeoutExpired:
            return {"status":"BUDGET_TIMEOUT",
                    "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
                    "process_command_arguments_version":"Golem-071-LIA" if cohort=="LIA_MULTIPHASE" else "Eldarica-22-Array",
                    "budget_s":cap_s}
    lines=[x.strip() for x in out.stdout.splitlines() if x.strip()]
    answers=[line.lower() for line in lines if line.lower() in ("sat","unsat","unknown")]
    if out.returncode==0 and len(answers)==1 and answers[0] in ("sat","unsat"):
        status="NATIVE_"+answers[0].upper()+"_CLAIM"
    elif out.returncode==0 and answers==["unknown"]:
        status="NATIVE_UNKNOWN"
    else:
        status="UNSUPPORTED_OR_ERROR_OR_NO_EXACT_VERDICT"
    return {"status":status,"wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
      "stdout_sha256":sha(out.stdout.encode()),"exit":out.returncode,
      "stdout_excerpt":out.stdout[:950],"stderr_tail":out.stderr[-550:],
      "stdout_exact_verdict_tokens":answers[:5],"budget_s":cap_s}

def audit_and_run(cohort:str,first:Path,official:Path,binary:Path):
    if cohort not in FIRST_SHA:
        raise ValueError("NOT_A_PREREGISTERED_POSTFIRST_FAILED_COHORT")
    original,labels=check_first(cohort,first,official)
    source_spec=json.loads(PRE.read_text())
    err=json.loads(FIX.read_text())["exact_single_metadata_transcription_error"]
    contract=json.loads(CON.read_text())
    group=next(x for x in source_spec["cohorts"] if x["id"]==cohort)
    peertype="Golem-0.7.1" if cohort=="LIA_MULTIPHASE" else "Eldarica-2.2"
    if contract["source_first"]["run"]!=42174775254:
        raise ValueError("SOURCE_FIRST_RUN_DRIFT")
    if len(group["targets"])!=8 or len(original["rows"])!=8:
        raise ValueError("CHC_COHORT_DENOMINATOR_CHANGED")
    lookup={(e["cohort"],e["file"]):e for e in labels["cases"]}
    rows=[]
    for item,first_row in zip(group["targets"],original["rows"]):
        name=item["file"]
        if first_row["file"]!=name:
            raise ValueError("SOURCE_FIRST_TASK_ORDER_CHANGED")
        z3=next(x for x in first_row["native"] if x["engine"]=="Z3")
        if cohort=="LIA_MULTIPHASE" and z3["status"]=="SAT_CLAIM_UNVERIFIED":
            # The sole previously solved LIA original is an immutable
            # negative control, not one of the seven residual tasks.
            rows.append({"name":name,"original_Z3_status":z3["status"],
                "status":"OLD_NATIVE_ALREADY_SOLVED_NEVER_REEVALUATED",
                "peer_executed":False,"claimed_correct":False})
            continue
        if z3["status"]!="NO_GROUNDED_VERDICT":
            raise ValueError("POSTFIRST_PEER_ORIGINAL_NOT_A_Z3_BUDGET_FAILURE")
        url="https://raw.githubusercontent.com/"+source_spec["upstream"]["repo"]+"/"+source_spec["upstream"]["commit"]+"/"+group["folder"]+"/"+name
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-2025-comp-peer-solver"}),timeout=40) as u:
            source=u.read(60000)
        expect=(err["publisher_verified_40hex"] if group["folder"]==err["folder"] and name==err["file"] else item["git_blob"])
        if gitblob(source)!=expect or gitblob(source)!=first_row["git_blob"] or sha(source)!=first_row["original_source_sha256"]:
            raise ValueError("CHANGED_PUBLISHED_SOURCE_BLOB_OR_BYTE_CONTENT")
        result=single_peer(binary,cohort,source,15)
        official_label=lookup[(cohort,name)]["official_competition"]["expected"]
        candidate="SAT" if result["status"]=="NATIVE_SAT_CLAIM" else "UNSAT" if result["status"]=="NATIVE_UNSAT_CLAIM" else None
        matches=(candidate is not None and candidate==official_label)
        conflicts=(candidate is not None and official_label in ("SAT","UNSAT") and candidate!=official_label)
        rows.append({"name":name,"source_blob":expect,"source_sha256":sha(source),
          "original_Z3_status":z3["status"],"official_2025_expected":official_label,
          "peer_name":peertype,"peer":result,"peer_executed":True,
          "official_competition_verdict_matches":matches,
          "disagrees_with_official_competition":conflicts,
          "claimed_correct":matches,
          "classification":(
             "SOURCE_COMPETITION_CORROBORATED_PEER_VERDICT" if matches else
             "CONTRADICTORY_PEER_RESULT_FAIL_CLOSED" if conflicts else
             "NATIVE_CLAIM_UNCONFIRMED_NO_PUBLISHED_GOLD" if candidate else
             "NATIVE_BUDGET_OR_UNKNOWN_NOT_UNSOLVABLE"
           )})
    stats={
       "source_denominator":8,
       "previously_Z3_budget_unresolved":7 if cohort=="LIA_MULTIPHASE" else 8,
       "peer_originals_executed":sum(x["peer_executed"] for x in rows),
       "peer_sat_unsat_raw":sum(x.get("peer",{}).get("status") in ("NATIVE_SAT_CLAIM","NATIVE_UNSAT_CLAIM") for x in rows),
       "peer_verdict_agrees_with_official_competition":sum(x["claimed_correct"] for x in rows),
       "peer_verdict_conflicts_with_official_competition":sum(x.get("disagrees_with_official_competition",False) for x in rows),
       "peer_native_remaining_no_verdict":sum(x["peer_executed"] and
           x.get("peer",{}).get("status") not in ("NATIVE_SAT_CLAIM","NATIVE_UNSAT_CLAIM") for x in rows),
       "originals_without_published_label":sum(x["peer_executed"] and x["official_2025_expected"] not in ("SAT","UNSAT") for x in rows),
       "student_neural_training_invocations":0,
       "new_ARC_eval_originals":0
    }
    return {
      "schema":"neumann.q3.g3.postfirst-reproduction-native-CHCCOMP2025-actual-peers.v1",
      "cohort":cohort,"peer_version":peertype,
      "science_status":"POSTFIRST_KNOWN_NATIVE_COMPARISON_NEUMANN_LEARNED_Q3_OPEN",
      "first_z3_original_sha256":FIRST_SHA[cohort],
      "first_official_competition_audit_sha256":OFFICIAL_SHA,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "stats":stats,"rows":rows
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--cohort",required=True,choices=list(FIRST_SHA))
    p.add_argument("--first",required=True,type=Path)
    p.add_argument("--official",required=True,type=Path)
    p.add_argument("--binary",required=True,type=Path)
    a=p.parse_args()
    try:
        print(json.dumps(audit_and_run(a.cohort,a.first,a.official,a.binary),
                         indent=2,sort_keys=True))
    except Exception as e:
        print(json.dumps({"science_status":"POSTFIRST_NATIVE_INFRA_FAIL_NOT_NEUMANN_Q3",
          "error":type(e).__name__+":"+str(e)[:250]}))
        raise SystemExit(2)
