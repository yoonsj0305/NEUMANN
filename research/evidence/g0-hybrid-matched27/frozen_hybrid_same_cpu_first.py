"""G0 same-host original 27 matched Z3-only versus structural->Z3 hybrid.

PRE-REGISTERED: https://github.com/yoonsj0305/NEUMANN/issues/223
Already opened development source family. No new learned weights, Q1-Q7 remain OPEN.
Use frozen algorithms UNMODIFIED, by raw Git blob hash, from completed prior G0.
"""
import collections,hashlib,importlib.util,json,os,subprocess,sys,time,urllib.request
from pathlib import Path

OUT=Path("/tmp/g0_hybrid27_first_matched_allin_receipt.json")
SOURCE_COMMIT="7f993a017850ba547c6ea19a1bf3b54adf54a449"
SOURCE_FAMILY="20230328-sqrtmodinv-hoenicke"
SCRIPT_ROOT=Path("/tmp/g0_matched_hybrid_frozen_src")
SCRIPT_ROOT.mkdir(parents=True,exist_ok=True)
OLD_COMMIT_PROVER="c051985ceb216c5e2e3685e28c5f5a0e064850e2"
OLD_COMMIT_BASELINE="8908cee332c6984752be8edb8d0764ce3ea84312"
SOURCES={
  "one_shot_integer_polynomial_proof.py":(
     OLD_COMMIT_PROVER,
     "research/evidence/g0-newton-hoenicke27/one_shot_integer_polynomial_proof.py",
     "ff493a21b626733e2797487974388fa6e93b56ec"),
  "first_whole_27_z3_cvc5_comparator.py":(
     OLD_COMMIT_BASELINE,
     "research/evidence/g0-newton-hoenicke27/first_whole_27_z3_cvc5_comparator.py",
     "c60ba47adc8a0a9b811ee7318bf3599491075de9")}
EXPECTED_NAME_COUNT=27
EXPECTED_PAST_STATUS={"UNSAT_SOURCE_CERTIFICATES":4,"Z3_UNSAT_AT_3S":17}

def fetch(url,path):
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-G0-registered-same-host-hybrid"})
    with urllib.request.urlopen(req,timeout=45) as src,open(path,"wb") as dst:
        import shutil
        shutil.copyfileobj(src,dst)
    return Path(path).read_bytes()

def import_frozen(name,path):
    sp=importlib.util.spec_from_file_location(name,str(path))
    m=importlib.util.module_from_spec(sp)
    sys.modules[sp.name]=m
    sp.loader.exec_module(m)
    return m

def run_once():
    started=time.perf_counter()
    receipt={"status":"INCOMPLETE","preregistered_issue":223,
       "frozen_unmodified_sources":{k:{"commit":v[0],"path":v[1],"git_blob_sha1":v[2]} for k,v in SOURCES.items()},
       "source_commit":SOURCE_COMMIT,"original_source_family":SOURCE_FAMILY,
       "originals_required":27,"matched_one_host":True,
       "per_case_external_wall_limit_seconds":3.0,
       "original_task_gold_answers_not_used_to_solve":True,
       "no_model_inference_or_training":True,"no_gpu_or_paid_api":True,
       "G1":"HOLD_LEARNING","G2":"BLOCKED","Q1_Q7_GLOBAL":"OPEN","files":[]}
    def persist():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    persist()
    try:
        # Import and verify exact historical proof and comparison implementations.
        before_import=time.perf_counter()
        for filename,(sha,path,git_blob) in SOURCES.items():
            raw=fetch(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{sha}/{path}",
                      SCRIPT_ROOT/filename)
            found=subprocess.run(["git","hash-object",str(SCRIPT_ROOT/filename)],
                    text=True,capture_output=True,timeout=10,check=True).stdout.strip()
            if found!=git_blob:raise RuntimeError("FROZEN_PROGRAM_BLOB_CHANGED:"+filename)
            receipt.setdefault("downloaded_script_sha256",{})[filename]=hashlib.sha256(raw).hexdigest()
        M=import_frozen("g0_frozen_prover_original",SCRIPT_ROOT/"one_shot_integer_polynomial_proof.py")
        C=import_frozen("g0_frozen_classical_control",SCRIPT_ROOT/"first_whole_27_z3_cvc5_comparator.py")
        receipt["frozen_engine_fetch_plus_import_wall_seconds_conservatively_charged_to_hybrid"]=round(
            time.perf_counter()-before_import,6)
        if len(M.NAMES)!=EXPECTED_NAME_COUNT or C.M.NAMES!=M.NAMES:
            raise RuntimeError("FROZEN_ORIGINAL_NAME_LIST_DIVERGED")
        if M.SOURCE_COMMIT!=SOURCE_COMMIT:raise RuntimeError("ORIGINAL_SHA_DRIFT")
        from z3 import get_version_string
        if get_version_string()!="4.15.4":raise RuntimeError("Z3_WRONG_VERSION")
        receipt["z3_version"]=get_version_string()

        # Shared downloads up front: same exact unmodified raw input bytes for both arms.
        before_data=time.perf_counter()
        for fname in M.NAMES:
            path,raw=M.fetch(fname)
            assert fname==path.name
            if "(set-logic QF_NIA)" not in raw.decode("utf-8"):
                raise RuntimeError("SOURCE_QF_NIA_BAD_HEADER")
            receipt.setdefault("source_raw_sha256",{})[fname]=hashlib.sha256(raw).hexdigest()
        receipt["shared_source_download_wall_seconds"]=round(time.perf_counter()-before_data,6)
        receipt["shared_original_bytes"]=sum((M.WORK/f).stat().st_size for f in M.NAMES)

        # All 27 cases; alternate A/B order based only on pre-frozen original index.
        for index,name in enumerate(M.NAMES):
            path=M.WORK/name
            row={"filename":name,"source_sha256":receipt["source_raw_sha256"][name],
                 "comparison_order":"Z3_THEN_HYBRID" if index%2==0 else "HYBRID_THEN_Z3"}
            def baseline():
                begin=time.perf_counter()
                response=C.run([sys.executable,"-c",C.Z3,str(path)],index,"z3")
                return {
                 "raw_solver_status":response["answer"],
                 "external_wall_timeout":response["external_wall_timeout"],
                 "process_wall_seconds":response["wall_s"],
                 "rss_kib":response["peak_rss_kib"],
                 "baseline_workflow_wall_seconds":round(time.perf_counter()-begin,6)}
            def hybrid():
                begin=time.perf_counter()
                begin_proof=time.perf_counter()
                proof_error=None
                try: p=M.prove_one_original(path)
                except Exception as e:
                    p={"status":"STRUCTURE_ENGINE_ERROR"}
                    proof_error=type(e).__name__
                proof_elapsed=time.perf_counter()-begin_proof
                certified=p["status"]=="ORIGINAL_UNSAT_CERTIFIED"
                fallback=None
                if not certified:
                    fallback=C.run([sys.executable,"-c",C.Z3,str(path)],index,"z3")
                return {
                    "verified_original_unsat_certificate":certified,
                    "structural_proof_status":p["status"],
                    "proof_failure_type":proof_error,
                    "source_mathematical_certificate_method":p.get("method"),
                    "proof_and_independent_original_check_seconds":round(proof_elapsed,6),
                    "used_z3_fallback":fallback is not None,
                    "fallback_solver_raw_status":fallback["answer"] if fallback else None,
                    "fallback_z3_wall_seconds":fallback["wall_s"] if fallback else None,
                    "hybrid_total_case_wall_seconds":round(time.perf_counter()-begin,6),
                    "certified_or_solver_unsat_answer":certified or (fallback is not None and fallback["answer"]=="unsat")}
            if index%2==0:
                row["baseline_z3"]=baseline()
                row["hybrid"]=hybrid()
            else:
                row["hybrid"]=hybrid()
                row["baseline_z3"]=baseline()
            receipt["files"].append(row)
            persist()
        if len(receipt["files"])!=27:raise RuntimeError("NOT_ALL_SOURCE_FILES_SERVED")
        base=sum(r["baseline_z3"]["raw_solver_status"]=="unsat" for r in receipt["files"])
        hybr=sum(r["hybrid"]["certified_or_solver_unsat_answer"] for r in receipt["files"])
        certified=sum(r["hybrid"]["verified_original_unsat_certificate"] for r in receipt["files"])
        unique=sum(r["hybrid"]["verified_original_unsat_certificate"] and
                   r["baseline_z3"]["raw_solver_status"]!="unsat" for r in receipt["files"])
        base_wall=sum(r["baseline_z3"]["baseline_workflow_wall_seconds"] for r in receipt["files"])
        hybrid_wall=sum(r["hybrid"]["hybrid_total_case_wall_seconds"] for r in receipt["files"])
        hybrid_conservative_wall=(hybrid_wall+
            receipt["frozen_engine_fetch_plus_import_wall_seconds_conservatively_charged_to_hybrid"])
        wall_gate=hybrid_conservative_wall<=base_wall
        assert all(r["source_sha256"]==receipt["source_raw_sha256"][r["filename"]] for r in receipt["files"])
        receipt["summary"]={
          "z3_only_original_unsat_answers":base,
          "hybrid_verified_or_z3_unsat_answers":hybr,
          "standalone_source_mathematically_verified":certified,
          "genuine_extra_math_certificates_where_z3_noanswer":unique,
          "z3_only_measured_wall_s_excluding_shared_raw_source_download":round(base_wall,6),
          "hybrid_measured_27_cases_wall_s":round(hybrid_wall,6),
          "hybrid_conservative_wall_including_pinned_engine_fetch_and_import_s":round(hybrid_conservative_wall,6),
          "shared_original_download_wall_s":receipt["shared_source_download_wall_seconds"],
          "additional_accepted_answers":hybr-base,
          "accuracy_admission":hybr>base and unique>=1,
          "same_host_total_compute_wall_admission":wall_gate,
          "bounded_development_hybrid_gate": "PASS" if hybr>base and unique>=1 and wall_gate else "FAIL_OR_INCOMPLETE",
          "no_optimized_specialist_or_blind_generalization_claim":True}
        receipt["status"]="MATCHED_27_ORIGINAL_HYBRID_FIRST_DONE"
        receipt["entire_execution_wall_seconds"]=round(time.perf_counter()-started,6)
        persist()
        print("G0_HYBRID_27_MATCHED_FIRST",json.dumps(receipt["summary"],sort_keys=True),flush=True)
    except Exception as e:
        receipt["status"]="FIRST_HYBRID_MATCHED_EXECUTION_BLOCKED"
        receipt["first_failure_type"]=type(e).__name__
        receipt["first_failure_message"]=str(e)[:300]
        receipt["entire_execution_wall_seconds"]=round(time.perf_counter()-started,6)
        persist()
        print("G0_HYBRID_27_MATCHED_FIRST_FAILURE",receipt["first_failure_message"],flush=True)
        raise

if __name__=="__main__":run_once()
