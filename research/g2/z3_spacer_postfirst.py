"""Post-FIRST existing STRONG classical alternate: Z3 Spacer over original SyGuS INV.

We do not run NEUMANN model or reuse prior manually derived invariants.
Convert original Pre,Trans,Post specs into universally quantified CHC rules:
Pre(s) => I(s), I(s) & Trans(s,s') => I(s'), I(s) & !Post(s) => BAD.
SPACER query BAD: UNSAT certifies source safety under all reachable states,
SAT means reachability of BAD if fixedpoint can soundly solve.
UNKNOWN and timeout are NOT declared unsolvable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request,urlopen

from research.g2.postfirst_three_analytic_source_proofs import original_semantics

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/experiments/G2_POSTFIRST_Z3_SPACER_ALL12_NATIVE_COMPARATOR_CONTRACT_2026_11_06.json"
REG=ROOT/"docs/experiments/G2_NATIVE_RESIDUAL_24_SOURCE_METADATA_FIRST_PREREG_2026_11_06.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def horn(original:str)->str:
    spec=original_semantics(original)
    args=spec["names"]
    primed=[a+"!" for a in args]
    def call(name,ps):
        return "("+name+" "+" ".join(ps)+")"
    names="\n".join("(declare-var "+a+" Int)" for a in args+primed)
    definitions="\n".join(spec["definitions"])
    invariant="Inv"
    arg_sorts=" ".join("Int" for _ in args)
    rules=[
      "(rule (=> "+call(spec["pre"],args)+" "+call(invariant,args)+"))",
      "(rule (=> (and "+call(invariant,args)+" "+
        call(spec["trans"],args+primed)+") "+call(invariant,primed)+"))",
      "(rule (=> (and "+call(invariant,args)+
        " (not "+call(spec["post"],args)+")) Bad))"
    ]
    return (
       "(set-logic HORN)\n"
       "(set-option :fixedpoint.engine spacer)\n"+
       definitions+"\n"+
       "(declare-rel Inv ("+arg_sorts+"))\n"+
       "(declare-rel Bad ())\n"+names+"\n"+
       "\n".join(rules)+"\n(query Bad)\n"
    )

def run_z3(script:str,timeout:int=15)->dict:
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf8") as out:
        out.write(script);out.flush()
        start=time.perf_counter_ns()
        try:
            p=subprocess.run(["z3","-smt2",f"-T:{timeout}",out.name],
                 capture_output=True,text=True,timeout=timeout+3)
        except subprocess.TimeoutExpired:
            return {"status":"BUDGET_TIMEOUT","wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
    stdout=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    first=stdout[0] if stdout else None
    answer=("SAFE_UNSAT" if p.returncode==0 and first=="unsat" else
         "UNSAFE_SAT" if p.returncode==0 and first=="sat" else
         "UNKNOWN_OR_SOURCE_ERROR")
    return {"status":answer,
      "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
      "exit":p.returncode,
      "answer_head":stdout[:4],
      "stderr_tail":p.stderr[-450:],
      "stdout_sha256":sha(p.stdout.encode())}

def synthetic_controls():
    safe="""(set-logic LIA)
    (synth-inv inv-f ((x Int)))
    (declare-primed-var x Int)
    (define-fun pre-f ((x Int)) Bool (= x 0))
    (define-fun trans-f ((x Int) (x! Int)) Bool (= x! (+ x 1)))
    (define-fun post-f ((x Int)) Bool (>= x 0))
    (inv-constraint inv-f pre-f trans-f post-f)
    (check-synth)
    """
    unsafe=safe.replace("(>= x 0)","(<= x 0)")
    a=run_z3(horn(safe),8)
    b=run_z3(horn(unsafe),8)
    return {"safe":a,"unsafe":b,
       "controls_pass":a["status"]=="SAFE_UNSAT" and b["status"]=="UNSAFE_SAT"}

def original_all():
    c=json.loads(CONTRACT.read_text())
    reg=json.loads(REG.read_text())
    if c["original_denominator"]!=12:raise ValueError("PRECOMMITTED_N_CHANGED")
    inv=next(x for x in reg["cohorts"] if x["id"]=="INV_INDUCTION")
    if len(inv["targets"])!=12:raise ValueError("INV_MANIFEST_CHANGED")
    results=[]
    for entry in inv["targets"]:
        url="https://raw.githubusercontent.com/"+reg["original"]["repo"]+"/"+reg["original"]["commit"]+"/"+inv["folder"]+"/"+entry["file"]
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G2-independent-Spacer"}),timeout=45) as r:
            original_bytes=r.read(20000)
        if gitblob(original_bytes)!=entry["git_blob"]:
            raise ValueError("EXTERNAL_ORIGINAL_SOURCE_BLOB_DRIFT_"+entry["file"])
        row={"name":entry["file"],"git_blob":entry["git_blob"],
             "source_bytes":len(original_bytes)}
        try:
            script=horn(original_bytes.decode("utf8"))
            row["CHC_source_sha256"]=sha(script.encode())
            row["native_SPACER"]=run_z3(script,15)
            row["status"]=row["native_SPACER"]["status"]
        except Exception as e:
            row.update({"status":"INFRA_OR_UNSUPPORTED_SOURCE",
                "detail":type(e).__name__+":"+str(e)[:220]})
        results.append(row)
    if len(results)!=12:raise ValueError("12_ORIGINAL_FIRST_SOURCE_DENOMINATOR_DRIFT")
    stats={
       "original_registered":12,
       "safe_proven_by_Z3_Spacer":sum(r["status"]=="SAFE_UNSAT" for r in results),
       "unsafe_detected_by_Z3_Spacer":sum(r["status"]=="UNSAFE_SAT" for r in results),
       "UNKNOWN_OR_TIMEOUT":sum(r["status"] in ("UNKNOWN_OR_SOURCE_ERROR","BUDGET_TIMEOUT") for r in results),
       "unsupported":sum(r["status"]=="INFRA_OR_UNSUPPORTED_SOURCE" for r in results),
       "original_arc_eval_IDs_used":0,
       "training_runs":0}
    return {"schema":"neumann.q3.g2.postfirst-native-z3-spacer-all12.v1",
      "science_status":"POSTFIRST_STRONGER_NATIVE_CLASSICAL_COMPARATOR_ONLY",
      "engine":"real Z3 Spacer in QF LIA CHC",
      "original_12_already_exposed":True,
      "not_equal_rights_neumann_cost_or_novelty":True,
      "stats":stats,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "rows":results}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--synthetic",action="store_true")
    a=parser.parse_args()
    if a.synthetic:
        outcome=synthetic_controls()
        print(json.dumps(outcome,indent=2,sort_keys=True))
        return 0 if outcome["controls_pass"] else 1
    print(json.dumps(original_all(),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"science_status":"Z3_CHC_INFRASTRUCTURE_FAIL_CLOSED",
            "error":type(e).__name__+":"+str(e)[:250]}))
        raise SystemExit(2)
