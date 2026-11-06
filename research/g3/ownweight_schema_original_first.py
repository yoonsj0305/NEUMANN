"""FIRST frozen-own-weight quantifier AST transfer to two untrained original CHC inputs.

Never retrain or change weights after first original source retrieval. All
original Horn assertions are negated individually by independent Z3. Strong
native original solver and existing human G3 rule use same source rights.
Not an autonomous new-operator/Q3 claim, and not an unseen formalism.
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

from research.g3.array_fill_parametric_invariant import (
    blob, sha, source, prove_each, solution_from_original
)
from research.g3.ownweight_schema_student import (
    load, compile_from_weights, HEADS, FEATURE_COUNT, CATEGORIES
)

ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/"docs/experiments/G3_OWNWEIGHT_QUANTIFIER_STUDENT_FROZEN_BEFORE_INIT2_INIT3_2026_11_06.json"


def native_original(raw:bytes, time_cap:int)->dict:
    with tempfile.NamedTemporaryFile("wb",suffix=".smt2") as f:
        f.write(raw);f.flush()
        started=time.perf_counter_ns()
        try:
            result=subprocess.run(["z3","-smt2","-T:"+str(time_cap),f.name],
                capture_output=True,text=True,timeout=time_cap+2,check=False)
            answer=[line.strip() for line in result.stdout.splitlines() if line.strip()]
            grounded=(result.returncode==0 and len(answer)==1 and answer[0] in ("sat","unsat"))
            return {"status":"GROUNDED_SOURCE_VERDICT" if grounded else "UNKNOWN_OR_ERROR",
                "verdict":answer[0] if grounded else None,
                "stdout_sha256":sha(result.stdout.encode()),
                "stderr_tail":result.stderr[-250:],
                "exit":result.returncode,
                "wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}
        except subprocess.TimeoutExpired:
            return {"status":"TIMEOUT_CENSORED_NOT_SOLVER_IMPOSSIBLE",
                "verdict":None,
                "wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}


def verify_compiler(raw:str,weights:np.ndarray,proof_cap:int)->dict:
    started=time.perf_counter_ns()
    try:
        ast=compile_from_weights(raw,weights)
        compiled_ms=(time.perf_counter_ns()-started)/1e6
        original=prove_each(ast,budget_per_clause_s=proof_cap)
        return {
            "status":"ORIGINAL_ALL_CLAUSES_PROVEN" if original["all_original_clauses_proven"] else "FAIL_OR_UNKNOWN",
            "num_stages":ast["num_stages"],
            "student_fourhead_AST_by_stage":ast["predicted_AST_tokens"],
            "independent_original_clauses":original["total_original_clauses"],
            "original_independently_proven":original["original_clauses_independently_proven"],
            "first_nonproof":original["first_nonproof"],
            "emitted_prefix_sha256":sha(ast["prefix"].encode()),
            "compiler_wall_ms":round(compiled_ms,3),
            "complete_wall_ms":round((time.perf_counter_ns()-started)/1e6,3)
        }
    except Exception as exc:
        return {
            "status":"FAIL_CLOSED_NO_PROVEN_ORIGINAL",
            "error":type(exc).__name__+": "+str(exc)[:250],
            "complete_wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
            "original_independently_proven":0,
            "independent_original_clauses":None
        }


def human_baseline(raw:str,proof_cap:int)->dict:
    started=time.perf_counter_ns()
    try:
        x=solution_from_original(raw)
        cert=prove_each(x,budget_per_clause_s=proof_cap)
        return {
            "status":"ORIGINAL_ALL_CLAUSES_PROVEN" if cert["all_original_clauses_proven"] else "FAIL_OR_UNKNOWN",
            "independent_original_clauses":cert["total_original_clauses"],
            "original_independently_proven":cert["original_clauses_independently_proven"],
            "first_nonproof":cert["first_nonproof"],
            "complete_wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}
    except Exception as exc:
        return {"status":"FAIL_CLOSED_NO_PROVEN_ORIGINAL",
            "error":type(exc).__name__+": "+str(exc)[:250],
            "complete_wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}


def run(checkpoint:Path)->dict:
    freeze=json.loads(FREEZE.read_text())
    ck=freeze["training_first"]
    train_bytes=checkpoint.read_bytes()
    if hashlib.sha256(train_bytes).hexdigest()!=ck["checkpoint_sha256"]:
        raise ValueError("FROZEN_PRE_ORIGINAL_TRAIN_FIRST_WEIGHT_HASH_MISMATCH")
    if ck["run_id"]!=42198111692 or ck["opened_train_proved_clauses"]!=49:
        raise ValueError("HISTORIC_TRAIN_FIRST_RECEIPT_DRIFT")
    model=load(checkpoint,expected_sha=ck["checkpoint_sha256"])
    if freeze["eval_executed"] is not False or len(freeze["target_registry"])!=2:
        raise ValueError("UNFROZEN_OR_REPLAYED_FIRST_PROTOCOL")
    seeded=np.random.default_rng(2077).normal(0,0.006,size=(HEADS,FEATURE_COUNT,CATEGORIES))
    if seeded.shape!=model.shape or np.array_equal(seeded,model):
        raise ValueError("NO_ACTUAL_TRAINED_INITIALIZATION_DIFFERENCE")
    begin=time.perf_counter_ns()
    rows=[]
    for target in freeze["target_registry"]:
        raw=source(target["file"],target["blob"])
        if blob(raw)!=target["blob"] or len(raw)!=target["bytes"]:
            raise ValueError("ORIGINAL_EXTERNAL_SOURCE_BYTE_PIN_DRIFT")
        text=raw.decode("utf8")
        # Student AST and untrained control are committed in memory BEFORE
        # human baseline and native source solver are invoked.
        student=verify_compiler(text,model,freeze["original_eval_budget"]["per_clause_proof_seconds"])
        untrained=verify_compiler(text,seeded,freeze["original_eval_budget"]["per_clause_proof_seconds"])
        human=human_baseline(text,freeze["original_eval_budget"]["per_clause_proof_seconds"])
        native=native_original(raw,freeze["original_eval_budget"]["native_z3_seconds_per_original"])
        rows.append({
            "original_file":target["file"], "original_git_blob":blob(raw),
            "original_sha256":sha(raw), "original_bytes":len(raw),
            "trained_own_weight":student,
            "untrained_original_seed_weight":untrained,
            "human_written_G3_template":human,
            "native_Z3_full_original":native
        })
    verified=lambda key: sum(r[key]["status"]=="ORIGINAL_ALL_CLAUSES_PROVEN" for r in rows)
    stats={
        "registered_originals":len(rows),
        "student_full_original_proofs":verified("trained_own_weight"),
        "untrained_full_original_proofs":verified("untrained_original_seed_weight"),
        "human_explicit_G3_rule_full_original_proofs":verified("human_written_G3_template"),
        "native_raw_grounded_verdicts":sum(r["native_Z3_full_original"]["status"]=="GROUNDED_SOURCE_VERDICT" for r in rows),
        "student_original_proved_clauses":sum(r["trained_own_weight"]["original_independently_proven"] for r in rows),
        "target_original_source_bodies_fetched_after_student_SHA_frozen":len(rows),
        "new_training_runs":0,
        "entire_original_eval_wall_seconds":round((time.perf_counter_ns()-begin)/1e9,4),
        "total_training_and_experiment_cost_including_prior_human_rule_design":"UNKNOWN_NOT_METERED",
    }
    scoped=(stats["student_full_original_proofs"]==2
            and stats["untrained_full_original_proofs"]<2)
    return {
        "schema":"neumann.g3.frozen-ownweight-quantifier-external-two-original-first.v1",
        "scientific_status":("OWNWEIGHT_HUMAN_TEACHER_DISTILLATION_TRANSFER_PASS_SCOPED" if scoped
            else "OWNWEIGHT_HUMAN_TEACHER_DISTILLATION_TRANSFER_FAIL"),
        "original_student_weight_SHA256":ck["checkpoint_sha256"],
        "frozen_training_first_run":ck["run_id"],
        "scope":"SAME_AUTHOR_FAMILY_ARRAY_INIT2_INIT3_NOT_CROSS_FORMALISM",
        "student_proposes_four_factorized_quantifier_AST_tokens":True,
        "new_base_operator_human_not_model_invented":True,
        "no_original_target_model_training":True,
        "source_original_clauses_unchanged":True,
        "official_original_competition_expected_label_NOT_used":True,
        "original_problem_solver_censored_times_not_native_failures":True,
        "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
        "stats":stats,"rows":rows
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--checkpoint",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    outcome=run(args.checkpoint)
    args.report.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in outcome.items() if k!="rows"},indent=2,sort_keys=True))
    if outcome["scientific_status"]!="OWNWEIGHT_HUMAN_TEACHER_DISTILLATION_TRANSFER_PASS_SCOPED":
        raise SystemExit(1)


if __name__=="__main__":
    main()
