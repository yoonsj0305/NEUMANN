"""All-N ARRAY-FILL induction: source-free quantified SMT theorem generator.

No benchmark input/expected verdict, no finite unrolled stage count.
A generic stage writes one cell A[n+i] := new, advances i.
The conditional invariant tracks prefix/new and suffix/old for ALL Int
indices, arbitrary L>0, n>0, i∈[0,L], arbitrary old/new values.

A real SMT2 solver proves each negated implication UNSAT, while two
nonvacuity and mutation tests MUST return SAT. A definite proof requires
all six positive obligations UNSAT, not Z3 printing success to stdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

BASE="""(set-logic ALL)
(declare-const n Int)
(declare-const L Int)
(declare-const i Int)
(declare-const v Int)
(declare-const w Int)
(declare-const A (Array Int Int))
(define-fun prefix ((a (Array Int Int)) (k Int) (value Int)) Bool
  (forall ((j Int))
    (=> (and (<= 0 j) (< j k))
        (= (select a (+ n j)) value))))
(define-fun suffix ((a (Array Int Int)) (k Int) (value Int)) Bool
  (forall ((j Int))
    (=> (and (<= k j) (< j L))
        (= (select a (+ n j)) value))))
(define-fun entire ((a (Array Int Int)) (value Int)) Bool
  (forall ((j Int))
    (=> (and (<= 0 j) (< j L))
        (= (select a (+ n j)) value))))
(define-fun Inv ((a (Array Int Int)) (k Int) (next_value Int) (prev_value Int)) Bool
  (and (> n 0) (> L 0) (<= 0 k) (<= k L)
       (prefix a k next_value)
       (suffix a k prev_value)))
"""
# Each test is an existential counterexample to a universal implication
# (or a positive witness for nonvacuity/mutant), using symbolic parameters.
OBLIGATIONS=[
 ("stage0_any_original_array", "unsat",
  "(and (> n 0) (> L 0) (not (prefix A 0 v)))"),
 ("stage_handoff_at_cursor_zero", "unsat",
  "(and (> n 0) (> L 0) (entire A w) (not (Inv A 0 v w)))"),
 ("atomic_correct_store_preserves_prefix_suffix", "unsat",
  "(and (Inv A i v w) (< i L) (not (Inv (store A (+ n i) v) (+ i 1) v w)))"),
 ("completed_stage_is_entire_new_value", "unsat",
  "(and (Inv A L v w) (not (entire A v)))"),
 ("final_read_respects_completed_stage", "unsat",
  "(and (> n 0) (> L 0) (<= 0 i) (< i L) (entire A v) "
     "(not (= (select A (+ n i)) v)))"),
 ("all_N_parameters_symbolic_nonvacuity", "sat",
  "(and (= n 1) (= L 3) (= i 1) (= v 43) (= w 42) "
    "(= A (store ((as const (Array Int Int)) 42) (+ n 0) 43)) "
    "(Inv A i v w))"),
 ("wrong_value_store_has_REAL_counterexample", "sat",
  "(and (= n 1) (= L 3) (= i 1) (= v 43) (= w 42) "
    "(= A (store ((as const (Array Int Int)) 42) (+ n 0) 43)) "
    "(Inv A i v w) "
    "(not (Inv (store A (+ n i) (+ v 1)) (+ i 1) v w)))")
]

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def run_proof(source:str,budget:int=10)->dict:
    with tempfile.NamedTemporaryFile("w",encoding="utf8",suffix=".smt2") as f:
        f.write(source);f.flush()
        start=time.perf_counter_ns()
        try:
            p=subprocess.run(["z3","-smt2","-T:"+str(budget),f.name],
                capture_output=True,text=True,timeout=budget+2,check=False)
        except subprocess.TimeoutExpired:
            return {"status":"TIMEOUT","wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
    answers=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    actual=answers[0] if len(answers)==1 and p.returncode==0 else "CHECKER_FAIL"
    return {"status":actual if actual in ("sat","unsat") else "CHECKER_FAIL",
       "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
       "solver_exit":p.returncode,"stdout_head":answers[:4],
       "stderr_tail":p.stderr[-250:]}

def execute(destination:Path)->dict:
    destination.mkdir(parents=True,exist_ok=True)
    results=[]
    for idx,(name,expected,claim) in enumerate(OBLIGATIONS):
        if name in ("all_N_parameters_symbolic_nonvacuity","wrong_value_store_has_REAL_counterexample"):
            pass
        elif expected!="unsat":raise ValueError("VALID_THEOREM_MUST_HAVE_NEGATED_COUNTEREXAMPLE_UNSAT")
        source=BASE+"(assert "+claim+")\n(check-sat)\n"
        path=destination/(f"{idx:02d}_{name}.smt2")
        path.write_text(source)
        r=run_proof(source)
        results.append({"lemma":name,"expected":expected,
            "verified":r["status"]==expected,
            "obligation_SMTSHA256":digest(source.encode()),
            "original_expression":claim,
            **r})
    audit={
       "schema":"neumann.g3.array-fill-all-N-inductive-conditional-theorem.v1",
       "science_scope":"PARAMETRIC_MATH_PROOF_NOT_NEURAL_Q3",
       "stage_count_symbolic_not_unrolled":True,
       "arbitrary_original_arrays_and_symbolic_integer_values":True,
       "number_of_native_universal_lemmas":5,
       "number_of_nonvacuity_and_wrong_rule_refutations":2,
       "all_valid_theorems_UNSAT_and_mutant_SAT":all(r["verified"] for r in results),
       "original_source_tasks_fetched":0,
       "no_neural_training":True,
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
       "lemmas":results
    }
    (destination/"G3-ARRAY-FILL-ALL-N-THEOREM.json").write_text(
        json.dumps(audit,indent=2,sort_keys=True)+"\n")
    return audit

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=execute(args.output)
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["all_valid_theorems_UNSAT_and_mutant_SAT"]:
        raise SystemExit(1)
