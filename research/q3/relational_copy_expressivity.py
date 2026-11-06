"""Q3 expressivity barrier and the minimal cross-array COPY primitive.

This is a symbolic, source-free theorem battery. It proves that ANY predicate
that observes only a destination array cannot represent a relation to an
independently varying source array, even if that destination predicate has
arbitrarily complex constant comparisons. It then independently checks
induction for a new two-array quantified relation over symbolic indices.

NOT a learned invention, NOT proof of a specific source CHC benchmark, and
NOT evidence of whole-system 10x compute improvement.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

SCHEMA="neumann.q3.H0-one-array-vs-H1-two-array-copy-all-sizes.v1"

TYPED_RELATION = r"""
(set-logic AUFLIA)
(declare-const src (Array Int Int))
(declare-const dst (Array Int Int))
(declare-const n Int)
(declare-const m Int)
(declare-const i Int)
(declare-const lim Int)
(declare-const k Int)
(define-fun Prefix ((S (Array Int Int)) (D (Array Int Int))
                    (a Int) (b Int) (cursor Int)) Bool
  (forall ((j Int))
    (=> (and (<= 0 j) (< j cursor))
        (= (select D (+ a j)) (select S (+ b j))))))
"""

# Grounding n and m to 0 only for two H0 separation witnesses is valid:
# a single counterexample to universal equivalence disproves every H0(D).
H0_BASE=r"""
(set-logic AUFLIA)
(declare-const dst (Array Int Int))
(declare-const good_src (Array Int Int))
(declare-const bad_src (Array Int Int))
(declare-const p Bool)
(assert (= dst ((as const (Array Int Int)) 0)))
(assert (= good_src dst))
(assert (= bad_src (store dst 0 1)))
"""
# We deliberately use a Boolean p representing ANY destination-only formula
# on the fixed dst, as it must have the SAME value with either source.
# The target true-copy relation changes between the two source arrays.
OBLIGATIONS={
 "H0_DST_ONLY_CANNOT_EQUAL_CROSS_ARRAY_RELATION":("unsat",H0_BASE+r"""
(assert (= p (= (select dst 0) (select good_src 0))))
(assert (= p (= (select dst 0) (select bad_src 0))))
"""),
 "H0_NONVACUOUS_SOURCE_DISTINGUISHABILITY":("sat",H0_BASE+r"""
(assert (= (select dst 0) (select good_src 0)))
(assert (not (= (select dst 0) (select bad_src 0))))
"""),
 "H1_COPY_EMPTY_PREFIX_INIT":("unsat",TYPED_RELATION+r"""
(assert (> lim 0))
(assert (not (Prefix src dst n m 0)))
"""),
 "H1_COPY_ONE_STORE_PRESERVES_PREFIX":("unsat",TYPED_RELATION+r"""
(assert (> lim 0))
(assert (<= 0 i))
(assert (< i lim))
(assert (Prefix src dst n m i))
(assert (not (Prefix src
  (store dst (+ n i) (select src (+ m i)))
  n m (+ i 1))))
"""),
 "H1_COPY_UNTOUCHED_SUFFIX_FRAME":("unsat",TYPED_RELATION+r"""
(assert (> lim 0))
(assert (<= 0 i))
(assert (< i lim))
(assert (not
  (forall ((j Int))
    (=> (and (<= (+ i 1) j) (< j lim))
        (= (select (store dst (+ n i) (select src (+ m i))) (+ n j))
           (select dst (+ n j)))))))
"""),
 "H1_COPY_FULL_INTERVAL_AT_COMPLETION":("unsat",TYPED_RELATION+r"""
(assert (> lim 0))
(assert (<= 0 k))
(assert (< k lim))
(assert (Prefix src dst n m lim))
(assert (not (= (select dst (+ n k)) (select src (+ m k)))))
"""),
 "H1_COPY_NONVACUOUS_2_CELL_INSTANCE":("sat",TYPED_RELATION+r"""
(assert (= src ((as const (Array Int Int)) 3)))
(assert (= dst ((as const (Array Int Int)) 3)))
(assert (= lim 4))
(assert (= i 2))
(assert (Prefix src dst n m i))
"""),
 "H1_CORRUPTED_STORE_VALUE_HAS_REAL_COUNTEREXAMPLE":("sat",TYPED_RELATION+r"""
(assert (= n 0))
(assert (= m 0))
(assert (= i 0))
(assert (= lim 1))
(assert (= src ((as const (Array Int Int)) 0)))
(assert (= dst ((as const (Array Int Int)) 0)))
(assert (Prefix src dst n m i))
(assert (not (Prefix src
   (store dst (+ n i) (+ (select src (+ m i)) 1))
   n m (+ i 1))))
"""),
}


def run(out_dir:Path,seconds:float=7.0)->dict:
    if not shutil.which("z3"):
        raise RuntimeError("INDEPENDENT_Z3_CLI_REQUIRED")
    if out_dir.exists():
        raise ValueError("NO_OVERWRITE_FIRST_ORIGINAL_PROOF_RECEIPTS")
    out_dir.mkdir(parents=True)
    receipts=[]
    for name,(expected,part) in OBLIGATIONS.items():
        script=part+"\n(check-sat)\n"
        filename=out_dir/(name+".smt2")
        filename.write_text(script)
        begin=time.perf_counter_ns()
        try:
            completed=subprocess.run(["z3","-smt2",str(filename)],
                                     capture_output=True,text=True,timeout=seconds)
            tokens=[s.strip() for s in completed.stdout.splitlines() if s.strip()]
            actual=tokens[0] if completed.returncode==0 and len(tokens)==1 and tokens[0] in ("sat","unsat") else "UNKNOWN_OR_ENGINE_ERROR"
            stderr=completed.stderr[-300:]
            exitcode=completed.returncode
        except subprocess.TimeoutExpired:
            actual="TIMEOUT_NOT_PROOF";stderr="TIMEOUT";exitcode=None
        receipts.append({
            "proof_name":name,"expected":expected,"actual":actual,"pass":expected==actual,
            "smt2_sha256":hashlib.sha256(script.encode()).hexdigest(),
            "z3_exit":exitcode,"z3_stderr_tail":stderr,
            "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
            "is_genuine_counterexample":expected=="sat",
            "original_external_CHC_problem_solved":False
        })
    report={
        "schema":SCHEMA,
        "theorem_scope":"ONE_ARRAY_DEST_ONLY_CANNOT_REPRESENT_CROSS_ARRAY_COPY_FOR_ALL_SOURCE_ARRAYS",
        "new_operator":"COPY_PREFIX(src,dst,src_base,dst_base,cursor) with forall j [0,cursor): dst[dst_base+j]=src[src_base+j]",
        "operator_origin":"HUMAN_CONSTRUCTED_AND_Z3_CHECKED_NOT_OWNWEIGHT_GENERATED",
        "H0_expressivity_barrier_proven":receipts[0]["pass"] and receipts[1]["pass"],
        "H1_inductive_abstract_copy_under_explicit_premises_proven":all(x["pass"] for x in receipts[2:]),
        "theorems_total":len(receipts),
        "theorems_passed":sum(x["pass"] for x in receipts),
        "strong_native_verifier_used":"z3",
        "total_proof_wall_ms":round(sum(x["wall_ms"] for x in receipts),3),
        "direct_source_CHC_evaluation":"NOT_RUN",
        "trained_neural_student_evaluation":"NOT_RUN",
        "zero_new_ARC_eval_IDs":True,
        "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
        "receipts":receipts
    }
    (out_dir/"first_theorem_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if report["theorems_passed"]!=len(receipts):
        raise RuntimeError("H0_H1_PROOF_OBLIGATION_FAILED_OR_UNKNOWN")
    return report


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=run(args.out)
    print(json.dumps({k:v for k,v in result.items() if k!="receipts"},indent=2,sort_keys=True))
