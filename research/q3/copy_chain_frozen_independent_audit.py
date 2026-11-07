"""Read-only independent audit of frozen COPY2/COPY3 semantic-role receipts.

This script DOES NOT import the generator or execute its invariant-construction
code. It reads the exact first post-repair GitHub artifact, checks immutable
original source assertions against each generated proof obligation, reruns
original SMT2 obligations independently, and tests SAT nonvacuity of every
generated stage relation. It never accesses a new original source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from research.q3.real_copy2_chc_h1 import forms, blob

FROZEN_POSTFIRST_SHA="1708ea42cafc72f45841c4bc9ed73711931e65bbb4332bb6e1ce15b4fd787821"
EXPECTED={
    "copy2":("30b3bab8834aa6f834cf493539180e6b92caf16f",9,3),
    "copy3":("f8fd0b73c3aa45ee5f49426416a378bcfc462605",11,4)
}

def digest(x:bytes):
    return hashlib.sha256(x).hexdigest()

def check_z3(script:str, seconds:int=7):
    start=time.perf_counter_ns()
    try:
        p=subprocess.run(["z3","-smt2","-in"],input=script,text=True,
                         capture_output=True,timeout=seconds)
        rows=[r.strip() for r in p.stdout.splitlines() if r.strip()]
        verdict=rows[0] if p.returncode==0 and rows in (["sat"],["unsat"]) else "UNKNOWN_CHECKER"
    except subprocess.TimeoutExpired:
        verdict="UNKNOWN_TIMEOUT"
    return verdict,round((time.perf_counter_ns()-start)/1e6,3)

def audit(root:Path,out:Path):
    raw=(root/"POSTFIRST_REPORT.json").read_bytes()
    if digest(raw)!=FROZEN_POSTFIRST_SHA:
        raise ValueError("FIRST_POSTFIRST_JSON_RECEIPT_DRIFT")
    original_record=json.loads(raw)
    if original_record.get("original_first_status")!="FAILED_12_OF_20_UNMODIFIED_CLAUSES":
        raise ValueError("HISTORIC_FIRST_FAILURE_NOT_PRESERVED")
    if original_record.get("programs_pass")!=2 or len(original_record.get("rows",[]))!=2:
        raise ValueError("NO_VALID_ORIGINAL_POSTFIRST_RECORD")
    started=time.perf_counter_ns()
    rows=[]
    for case in original_record["rows"]:
        name=case["case"]
        if name not in EXPECTED:
            raise ValueError("UNKNOWN_ORIGINAL_NAME")
        original_blob,nclauses,nstages=EXPECTED[name]
        sub=root/name
        source=(sub/"original.smt2").read_bytes()
        if blob(source)!=original_blob:
            raise ValueError("PUBLIC_SOURCE_ORIGINAL_BLOB_DRIFT")
        original_assertions=[
           x for x in forms(source.decode("utf8"))
           if re.match(r"^\(\s*assert\s+",x)
        ]
        if len(original_assertions)!=nclauses:
            raise ValueError("ORIGINAL_CHC_CLAUSE_COUNT_MISMATCH")
        positive=[]
        for k,original in enumerate(original_assertions):
            proofpath=sub/"original_unchanged_clauses"/f"obligation_{k:02d}.smt2"
            saved=proofpath.read_bytes()
            evidence=case["proofs"][k]
            if evidence["index"]!=k or digest(original.encode())!=evidence["original_assert_sha256"]:
                raise ValueError("ALTERED_ORIGINAL_CLAUSE_OR_ORDER")
            if digest(saved)!=evidence["negated_obligation_sha256"]:
                raise ValueError("POSTFIRST_COMPILED_PROOF_FILE_DRIFT")
            if "(assert (not " not in saved.decode("utf8"):
                raise ValueError("NOT_A_NEGATED_ORIGINAL_HORN_OBLIGATION")
            answer,ms=check_z3(saved.decode("utf8"))
            positive.append({"index":k,"verdict":answer,"ms":ms,
                             "rechecked_sha256":digest(saved)})
        mutant_checks=[]
        for original in case["mutant_proofs"]:
            k=original["index"]
            path=sub/"mutant"/f"obligation_{k:02d}.smt2"
            saved=path.read_bytes()
            if digest(saved)!=original["negated_obligation_sha256"]:
                raise ValueError("MUTANT_RECEIPT_DRIFT")
            answer,ms=check_z3(saved.decode("utf8"))
            mutant_checks.append({"index":k,"verdict":answer,"ms":ms})
        # SAT for each invariant interpretation: reject empty/contradictory
        # predicates that could make some Horn steps trivially valid.
        example=(sub/"original_unchanged_clauses"/"obligation_00.smt2").read_text()
        prefix=example.split("(assert (not ",1)[0]
        stage_sat=[]
        for n,text in enumerate(case["generated_relations"]):
            pattern=re.match(r"\(define-fun\s+\|main@([^|]+)\|",text)
            if not pattern:
                raise ValueError("BAD_STAGE_DECLARATION")
            stage=pattern.group(1)
            param_types=re.findall(r"\(x\d+\s+(Int|\(Array\s+Int\s+Int\))\)",text)
            if not param_types:
                raise ValueError("UNREADABLE_STAGE_TYPE_SIGNATURE")
            declarations="\n".join(f"(declare-const witness_{i} {t})"
                                   for i,t in enumerate(param_types))
            args=" ".join(f"witness_{i}" for i in range(len(param_types)))
            sat_script=prefix+declarations+"\n(assert (|main@"+stage+"| "+args+"))\n(check-sat)\n"
            answer,ms=check_z3(sat_script)
            stage_sat.append({"stage":stage,"verdict":answer,
                              "ms":ms,"script_sha256":digest(sat_script.encode())})
        row={
          "case":name,
          "verified_original_clause_count":sum(x["verdict"]=="unsat" for x in positive),
          "expected_clause_count":nclauses,
          "mutant_sat":any(x["verdict"]=="sat" for x in mutant_checks),
          "nonvacuous_stage_sat_count":sum(x["verdict"]=="sat" for x in stage_sat),
          "expected_stage_count":nstages,
          "positive_clauses":positive,
          "wrong_mutant_checks":mutant_checks,
          "stage_satisfiability":stage_sat
        }
        rows.append(row)
    report={
       "schema":"neumann.q3.postfirst-independent-frozen-receipt-nonvacuity.v1",
       "source_postfirst_sha256":digest(raw),
       "original_failed_first_preserved":True,
       "verified_originals":len(rows),
       "all_original_horn_clauses_rechecked":sum(r["verified_original_clause_count"] for r in rows),
       "original_horn_clauses_expected":20,
       "all_recovered_invariant_stages_sat":sum(r["nonvacuous_stage_sat_count"] for r in rows),
       "invariant_stages_expected":7,
       "all_wrong_operator_mutants_refuted":all(r["mutant_sat"] for r in rows),
       "new_training":False,"new_external_originals":0,
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN",
       "wall_seconds":round((time.perf_counter_ns()-started)/1e9,4),
       "rows":rows
    }
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2,sort_keys=True))
    if (report["all_original_horn_clauses_rechecked"]!=20 or
        report["all_recovered_invariant_stages_sat"]!=7 or
        not report["all_wrong_operator_mutants_refuted"]):
        raise RuntimeError("INDEPENDENT_COPY_PROOF_AUDIT_FAILED_OR_UNKNOWN")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    audit(a.artifact_dir,a.out)
