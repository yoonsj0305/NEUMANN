"""NEUMANN R10 | LAST heterogeneous original-source classical portfolio control.
Exactly 16 2022 STC, 27 2023 Hoenicke, 9 2025 Elster = 52 ORIGINALS.
Preregistered Issue #233, no source/label-based routing and NO neural inference.
A Z3; B old R3 exact Math + Z3; C R9 exact cubes + Z3;
D R9 -> R3 -> Z3, each certification on ORIGINAL, no hallucinated pass.
All 4 arms are full cold-process with fresh fallbacks and all their costs.
"""
import collections,hashlib,importlib.util,json,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path("/tmp/neumann_r10_52");ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path("/tmp/neumann_r10_original_52_first.json")
R3_COMMIT="01acd8153f3268754a7a01e93509259bb97696bc"
R3_PATH="research/evidence/r3-exact-ast-gate-36/one_shot_old_vs_token_vs_exact_ast.py"
R3_BLOB="7e378010ac671e34bf7784b83a4a7cf37354769a"
OLD_BLOB="ff493a21b626733e2797487974388fa6e93b56ec"
R9_COMMIT="e53b00c110b7528050de42c9f0b7facdb595e9b6"
R9_PATH="research/evidence/r9-specialist-cube9/specialist_original_smt_cube9.py"
R9_BLOB="fd2fdbda8637b3ba0150cc22257d73c9dfcc22cb"
R9_MANIFEST_COMMIT="1815cfee35e490af3478b9bc4ec13faef0171a76"
R9_MANIFEST_PATH="research/evidence/r9-specialist-cube9/one_shot_16_original_3repeat_headroom.py"
R9_MANIFEST_BLOB="0a483d8ad23a4071045f5549c1d080e5890d5de7"
SAT_UNSAT={"sat","unsat"}
SPECIAL_OK="INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE"
PY_Z3=r"""
import json,sys,z3
try:
 solver=z3.Solver();solver.from_file(sys.argv[1]);solver.set(timeout=2700)
 verdict=solver.check()
 print(json.dumps({"answer":str(verdict),
  "reason":solver.reason_unknown()[:90] if verdict==z3.unknown else ""}))
except Exception as exc:
 print(json.dumps({"answer":"ERROR","error":type(exc).__name__}))
"""

def grab(url,dest):
 request=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R10-first-heterogeneous52"})
 with urllib.request.urlopen(request,timeout=60) as inp,dest.open("wb") as out:
  import shutil
  shutil.copyfileobj(inp,out)
 return dest.read_bytes()

def ghblob(path):
 return subprocess.run(["git","hash-object",str(path)],capture_output=True,
      text=True,check=True,timeout=10).stdout.strip()

def module(path,name):
 sp=importlib.util.spec_from_file_location(name,str(path))
 m=importlib.util.module_from_spec(sp)
 sys.modules[name]=m;sp.loader.exec_module(m)
 return m

def subprocess_single(label,source,kind,argv,max_wall):
 peak=ROOT/("rss_"+kind+"_"+label.replace(".","_").replace("/","_")+".txt")
 start=time.perf_counter()
 try:
  p=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak)]+argv,
    text=True,capture_output=True,timeout=max_wall)
  try:payload=json.loads(p.stdout.splitlines()[-1])
  except (ValueError,IndexError):payload={"status":"NO_VALID_JSON_OUTPUT"}
  payload["exit_code"]=p.returncode
  payload["outer_wall_timeout"]=False
  payload["stderr_sha256"]=hashlib.sha256(p.stderr.encode()).hexdigest()
 except subprocess.TimeoutExpired:
  payload={"status":"OUTER_WALL_TIMEOUT","exit_code":None,
           "outer_wall_timeout":True}
 payload["wall_s"]=round(time.perf_counter()-start,6)
 payload["peak_rss_kib"]=int(peak.read_text().strip()) if (
   peak.exists() and peak.read_text().strip().isdigit()) else None
 return payload

def z3original(label,source):
 r=subprocess_single(label,source,"z3",[sys.executable,"-c",PY_Z3,str(source)],3)
 if "answer" not in r:r["answer"]="NO_USABLE_ANSWER"
 return r

def special(label,source,special_script,source_sha):
 r=subprocess_single(label,source,"specialist",
    [sys.executable,str(special_script),str(source)],3)
 valid=(r.get("exit_code")==0 and not r.get("outer_wall_timeout") and
   r.get("status")==SPECIAL_OK and
   r.get("source_sha256")==source_sha and
   r.get("target_residue_absent") is True and
   r.get("crosscheck_different_enumeration") is True and
   r.get("independent_full_residue_checks")==729)
 r["independent_original_unsat"]=valid
 return r

def r3source(group,name,src,r3,oldmath):
 r=r3.child(group,name,src,"ast",oldmath)
 valid=(r.get("cert") is True and
   r.get("status")=="ORIGINAL_UNSAT_CERTIFIED" and
   r.get("exit_code")==0 and not r.get("timeout"))
 r["independent_original_unsat"]=valid
 return r

def algorithm(label,group,name,path,sha,arm,r3,oldmath,special_script):
 start=time.perf_counter()
 steps=[]
 cert_type=None
 if arm in ("specialist_only","joint"):
  spec=special(label,path,special_script,sha)
  steps.append({"phase":"exact_cubes_mod9","outcome":spec})
  if spec["independent_original_unsat"]:cert_type="exact_cubes_mod9"
 if cert_type is None and arm in ("r3_only","joint"):
  old=r3source(group,name,path,r3,oldmath)
  steps.append({"phase":"source_integer_polynomial_R3","outcome":old})
  if old["independent_original_unsat"]:cert_type="original_r3_integer_polynomial"
 if cert_type is None:
  fallback=z3original(label+"_"+arm,path)
  steps.append({"phase":"new_independent_z3_fallback","outcome":fallback})
  answer=fallback["answer"]
 else:answer="unsat"
 return {"accepted_answer":answer,"independent_source_unsat_cert":cert_type is not None,
         "certificate_type":cert_type,"stages":steps,
         "full_case_wall_s":round(time.perf_counter()-start,6)}

def main():
 t0=time.perf_counter()
 result={"status":"R10_FIRST_NOT_COMPLETE","issue":233,
 "source_set":"16 2022 STC + 27 2023 Hoenicke + 9 2025 Elster",
 "originals_opened_source_families":True,"no_source_or_gold_metadata_in_router":True,
 "frozen_sources":{"r3":R3_BLOB,"integer_polynomial":OLD_BLOB,
   "cube9_specialist":R9_BLOB,"stc_sha_manifest":R9_MANIFEST_BLOB},
 "no_neural_model_or_training":True,"no_GPU_or_paid_API":True,
 "G0_FULL":"OPEN","G1":"HOLD_LEARNING","G2":"BLOCKED","Q1_Q7_GLOBAL":"OPEN",
 "originals":[],"evaluations":[]}
 def save():OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 save()
 try:
  # Byte-frozen original engines, not selected by benchmark names.
  plans={
   "r3":(R3_COMMIT,R3_PATH,R3_BLOB),
   "old":("c051985ceb216c5e2e3685e28c5f5a0e064850e2",
       "research/evidence/g0-newton-hoenicke27/one_shot_integer_polynomial_proof.py",OLD_BLOB),
   "specialist":(R9_COMMIT,R9_PATH,R9_BLOB),
   "stc_manifest":(R9_MANIFEST_COMMIT,R9_MANIFEST_PATH,R9_MANIFEST_BLOB)}
  programs={}
  for key,(commit,p,expected) in plans.items():
   started=time.perf_counter()
   dest=ROOT/("engine_"+key+".py")
   raw=grab(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{commit}/{p}",dest)
   if ghblob(dest)!=expected:raise RuntimeError("FROZEN_PROGRAM_GIT_BLOB_MISMATCH_"+key)
   programs[key]=dest
   result["program_fetch_"+key+"_s"]=round(time.perf_counter()-started,6)
   result["program_sha256_"+key]=hashlib.sha256(raw).hexdigest()
  R3=module(programs["r3"],"frozen_r10_R3_original")
  R9_MANIFEST=module(programs["stc_manifest"],"frozen_r10_16_original_stc_manifest")
  if len(R3.CASES)!=36 or len(R9_MANIFEST.FILES)!=16:
   raise RuntimeError("FROZEN_SOURCE_INPUT_COUNT_DRIFT")
  zver=subprocess.run([sys.executable,"-c",
    "import z3;print(z3.get_version_string())"],
    capture_output=True,text=True,check=True,timeout=10).stdout.strip()
  if zver!="4.15.4":raise RuntimeError("WRONG_Z3_VERSION")
  result["z3_version"]=zver

  # Input family is AUDIT-ONLY and NEVER passed as gold to the code's proof decision.
  all_cases=[]
  stc_base=R9_MANIFEST.SOURCE_PREFIX
  for name,expected_sha in R9_MANIFEST.FILES.items():
   all_cases.append(("stc_2022",name,stc_base+name,expected_sha,None))
  for group,name,blobid in R3.CASES:
   version=R3.H_SOURCE if group=="hoenicke" else R3.E_SOURCE
   repo="benchmark-submission-2023" if group=="hoenicke" else "benchmark-submission-2025"
   family="20230328-sqrtmodinv-hoenicke" if group=="hoenicke" else "20250331-elster"
   url=f"https://raw.githubusercontent.com/SMT-LIB/{repo}/{version}/non-incremental/QF_NIA/{family}/{name}"
   all_cases.append((group,name,url,None,blobid))
  if len(all_cases)!=52:raise RuntimeError("52_ORIGINAL_COUNT_MISSING")
  original_begin=time.perf_counter()
  fixed=[]
  for i,(group,name,url,expected_sha,expected_blob) in enumerate(all_cases):
   path=ROOT/("original_"+group+"_"+name)
   original=grab(url,path)
   hashhex=hashlib.sha256(original).hexdigest()
   if expected_sha and hashhex!=expected_sha:raise RuntimeError("OLD_R8_SOURCE_SHA_MISMATCH:"+name)
   actual_blob=ghblob(path)
   if expected_blob and expected_blob!=actual_blob:raise RuntimeError("OLD_R3_SOURCE_BLOB_MISMATCH:"+name)
   if b"(set-logic QF_NIA)" not in original:raise RuntimeError("ORIGINAL_LOGIC_MISMATCH:"+name)
   record={"family_provenance_group":group,"name":name,
      "source_sha256":hashhex,"original_git_blob":actual_blob,
      "byte_count":len(original)}
   result["originals"].append(record)
   fixed.append((group,name,path,hashhex,record))
  if len({r["source_sha256"] for r in result["originals"]})!=52:
   raise RuntimeError("DUPLICATE_ORIGINAL_HASH")
  result["shared_52_original_download_wall_s"]=round(time.perf_counter()-original_begin,6)
  save()

  allarms=["z3_only","r3_only","specialist_only","joint"]
  for index,(group,name,path,source_sha,source) in enumerate(fixed):
   row={"name":name,"original_sha256":source_sha,
       "source_group_audit_only":group,"order":allarms[index%4:]+allarms[:index%4]}
   for arm in row["order"]:
    if arm=="z3_only":
     r=z3original(name+"_z3_only",path)
     row[arm]={"accepted_answer":r["answer"],
       "independent_source_unsat_cert":False,"certificate_type":None,
       "stages":[{"phase":"new_cold_z3","outcome":r}],
       "full_case_wall_s":r["wall_s"]}
    else:
     row[arm]=algorithm(name+"_"+arm,group,name,path,source_sha,arm,
          R3,programs["old"],programs["specialist"])
   result["evaluations"].append(row);save()
  if len(result["evaluations"])!=52:raise RuntimeError("ALL52_NOT_MEASURED")
  # These identities are historical independently verified original certs;
  # only check after routing, NEVER condition any decision on them.
  expected_r3={"modInvStep.smt2","modInvStepSimplified.smt2",
      "modInvVar1.smt2","modSimpleTest.smt2"}
  for item in result["evaluations"]:
   group=item["source_group_audit_only"]
   if group=="stc_2022":
    if item["specialist_only"]["certificate_type"]!="exact_cubes_mod9" or item["joint"]["certificate_type"]!="exact_cubes_mod9":
     raise RuntimeError("LOST_R8_ORIGINAL_CUBE_CERTIFICATE:"+item["name"])
   if group=="hoenicke" and item["name"] in expected_r3:
    if item["r3_only"]["certificate_type"]!="original_r3_integer_polynomial" or item["joint"]["certificate_type"]!="original_r3_integer_polynomial":
     raise RuntimeError("LOST_HOENICKE_ORIGINAL_CERTIFICATE:"+item["name"])
  engine_fetch={
   "z3_only":0.,
   "r3_only":result["program_fetch_r3_s"]+result["program_fetch_old_s"],
   "specialist_only":result["program_fetch_specialist_s"],
   "joint":result["program_fetch_specialist_s"]+result["program_fetch_r3_s"]+result["program_fetch_old_s"]}
  summary={}
  for arm in allarms:
   rows=result["evaluations"]
   totals=sum(x[arm]["full_case_wall_s"] for x in rows)
   answers=sum(x[arm]["accepted_answer"] in SAT_UNSAT for x in rows)
   proofcount=sum(x[arm]["independent_source_unsat_cert"] for x in rows)
   saved={"accepted_raw_sat_or_unsat_claims":answers,
     "independent_mathematically_original_source_certificates":proofcount,
     "full_case_wall_s":round(totals,6),
     "unique_engine_source_fetch_charged_s":round(engine_fetch[arm],6),
     "conservative_full_corpus_wall_s":round(totals+engine_fetch[arm],6),
     "source_group_wall_s":{g:round(sum(x[arm]["full_case_wall_s"]
          for x in rows if x["source_group_audit_only"]==g),6)
          for g in ("stc_2022","hoenicke","elster")},
     "source_group_accepted":{g:sum(x[arm]["accepted_answer"] in SAT_UNSAT
          for x in rows if x["source_group_audit_only"]==g)
          for g in ("stc_2022","hoenicke","elster")},
     "total_stage_invocations":sum(len(x[arm]["stages"]) for x in rows),
     "fallback_z3_count":sum(any(y["phase"]=="new_independent_z3_fallback"
          for y in x[arm]["stages"]) for x in rows)}
   summary[arm]=saved
  competitor=max((summary[a]["accepted_raw_sat_or_unsat_claims"] for a in allarms if a!="joint"))
  strongest_cost=min(summary[a]["conservative_full_corpus_wall_s"] for a in allarms if a!="joint")
  pass_science=summary["joint"]["accepted_raw_sat_or_unsat_claims"]>competitor
  pass_cost=summary["joint"]["conservative_full_corpus_wall_s"]<=strongest_cost
  summary["adjudication"]={
    "all_originals":52,"independent_original_proof_expected_by_joint":20,
    "joint_certificate_count":summary["joint"]["independent_mathematically_original_source_certificates"],
    "strictly_more_reported_source_outcomes_than_best_single_arm":pass_science,
    "joint_full_cost_below_or_equal_cheapest_single_arm":pass_cost,
    "registered_full_heterogeneous_portfolio":"PASS" if (pass_science and pass_cost and
        summary["joint"]["independent_mathematically_original_source_certificates"]==20)
        else "NO_GO",
    "new_task_or_cross_source_generalization":"NOT_TESTED_OPENED_CORPORA",
    "learned_autonomous_structure_selector":"NOT_TESTED_ZERO_NEURAL",
    "safety_soundness":"ALL_ACCEPTED_SOURCE_CERTIFICATES_INDEPENDENT_CLASSICAL"}
  result["summary"]=summary
  result["status"]="R10_FIRST_52_ORIGINAL_FOUR_FULL_ARMS_COMPLETE"
  result["total_measured_workflow_wall_s_excluding_environment"]=round(time.perf_counter()-t0,6)
  save()
  print("NEUMANN_R10_FIRST_HETEROGENEOUS_FULL",json.dumps(summary,sort_keys=True),flush=True)
 except Exception as exc:
  result["status"]="R10_FIRST_EXECUTION_FAILED_OR_BLOCKED"
  result["failure_type"]=type(exc).__name__
  result["failure_message"]=str(exc)[:330]
  result["run_wall_s"]=round(time.perf_counter()-t0,6)
  save()
  print("NEUMANN_R10_FIRST_FAILURE",result["failure_type"],result["failure_message"],flush=True)
  raise

if __name__=="__main__":main()
