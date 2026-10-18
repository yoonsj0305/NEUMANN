"""R1 G0 LAST prospectively frozen source-family transfer: Elster 2025 ALL NINE.

Issue #224 prereg BEFORE any new source body viewed. Exact existing Newton
integer-polynomial proof code loaded by historic Git blob. No learned model.
This is an independent source-family test and a research DECISION gate.
"""
import collections,hashlib,json,re,subprocess,sys,time,urllib.request,importlib.util
from pathlib import Path

ORG="SMT-LIB/benchmark-submission-2025"
SRC_SHA="37c6cd5d98edb46057f30cef35ba7c7250fe0161"
FAMILY="20250331-elster"
FROZEN={
"A_1.smt2":"d6d20f10f78e2060d7037fd5493425cc3d820587",
"B_1.smt2":"62d505ab915f7cf51f563e053552feaf50268dfe",
"B_2.smt2":"c9714bb59597ebb4e218c0c3d1ccb53700a550c7",
"C_1.smt2":"e4e1ae1731d533117f1c3b761b121ef0775f40b9",
"C_2.smt2":"b806486b03f136a02f10b7a78ddccf882544e740",
"D_1.smt2":"76289b3309508128ebd15e30207f85af739f4f93",
"D_2.smt2":"6c7f4a9d3f71687cb2b6a79185ead71eaf877628",
"E_1.smt2":"20422aba0dd9ca634833b857f8ec0123a4abd190",
"E_2.smt2":"bc25ca78c39c86e159bac59b01d29b08297889a3"}
ORIG_BASE=(f"https://raw.githubusercontent.com/{ORG}/{SRC_SHA}/"
           f"non-incremental/QF_NIA/{FAMILY}/")
PROOF_COMMIT="c051985ceb216c5e2e3685e28c5f5a0e064850e2"
PROOF_PATH="research/evidence/g0-newton-hoenicke27/one_shot_integer_polynomial_proof.py"
PROOF_BLOB="ff493a21b626733e2797487974388fa6e93b56ec"
ROOT=Path("/tmp/r1_g0_elster9_final")
ROOT.mkdir(exist_ok=True,parents=True)
OUT=Path("/tmp/r1_g0_elster9_final_receipt.json")
MAX_Z3_WALL=3
MAX_CVC5_WALL=3
MAX_PROOF_WALL=4
Z3_RUN=r"""
import json,sys,z3
try:
 p=sys.argv[1];s=z3.Solver();s.from_file(p);s.set(timeout=2700)
 ans=s.check()
 print(json.dumps({"answer":str(ans),"reason":s.reason_unknown()[:90] if ans==z3.unknown else ""}))
except Exception as exc:
 print(json.dumps({"answer":"ERROR","error_type":type(exc).__name__}))
"""
PROOF_RUN=r"""
import json,sys,z3,importlib.util
p=sys.argv[1];src=sys.argv[2]
try:
 spec=importlib.util.spec_from_file_location("frozen_original_source",src)
 m=importlib.util.module_from_spec(spec)
 sys.modules[spec.name]=m;spec.loader.exec_module(m)
 receipt=m.prove_one_original(p)
 certified=(receipt.get("status")=="ORIGINAL_UNSAT_CERTIFIED" and
     receipt.get("independent_original_plus_proven_lemma")=="unsat" and
     receipt.get("no_source_assertion_removed") is True)
 print(json.dumps({"status":receipt.get("status"),
          "original_unsat_independently_certified":certified,
          "method":receipt.get("method"),"source_assertions":receipt.get("original_assertions"),
          "eligible_negative_mod_eq1_targets":receipt.get("eligible_negative_mod_eq1_targets")}))
except Exception as exc:
 print(json.dumps({"status":"PROOF_ERROR","original_unsat_independently_certified":False,
                   "error_type":type(exc).__name__}))
"""

def download(url,path):
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-FASTCLOSE-final-frozen-elster9"})
    with urllib.request.urlopen(req,timeout=50) as src,open(path,"wb") as dst:
        import shutil
        shutil.copyfileobj(src,dst)
    return path.read_bytes()

def git_blob(path):
    p=subprocess.run(["git","hash-object",str(path)],capture_output=True,text=True,check=True,timeout=15)
    return p.stdout.strip()

def one_proc(name,who,cmd,seconds):
    peak=ROOT/("peak_"+name.replace(".","_")+"_"+who+".txt")
    started=time.perf_counter()
    try:
        p=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak)]+cmd,
                         text=True,capture_output=True,timeout=seconds)
        lines=p.stdout.splitlines()
        parsed={}
        if who=="cvc5":
            answers=[l.strip() for l in lines if l.strip() in ("sat","unsat","unknown")]
            parsed={"answer":answers[0] if answers else "NO_USABLE_ANSWER"}
        else:
            try:parsed=json.loads(lines[-1])
            except (IndexError,ValueError):parsed={"answer":"UNPARSEABLE_OUTPUT"}
        result={"answer":parsed.get("answer",parsed.get("status","NO_RESULT")),
                "valid_source_unsat_certificate":bool(parsed.get("original_unsat_independently_certified",False)),
                "proof_method":parsed.get("method"),
                "error_type":parsed.get("error_type"),
                "eligible_mod1_targets":parsed.get("eligible_negative_mod_eq1_targets"),
                "return_code":p.returncode,
                "stderr_sha256":hashlib.sha256(p.stderr.encode()).hexdigest(),
                "process_timeout":False}
    except subprocess.TimeoutExpired:
        result={"answer":"EXTERNAL_WALL_TIMEOUT","valid_source_unsat_certificate":False,
                "return_code":None,"process_timeout":True}
    result["wall_seconds"]=round(time.perf_counter()-started,6)
    result["peak_rss_kib"]=(int(peak.read_text().strip()) if
        peak.exists() and peak.read_text().strip().isdigit() else None)
    return result

def run():
    totalstart=time.perf_counter()
    receipt={"status":"FIRST_EXECUTION_NOT_COMPLETE",
      "preregistration_issue":"https://github.com/yoonsj0305/NEUMANN/issues/224",
      "source_git_commit":SRC_SHA,"source_family":FAMILY,
      "complete_frozen_names_and_git_blobs":FROZEN,
      "original_count":9,
      "frozen_proof_git_sha":PROOF_COMMIT,"frozen_proof_blob":PROOF_BLOB,
      "max_seconds_per_z3":MAX_Z3_WALL,
      "max_seconds_per_cvc5":MAX_CVC5_WALL,
      "max_seconds_per_structural_prover":MAX_PROOF_WALL,
      "learning_or_neural_forwards":0,"paid_api_or_gpu":0,
      "global_q1_q7":"OPEN","g1":"HOLD_LEARNING","g2":"BLOCKED","tasks":[]}
    def store():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    store()
    try:
        before_engine=time.perf_counter()
        proof_file=ROOT/"exact_prior_frozen_newton_prover.py"
        proof_bytes=download(
          f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{PROOF_COMMIT}/{PROOF_PATH}",
          proof_file)
        if git_blob(proof_file)!=PROOF_BLOB:
            raise RuntimeError("PROOF_SOURCE_NOT_BYTE_IDENTICAL_TO_FROZEN")
        receipt["proof_source_sha256"]=hashlib.sha256(proof_bytes).hexdigest()
        receipt["proof_download_wall_seconds_charged_to_hybrid"]=round(
            time.perf_counter()-before_engine,6)
        v=subprocess.run(["cvc5","--version"],capture_output=True,text=True,timeout=8)
        if v.returncode:raise RuntimeError("CVC5_NOT_EXECUTABLE")
        receipt["cvc5_version"]=v.stdout.strip().splitlines()[0]
        receipt["z3_version_expected"]="4.15.4"
        before_originals=time.perf_counter()
        files={}
        for name,expected_git_blob in FROZEN.items():
            path=ROOT/name
            raw=download(ORIG_BASE+name,path)
            if git_blob(path)!=expected_git_blob:raise RuntimeError("ORIGINAL_INPUT_GIT_BLOB_MISMATCH")
            files[name]=(path,hashlib.sha256(raw).hexdigest(),len(raw))
        receipt["originals_shared_download_wall_seconds"]=round(time.perf_counter()-before_originals,6)
        receipt["all_original_bytes"]=sum(v[2] for v in files.values())
        # Each file/arm independent. Alternating first solver order by index only.
        for index,name in enumerate(FROZEN):
            path,sha,nbytes=files[name]
            row={"filename":name,"original_sha256":sha,"original_bytes":nbytes,
                 "comparison_order":"native_first" if index%2==0 else "hybrid_first"}
            def classical():
                row["z3"]=one_proc(name,"z3",[sys.executable,"-c",Z3_RUN,str(path)],MAX_Z3_WALL)
                row["cvc5"]=one_proc(name,"cvc5",
                     ["cvc5","--lang=smt2","--tlimit=2700",str(path)],MAX_CVC5_WALL)
            def hybrid():
                start=time.perf_counter()
                row["structural_proof"]=one_proc(name,"proof",
                     [sys.executable,"-c",PROOF_RUN,str(path),str(proof_file)],MAX_PROOF_WALL)
                certified=row["structural_proof"]["valid_source_unsat_certificate"]
                if certified:
                    row["fallback_z3"]=None
                    row["hybrid_accepted_unsat"]=True
                else:
                    row["fallback_z3"]=one_proc(name,"fallback_z3",
                         [sys.executable,"-c",Z3_RUN,str(path)],MAX_Z3_WALL)
                    row["hybrid_accepted_unsat"]=row["fallback_z3"]["answer"]=="unsat"
                row["hybrid_case_wall_seconds"]=round(time.perf_counter()-start,6)
            if index%2==0:
                classical();hybrid()
            else:
                hybrid();classical()
            receipt["tasks"].append(row)
            store()
        if len(receipt["tasks"])!=9:raise RuntimeError("NOT_ALL_NINE_REGISTERED_INPUTS")
        # Gold source annotations read AFTER all algorithms have run.
        for row in receipt["tasks"]:
            source_text=files[row["filename"]][0].read_text(encoding="utf-8")
            m=re.search(r"\(set-info\s+:status\s+(sat|unsat|unknown)\s*\)",source_text)
            row["source_expected_status_after_proofs"]=m.group(1) if m else "NOT_DECLARED"
            row["source_qf_nia_present"]=bool(re.search(r"\(set-logic\s+QF_NIA\s*\)",source_text))
            row["source_license_present"]=":license" in source_text
        z3_unsat=sum(t["z3"]["answer"]=="unsat" for t in receipt["tasks"])
        cvc5_unsat=sum(t["cvc5"]["answer"]=="unsat" for t in receipt["tasks"])
        proofs=sum(t["structural_proof"]["valid_source_unsat_certificate"] for t in receipt["tasks"])
        hybrid_unsat=sum(t["hybrid_accepted_unsat"] for t in receipt["tasks"])
        stronger_union=sum(t["z3"]["answer"]=="unsat" or t["cvc5"]["answer"]=="unsat" for t in receipt["tasks"])
        extra=sum(t["structural_proof"]["valid_source_unsat_certificate"] and
             t["z3"]["answer"]!="unsat" and t["cvc5"]["answer"]!="unsat"
             for t in receipt["tasks"])
        wall_z3=sum(t["z3"]["wall_seconds"] for t in receipt["tasks"])
        wall_cvc5=sum(t["cvc5"]["wall_seconds"] for t in receipt["tasks"])
        hybrid_case_wall=sum(t["hybrid_case_wall_seconds"] for t in receipt["tasks"])
        hybrid_all=hybrid_case_wall+receipt["proof_download_wall_seconds_charged_to_hybrid"]
        status=("NO_GO_NO_CROSS_ORIGIN_PROOF" if proofs==0 else
           ("NO_GO_NO_NEW_SOLVES_OVER_CLASSICAL_PORTFOLIO" if extra==0 else
           ("RESTRICTED_G0_POTENTIAL_GO" if hybrid_unsat>stronger_union and
                   hybrid_all<=min(wall_z3,wall_cvc5)
            else "NO_GO_NO_STRONG_PORTFOLIO_COST_ADVANTAGE")))
        receipt["metrics"]={
            "originals":9,"source_verified_unsat":proofs,
            "z3_native_unsat_claims":z3_unsat,"cvc5_native_unsat_claims":cvc5_unsat,
            "strong_two_solver_union_unsat_claims":stronger_union,
            "hybrid_unsat_claims_plus_mathematical_certificates":hybrid_unsat,
            "mathematically_independent_new_beyond_two_baselines":extra,
            "z3_native_9_wall_seconds":round(wall_z3,6),
            "cvc5_native_9_wall_seconds":round(wall_cvc5,6),
            "hybrid_9_cases_wall_seconds":round(hybrid_case_wall,6),
            "hybrid_conservative_engine_fetch_plus_9_cases_wall_seconds":round(hybrid_all,6),
            "common_original_download_excluded_symmetrically_seconds":receipt["originals_shared_download_wall_seconds"],
            "same_runner_g0_research_decision":status,
            "label_statuses_after":dict(collections.Counter(t["source_expected_status_after_proofs"] for t in receipt["tasks"])),
            "no_global_Q_question_automatically_closed":True}
        receipt["status"]="R1_G0_FINAL_SOURCE_ISOLATED_COHORT_COMPLETE"
        receipt["total_wall_seconds"]=round(time.perf_counter()-totalstart,6)
        store()
        print("NEUMANN_R1_FINAL_G0_FIRST",json.dumps(receipt["metrics"],sort_keys=True),flush=True)
    except Exception as e:
        receipt["status"]="FIRST_FINAL_SOURCE_ISOLATED_STUDY_BLOCKED"
        receipt["first_failure_type"]=type(e).__name__
        receipt["first_failure_message"]=str(e)[:300]
        receipt["total_wall_seconds"]=round(time.perf_counter()-totalstart,6)
        store()
        print("NEUMANN_R1_FINAL_FIRST_FAILURE",receipt["first_failure_message"],flush=True)
        raise

if __name__=="__main__":run()
