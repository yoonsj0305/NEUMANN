"""Post-FIRST strong modern Z3 HORN baseline on exact pinned CHC-COMP 2025 Array8.

Uses official PyPI z3-solver 5.0.0.0 (2026), SolverFor("HORN").
Preserves original first 2025 Z3 4.8.12 results and selection. Every
native source is exactly the published SMT-LIB2 byte sequence.
No manually supplied invariants, learning, target selection, or label oracle.
A candidate SAT/UNSAT without original independent witness remains a CLAIM.
"""
from __future__ import annotations

import argparse,hashlib,json,re,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
CON=ROOT/"docs/experiments/G3_POSTFIRST_MODERN_Z3_5_NATIVE_ARRAY8_CONTRACT_2026_11_06.json"
ERR=ROOT/"docs/experiments/G3_SOURCEFREE_PREOPEN_ONE_GIT_BLOB_ERRATUM_2026_11_06.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def worker(filename:Path):
    import z3
    raw=filename.read_text(encoding="utf8")
    if not re.search(r"\(\s*set-logic\s+HORN\s*\)",raw):
        return {"status":"UNSUPPORTED_ORIGINAL_LOGIC","z3_version":z3.get_version_string()}
    s=z3.SolverFor("HORN")
    s.set(timeout=15000)
    try:
        s.from_string(raw)
        answer=s.check()
        result=str(answer)
        if result=="sat":state="SAT_CLAIM_UNVERIFIED"
        elif result=="unsat":state="UNSAT_CLAIM_UNVERIFIED"
        elif result=="unknown":state="UNKNOWN"
        else:state="NONDETERMINISTIC_UNKNOWN"
        try:
            reason=s.reason_unknown() if state=="UNKNOWN" else None
        except Exception:
            reason=None
        return {"status":state,"z3_version":z3.get_version_string(),
          "answer":result,"reason_unknown":reason}
    except Exception as err:
        return {"status":"SOURCE_OR_SOLVER_INTERFACE_FAILURE",
          "z3_version":z3.get_version_string(),
          "exception":type(err).__name__,"message":str(err)[:550]}

def run_one(data:bytes,cap_s:int=15):
    with tempfile.TemporaryDirectory(prefix="g3modern_z3_") as td:
        src=Path(td)/"original.smt2"
        src.write_bytes(data)
        start=time.perf_counter_ns()
        try:
            out=subprocess.run([sys.executable,"-m","research.g3.modern_z3_2026",
                      "--worker",str(src)],capture_output=True,text=True,
                     timeout=cap_s+3,check=False)
        except subprocess.TimeoutExpired:
            return {"status":"HARD_PROCESS_TIMEOUT",
                "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
                "cap_s":cap_s}
        wall=round((time.perf_counter_ns()-start)/1e6,3)
    try:
        result=json.loads(out.stdout.strip())
    except json.JSONDecodeError:
        return {"status":"NO_MACHINE_VERDICT","wall_ms":wall,
          "stdout_tail":out.stdout[-300:],"stderr_tail":out.stderr[-400:],
          "worker_exit":out.returncode,"cap_s":cap_s}
    if out.returncode!=0:
        result["status"]="WORKER_PROCESS_FAILED"
    result.update({"wall_ms":wall,"worker_exit":out.returncode,"cap_s":cap_s,
      "worker_stderr_tail":out.stderr[-250:]})
    return result

SYNTHETIC_SAFE=b"""(set-logic HORN)
(declare-fun I (Int) Bool)
(assert (forall ((n Int)) (=> (= n 0) (I n))))
(assert (forall ((n Int) (m Int)) (=> (and (I n) (= m (+ n 1))) (I m))))
(assert (forall ((n Int)) (=> (and (I n) (< n 0)) false)))
(check-sat)
"""

def synthetic_controls():
    safe=run_one(SYNTHETIC_SAFE,6)
    bad=run_one(SYNTHETIC_SAFE.replace(b"(< n 0)",b"(> n 0)"),6)
    return {"schema":"neumann.g3.modern-z3-sourcefree-HORN-control.v1",
      "safe":safe,"unsafe":bad,
      "controls_pass":safe["status"]=="SAT_CLAIM_UNVERIFIED" and
                     bad["status"]=="UNSAT_CLAIM_UNVERIFIED",
      "original_8_bodies_opened_by_this_control":False}

def fetch_exact(folder:str,target:dict,commit:str)->bytes:
    url=("https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/"
       +commit+"/"+folder+"/"+target["file"])
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-modern-Z3-2026-source-only"}),timeout=40) as r:
        raw=r.read(50000)
    if gitblob(raw)!=target["git_blob"]:
        raise ValueError("MODERN_NATIVE_ORIGINAL_GIT_BLOB_CHANGED_"+target["file"])
    return raw

def pilot():
    r=fetch_exact("extra-small-lia",{"file":"const_mod_1_000.smt2",
        "git_blob":"3f814a05b5e518c3a0bf18d3e67c22a50bd6a185"},
        "ddd279cab0717db6effe69baad451a8eb04ffd86")
    x=run_one(r,6)
    return {"pilot_source":"const_mod_1_000.smt2","not_in_registered_8":True,
       "source_git_blob":gitblob(r),"modern_Z3":x,
       "pilot_pass":x["status"]=="SAT_CLAIM_UNVERIFIED"}

def original_array8():
    reg=json.loads(PRE.read_text())
    contract=json.loads(CON.read_text())
    co=next(c for c in reg["cohorts"] if c["id"]=="ARRAY_CHC")
    if len(co["targets"])!=8 or co["folder"]!="quic3/data":
        raise ValueError("ORIGINAL_8_SOURCE_MANIFEST_DRIFT")
    if contract["source_first_ARRAY_sha256"]!="47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8":
        raise ValueError("PREVIOUS_FIRST_ORIGINAL_SHA_CHANGED")
    out=[]
    for target in co["targets"]:
        row={"file":target["file"],"original_git_blob":target["git_blob"]}
        try:
            raw=fetch_exact(co["folder"],target,reg["upstream"]["commit"])
            row["bytes"]=len(raw)
            row["original_source_sha256"]=sha(raw)
            row["solver"]=run_one(raw,15)
        except Exception as err:
            row["solver"]={"status":"SOURCE_OR_RUNTIME_ERROR",
               "message":type(err).__name__+":"+str(err)[:220]}
        out.append(row)
    if len(out)!=8:
        raise ValueError("ORIGINAL_ARRAY_DENOMINATOR_CHANGED")
    stats={
       "original_count":len(out),
       "native_SAT_claims":sum(r["solver"]["status"]=="SAT_CLAIM_UNVERIFIED" for r in out),
       "native_UNSAT_claims":sum(r["solver"]["status"]=="UNSAT_CLAIM_UNVERIFIED" for r in out),
       "native_UNKNOWN":sum(r["solver"]["status"] in ("UNKNOWN","HARD_PROCESS_TIMEOUT") for r in out),
       "source_or_engine_error":sum(r["solver"]["status"] in
             ("SOURCE_OR_SOLVER_INTERFACE_FAILURE","SOURCE_OR_RUNTIME_ERROR","WORKER_PROCESS_FAILED",
              "UNSUPPORTED_ORIGINAL_LOGIC","NO_MACHINE_VERDICT") for r in out),
       "neumann_student_trained":False,
       "original_ARC_eval_IDs_consumed":0
    }
    return {"schema":"neumann.g3.postfirst-modern-2026-z3-pypi-array8-native.v1",
      "science_status":"MODERN_NATIVE_CLASSICAL_ONLY_NOT_NEUMANN_LEARNED_RESULT",
      "previous_original_first_run":42174775254,
      "older_Z3_source_FIRST_sha256":contract["source_first_ARRAY_sha256"],
      "new_result_does_not_overwrite_first":True,
      "originals_previously_opened_in_2025_first":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "stats":stats,"rows":out}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--worker",type=Path)
    p.add_argument("--synthetic",action="store_true")
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--array8",action="store_true")
    args=p.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker),sort_keys=True))
        return 0
    if args.synthetic:
        x=synthetic_controls()
        print(json.dumps(x,indent=2,sort_keys=True))
        return 0 if x["controls_pass"] else 1
    if args.pilot:
        x=pilot()
        print(json.dumps(x,indent=2,sort_keys=True))
        return 0 if x["pilot_pass"] else 1
    if args.array8:
        print(json.dumps(original_array8(),indent=2,sort_keys=True))
        return 0
    raise ValueError("SELECT_SOURCE_FREE_OR_ORIGINAL_EXPERIMENT")

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"science_status":"G3_MODERN_Z3_INFRA_FAIL_CLOSED",
           "error":type(e).__name__+":"+str(e)[:260]}))
        raise SystemExit(2)
