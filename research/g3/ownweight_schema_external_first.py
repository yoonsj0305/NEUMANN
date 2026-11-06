"""One frozen own-weight checkpoint, FIRST external init2/init3 original proof.

Source pin and checkpoint SHA MUST be verified before any source fetch.
No fitting, heuristic tuning or human-template access before student proposals
for BOTH originals are compiled and their SHA frozen in memory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np

from research.g3.ownweight_schema_student import (
    ROOT, CONTRACT, compile_from_weights, load
)
from research.g3.array_fill_parametric_invariant import (
    source, prove_each, solution_from_original
)


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def native_z3(original:str,timeout_s:int=15)->dict:
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf8") as f:
        f.write(original);f.flush()
        t=time.perf_counter_ns()
        try:
            p=subprocess.run(["z3","-smt2","-T:"+str(timeout_s),f.name],
                             text=True,capture_output=True,timeout=timeout_s+2,check=False)
            lines=[v.strip() for v in p.stdout.splitlines() if v.strip()]
            ans=lines[0] if len(lines)==1 and p.returncode==0 and lines[0] in ("sat","unsat","unknown") else "CHECKER_ERROR"
            result={"bounded_native_verdict":ans,
              "exit":p.returncode,
              "stdout_sha256":sha(p.stdout.encode()),
              "stderr_tail":p.stderr[-250:]}
        except subprocess.TimeoutExpired:
            result={"bounded_native_verdict":"TIMEOUT_NOT_INTRACTABLE_PROOF"}
        result["wall_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
        result["native_time_cap_s"]=timeout_s
        return result


def evidence(checkpoint:Path,destination:Path,expected_sha:str,training_run:int)->dict:
    frozen=json.loads(CONTRACT.read_text())
    targets=frozen["external_first_candidate"]["cross_independent_original_cohort"]
    if len(targets)!=2 or [r["file"] for r in targets]!=[
      "standard_init2_true-unreach-call_ground_000.smt2",
      "standard_init3_true-unreach-call_ground_000.smt2"]:
        raise ValueError("UNAUTHORIZED_EXTERNAL_TARGET_CHANGE")
    if training_run!=42198111692:
        raise ValueError("WRONG_FIRST_TRAIN_RUN")
    W=load(checkpoint,expected_sha)
    zero=np.zeros_like(W)
    report={
       "schema":"neumann.g3.ownweight-quantified-AST-two-original-first.v1",
       "science_scope":"OWN_WEIGHT_TEACHER_DISTILLATION_NOT_AUTONOMOUS_INVENTION",
       "checkpoint_SHA256":expected_sha,
       "train_source_only_actual_run":training_run,
       "student_weights_retrained_after_external_first":False,
       "first_external_corpus_size":2,
       "proposals_frozen_before_any_verification":True,
       "all_originals_source_blobs_pre_registered":True,
       "target_specific_after_first_edits":False,
       "source_gold_or_expected_verdict_sent_to_model":False,
       "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
       "rows":[]
    }
    start=time.perf_counter_ns()
    frozen_candidates=[]
    # Source bodies become visible ONLY now, after checkpoint identity pin.
    # Student proposals for both sources are materialized BEFORE any
    # independent verifier or human-template baseline executes.
    for row in targets:
        name=row["file"]
        raw=source(name,row["git_blob"])
        if len(raw)!=row["bytes"]:
            raise ValueError("FROZEN_UNSEEN_ORIGINAL_BYTES_CHANGED_"+name)
        original=raw.decode("utf8")
        proposed={"name":name,"original_git_blob":row["git_blob"],
                  "source_sha256":sha(raw),"source_bytes":len(raw)}
        t=time.perf_counter_ns()
        try:
            candidate=compile_from_weights(original,W)
            proposed["student_proposal_status"]="COMPILED"
            proposed["student_ast_tokens"]=candidate["predicted_AST_tokens"]
            proposed["student_interpretation_sha256"]=sha(candidate["prefix"].encode())
            proposed["student_compile_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
        except Exception as ex:
            candidate=None
            proposed["student_proposal_status"]="INVALID_OR_ABSTAIN"
            proposed["student_proposal_error"]=type(ex).__name__+":"+str(ex)[:220]
            proposed["student_compile_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
        frozen_candidates.append((original,candidate,proposed))
    # Execution of any verifier or classical original code only after above.
    for orig, candidate, row in frozen_candidates:
        row["original_source_strong_native"]=native_z3(orig,15)
        if candidate is None:
            row["student_proven"]=False
            row["student_original_clauses_checked"]=0
            row["student_original_clauses_proven"]=0
        else:
            t=time.perf_counter_ns()
            proof=prove_each(candidate,budget_per_clause_s=7)
            row["student_proven"]=proof["all_original_clauses_proven"]
            row["student_original_clauses_checked"]=proof["original_clauses_examined"]
            row["student_original_clauses_proven"]=proof["original_clauses_independently_proven"]
            row["student_original_total_clauses"]=proof["total_original_clauses"]
            row["student_first_nonproof"]=proof["first_nonproof"]
            row["student_original_verifier_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
        # Matching untrained head (all-zero) has same AST grammar and source.
        try:
            ablated=compile_from_weights(orig,zero)
            ablation=prove_each(ablated,budget_per_clause_s=7)
            row["untrained_zero_weights_original_verified"]=ablation["all_original_clauses_proven"]
        except (ValueError,RuntimeError) as ex:
            row["untrained_zero_weights_original_verified"]=False
            row["untrained_abstention_reason"]=type(ex).__name__+":"+str(ex)[:160]
        # Author-specified reusable rule is a stronger equal-source-rights
        # classical generator and MUST be counted, not hidden.
        t=time.perf_counter_ns()
        direct=solution_from_original(orig)
        dproof=prove_each(direct,budget_per_clause_s=7)
        row["human_G3_template_original_proven"]=dproof["all_original_clauses_proven"]
        row["human_G3_template_original_clauses_proven"]=dproof["original_clauses_independently_proven"]
        row["human_G3_template_total_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
        report["rows"].append(row)
    report["first_total_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    report["student_originals_proven"]=sum(x.get("student_proven",False) for x in report["rows"])
    report["untrained_originals_proven"]=sum(x.get("untrained_zero_weights_original_verified",False) for x in report["rows"])
    report["human_originals_proven"]=sum(x.get("human_G3_template_original_proven",False) for x in report["rows"])
    report["native_originals_solved_within_15s"]=sum(
       x["original_source_strong_native"]["bounded_native_verdict"] in ("sat","unsat")
       for x in report["rows"])
    report["student_verified_original_clauses"]=sum(
       x.get("student_original_clauses_proven",0) for x in report["rows"])
    report["scoped_teacher_distilled_learning_gate_pass"]=(
       report["student_originals_proven"]==2
       and report["untrained_originals_proven"]<2
       and report["human_originals_proven"]==2)
    report["original_Q3_autonomous_invention"]=False
    report["new_operator_absent_from_training_grammar"]=False
    report["iso_capability_total_10x_claim"]=False
    destination.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--expected-sha",required=True)
    p.add_argument("--training-run",type=int,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    r=evidence(a.checkpoint,a.report,a.expected_sha,a.training_run)
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},indent=2,sort_keys=True))
    for row in r["rows"]:
        print(json.dumps({k:v for k,v in row.items() if k!="student_ast_tokens"},sort_keys=True))
    if not r["scoped_teacher_distilled_learning_gate_pass"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
