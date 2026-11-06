"""Proof-reward learned relational selector with exact symbolic Z3 certificates.

This is a small *tabular own-weight* policy trained from independent Z3 proof
rewards. It generates a typed two-array predicate outside fixed H0, but H1
grammar and all candidate offsets are HUMAN supplied, so autonomous Q3 is OPEN.
Synthetic, source-free trials only; NEVER claim external original CHC solved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"docs/experiments/Q3_PROOF_REWARD_RELATIONAL_STRUCTURE_FIRST_PREREG_2026_11_06.json"
OPS=("COPY","ADD1","SUB1")
CANDIDATES=(None,-2,-1,0,1,2)
SCHEMA="neumann.q3.proof-reward-owned-typed-relational-first.v1"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def actual_source_delta(op:str)->int:
    # The evaluator, not the learned scorer, owns this code-semantics mapping.
    if op not in OPS:
        raise ValueError("INCOMPATIBLE_SOURCE_AST_OPERATOR")
    return {"COPY":0,"ADD1":1,"SUB1":-1}[op]


def negative_integer(n:int)->str:
    return str(n)


def predicate(cand:int|None)->str:
    dst="(select D (+ a j))"
    if cand is None:
        right="0" # H0 sees destination only, never reads independently varying source.
    else:
        right="(+ (select S (+ b j)) "+negative_integer(cand)+")"
    return ("(define-fun P ((S (Array Int Int)) (D (Array Int Int))"
            " (a Int) (b Int) (i Int)) Bool "
            "(forall ((j Int)) (=> (and (<= 0 j) (< j i)) "
            "(= "+dst+" "+right+"))))")


def script(task:dict,candidate:int|None,kind:str)->str:
    if type(task) is not dict or set(task)!={"op","src_shift","dst_shift"}:
        raise ValueError("EXACT_TYPED_TASK_REQUIRED")
    if any(type(task[x]) is not int for x in ("src_shift","dst_shift")):
        raise ValueError("NONINTEGER_ADDRESS_SHIFT")
    delta=actual_source_delta(task["op"])
    if candidate not in CANDIDATES:
        raise ValueError("NOT_IN_FROZEN_OPERATOR_GRAMMAR")
    base=(
      "(set-logic AUFLIA)\n"
      "(declare-const src (Array Int Int))\n"
      "(declare-const dst (Array Int Int))\n"
      "(declare-const base Int)\n"
      "(declare-const cursor Int)\n"
      "(declare-const limit Int)\n"+
      "(define-fun a () Int (+ base "+str(task["dst_shift"])+"))\n"+
      "(define-fun b () Int (+ base "+str(task["src_shift"])+"))\n"+
      predicate(candidate)+"\n")
    if kind=="INIT":
        return base+"(assert (not (P src dst a b 0)))\n(check-sat)\n"
    if kind in ("STEP","WRONG_CONTROL"):
        changed=delta+(1 if kind=="WRONG_CONTROL" else 0)
        updated="(store dst (+ a cursor) (+ (select src (+ b cursor)) "+str(changed)+"))"
        return (base+"(assert (> limit 0))\n(assert (<= 0 cursor))\n"
          "(assert (< cursor limit))\n"
          "(assert (P src dst a b cursor))\n"
          "(assert (not (P src "+updated+" a b (+ cursor 1))))\n"
          "(check-sat)\n")
    if kind=="NONVACUITY":
        return (base+"(assert (> limit 0))\n(assert (= cursor 1))\n"
          "(assert (= base 0))\n(assert (P src dst a b cursor))\n"
          "(check-sat)\n")
    raise ValueError("INVALID_INDEPENDENT_PROOF_KIND")


def z3(script_text:str,budget_s:int)->dict:
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf-8") as f:
        f.write(script_text)
        f.flush()
        before=time.perf_counter_ns()
        try:
            p=subprocess.run(["z3","-smt2","-T:"+str(budget_s),f.name],
                             capture_output=True,text=True,timeout=budget_s+2,check=False)
            lines=[line.strip() for line in p.stdout.splitlines() if line.strip()]
            v=(lines[0] if p.returncode==0 and len(lines)==1 and
               lines[0] in ("sat","unsat") else "UNKNOWN_OR_CHECKER_ERROR")
            error=p.stderr[-220:]
        except subprocess.TimeoutExpired:
            v="TIMEOUT_CENSORED_NOT_PROOF"
            error=""
        return {"verdict":v,"script_sha256":sha(script_text.encode()),
                "wall_ms":round((time.perf_counter_ns()-before)/1e6,3),
                "stderr_tail":error}


def prove(task:dict,candidate:int|None,budget_s:int,controls:bool=False)->dict:
    required={"INIT":"unsat","STEP":"unsat"}
    if controls:
        required.update({"NONVACUITY":"sat","WRONG_CONTROL":"sat"})
    receipts=[]
    for name,expected in required.items():
        record=z3(script(task,candidate,name),budget_s)
        record.update({"check":name,"required":expected,
                       "confirmed":record["verdict"]==expected})
        receipts.append(record)
        if not record["confirmed"]:
            break
    return {"candidate":candidate if candidate is not None else "H0_DST_ONLY",
            "proven":len(receipts)==len(required) and all(x["confirmed"] for x in receipts),
            "checks":receipts,"num_z3_calls":len(receipts),
            "total_z3_wall_ms":round(sum(x["wall_ms"] for x in receipts),3)}


def argmax(row:list[float])->int:
    if len(row)!=len(CANDIDATES) or any(not math.isfinite(v) for v in row):
        raise ValueError("INVALID_WEIGHT_VECTOR")
    return max(range(len(row)),key=lambda k:(row[k],-k))


def task(op:str,shift_pair:list[int])->dict:
    if op not in OPS or type(shift_pair) is not list or len(shift_pair)!=2:
        raise ValueError("INVALID_FROZEN_TASK")
    return {"op":op,"src_shift":shift_pair[0],"dst_shift":shift_pair[1]}


def train_and_evaluate(out:Path)->dict:
    if not shutil.which("z3"):
        raise RuntimeError("REQUIRES_INDEPENDENT_Z3_SOURCE_PROVER")
    m=json.loads(MANIFEST.read_text())
    if m["first_result"]!="NOT_RUN" or m["training_cases"]["n"]!=6 or m["heldout_cases"]["n"]!=12:
        raise ValueError("FROZEN_COHORT_CONTRACT_CHANGED")
    if m["H1_proposals_by_generic_typed_composition"]!=[
        "destination_only_constant","cross_array_offset_-2","cross_array_offset_-1",
        "cross_array_offset_0","cross_array_offset_1","cross_array_offset_2"]:
        raise ValueError("HUMAN_TYPED_GRAMMAR_CHANGED")
    train_tasks=[task(op,sp) for op in m["training_cases"]["operator"]
                 for sp in m["training_cases"]["source_destination_index_shift_pairs"]]
    heldout=[task(op,sp) for op in m["heldout_cases"]["operator"]
              for sp in m["heldout_cases"]["source_destination_index_shift_pairs"]]
    if len(train_tasks)!=6 or len(heldout)!=12:
        raise ValueError("TASK_COUNT_CHANGED")
    started=time.perf_counter_ns()
    W=[[0.0]*len(CANDIDATES) for _ in OPS]
    frozen_before_training_sha=sha(json.dumps(W).encode())
    train_receipts=[]
    z3_train_calls=0
    # The learner receives ONLY independent proof booleans, never evaluator's
    # hidden actual delta/class. It first tests all grammar-generated structures
    # on TRAIN; then updates the own-weight selector from successful proofs.
    for original in train_tasks:
        row=W[OPS.index(original["op"])]
        checked=[]
        successful=[]
        for j,candidate in enumerate(CANDIDATES):
            result=prove(original,candidate,3)
            z3_train_calls+=result["num_z3_calls"]
            checked.append({"j":j,"candidate":result["candidate"],
                            "certified_reward":int(result["proven"]),
                            "num_z3_calls":result["num_z3_calls"],
                            "z3_wall_ms":result["total_z3_wall_ms"],
                            "first_nonproof":next((x["verdict"] for x in result["checks"] if
                                not x["confirmed"]),None)})
            if result["proven"]:
                successful.append(j)
        if len(successful)!=1 or successful[0]==0:
            raise ValueError("TRAINING_Z3_COULD_NOT_IDENTIFY_ONE_NON_H0_SUCCESS")
        for j in range(len(CANDIDATES)):
            row[j]+=(1.0 if j==successful[0] else -0.2)
        train_receipts.append({"task_source_AST":original,
                               "proof_rewards":checked,
                               "trained_operator_index_from_proof":successful[0]})
    trained_sha=sha(json.dumps(W,separators=(",",":"),sort_keys=True).encode())
    training_seconds=(time.perf_counter_ns()-started)/1e9
    # Freeze trained 3x6 learned weights before HELDOUT evaluation calls.
    frozen=json.loads(json.dumps(W))
    frozen_sha_again=sha(json.dumps(frozen,separators=(",",":"),sort_keys=True).encode())
    if trained_sha!=frozen_sha_again or trained_sha==frozen_before_training_sha:
        raise ValueError("NO_REAL_FROZEN_WEIGHTS")
    rows=[]
    heldout_calls=0
    for original in heldout:
        idx=OPS.index(original["op"])
        learned_choice=argmax(frozen[idx])
        untrained_choice=argmax([0.0]*len(CANDIDATES))
        student=prove(original,CANDIDATES[learned_choice],3,controls=True)
        zero=prove(original,CANDIDATES[untrained_choice],3)
        heldout_calls+=student["num_z3_calls"]+zero["num_z3_calls"]
        # Same-rights strong classical, direct source-AST reader: this is
        # deliberately a stronger, cheaper algorithm than the learned policy.
        classical_choice=CANDIDATES.index(actual_source_delta(original["op"]))
        direct=prove(original,CANDIDATES[classical_choice],3,controls=True)
        heldout_calls+=direct["num_z3_calls"]
        row={"heldout_source_AST":original,"learned_candidate":student["candidate"],
             "learned_chosen_index":learned_choice,
             "learned_independent_proof":student["proven"],
             "untrained_independent_proof":zero["proven"],
             "same_rights_classical_direct_proof":direct["proven"],
             "independent_z3_recipts":{
                 "student":student,"untrained":zero,"classical":direct}}
        rows.append(row)
    n=len(rows)
    student_pass=sum(x["learned_independent_proof"] for x in rows)
    untrained_pass=sum(x["untrained_independent_proof"] for x in rows)
    classical_pass=sum(x["same_rights_classical_direct_proof"] for x in rows)
    claim=student_pass==n and untrained_pass==0 and classical_pass==n
    result={
      "schema":SCHEMA,
      "scientific_status":"PASS_SCOPED_PROOF_REWARD_POLICY_SELECTION" if claim else "FAIL_CLOSED",
      "train_sourcefree_synthetic_tasks":len(train_tasks),
      "heldout_sourcefree_synthetic_tasks":n,
      "training_uses_only_independent_Z3_proof_feedback":True,
      "model_form":"ACTUAL_TRAINED_OWN_WEIGHT_TABLE_3_BY_6_NOT_NEURAL_NETWORK",
      "frozen_student_weights_sha256":trained_sha,"trained_weights":frozen,
      "trained_policy_proven":student_pass,"untrained_policy_proven":untrained_pass,
      "classical_direct_original_proven":classical_pass,
      "baseline_stronger_or_equal_capability":classical_pass>=student_pass,
      "student_proposes_cross_array_relation_outside_H0":student_pass>0,
      "typed_H1_grammar_given_by_humans":True,
      "new_general_operator_invented_by_model":False,
      "independent_external_original_CHC_solved":0,
      "new_different_formalism_transfer":False,
      "unseen_original_benchmark_ids_consumed":0,
      "original_teacher_code_or_labels_used_by_trainer":False,
      "training_actual_wall_seconds":round(training_seconds,4),
      "complete_experiment_wall_seconds":round((time.perf_counter_ns()-started)/1e9,4),
      "train_z3_calls":z3_train_calls,"heldout_z3_calls":heldout_calls,
      "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "training_evidence":train_receipts,"heldout_evidence":rows
    }
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=train_and_evaluate(a.out)
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("trained_weights","training_evidence","heldout_evidence")},indent=2,sort_keys=True))
    if result["scientific_status"]!="PASS_SCOPED_PROOF_REWARD_POLICY_SELECTION":
        raise SystemExit(1)


if __name__=="__main__":
    main()
