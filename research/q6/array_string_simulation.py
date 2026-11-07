"""Source-free cross-theory simulation certificate: Int arrays -> Unicode strings.

Map a finite string x to the abstract index-observation array
alpha(x)[j] := str.at(x, j), for 0<=j<len(x).  Check in Z3 that replacing
position i in a string is observationally equivalent to store(alpha(d),i,at(s,i)),
and check independent array/string copy prefix induction and wrong-step SAT.

This is a HUMAN-SPECIFIED abstraction and human-created semantics; it does
NOT demonstrate a learned Q6 transfer, even on PASS. Never opens original CHC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

SCHEMA="neumann.q6.array-string-pointwise-simulation-sourcefree-v1"

ARRAY=r"""
(set-logic AUFLIA)
(declare-const src (Array Int Int))
(declare-const dst (Array Int Int))
(declare-const i Int)
(declare-const n Int)
(define-fun Prefix ((s (Array Int Int)) (d (Array Int Int)) (c Int)) Bool
  (forall ((j Int)) (=> (and (<= 0 j) (< j c))
    (= (select s j) (select d j)))))
"""

STRING=r"""
(set-logic ALL)
(declare-const src String)
(declare-const dst String)
(declare-const i Int)
(declare-const j Int)
(declare-const n Int)
(assert (= n (str.len src)))
(assert (= n (str.len dst)))
(define-fun next () String
 (str.++ (str.substr dst 0 i) (str.at src i)
          (str.substr dst (+ i 1) (- n (+ i 1)))))
(define-fun Prefix ((s String) (d String) (c Int)) Bool
 (= (str.substr s 0 c) (str.substr d 0 c)))
"""

# These are explicit *counterexample queries*.  UNSAT establishes the
# conditional property, SAT establishes a genuine negative/witness example.
OBLIGATIONS={
 "ARRAY_EMPTY_PREFIX":("unsat",ARRAY+r"""
 (assert (not (Prefix src dst 0)))"""),
 "ARRAY_INDUCTIVE_STORE":("unsat",ARRAY+r"""
 (assert (<= 0 i)) (assert (< i n))
 (assert (Prefix src dst i))
 (assert (not (Prefix src (store dst i (select src i)) (+ i 1))))"""),
 "ARRAY_FINISH":("unsat",ARRAY+r"""
 (assert (<= 0 j)) (assert (< j n))
 (assert (Prefix src dst n))
 (assert (not (= (select dst j) (select src j))))"""),
 "STRING_EMPTY_PREFIX":("unsat",STRING+r"""
 (assert (not (Prefix src dst 0)))"""),
 "STRING_ONE_REPLACEMENT_STEP":("unsat",STRING+r"""
 (assert (<= 0 i)) (assert (< i n))
 (assert (Prefix src dst i))
 (assert (not (Prefix src next (+ i 1))))"""),
 "STRING_FINISH":("unsat",STRING+r"""
 (assert (Prefix src dst n))
 (assert (not (= src dst)))"""),
 "ALPHA_STORE_COMMUTING_POINTWISE":("unsat",STRING+r"""
 (assert (<= 0 i)) (assert (< i n))
 (assert (<= 0 j)) (assert (< j n))
 (assert (not
  (= (str.at next j)
     (ite (= j i) (str.at src i) (str.at dst j)))))"""),
 "NONVACUOUS_REPLACEMENT":("sat",STRING+r"""
 (assert (= src "ab")) (assert (= dst "xy"))
 (assert (= i 0))
 (assert (= next "ay"))"""),
 "CORRUPTED_WRITE_HAS_COUNTEREXAMPLE":("sat",STRING+r"""
 (assert (= src "b")) (assert (= dst "x"))
 (assert (= i 0))
 (assert (Prefix src dst 0))
 (assert (not
  (Prefix src
   (str.++ (str.substr dst 0 i) "a"
           (str.substr dst (+ i 1) (- n (+ i 1))))
   (+ i 1))))""")
}


def query(script,cap_s=8):
    start=time.perf_counter_ns()
    try:
        p=subprocess.run(["z3","-smt2","-in"],input=script+"\n(check-sat)\n",
                text=True,capture_output=True,timeout=cap_s)
        lines=[r.strip() for r in p.stdout.splitlines() if r.strip()]
        verdict=lines[0] if p.returncode==0 and lines in (["sat"],["unsat"]) else "UNKNOWN_OR_CHECKER_ERROR"
        tail=p.stderr[-300:]
    except subprocess.TimeoutExpired:
        verdict="TIMEOUT_NOT_PROOF";tail="TIMEOUT"
    return verdict,round((time.perf_counter_ns()-start)/1e6,3),tail


def run(out_dir:Path):
    if out_dir.exists():raise ValueError("NO_OVERWRITE_FIRST")
    if not shutil.which("z3"):raise RuntimeError("INDEPENDENT_Z3_REQUIRED")
    out_dir.mkdir(parents=True)
    rows=[]
    for name,(expected,body) in OBLIGATIONS.items():
        script=body+"\n(check-sat)\n"
        (out_dir/(name+".smt2")).write_text(script)
        observed,wall,err=query(body)
        rows.append({"obligation":name,"expected":expected,"observed":observed,
           "passed":expected==observed,"wall_ms":wall,
           "query_sha256":hashlib.sha256(script.encode()).hexdigest(),
           "stderr_tail":err})
    report={"schema":SCHEMA,"obligations":len(rows),
       "passed":sum(x["passed"] for x in rows),
       "total_solver_process_ms":round(sum(x["wall_ms"] for x in rows),3),
       "cross_theory":"Array Int Int vs String substr/at/concat",
       "abstraction":"human-designed alpha(x)[j]=str.at(x,j), 0<=j<len(x)",
       "abstraction_machine_checked_pointwise":
         next(x for x in rows if x["obligation"]=="ALPHA_STORE_COMMUTING_POINTWISE")["passed"],
       "weights_trained":False,
       "autonomous_operator_invention":False,
       "new_independent_author_originals_solved":0,
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
       "receipts":rows}
    (out_dir/"FIRST_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="receipts"},indent=2,sort_keys=True))
    print(json.dumps([{"id":x["obligation"],"result":x["observed"],"expected":x["expected"]} for x in rows],indent=2))
    if report["passed"]!=len(rows):raise RuntimeError("SOURCEFREE_CROSS_THEORY_UNPROVEN_KEEP_OPEN")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    run(p.parse_args().out)
