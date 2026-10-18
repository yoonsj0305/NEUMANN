"""NEUMANN R7 first source-body-hidden metadata-adapted 2022 MathProblems trial. PRE-REGISTERED Issue #230 (metadata-adapted after R6).
One official 2026 SMT-COMP eligibility selection on original 2022 MathProblems:
exact source family, official reference UNSAT, >=2 distinct solver UNSAT claims,
zero competing SAT claims, first 8 sorted names from 27 eligible with one UNSAT solver. NO raw formula before selection.
Same-host Z3, cvc5, original unchanged R3 classical structural+Z3 fallback.
STOP on insufficient eligibility; NO learned model, paid API or GPU.
"""
import collections,gzip,hashlib,importlib.util,json,subprocess,sys,time,urllib.request
from pathlib import Path
import ijson

ROOT=Path("/tmp/neumann_r7_first");ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path("/tmp/neumann_r7_math2022_first_evidence.json")
OFFICIAL_COMMIT="cd15cbedd4ef312d615448100797a80e922cf575"
OFFICIAL_BASE=f"https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/{OFFICIAL_COMMIT}/data/"
OFFICIAL_DIGEST={
 "benchmarks-2026.json.gz":"ba855e47e1ed88e2e6bb26272e84a20a0e8f0c320adc704b062f4c287e586a54",
 "results-sq-2026.json.gz":"7abe5cadf800cc84db00506f85176378f714cdaa8c02a0e491059835f5039c58"}
ORIGINAL_REPO="SMT-LIB/benchmark-submission-2022"
ORIGINAL_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
ORIGINAL_FAMILY="20220315-MathProblems"
ORIGINAL_BASE=(f"https://raw.githubusercontent.com/{ORIGINAL_REPO}/{ORIGINAL_COMMIT}/"
              f"non-incremental/QF_NIA/{ORIGINAL_FAMILY}/")
R3_COMMIT="01acd8153f3268754a7a01e93509259bb97696bc"
R3_PATH="research/evidence/r3-exact-ast-gate-36/one_shot_old_vs_token_vs_exact_ast.py"
R3_BLOB="7e378010ac671e34bf7784b83a4a7cf37354769a"
OLD_BLOB="ff493a21b626733e2797487974388fa6e93b56ec"
TIMEOUT_Z3=3
TIMEOUT_CVC5=3
TIMEOUT_PROOF=5
Z3_SCRIPT=r"""
import json,sys,z3
try:
 s=z3.Solver();s.from_file(sys.argv[1]);s.set(timeout=2700)
 v=s.check()
 print(json.dumps({"answer":str(v),"unknown_reason":s.reason_unknown()[:100] if v==z3.unknown else ""}))
except Exception as e:
 print(json.dumps({"answer":"ERROR","error_type":type(e).__name__}))
"""

def get(url,dest):
 req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R7-preregistered-2026-grounded-unseen"})
 with urllib.request.urlopen(req,timeout=70) as i,open(dest,"wb") as o:
  import shutil
  shutil.copyfileobj(i,o)
 return dest.read_bytes()

def git_blob(dest):
 return subprocess.run(["git","hash-object",str(dest)],capture_output=True,text=True,
                       check=True,timeout=9).stdout.strip()

def module(path):
 s=importlib.util.spec_from_file_location("r7_frozen_r3_original",str(path))
 m=importlib.util.module_from_spec(s)
 sys.modules[s.name]=m;s.loader.exec_module(m)
 return m

def subprocess_eval(name,arm,command,wallcap):
 peak=ROOT/("rss_"+arm+"_"+name.replace(".","_")+".txt")
 start=time.perf_counter()
 try:
  p=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak)]+command,
     capture_output=True,text=True,timeout=wallcap)
  if arm=="cvc5":
   ans=next((x.strip() for x in p.stdout.splitlines()
             if x.strip() in ("unsat","sat","unknown")),"NO_VALID_ANSWER")
   extra={}
  else:
   try:extra=json.loads(p.stdout.splitlines()[-1])
   except (ValueError,IndexError):extra={}
   ans=extra.get("answer","NO_VALID_ANSWER")
  x={"answer":ans,"error_type":extra.get("error_type"),
     "exit_code":p.returncode,"timed_out":False,
     "stderr_sha256":hashlib.sha256(p.stderr.encode()).hexdigest()}
 except subprocess.TimeoutExpired:
  x={"answer":"EXTERNAL_3S_TIMEOUT","exit_code":None,"timed_out":True}
 x["wall_s"]=round(time.perf_counter()-start,6)
 x["peak_rss_kib"]=(int(peak.read_text().strip()) if
     peak.exists() and peak.read_text().strip().isdigit() else None)
 return x

def main():
 start=time.perf_counter()
 receipt={"status":"FIRST_R7_NOT_COMPLETE","issue":230,
 "original_repo":ORIGINAL_REPO,"original_source_commit":ORIGINAL_COMMIT,
 "original_family":ORIGINAL_FAMILY,
 "official_source_git_commit":OFFICIAL_COMMIT,
 "official_digests":OFFICIAL_DIGEST,
 "frozen_r3_blob":R3_BLOB,"frozen_old_proof_blob":OLD_BLOB,
 "preregistered_source_selection":"official 2026 QF_NIA MathProblems UNSAT and >=1 named UNSAT solver results, no SAT; alphabetic first 8",
 "input_labels_never_used_by_prover":True,
 "no_neural_calls":True,"no_gpu":True,"no_paid_calls":True,
 "G0_FULL":"OPEN","G1":"HOLD_LEARNING","G2":"BLOCKED","Q1_Q7_GLOBAL":"OPEN",
 "official_family_statuses":[],"chosen":[],"cases":[]}
 def save():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
 save()
 try:
  # No raw original problem bodies touched until this fixed official-data eligibility is complete.
  for key,expected in OFFICIAL_DIGEST.items():
   dest=ROOT/key
   blob=get(OFFICIAL_BASE+key,dest)
   if hashlib.sha256(blob).hexdigest()!=expected:
    raise RuntimeError("OFFICIAL_REFERENCE_DIGEST_MISMATCH_"+key)
  source_index={}
  with gzip.open(ROOT/"benchmarks-2026.json.gz","rb") as f:
   for row in ijson.items(f,"non_incremental.item"):
    item=row.get("file") or {}
    if item.get("logic")!="QF_NIA" or item.get("family",[])[:1]!=[ORIGINAL_FAMILY]:
     continue
    name=item.get("name")
    if name in source_index:raise RuntimeError("DUPLICATE_OFFICIAL_BENCHMARK_NAME")
    source_index[name]=str(row.get("status","unknown")).lower()
  results=collections.defaultdict(dict)
  with gzip.open(ROOT/"results-sq-2026.json.gz","rb") as f:
   for row in ijson.items(f,"results.item"):
    item=row.get("file") or {}
    if row.get("track")!="SingleQuery" or item.get("logic")!="QF_NIA" or item.get("family",[])[:1]!=[ORIGINAL_FAMILY]:
     continue
    name=item.get("name")
    solver=str(row.get("solver",""))
    if not solver:raise RuntimeError("MISSING_SOLVER_NAME")
    outcome=str(row.get("result","")).lower()
    if solver in results[name]:raise RuntimeError("DUPLICATE_SOLVER_RESULT")
    results[name][solver]=outcome
  for name in sorted(source_index):
   outcomes=results.get(name,{})
   ref=source_index[name]
   unsat={k for k,v in outcomes.items() if v=="unsat"}
   sat={k for k,v in outcomes.items() if v=="sat"}
   receipt["official_family_statuses"].append({
    "name":name,"official_reference_status":ref,
    "official_distinct_unsat_solver_count":len(unsat),
    "official_conflicting_sat_solver_count":len(sat),
    "official_result_count":len(outcomes),
    "eligible":ref=="unsat" and len(unsat)>=1 and not sat})
  eligible=[v for v in receipt["official_family_statuses"] if v["eligible"]]
  receipt["full_official_2026_source_index_count"]=len(source_index)
  receipt["official_2026_selected_exact_family_count"]=len(results)
  receipt["total_eligible_origins"]=len(eligible)
  if len(eligible)!=27:raise RuntimeError("R7_ADAPTED_METADATA_COERCION_OR_COHORT_DRIFT")
  receipt["official_original_status_counts"]=dict(collections.Counter(source_index.values()))
  receipt["chosen"]=[v["name"] for v in eligible[:8]]
  save()
  if len(eligible)<8:
   receipt["status"]="R7_OFFICIAL_ELIGIBILITY_STOP"
   receipt["decision"]="NO_GO_ELIGIBILITY_FEWER_THAN_8_TWO_SOLVER_UNSAT"
   save()
   print("R7_FIRST_DATA_AUDIT_STOP",json.dumps({
      "total":len(source_index),"with_results":len(results),
      "eligible":len(eligible),"status_count":receipt["official_original_status_counts"]}),flush=True)
   return
  engine_start=time.perf_counter()
  r3path=ROOT/"frozen_r3.py"
  src=get(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{R3_COMMIT}/{R3_PATH}",r3path)
  if git_blob(r3path)!=R3_BLOB:raise RuntimeError("R3_ENGINE_NOT_PINNED")
  R3=module(r3path)
  oldpath=ROOT/"frozen_old_math.py"
  old=get(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{R3.PROVER_SHA}/{R3.PROVER_PATH}",oldpath)
  if git_blob(oldpath)!=OLD_BLOB:raise RuntimeError("OLD_ENGINE_NOT_PINNED")
  receipt["engine_fetch_plus_import_wall_s"]=round(time.perf_counter()-engine_start,6)
  receipt["engine_r3_sha256"]=hashlib.sha256(src).hexdigest()
  receipt["engine_old_sha256"]=hashlib.sha256(old).hexdigest()
  cvc5_version=subprocess.run(["cvc5","--version"],capture_output=True,text=True,timeout=8)
  if cvc5_version.returncode:raise RuntimeError("CVC5_CONTROL_NOT_AVAILABLE")
  receipt["cvc5_version"]=cvc5_version.stdout.strip().splitlines()[0]
  zv=subprocess.run([sys.executable,"-c","import z3;print(z3.get_version_string())"],
      capture_output=True,text=True,check=True,timeout=12)
  receipt["z3_version"]=zv.stdout.strip()
  if receipt["z3_version"]!="4.15.4":raise RuntimeError("Z3_CONTROL_CHANGED")
  selected=[]
  input_begin=time.perf_counter()
  for name in receipt["chosen"]:
   if not name.endswith(".smt2") or "/" in name or "\\" in name:
    raise RuntimeError("UNSAFE_OFFICIAL_SOURCE_NAME")
   path=ROOT/("original_"+name)
   raw=get(ORIGINAL_BASE+name,path)
   if b"(set-logic QF_NIA)" not in raw:
    raise RuntimeError("EXACT_ORIGINAL_SOURCE_LOGIC_NOT_QF_NIA")
   selected.append((name,path,hashlib.sha256(raw).hexdigest(),git_blob(path)))
  receipt["selected_original_download_wall_s"]=round(time.perf_counter()-input_begin,6)
  receipt["selected_source_hashes"]=[{"name":n,"sha256":sha,"git_blob":gb} for n,_,sha,gb in selected]
  save()
  for i,(name,path,sha,gb) in enumerate(selected):
   row={"name":name,"original_sha256":sha,"original_git_blob":gb,
        "solver_order":[("z3","cvc5","hybrid"),("cvc5","hybrid","z3"),
                        ("hybrid","z3","cvc5")][i%3]}
   for arm in row["solver_order"]:
    if arm=="z3":row["z3"]=subprocess_eval(name,"z3",
       [sys.executable,"-c",Z3_SCRIPT,str(path)],TIMEOUT_Z3)
    elif arm=="cvc5":row["cvc5"]=subprocess_eval(name,"cvc5",
       ["cvc5","--lang=smt2","--tlimit=2700",str(path)],TIMEOUT_CVC5)
    else:
     begin=time.perf_counter()
     proof=R3.child("math2022",name,path,"ast",oldpath)
     certified=(proof.get("cert")==True and
           proof.get("status")=="ORIGINAL_UNSAT_CERTIFIED" and
           proof.get("exit_code")==0 and not proof.get("timeout"))
     fallback=None
     if not certified:
      fallback=subprocess_eval(name,"z3fallback",
       [sys.executable,"-c",Z3_SCRIPT,str(path)],TIMEOUT_Z3)
     row["hybrid"]={"proof":proof,
       "source_mathematically_verified_unsat":certified,
       "fallback":fallback,
       "accepted_answer":"unsat" if certified else fallback["answer"],
       "full_case_wall_s":round(time.perf_counter()-begin,6)}
   receipt["cases"].append(row)
   save()
  if len(receipt["cases"])!=8:raise RuntimeError("NOT_ALL_FROZEN_8_COMPLETE")
  records=receipt["cases"]
  proofs=[x for x in records if x["hybrid"]["source_mathematically_verified_unsat"]]
  independent=[x for x in proofs if x["z3"]["answer"]!="unsat" and x["cvc5"]["answer"]!="unsat"]
  z=sum(x["z3"]["answer"]=="unsat" for x in records)
  c=sum(x["cvc5"]["answer"]=="unsat" for x in records)
  h=sum(x["hybrid"]["accepted_answer"]=="unsat" for x in records)
  zsec=sum(x["z3"]["wall_s"] for x in records)
  csec=sum(x["cvc5"]["wall_s"] for x in records)
  hsec=sum(x["hybrid"]["full_case_wall_s"] for x in records)+receipt["engine_fetch_plus_import_wall_s"]
  if len(proofs)==0:verdict="NO_GO_ZERO_FROZEN_STRUCTURAL_ORIGINAL_CERTIFICATES"
  elif len(independent)==0:verdict="NO_GO_NO_ADDITIONAL_RESULT_OVER_TWO_SPECIALISTS"
  elif h>max(z,c) and hsec<=min(zsec,csec):
   verdict="RESTRICTED_FIRST_CROSS_ORIGIN_CERTIFIED_HEADROOM_CANDIDATE"
  else:verdict="NO_GO_NO_PRESPECIFIED_ALL_IN_COST_GAIN"
  receipt["metrics"]={"eligible_total":len(eligible),"tested_originals":8,
    "z3_return_unsat":z,"cvc5_return_unsat":c,
    "hybrid_unsat_verdicts":h,
    "original_independent_math_certificates":len(proofs),
    "new_certificates_not_solved_by_either_baseline":len(independent),
    "z3_8cold_wall_s":round(zsec,6),"cvc5_8cold_wall_s":round(csec,6),
    "hybrid_8_all_in_engine_wall_s":round(hsec,6),
    "matched_comparison_excludes_shared_input_download":True,
    "verdict":verdict}
  receipt["status"]="R7_FIRST_8_FROZEN_TRUE_UNSAT_ORIGINALS_COMPLETE"
  receipt["total_workflow_excluding_env_setup_wall_s"]=round(time.perf_counter()-start,6)
  save()
  print("NEUMANN_R7_FINAL",json.dumps(receipt["metrics"],sort_keys=True),flush=True)
 except Exception as exc:
  receipt["status"]="R7_FIRST_EVIDENCE_EXECUTION_BLOCKED"
  receipt["failure"]=type(exc).__name__+":"+str(exc)[:320]
  receipt["total_workflow_excluding_env_setup_wall_s"]=round(time.perf_counter()-start,6)
  save()
  print("NEUMANN_R7_FIRST_BLOCKER",receipt["failure"],flush=True)
  raise
if __name__=="__main__":main()
