"""Strict post-FIRST original native time comparator for N=5,8,9.

Original first learned? NO. The one-rule human-designed program was already
source-frozen and independently proved 3/3 original CHC families. This new
script never feeds its learned/generated invariants to Z3 or Eldarica.
Same original byte inputs and Git blobs, same GitHub runner class; only
comparable solver-process wall times, not human-development or training cost.
"""
from __future__ import annotations

import argparse,hashlib,json,re,subprocess,tempfile,time
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
SHA_FIRST="86cc31057e2fe96c412d39b5ff395ecde03aef9990df0df30ec63be6091c883a"
SOURCE="docs/experiments/G3_ARRAY_FILL_ONE_RULE_UNSEEN_N5_N8_N9_FIRST_PREREG_2026_11_06.json"
CONTRACT="docs/experiments/G3_ARRAY_FILL_POSTFIRST_NATIVE_COST_GATE_2026_11_06.json"

def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def blob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def run_engine(engine:str,exe:Path,body:bytes,seconds:int):
    with tempfile.NamedTemporaryFile("wb",suffix=".smt2") as file:
        file.write(body);file.flush()
        cmd=[str(exe),"-smt2","-T:"+str(seconds),file.name] if engine=="Z3" else [str(exe),file.name]
        begin=time.perf_counter_ns()
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=seconds+1)
        except subprocess.TimeoutExpired:
            return {"engine":engine,"status":"TIMEOUT",
                "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
                "cap_seconds":seconds}
    lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    status=(
      "SOURCE_OR_EXECUTION_ERROR" if p.returncode!=0 or any(x.lower().startswith("(error") for x in lines) else
      "SAT_CLAIM_NOT_INDEPENDENTLY_PROVEN" if lines==["sat"] else
      "UNSAT_CLAIM_NOT_INDEPENDENTLY_PROVEN" if lines==["unsat"] else
      "UNKNOWN_OR_NO_VERDICT")
    return {"engine":engine,"status":status,
       "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
       "cap_seconds":seconds,"process_exit":p.returncode,
       "stdout_excerpt":p.stdout[-450:],
       "stderr_tail":p.stderr[-350:],
       "stdout_SHA256":sha(p.stdout.encode())}

def original(ref:str,file:str,wantblob:str):
    url="https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/"+ref+"/quic3/data/"+file
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-matched-native-after-first"}),timeout=45) as r:
        body=r.read(25000)
    if blob(body)!=wantblob:
        raise ValueError("ORIGINAL_SOURCE_GIT_BLOB_CHANGED_"+file)
    return body

def run(first_path:Path,z3:Path,eld:Path):
    contract=json.loads((ROOT/CONTRACT).read_text())
    manifest=json.loads((ROOT/SOURCE).read_text())
    raw=first_path.read_bytes()
    if sha(raw)!=SHA_FIRST or contract["frozen_unseen_first"]["receipt_sha256"]!=SHA_FIRST:
        raise ValueError("ORIGINAL_UNSEEN_FIRST_RECEIPT_SHA_DRIFT")
    first=json.loads(raw)
    targets=manifest["unopened_heldout_transfer"]["selected_file_metadata_before_body"]
    if len(targets)!=3 or len(first["cases"])!=3:
        raise ValueError("BLIND_TEST_DENOMINATOR_DRIFT")
    if [x["file"] for x in targets]!=contract["specialist_baselines"]["target_n_3_exact"]:
        raise ValueError("REGISTERED_ORIGINAL_TARGET_NAMES_CHANGED")
    rows=[]
    for data,firstrow in zip(targets,first["cases"]):
        if data["file"]!=firstrow["source"] or data["git_blob"]!=firstrow["original_git_blob"]:
            raise ValueError("ORIGINAL_UNSEEN_FIRST_TASK_ORDER_OR_BLOB_CHANGED")
        if not firstrow["certified_original"]:
            raise ValueError("FIRST_FAILURE_CANNOT_BE_RELABELED_AS_SUCCESS")
        body=original(manifest["unopened_heldout_transfer"]["commit"],data["file"],data["git_blob"])
        if firstrow["source_sha256"]!=sha(body):
            raise ValueError("ORIGINAL_UNSEEN_SOURCE_BYTES_CHANGED")
        ref_ms=firstrow["total_wall_ms"]
        native=[run_engine("Z3",z3,body,15),run_engine("Eldarica",eld,body,20)]
        timeouts=[r for r in native if r["status"]=="TIMEOUT"]
        ratio=round(min(r["wall_ms"] for r in timeouts)/ref_ms,2) if timeouts and ref_ms>0 else None
        rows.append({"original_file":data["file"],"git_blob":data["git_blob"],
          "structural_first_all_original_clauses_unsat":True,
          "original_first_generated_rule_and_full_proof_wall_ms":ref_ms,
          "native":native,
          "observed_timeout_vs_rule_lower_bound_wall_ratio":ratio,
          "ratio_excludes_human_rule_development":True,
          "original_2025_native_verdict_not_a_proof_object":True})
    return {"schema":"neumann.g3.array-fill-three-unseen-postfirst-native-comparator.v1",
       "scope":"POSTFIRST_RAW_SOURCE_NATIVE_TIMING_VS_FROZEN_RULE_ORIGINAL_PROOF",
       "first_unseen_original_SHA256":SHA_FIRST,
       "no_generator_changes_or_neural_training":True,
       "cohort_original":len(rows),
       "per_instance_frozen_generator_proof_verified":sum(r["structural_first_all_original_clauses_unsat"] for r in rows),
       "native_z3_solved_original":sum(r["native"][0]["status"] in ("SAT_CLAIM_NOT_INDEPENDENTLY_PROVEN","UNSAT_CLAIM_NOT_INDEPENDENTLY_PROVEN") for r in rows),
       "native_eldarica_solved_original":sum(r["native"][1]["status"] in ("SAT_CLAIM_NOT_INDEPENDENTLY_PROVEN","UNSAT_CLAIM_NOT_INDEPENDENTLY_PROVEN") for r in rows),
       "all_in_10x_model_advantage":"NOT_PROVEN_HUMAN_RULE_DESIGN_COST_NOT_METERED",
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN","rows":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--first",type=Path,required=True)
    p.add_argument("--z3",type=Path,required=True)
    p.add_argument("--eld",type=Path,required=True)
    a=p.parse_args()
    try:print(json.dumps(run(a.first,a.z3,a.eld),indent=2,sort_keys=True))
    except Exception as e:
        print(json.dumps({"science_status":"POSTFIRST_NATIVE_COMPARISON_INFRA_FAILURE",
            "error":type(e).__name__+":"+str(e)[:250]}))
        raise SystemExit(2)
