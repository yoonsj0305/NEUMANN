"""Independent post-FIRST COMPLETE collision certificate for a typed affine AST family.

Unlike the original quick H0 witness, this verifier does NOT pin source values
to 0 and 1 or cursor to 0. It asks whether there exist ANY two arbitrary
source arrays and ANY integer index with identical observed destination
array/metadata but different required values. SMT UNSAT therefore certifies
that target value genuinely factors through H0 observations for this
registered program class; SAT certifies an insufficiency witness.

No learned policy imported/executed, no retraining, no new target source.
Original first scientific FAIL and earlier success remain immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT/"docs/experiments/Q3_CEX_SEMANTIC_CANCELLATION_FIRST_PREREG_2026_11_06.json"
ORIGINAL = ROOT/"docs/experiments/Q3_COUNTEREXAMPLE_GROWER_FIRST_PREREG_2026_11_06.json"
FIRST_GOOD_SHA = "c05a039ecb371279de66714bafcd1a5b6c05ebc18d7477ce4c77f302d9e21127"


def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def emit(tree,index:str,source:str)->str:
    # Intentionally independent interpreter from prior learning implementation.
    if not isinstance(tree,list) or not tree or not isinstance(tree[0],str):
        raise ValueError("INVALID_ABSTRACT_TYPED_EXPRESSION")
    t=tree[0]
    if t=="const" and len(tree)==2 and type(tree[1])==int:
        return str(tree[1])
    if t=="var" and len(tree)==2 and tree[1] in ("i","b"):
        return index if tree[1]=="i" else "b"
    if t=="select" and len(tree)==3 and tree[1]=="S":
        return "(select "+source+" "+emit(tree[2],index,source)+")"
    if t in ("add","mul") and len(tree)==3:
        if t=="mul" and not (isinstance(tree[1],list) and tree[1][0]=="const"
                            or isinstance(tree[2],list) and tree[2][0]=="const"):
            raise ValueError("NOT_LINEAR_ARITHMETIC")
        return ("(" + ("+" if t=="add" else "*") + " "
                + emit(tree[1],index,source) + " "
                + emit(tree[2],index,source) + ")")
    if t=="neg" and len(tree)==2:
        return "(- "+emit(tree[1],index,source)+")"
    raise ValueError("UNKNOWN_OPERATOR_OR_UNSAFE_TYPED_INPUT")


def full_collision_script(task:dict)->str:
    if type(task)!=dict or set(task)!={"expr","db","sb"}:
        raise ValueError("EXACT_REGISTERED_TASK_REQUIRED")
    if type(task["db"])!=int or type(task["sb"])!=int:
        raise ValueError("BAD_INDEX_BASE_TYPE")
    lhs=emit(task["expr"],"idx","S0")
    rhs=emit(task["expr"],"idx","S1")
    return (
      "(set-logic AUFLIA)\n"
      "(declare-const S0 (Array Int Int))\n"
      "(declare-const S1 (Array Int Int))\n"
      "(declare-const D (Array Int Int))\n"
      "(declare-const base Int)\n"
      "(declare-const idx Int)\n"
      "(define-fun a () Int (+ base "+str(task["db"])+"))\n"
      "(define-fun b () Int (+ base "+str(task["sb"])+"))\n"
      "(assert (>= idx 0))\n"
      "(assert (= (select D (+ a idx)) "+lhs+"))\n"
      "(assert (not (= (select D (+ a idx)) "+rhs+")))\n"
      "(check-sat)\n"
    )


def check(script:str)->dict:
    t=time.perf_counter_ns()
    with tempfile.NamedTemporaryFile("w",suffix=".smt2") as f:
        f.write(script);f.flush()
        try:
            p=subprocess.run(["z3","-smt2","-T:5",f.name],capture_output=True,
                             text=True,timeout=7,check=False)
            outputs=[x.strip() for x in p.stdout.splitlines() if x.strip()]
            answer=outputs[0] if p.returncode==0 and outputs in (["sat"],["unsat"]) else "UNKNOWN"
            tail=p.stderr[-200:]
        except subprocess.TimeoutExpired:
            answer="TIMEOUT";tail=""
    return {"verdict":answer,"script_sha256":digest(script.encode()),
            "wall_ms":round((time.perf_counter_ns()-t)/1e6,3),
            "stderr_tail":tail}


def audit(first_train:Path, first_adversary:Path, output:Path)->dict:
    a=json.loads(CONTRACT.read_text())
    b=json.loads(ORIGINAL.read_text())
    original=first_train.read_bytes()
    if digest(original)!=FIRST_GOOD_SHA:
        raise ValueError("FIRST_LEARNED_RESULT_UNCHANGED_SHA_REQUIRED")
    old=json.loads(original)
    if old["scientific_status"]!="PASS_SCOPED_COLLISION_TO_TYPED_RELATION" or old["sourcefree_heldout_correct_policy"]!=8:
        raise ValueError("NOT_ORIGINAL_LEARNED_FIRST")
    firstbad=json.loads(first_adversary.read_bytes())
    if firstbad.get("scientific_status")!="FAIL_SEMANTIC_RELEVANCE_LEXICAL_PROXY":
        raise ValueError("ORIGINAL_ADVERSARIAL_FIRST_FAIL_MUST_BE_UNCHANGED")
    if firstbad.get("stats",{}).get("trained_frozen_correct")!=2:
        raise ValueError("ORIGINAL_ADVERSARIAL_FIRST_COUNT_DRIFT")
    test_a=b["heldout"]["examples"]
    test_b=a["preregistered_heldout_not_in_initial_first"]
    if len(test_a)!=8 or len(test_b)!=6:
        raise ValueError("ORIGINAL_TWO_SOURCEFREE_COHORT_SIZE_DRIFT")
    groups=[
        ("first_8",test_a,
         [r["source_dependency_oracle_SAT"] for r in old["first_heldout_evidence"]]),
        ("new_6",test_b,
         [r["requires_H0_expansion_proved_from_Z3"] for r in firstbad["first_rows"]])
    ]
    rows=[]
    for cohort,tasks,old_verdicts in groups:
        for index,(t,old_truth) in enumerate(zip(tasks,old_verdicts)):
            proof=check(full_collision_script(t))
            if proof["verdict"] not in ("sat","unsat"):
                raise ValueError("SMT_ALL_SOURCE_AND_INDEX_VALUES_ORACLE_UNKNOWN")
            now=proof["verdict"]=="sat"
            rows.append({
              "cohort":cohort,"index":index,
              "task_AST_sha256":digest(json.dumps(t,sort_keys=True).encode()),
              "original_quick_oracle_missing_info":bool(old_truth),
              "all_source_arrays_and_indices_semantic_missing_info":now,
              "original_quick_oracle_matches_complete_SMT_semantic_check":now==bool(old_truth),
              "proof":proof
            })
    agreement=sum(r["original_quick_oracle_matches_complete_SMT_semantic_check"] for r in rows)
    report={
      "schema":"neumann.q3.exact-two-input-congruence-counterexample-afterfirst.v1",
      "scientific_status":"PASS_ALL_INDEX_SEMANTIC_FIRST_AUDIT" if agreement==14 else "FAIL_OLD_ORACLE_WAS_UNSOUND",
      "mathematical_contract":"Exists x,y: same H0 observation phi(x)=phi(y) AND f(x)!=f(y) => representation insufficient. UNSAT of this existential is formal H0 congruence/sufficiency for the constrained typed AST.",
      "independently_quantified_over_all_integer_source_values_and_indices":True,
      "source_arrays_D_S0_S1_are_unconstrained_beyond_shared_D":True,
      "old_FIRST_8OF8_retained":True,
      "old_FIRST_2OF6_FAIL_retained":True,
      "number_of_opened_sourcefree_cases_checked":len(rows),
      "original_vs_complete_semantic_oracle_agreement":agreement,
      "complete_semantic_label_requires_expansion":sum(r["all_source_arrays_and_indices_semantic_missing_info"] for r in rows),
      "original_first_learned_result_sha256":digest(original),
      "old_first_adversary_result_sha256":digest(first_adversary.read_bytes()),
      "new_original_CHC_sources_fetched":0,"new_learning_updates":0,
      "new_model_proposals":0,"new_original_source_tasks_solved":0,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN",
      "verified_receipts":rows
    }
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original-learned-first",type=Path,required=True)
    p.add_argument("--original-adversarial-first",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.original_learned_first,args.original_adversarial_first,args.out)
    print(json.dumps({k:v for k,v in result.items() if k!="verified_receipts"},sort_keys=True,indent=2))
    if result["scientific_status"]!="PASS_ALL_INDEX_SEMANTIC_FIRST_AUDIT":
        raise SystemExit(1)
