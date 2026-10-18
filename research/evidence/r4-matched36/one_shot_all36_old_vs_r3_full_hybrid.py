"""R4 PRE-REGISTERED WHOLE-SYSTEM frozen 36-original same-runner A/B/C.
GitHub Issue #227 is immutable plan; R1 science NO-GO remains unchanged.
A Z3 cold, B old math proof -> fresh fallback Z3, C R3 AST gate -> fresh Z3.
Imports both actual previous fixed code; no math algorithm or prefilter change.
"""
import collections,hashlib,importlib.util,json,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path("/tmp/r4_samehost_36");ROOT.mkdir(exist_ok=True,parents=True)
OUT=Path("/tmp/r4_all36_samehost_first_full_system.json")
R3_COMMIT="01acd8153f3268754a7a01e93509259bb97696bc"
R3_PATH="research/evidence/r3-exact-ast-gate-36/one_shot_old_vs_token_vs_exact_ast.py"
R3_BLOB="7e378010ac671e34bf7784b83a4a7cf37354769a"
ORIGINAL_PROVER_BLOB="ff493a21b626733e2797487974388fa6e93b56ec"
Z3_VERSION="4.15.4"
Z3_CHILD=r"""
import json,sys,z3
try:
 s=z3.Solver();s.from_file(sys.argv[1]);s.set(timeout=2700)
 a=s.check()
 print(json.dumps({"answer":str(a),"reason":s.reason_unknown()[:100] if a==z3.unknown else ""}))
except Exception as e:
 print(json.dumps({"answer":"ERROR","error_type":type(e).__name__}))
"""
def get(url,p):
 req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R4-frozen-engine-match"})
 with urllib.request.urlopen(req,timeout=50) as src,p.open("wb") as out:
  import shutil
  shutil.copyfileobj(src,out)
 return p.read_bytes()
def git_blob(p):
 r=subprocess.run(["git","hash-object",str(p)],capture_output=True,text=True,check=True,timeout=10)
 return r.stdout.strip()
def import_fixed(path):
 sp=importlib.util.spec_from_file_location("neumann_r3_original_engine",path)
 m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
 return m
def z3cold(file,case_id,tag):
 peak=ROOT/("rss_z3_"+str(case_id)+"_"+tag+".txt")
 start=time.perf_counter()
 try:
  p=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak),
    sys.executable,"-c",Z3_CHILD,str(file)],capture_output=True,text=True,timeout=3)
  try:ans=json.loads(p.stdout.splitlines()[-1])
  except (IndexError,ValueError):ans={"answer":"OUTPUT_MALFORMED"}
  x={"answer":ans.get("answer","OUTPUT_MALFORMED"),
     "reason":ans.get("reason"),"error_type":ans.get("error_type"),
     "return_code":p.returncode,"outer_timeout":False,
     "stderr_sha256":hashlib.sha256(p.stderr.encode()).hexdigest()}
 except subprocess.TimeoutExpired:
  x={"answer":"EXTERNAL_3S_TIMEOUT","return_code":None,"outer_timeout":True}
 x["wall_s"]=round(time.perf_counter()-start,6)
 x["rss_kib"]=int(peak.read_text().strip()) if (
    peak.exists() and peak.read_text().strip().isdigit()) else None
 return x

def main():
 init=time.perf_counter()
 result={"status":"FIRST_MATCHED_36_FULL_SYSTEM_INCOMPLETE",
   "issue":"https://github.com/yoonsj0305/NEUMANN/issues/227",
   "r3_frozen_commit":R3_COMMIT,"r3_frozen_git_blob":R3_BLOB,
   "old_math_frozen_blob":ORIGINAL_PROVER_BLOB,
   "cases_expected":36,"input_corpus_opened_development":True,
   "same_host":True,"z3_timeout_external_seconds":3,
   "no_gold_answers_as_solver_inputs":True,"neural_forwards":0,
   "gpu_or_paid_model_calls":0,"G0_FULL":"OPEN","G1":"HOLD_LEARNING",
   "G2":"BLOCKED","global_Q1_Q7":"OPEN","originals":[]}
 def save():OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 save()
 try:
  fetch_start=time.perf_counter()
  r3file=ROOT/"r3_frozen_original_wrapper.py"
  source=get(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{R3_COMMIT}/{R3_PATH}",r3file)
  if git_blob(r3file)!=R3_BLOB:raise RuntimeError("R3_FROZEN_ROUTER_SHA_MISMATCH")
  R3=import_fixed(r3file)
  result["r3_raw_source_sha256"]=hashlib.sha256(source).hexdigest()
  oldfile=ROOT/"frozen_old_exact_original_polynomial_prover.py"
  oldsrc=get(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{R3.PROVER_SHA}/{R3.PROVER_PATH}",oldfile)
  if git_blob(oldfile)!=ORIGINAL_PROVER_BLOB:raise RuntimeError("OLD_MATH_SOURCE_BLOB_DRIFT")
  result["old_math_source_sha256"]=hashlib.sha256(oldsrc).hexdigest()
  result["two_hybrid_shared_frozen_engine_fetch_s"]=round(time.perf_counter()-fetch_start,6)
  import z3
  if z3.get_version_string()!=Z3_VERSION:raise RuntimeError("Z3_VERSION_CHANGED")
  result["z3_version"]=z3.get_version_string()
  all_paths=[]
  datastart=time.perf_counter()
  for group,name,expected_blob in R3.CASES:
   repo="benchmark-submission-2023" if group=="hoenicke" else "benchmark-submission-2025"
   src_sha=R3.H_SOURCE if group=="hoenicke" else R3.E_SOURCE
   fam="20230328-sqrtmodinv-hoenicke" if group=="hoenicke" else "20250331-elster"
   path=ROOT/(group+"_"+name)
   raw=get(f"https://raw.githubusercontent.com/SMT-LIB/{repo}/{src_sha}/non-incremental/QF_NIA/{fam}/{name}",path)
   if expected_blob and git_blob(path)!=expected_blob:
    raise RuntimeError("ORIGINAL_FILE_GIT_SHA_MISMATCH:"+name)
   if b"(set-logic QF_NIA)" not in raw:raise RuntimeError("ORIGINAL_LOGIC_MISMATCH")
   all_paths.append((group,name,path,hashlib.sha256(raw).hexdigest()))
  if len(all_paths)!=36:raise RuntimeError("ORIGINAL_COHORT_CHANGED")
  result["common_source_download_wall_seconds"]=round(time.perf_counter()-datastart,6)
  result["source_bytes"]=sum(x[2].stat().st_size for x in all_paths)
  result["all_source_sha256_unique"]=len({x[3] for x in all_paths})==36
  # Alternate A/B/C order on source filename index only, never on its gold.
  for i,(group,name,path,sha) in enumerate(all_paths):
   row={"source_group":group,"source_name":name,"source_sha256":sha}
   order=(["baseline","old_hybrid","r3_hybrid"],
          ["old_hybrid","r3_hybrid","baseline"],
          ["r3_hybrid","baseline","old_hybrid"])[i%3]
   row["execution_order"]=order
   def baseline():
    row["baseline"]=z3cold(path,i,"baseline")
   def hybrid(tag,kind):
    start=time.perf_counter()
    stage=R3.child(group,name,path,kind,oldfile)
    # If stage crashed or timed out, do not trust any proof. Fail closed to fallback,
    # and mark operational failure for honest interpretation.
    certified=stage.get("cert") is True and stage.get("status")=="ORIGINAL_UNSAT_CERTIFIED"
    fallback=None
    if not certified:
     fallback=z3cold(path,i,tag+"_fallback")
    row[tag]={"proof_stage":stage,"source_verified_unsat":certified,
      "fallback":fallback,"accepted_raw_answer":"unsat" if certified else fallback["answer"],
      "entire_case_wall_s":round(time.perf_counter()-start,6)}
   for arm in order:
    if arm=="baseline":baseline()
    elif arm=="old_hybrid":hybrid("old_hybrid","old")
    elif arm=="r3_hybrid":hybrid("r3_hybrid","ast")
    else:raise RuntimeError("MISSING_ARM")
   result["originals"].append(row);save()
  if len(result["originals"])!=36:raise RuntimeError("MISSING_ORIGINAL_RECORDS")
  cases=result["originals"]
  for row in cases:
   for arm in ("old_hybrid","r3_hybrid"):
    x=row[arm]["proof_stage"]
    if x.get("timeout") or x.get("exit_code")!=0 or x.get("status") in ("UNPARSEABLE","PROOF_ENGINE_ERROR"):
     raise RuntimeError("PROOF_PROCESS_ERROR_"+row["source_name"]+"_"+arm)
  old_source={row["source_group"]+":"+row["source_name"] for row in cases if row["old_hybrid"]["source_verified_unsat"]}
  r3_source={row["source_group"]+":"+row["source_name"] for row in cases if row["r3_hybrid"]["source_verified_unsat"]}
  required={"hoenicke:"+name for name in R3.HISTORIC_PROVEN}
  if old_source!=required or r3_source!=required:
   raise RuntimeError("HISTORICAL_CERTIFICATE_NOT_PRESERVED")
  stats={}
  for arm in ("baseline","old_hybrid","r3_hybrid"):
   def outcome(row):
    return row["baseline"]["answer"] if arm=="baseline" else row[arm]["accepted_raw_answer"]
   def duration(row):
    return row["baseline"]["wall_s"] if arm=="baseline" else row[arm]["entire_case_wall_s"]
   stats[arm]={
    "sat_raw":sum(outcome(r)=="sat" for r in cases),
    "unsat_raw_or_source_cert":sum(outcome(r)=="unsat" for r in cases),
    "accepted_total_sat_or_unsat":sum(outcome(r) in ("sat","unsat") for r in cases),
    "whole_36_cold_case_wall_s":round(sum(duration(r) for r in cases),6),
    "hoenicke_27_wall_s":round(sum(duration(r) for r in cases if r["source_group"]=="hoenicke"),6),
    "elster_9_wall_s":round(sum(duration(r) for r in cases if r["source_group"]=="elster"),6)}
  # Shared engine is fairly charged equally to the two hybrid systems,
  # original source fetch + env installation shared/excluded equally for all.
  for arm in ("old_hybrid","r3_hybrid"):
   stats[arm]["including_frozen_prover_fetch_wall_s"]=round(
      stats[arm]["whole_36_cold_case_wall_s"]+result["two_hybrid_shared_frozen_engine_fetch_s"],6)
   stats[arm]["source_cert_count"]=4
   stats[arm]["z3_fallback_runs"]=sum(r[arm]["fallback"] is not None for r in cases)
  old=stats["old_hybrid"];r3=stats["r3_hybrid"];z=stats["baseline"]
  source_preserved=(old_source==r3_source==required)
  cost_better=r3["including_frozen_prover_fetch_wall_s"]<old["including_frozen_prover_fetch_wall_s"]
  basematched=r3["accepted_total_sat_or_unsat"]>=z["accepted_total_sat_or_unsat"]
  not_worse_z=r3["including_frozen_prover_fetch_wall_s"]<z["whole_36_cold_case_wall_s"]
  stats["judgement"]={
   "preserved_exact_math_original_certificates":source_preserved,
   "r3_faster_than_old_hybrid":cost_better,
   "r3_additional_cost_saved_vs_old_seconds":round(
       old["including_frozen_prover_fetch_wall_s"]-r3["including_frozen_prover_fetch_wall_s"],6),
   "r3_saved_vs_old_percent":round(100*(
       old["including_frozen_prover_fetch_wall_s"]-r3["including_frozen_prover_fetch_wall_s"])/
       old["including_frozen_prover_fetch_wall_s"],4),
   "r3_at_least_z3_correct_answer_count":basematched,
   "r3_faster_than_z3_standalone":not_worse_z,
   "r4_pre_registered_full_dev_cost_gate":"PASS" if cost_better and source_preserved and basematched and not_worse_z else "FAIL",
   "underlying_new_source_independent_generalization":"NOT_TESTED",
   "best_classical_specialist_or_neural_frontier_claim":"NOT_TESTED"}
  result["metrics"]=stats
  result["status"]="R4_FIRST_36_MATCHED_FULL_HYBRID_COMPLETE"
  result["entire_job_36_wall_s_including_original_fetch"]=round(time.perf_counter()-init,6)
  save()
  print("NEUMANN_R4_MATCHED_ENDTOEND_FIRST",json.dumps(stats,sort_keys=True),flush=True)
 except Exception as e:
  result["status"]="R4_FIRST_36_MATCHED_EXECUTION_FAILED"
  result["failure_type"]=type(e).__name__;result["error"]=str(e)[:300]
  result["entire_job_36_wall_s_including_original_fetch"]=round(time.perf_counter()-init,6)
  save()
  print("NEUMANN_R4_FIRST_FAILURE",result["failure_type"],result["error"],flush=True)
  raise
if __name__=="__main__":main()
