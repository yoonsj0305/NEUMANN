"""Q6 after-FIRST compositional certificate.

The unchanged FIRST failed 7/9: string solver timed out proving a high-level
substring induction and Z3 returned an inconclusive array-finish query. We
retain FIRST unchanged. Avoid asking a general string solver to rediscover
a proof that factors through a strictly smaller representation.

Pointwise alpha(String)[k] = str.at(String,k), and each abstract array position
uses String of length 0 or 1. Prove string update implements store via the
unchanged original first commuting query, then prove the abstract store
preserves quantified prefix equality. Machine-verified transfer theorem is
SCOPED to pointwise observations, not an independent author's original source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

from research.q6.array_string_simulation import OBLIGATIONS

SCHEMA="neumann.q6.pointwise-commuting-compositional-transfer-postfirst-v1"
ABSTRACT_PREFIX=r"""
(set-logic AUFLIA)
(declare-const src (Array Int String))
(declare-const dst (Array Int String))
(declare-const next (Array Int String))
(declare-const i Int)
(declare-const j Int)
(declare-const n Int)
(define-fun Pfx ((s (Array Int String)) (d (Array Int String)) (c Int)) Bool
  (forall ((k Int)) (=> (and (<= 0 k) (< k c))
    (= (select s k) (select d k)))))
"""
CHECKS={
 "ABSTRACT_INIT":("unsat",ABSTRACT_PREFIX+r"""
 (assert (not (Pfx src dst 0)))"""),
 "ABSTRACT_STEP_COMPOSED_FROM_POINTWISE_STORE":("unsat",ABSTRACT_PREFIX+r"""
 (assert (<= 0 i)) (assert (< i n))
 (assert (Pfx src dst i))
 (assert (= next (store dst i (select src i))))
 (assert (<= 0 j)) (assert (< j (+ i 1)))
 (assert (not (= (select next j) (select src j))))"""),
 "ABSTRACT_FINISH_WITH_GROUND_INDEX":("unsat",ABSTRACT_PREFIX+r"""
 (assert (<= 0 j)) (assert (< j n))
 (assert (Pfx src dst n))
 (assert (not (= (select dst j) (select src j))))"""),
 # This cross-theory commuting formula is copied unmodified from the frozen
 # FIRST script, no weakening to obtain an easy proof.
 "STRING_TO_ARRAY_STORE_COMMUTES":OBLIGATIONS["ALPHA_STORE_COMMUTING_POINTWISE"],
 "STRING_SAME_LENGTH_EQUAL_PREFIX_FINISH":OBLIGATIONS["STRING_FINISH"],
 "CORRUPTED_REAL_STRING_UPDATE_WITNESS":OBLIGATIONS["CORRUPTED_WRITE_HAS_COUNTEREXAMPLE"]
}

def run(out:Path):
    if out.exists():raise ValueError("DO_NOT_OVERWRITE_AFTERFIRST_COMPOSITION")
    if not shutil.which("z3"):raise RuntimeError("Z3_INDEPENDENT_REQUIRED")
    out.mkdir(parents=True)
    items=[]
    for key,(expect,body) in CHECKS.items():
        script=body+"\n(check-sat)\n"
        (out/(key+".smt2")).write_text(script)
        begin=time.perf_counter_ns()
        try:
            p=subprocess.run(["z3","-smt2","-in"],input=script,text=True,
                capture_output=True,timeout=9)
            output=[x.strip() for x in p.stdout.splitlines() if x.strip()]
            verdict=output[0] if p.returncode==0 and output in (["sat"],["unsat"]) else "UNKNOWN"
            stderr=p.stderr[-240:]
        except subprocess.TimeoutExpired:
            verdict="TIMEOUT";stderr="TIMEOUT"
        items.append({"name":key,"expected":expect,"observed":verdict,
           "pass":verdict==expect,
           "script_sha256":hashlib.sha256(script.encode()).hexdigest(),
           "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
           "stderr":stderr})
    report={
      "schema":SCHEMA,
      "frozen_original_first_run":42322134104,
      "frozen_original_first_status":"FAIL_7_OF_9",
      "proof_mode":"COMPOSITION_OF_SEPARATELY_PROVED_ABSTRACT_STEP_AND_STRING_POINTWISE_STORE_SIMULATION",
      "checks":len(items),"passed":sum(r["pass"] for r in items),
      "total_z3_process_ms":round(sum(r["wall_ms"] for r in items),3),
      "human_defined_abstraction":True,"model_inference_calls":0,
      "external_original_tasks":0,"new_learning":False,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "receipts":items}
    (out/"POSTFIRST_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="receipts"},sort_keys=True,indent=2))
    print(json.dumps([{"name":r["name"],"verdict":r["observed"]} for r in items],indent=2))
    if report["passed"]!=len(items):
        raise RuntimeError("COMPOSITIONAL_TRANSFER_UNPROVEN_KEEP_OPEN")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    run(p.parse_args().out)
