"""G3 independent READ-ONLY 2025 competition official-verdict corroboration.

Accept ONLY the exact three SHA-locked FIRST run JSON receipts.
Fetch the 24 source Git blobs at pinned CHC-COMP 2025 commit again, along
with official Benchexec YAML metadata selected by the ORIGINAL source stem.
Verify input_files matches the exact source, and independent published
expected_verdict true=>sat, false=>unsat.
No native solver rerun, no model training, no original task swap.
UNKNOWN or 15-second Z3 failure is NOT a classical impossibility result.
"""
from __future__ import annotations

import argparse,hashlib,json,re,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
ERR=ROOT/"docs/experiments/G3_SOURCEFREE_PREOPEN_ONE_GIT_BLOB_ERRATUM_2026_11_06.json"
CON=ROOT/"docs/experiments/G3_OFFICIAL_2025_VERDICT_READONLY_AUDIT_PREREG_2026_11_06.json"
FIRST_SHA={
"LIA_MULTIPHASE":"c4529472973dc7e102e3b755ff866ccac5f285a9d7206488d65dd054f5b41535",
"ARRAY_CHC":"47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8",
"ADT_CHC":"84e35263eb08153776ccb1fb6ae97a1a76b82b8ca8959fd8b6502987474c6376",
}

def sha(x:bytes)->str:
    return hashlib.sha256(x).hexdigest()

def gitblob(x:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def name_of_official_yml(folder:str,file:str)->str:
    stem=file[:-len(".smt2")]
    if folder=="aeval-benchmarks/multi-phase":
        return stem+"_000.yml"
    return stem+".yml"

def fetch(repo:str,commit:str,path:str):
    u="https://raw.githubusercontent.com/"+repo+"/"+commit+"/"+path
    with urlopen(Request(u,headers={"User-Agent":"NEUMANN-G3-independent-official-YAML-audit"}),timeout=45) as r:
        return r.read(80000)

def read_official_yml(data:bytes,expected_file:str):
    t=data.decode("utf-8")
    if not re.search(r"(?m)^format_version:\s*['\"]?2\.0['\"]?\s*$",t):
        raise ValueError("INVALID_OFFICIAL_COMP_METADATA_VERSION")
    inputs=re.findall(r"(?m)^input_files:\s*(\S+)\s*$",t)
    if inputs!=[expected_file]:
        raise ValueError("OFFICIAL_METADATA_INPUT_FILENAME_MISMATCH")
    v=re.findall(r"(?m)^\s*-\s*expected_verdict:\s*(\w+)\s*$",t)
    if len(v)>1:
        raise ValueError("CONTRADICTORY_OFFICIAL_METADATA")
    if not v:
        return {"expected":"NOT_PUBLISHED","expected_sat":None}
    if v==["true"]:
        return {"expected":"SAT","expected_sat":True}
    if v==["false"]:
        return {"expected":"UNSAT","expected_sat":False}
    return {"expected":"AMBIGUOUS_OR_INCONSISTENT","expected_sat":None,"raw":v[0]}

def audit(paths:dict[str,Path])->dict:
    reg=json.loads(PRE.read_text())
    fix=json.loads(ERR.read_text())["exact_single_metadata_transcription_error"]
    con=json.loads(CON.read_text())
    if len(paths)!=3 or con["first_engine_job_run"]!=42174775254:
        raise ValueError("MISSING_FROZEN_SOURCE_FIRST")
    first={}
    for key,path in paths.items():
        raw=path.read_bytes()
        if sha(raw)!=FIRST_SHA[key]:
            raise ValueError("IMMUTABLE_ORIGINAL_FIRST_SHA_CHANGED_"+key)
        obj=json.loads(raw)
        if obj.get("cohort")!=key or obj.get("first_original_denominator")!=8 or len(obj.get("rows",[]))!=8:
            raise ValueError("ORIGINAL_FIRST_COHORT_DENOMINATOR_DRIFT")
        if obj["stats"].get("student_training_runs")!=0:
            raise ValueError("ORIGINAL_FIRST_NEURAL_RUN_FALSIFIED")
        if obj.get("science_status")!="NATIVE_RAW_CLAIM_FIRST_NEEDS_OFFICIAL_VERDICT_AND_ORIGINAL_SOURCE_AUDIT":
            raise ValueError("ORIGINAL_FIRST_SCOPE_PROMOTED")
        first[key]=obj
    out=[]
    errors=[]
    for cohort in reg["cohorts"]:
        key=cohort["id"]
        items=cohort["targets"]
        assert len(items)==8
        for i,t in enumerate(items):
            row=first[key]["rows"][i]
            if t["file"]!=row["file"]:
                errors.append("FROZEN_TASK_ORDER_DRIFT_"+key)
                continue
            blob_expect=(fix["publisher_verified_40hex"] if
                  cohort["folder"]==fix["folder"] and t["file"]==fix["file"] else t["git_blob"])
            source_path=cohort["folder"]+"/"+t["file"]
            src=fetch(reg["upstream"]["repo"],reg["upstream"]["commit"],source_path)
            if gitblob(src)!=blob_expect or gitblob(src)!=row.get("git_blob") or sha(src)!=row.get("original_source_sha256"):
                errors.append("FROZEN_SOURCE_GIT_BLOB_OR_BYTES_MISMATCH_"+key+"_"+t["file"])
                continue
            label_path=cohort["folder"]+"/"+name_of_official_yml(cohort["folder"],t["file"])
            try:
                yml=fetch(reg["upstream"]["repo"],reg["upstream"]["commit"],label_path)
                official=read_official_yml(yml,t["file"])
                official["metadata_sha256"]=sha(yml)
            except (URLError,HTTPError) as ex:
                official={"expected":"OFFICIAL_METADATA_UNAVAILABLE","expected_sat":None,
                    "error":str(ex)[:110]}
            except (UnicodeError,ValueError) as ex:
                errors.append("OFFICIAL_ORIGINAL_METADATA_INVALID_"+key+"_"+t["file"]+":"+str(ex))
                continue
            native=row.get("native",[])
            if len(native)!=2 or {x["engine"] for x in native}!={"Z3","CVC5"}:
                errors.append("ORIGINAL_NATIVE_ENGINE_RIGHTS_CHANGED_"+key+"_"+t["file"])
                continue
            measured={x["engine"]:x for x in native}
            z3=measured["Z3"]["status"]
            cv=measured["CVC5"]["status"]
            claim="SAT" if z3=="SAT_CLAIM_UNVERIFIED" else "UNSAT" if z3=="UNSAT_CLAIM_UNVERIFIED" else None
            corroborated=(claim is not None and claim==official["expected"])
            disagreement=(claim is not None and official["expected"] in ("SAT","UNSAT")
                          and claim!=official["expected"])
            if disagreement:
                errors.append("ORIGINAL_NATIVE_CONTRADICTS_OFFICIAL_VERDICT_"+key+"_"+t["file"])
            if z3=="NO_GROUNDED_VERDICT" and measured["Z3"].get("wall_ms",0)>14000:
                z3_limited="Z3_15S_BUDGET_NO_VERDICT"
            elif z3 in ("SAT_CLAIM_UNVERIFIED","UNSAT_CLAIM_UNVERIFIED"):
                z3_limited="Z3_NATIVE_VERDICT_CLAIM"
            else:
                z3_limited="Z3_OTHER_NOT_A_PROVEN_RESIDUAL"
            out.append({
             "cohort":key,"file":t["file"],
             "first_source_git_blob":row["git_blob"],
             "frozen_first_native_sha256":FIRST_SHA[key],
             "official_competition":official,
             "first_Z3_native_status":z3,
             "first_Z3_wall_ms":measured["Z3"].get("wall_ms"),
             "first_CVC5_native_status":cv,
             "Z3_native_claim_matches_competition_metadata":corroborated,
             "Z3_native_disagrees_with_published_metadata":disagreement,
             "Z3_budget_status":z3_limited,
             "original_source_provenance_verified":True,
             "native_synthesis_rerun":False
            })
    if len(out)!=24:errors.append("INCOMPLETE_24_SOURCE_AUDIT")
    totals={
      "original_cohorts":3,
      "original_total":len(out),
      "published_expected_SAT":sum(x["official_competition"]["expected"]=="SAT" for x in out),
      "published_expected_UNSAT":sum(x["official_competition"]["expected"]=="UNSAT" for x in out),
      "published_no_solved_verdict":sum(x["official_competition"]["expected"] not in ("SAT","UNSAT") for x in out),
      "first_Z3_results_corrob_by_competition":sum(x["Z3_native_claim_matches_competition_metadata"] for x in out),
      "first_Z3_15s_budget_no_verdict":sum(x["Z3_budget_status"]=="Z3_15S_BUDGET_NO_VERDICT" for x in out),
      "first_Z3_wrong_competition_claims":sum(x["Z3_native_disagrees_with_published_metadata"] for x in out),
      "first_CVC5_unknown":sum(x["first_CVC5_native_status"]=="UNKNOWN" for x in out),
      "first_source_authoritative_blobs_rechecked":sum(x["original_source_provenance_verified"] for x in out),
      "neumann_training_calls":0,
      "new_arc_eval_ids":0
    }
    return {"schema":"neumann.q3.g3.2025-official-competition-metadata-original-first-readonly.v1",
      "audit_pass":not errors,
      "errors":errors,
      "first_exact_receipt_shas":FIRST_SHA,
      "science_status":"PROVEN_NATIVE_VERDICTS_NOT_NEUMANN_LEARNED_ADVANTAGE",
      "competition_metadata_expected_verdict_is_not_universal_proof":True,
      "native_both_fail_not_classical_unsolvability":True,
      "neumann_original_solution_claim":"NONE",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "totals":totals,"cases":out}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for k in FIRST_SHA:
        parser.add_argument("--"+k.lower(),required=True,type=Path)
    x=parser.parse_args()
    files={k:getattr(x,k.lower()) for k in FIRST_SHA}
    try:
        result=audit(files)
        print(json.dumps(result,indent=2,sort_keys=True))
        if not result["audit_pass"]:raise SystemExit(1)
    except Exception as err:
        print("G3_OFFICIAL_SOURCE_READONLY_FAIL_CLOSED",type(err).__name__,str(err),file=sys.stderr)
        raise SystemExit(2)
