"""G3 native strong classical source-first screen, 2025 CHC-COMP.

Input source and Git blobs precommitted before inspecting these 24 original
bodies. Exactly eight each from three independent mathematical theories.
We only fetch original source and run the externally published unchanged
SMT-LIB2/HORN task through actual Z3 and cvc5. No learned NEUMANN run.

Both solver outputs are *claims* until official competition verdict/alternate
checker corroborates them. Unknown and timeouts ≠ unsolvable. Parsing errors
≠ native capability gaps. The original denominator is never filtered.
"""
from __future__ import annotations

import argparse,hashlib,json,re,subprocess,tempfile,sys,time
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"

def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def gitblob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def native_command(engine:str,file:str,cap_s:int):
    if engine=="Z3":
        return ["z3","-smt2","-T:"+str(cap_s),file]
    if engine=="CVC5":
        return ["cvc5","--lang=smt2","--tlimit-per="+str(cap_s*1000),file]
    raise ValueError("UNKNOWN_NAMED_NATIVE_ENGINE")

def one_engine(engine:str,content:bytes,cap_s:int=15)->dict:
    with tempfile.TemporaryDirectory(prefix="g3_2025_chc_") as tmp:
        file=str(Path(tmp)/"original-chc.smt2")
        Path(file).write_bytes(content)
        start=time.perf_counter_ns()
        try:
            run=subprocess.run(native_command(engine,file,cap_s),
                capture_output=True,text=True,timeout=cap_s+2,check=False)
        except subprocess.TimeoutExpired:
            return {"engine":engine,"status":"TIMEOUT",
                "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
                "budget_seconds":cap_s}
    t=round((time.perf_counter_ns()-start)/1e6,3)
    lines=[line.strip() for line in run.stdout.splitlines() if line.strip()]
    # SMT-LIB Horn "sat" means the Horn clauses are consistent.
    # "unsat" means inconsistency, *not* that a model was synthesized.
    first=lines[0] if lines else ""
    has_error=(run.returncode!=0 or any(line.lower().startswith("(error") for line in lines))
    status=("PARSE_OR_EXEC_ERROR" if has_error else
            "SAT_CLAIM_UNVERIFIED" if first=="sat" else
            "UNSAT_CLAIM_UNVERIFIED" if first=="unsat" else
            "UNKNOWN" if first=="unknown" else
            "NO_GROUNDED_VERDICT")
    return {
      "engine":engine,"status":status,"process_exit":run.returncode,
      "wall_ms":t,"budget_seconds":cap_s,
      "stdout_sha256":sha(run.stdout.encode()),
      "stdout_head":lines[:8],"stderr_tail":run.stderr[-400:]
    }

def source_probe(path:str,ref:str,entry:dict,cohort:str,cap:int=15)->dict:
    url="https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/"+ref+"/"+path+"/"+entry["file"]
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-original-source-blind-2025"}),timeout=40) as r:
        data=r.read(50000)
    got=gitblob(data)
    if got!=entry["git_blob"]:
        raise ValueError("EXTERNAL_CHCCOMP_SOURCE_GIT_BLOB_CHANGED_"+entry["file"])
    text=data.decode("utf-8")
    row={"cohort":cohort,"file":entry["file"],"git_blob":got,"source_bytes":len(data),
         "original_source_sha256":sha(data)}
    if not re.search(r"\(\s*check-sat\s*\)",text) or not re.search(r"\(\s*set-logic\s+HORN\s*\)",text):
        row.update({"status":"UNSUPPORTED_ORIGINAL_SOURCE_FORMAT",
            "reason":"NO_HORN_CHECK_SAT","native":[]})
        return row
    # Unmodified original source, independent strong native solvers.
    a=one_engine("Z3",data,cap)
    b=one_engine("CVC5",data,cap)
    row["native"]=[a,b]
    good=[x for x in [a,b] if x["status"] in ("SAT_CLAIM_UNVERIFIED","UNSAT_CLAIM_UNVERIFIED")]
    if len(good)==2 and good[0]["status"]!=good[1]["status"]:
        status="CONTRADICTORY_NATIVE_OUTCOMES_REQUIRE_EXTERNAL_ARBITRATION"
    elif len(good)>=1:
        status="AT_LEAST_ONE_NATIVE_GROUNDED_CLAIM_NOT_YET_INDEPENDENTLY_CERTIFIED"
    else:
        status="NO_NATIVE_GROUNDED_VERDICT_WITHIN_BUDGET"
    row["status"]=status
    row["claimed_satisfiable"]=(good[0]["status"]=="SAT_CLAIM_UNVERIFIED") if good else None
    row["cannot_infer_native_unsolvability"]=True
    row["source_verdict_independently_validated"]=False
    return row

def source_free_synthetic_controls()->dict:
    good=b"""(set-logic HORN)
(declare-fun Inv (Int) Bool)
(assert (forall ((x Int)) (=> (= x 0) (Inv x))))
(assert (forall ((x Int) (y Int)) (=> (and (Inv x) (= y (+ x 1))) (Inv y))))
(assert (forall ((x Int)) (=> (and (Inv x) (< x 0)) false)))
(check-sat)
"""
    unsafe=good.replace(b"(< x 0)",b"(> x 0)")
    zsafe=one_engine("Z3",good,6)
    zunsafe=one_engine("Z3",unsafe,6)
    cvsafe=one_engine("CVC5",good,6)
    cvunsafe=one_engine("CVC5",unsafe,6)
    # External source is NEVER opened in this stage.
    pass_synthetic=(zsafe["status"]=="SAT_CLAIM_UNVERIFIED" and
           zunsafe["status"]=="UNSAT_CLAIM_UNVERIFIED")
    return {"schema":"neumann.g3.sourcefree.synthetic-HORN-two-natives.v1",
       "Z3_safe":zsafe,"Z3_unsafe":zunsafe,
       "CVC5_safe":cvsafe,"CVC5_unsafe":cvunsafe,
       "sourcefree_Z3_semantic_controls_pass":pass_synthetic,
       "no_original_task_bodies_read":True}

def run_cohort(name:str):
    reg=json.loads(P.read_text())
    if len(reg["cohorts"])!=3 or sum(len(c["targets"]) for c in reg["cohorts"])!=24:
        raise ValueError("G3_SOURCE_MANIFEST_DENOMINATOR_CHANGED")
    c=next(x for x in reg["cohorts"] if x["id"]==name)
    if len(c["targets"])!=8:raise ValueError("G3_GROUP_N_CHANGED")
    rows=[]
    for item in c["targets"]:
        try:
            out=source_probe(c["folder"],reg["upstream"]["commit"],item,name,15)
        except Exception as error:
            out={"cohort":name,"file":item["file"],"original_expected_git_blob":item["git_blob"],
                "status":"SOURCE_ACCESS_OR_INFRA_FAIL_CLOSED",
                "error":type(error).__name__+":"+str(error)[:180],
                "source_verdict_independently_validated":False,
                "native":[]}
        rows.append(out)
    if len(rows)!=8:raise ValueError("G3_ORIGINAL_TOTAL_CHANGES")
    stats={
      "original_denominator":len(rows),
      "Z3_grounded_claim":sum(any(n["engine"]=="Z3" and n["status"] in ("SAT_CLAIM_UNVERIFIED","UNSAT_CLAIM_UNVERIFIED") for n in r["native"]) for r in rows),
      "CVC5_grounded_claim":sum(any(n["engine"]=="CVC5" and n["status"] in ("SAT_CLAIM_UNVERIFIED","UNSAT_CLAIM_UNVERIFIED") for n in r["native"]) for r in rows),
      "both_native_no_grounded_claim":sum(r["status"]=="NO_NATIVE_GROUNDED_VERDICT_WITHIN_BUDGET" for r in rows),
      "contradictory_native_outcomes":sum(r["status"]=="CONTRADICTORY_NATIVE_OUTCOMES_REQUIRE_EXTERNAL_ARBITRATION" for r in rows),
      "source_infra_or_unsupported":sum(r["status"] in ("SOURCE_ACCESS_OR_INFRA_FAIL_CLOSED","UNSUPPORTED_ORIGINAL_SOURCE_FORMAT") for r in rows),
      "one_or_both_native_genuine_source_verdicts_independently_certified":0,
      "student_training_runs":0,
      "ARC_public_eval_new_IDs":0,
    }
    return {"schema":"neumann.q3.g3.chccomp2025.24-native-source-original-first.v1",
      "cohort":name,"first_original_denominator":8,
      "science_status":"NATIVE_RAW_CLAIM_FIRST_NEEDS_OFFICIAL_VERDICT_AND_ORIGINAL_SOURCE_AUDIT",
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "stats":stats,"rows":rows}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cohort",choices=["LIA_MULTIPHASE","ARRAY_CHC","ADT_CHC"])
    parser.add_argument("--synthetic",action="store_true")
    parser.add_argument("--pilot",action="store_true")
    x=parser.parse_args()
    if x.synthetic:
        y=source_free_synthetic_controls()
        print(json.dumps(y,indent=2,sort_keys=True))
        return 0 if y["sourcefree_Z3_semantic_controls_pass"] else 1
    if x.pilot:
        p=source_probe("extra-small-lia",
            "ddd279cab0717db6effe69baad451a8eb04ffd86",
            {"file":"const_mod_1_000.smt2","git_blob":"3f814a05b5e518c3a0bf18d3e67c22a50bd6a185"},
            "NONSELECTED_FORMAT_PILOT",6)
        print(json.dumps(p,indent=2,sort_keys=True))
        return 0 if p["status"] not in ("UNSUPPORTED_ORIGINAL_SOURCE_FORMAT","SOURCE_ACCESS_OR_INFRA_FAIL_CLOSED") else 1
    if not x.cohort:raise ValueError("COHORT_REQUIRED")
    print(json.dumps(run_cohort(x.cohort),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as ex:
        print(json.dumps({"science_status":"G3_INFRA_FAIL_CLOSED_NOT_NATIVE_CEILING",
          "error":type(ex).__name__+":"+str(ex)[:250]}))
        raise SystemExit(2)
