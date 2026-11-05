"""NEUMANN P2.8 original ARC transfer48 independent read-only execution audit.

Original 48-task data and report remain immutable. No neural model; no test
answers consumed here. Freshly implement the entire 81-choice factorization
language in Python to independently establish P2.8 representability ceiling.
The prior five baseline engines are NOT independently reimplemented; their
reported Boolean scores are hash-locked and aggregate-counter checked.
"""
from __future__ import annotations
from hashlib import sha1,sha256
from itertools import product
from pathlib import Path
import json
import math
import sys

FIRST_SHA256="1b708e7ccb3686637ee8a8cefcbdba1e03b1aa4abfaebe48d3eba8e51f84bd78"
UPSTREAM="399030444e0ab0cc8b4e199870fb20b863846f34"
def sha_blob(path):
    b=Path(path).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def grid(g):
    return (type(g) is list and 1<=len(g)<=30 and
      type(g[0]) is list and 1<=len(g[0])<=30 and
      all(type(row) is list and len(row)==len(g[0]) and
      all(type(x) is int and 0<=x<=9 for x in row) for row in g))
def eligible_input(x):
    return grid(x) and len(x)**2<=30 and len(x[0])**2<=30
def apply(sel,x):
    if not eligible_input(x):return None
    h,w=len(x),len(x[0])
    y=[]
    for row in range(h*h):
        line=[]
        for col in range(w*w):
            a=x[row//h][col//w]
            b=x[row%h][col%w]
            idx=(2 if a==0 else 0)+(1 if b==0 else 0)
            choice=sel[idx]
            line.append(0 if choice==0 else a if choice==1 else b)
        y.append(line)
    return y
def independent_first(root,arc_root,report):
    root=Path(root);arc_root=Path(arc_root)
    b=Path(report).read_bytes()
    rec=json.loads(b)
    errors=[]
    def check(x,reason):
        if not x: errors.append(reason)
    check(sha256(b).hexdigest()==FIRST_SHA256,"FIRST_RECEIPT_BYTES_DRIFT")
    lock=json.loads((root/"docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_SOURCE_LOCK.json").read_text())
    cohort_path=root/"docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_COHORT_FROZEN.json"
    cohort=json.loads(cohort_path.read_text())
    check(sha_blob(cohort_path)==lock["cohort_blob"],"COHORT_SOURCE_BLOB_DRIFT")
    for name,hash_ in lock["source_blobs"].items():
        check(sha_blob(root/name)==hash_,"SOURCE_BLOB_DRIFT:"+name)
    previous=set()
    for m in cohort["historic_previous_manifests"]:
        p=root/m["path"]
        check(sha_blob(p)==m["blob"],"HISTORICAL_MANIFEST_DRIFT:"+m["path"])
        v=json.loads(p.read_text())
        check(len(v["ids"])==m["count"],"HISTORICAL_COUNT_DRIFT")
        previous.update(v["ids"])
    check(len(previous)==232,"PREVIOUS_UNIQUE_COUNT_DRIFT")
    check(rec["upstream"]=="fchollet/ARC-AGI@"+UPSTREAM,"FIRST_UPSTREAM_DRIFT")
    check(len(rec["rows"])==48 and len(cohort["ids"])==48,"COHORT_LENGTH_DRIFT")
    check(rec["transfer_cohort_source_blob"]==lock["cohort_blob"],"FIRST_COHORT_IDENTITY_DRIFT")
    check(rec["science_status"]=="P28_FRESH_TRANSFER_FAIL_STOP","UNAUTHORIZED_SCIENCE_PROMOTION")
    row_ids=[r["id"]+".json" for r in rec["rows"]]
    check(row_ids==cohort["ids"],"FIRST_ROW_IDENTITY_ORDER_DRIFT")
    original=arc_root/"data/evaluation"
    filenames=sorted(p.name for p in original.glob("*.json"))
    check(len(filenames)==400,"UPSTREAM_FILE_CENSUS_DRIFT")
    remaining=[x for x in filenames if x not in previous]
    def fnv(s):
        h=2166136261
        for c in s:
            h=((h^ord(c))*16777619)&0xffffffff
        return h
    key="neumann-q3-p28-FIRST-FRESH-TRANSFER-20261105|"
    expected=sorted(remaining,key=lambda s:(fnv(key+s),s))[:48]
    check(expected==cohort["ids"],"FILENAME_ONLY_BLIND_SELECTION_DRIFT")
    eligible,not_eligible,fit,submissions=0,0,0,0
    candidate_enumerations,pair_checks=0,0
    eligible_ids=[]
    for name,row in zip(cohort["ids"],rec["rows"]):
        data=(original/name).read_bytes()
        check(sha256(data).hexdigest()==row["original_file_sha256"],"ORIGINAL_DATA_BYTES_DRIFT:"+name)
        task=json.loads(data)
        train=task["train"]
        query=[v["input"] for v in task["test"]]
        scope=(len(train)>0 and len(query)>0 and
               all(eligible_input(p["input"]) and grid(p["output"]) for p in train)
               and all(eligible_input(x) for x in query))
        if scope:
            eligible+=1
            eligible_ids.append(name)
            independent_fit=0
            for sel in product((0,1,2),repeat=4):
                candidate_enumerations+=1
                fits=True
                for p in train:
                    pair_checks+=1
                    if apply(sel,p["input"])!=p["output"]:
                        fits=False
                        break
                if fits: independent_fit+=1
        else:
            not_eligible+=1
            independent_fit=0
        if independent_fit:fit+=1
        check(row["P28_train_fits"]==independent_fit,"TRAIN_FIT_COUNT_DRIFT:"+name)
        check(row["P28_enumerated"]==(81 if scope else 0),"CANDIDATE_ENUMERATION_DRIFT:"+name)
        check(row["P28_submitted"] is False,"UNREPORTED_P28_SUBMISSION:"+name)
        check(row["P28_ast"] is None,"UNREPORTED_EXECUTABLE_P28_PROGRAM:"+name)
        if row["P28_submitted"]:submissions+=1
    check(candidate_enumerations==rec["stats"]["P28_candidate_enumerations"],
          "TOTAL_PROGRAM_ENUMERATIONS_DRIFT")
    check(pair_checks==rec["stats"]["P28_train_pair_evaluations"],"TRAIN_PAIR_COST_DRIFT")
    summary=rec["stats"]
    counts={
      "n":len(rec["rows"]),
      "B":sum(bool(z["B_correct"]) for z in rec["rows"]),
      "P20":sum(bool(z["P20_correct"]) for z in rec["rows"]),
      "P24":sum(bool(z["P24_correct"]) for z in rec["rows"]),
      "P25":sum(bool(z["P25_correct"]) for z in rec["rows"]),
      "P27":sum(bool(z["P27_correct"]) for z in rec["rows"]),
      "P28":sum(bool(z["P28_correct"]) for z in rec["rows"]),
      "old_consensus_correct":sum(bool(z["old_consensus_correct"]) for z in rec["rows"]),
      "new_consensus_correct":sum(bool(z["new_consensus_correct"]) for z in rec["rows"]),
      "added_exact":sum(bool(z["new_consensus_additional_correct"]) for z in rec["rows"]),
      "lost_exact":sum(bool(z["new_consensus_correct_lost"]) for z in rec["rows"]),
      "P28_train_fit_count":sum(z["P28_train_fits"]>0 for z in rec["rows"]),
      "P28_submitted":sum(bool(z["P28_submitted"]) for z in rec["rows"]),
      "P28_false_submits":sum(bool(z["P28_wrong"]) for z in rec["rows"]),
      "P28_abstentions":sum(not z["P28_submitted"] for z in rec["rows"]),
      "combined_wrong":sum(bool(z["new_consensus_wrong"]) for z in rec["rows"]),
      "combined_submitted":sum(bool(z["new_consensus_submitted"]) for z in rec["rows"])
    }
    for key,val in counts.items():
        check(summary[key]==val,"RECEIPT_AGGREGATE_MISMATCH:"+key)
    check(fit==0 and eligible==4 and not_eligible==44,"FIRST_STRUCTURAL_CEILING_CHANGED")
    check(submissions==0 and summary["added_exact"]==0,"REPORTED_TRANSFER_RESULT_CHANGED")
    return {
      "schema":"neumann.q3.p28.first-transfer48-independent-python.v1",
      "original_first_sha256":sha256(b).hexdigest(),
      "auditor_pass":not errors,"errors":errors,
      "tested_originals":len(rec["rows"]),"original_baseline_correct_from_hashlocked_flags":counts["old_consensus_correct"],
      "original_baseline_engines_independently_reimplemented":False,
      "first_reported_additional_exact":summary["added_exact"],
      "input_scope_eligible":eligible,
      "input_scope_not_eligible":not_eligible,
      "eligible_ids":eligible_ids,
      "independently_train_fitting_programs":fit,
      "P28_submissions":submissions,
      "P28_candidates_tested":candidate_enumerations,
      "independent_train_pair_checks":pair_checks,
      "original_test_gold_consumed_by_independent_audit":False,
      "independent_interpreter_different_language":True,
      "conditional_ceiling":"Only "+str(eligible)+"/48 admitted by human-fixed P28 shape contract; no program in 81-class fits TRAIN for ANY admitted input. Ranker selection cannot rescue an empty set.",
      "status":"P28_FRESH_TRANSFER_FAIL_STOP",
      "Q3":"OPEN","Q6":"OPEN","Q7":"OPEN"
    }
if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("python experiments/q3_p28_transfer48_independent_audit.py ROOT ARC_ROOT FIRST_RECEIPT")
    r=independent_first(sys.argv[1],sys.argv[2],sys.argv[3])
    print(json.dumps(r,indent=2,sort_keys=True))
    if not r["auditor_pass"]:raise SystemExit(1)
