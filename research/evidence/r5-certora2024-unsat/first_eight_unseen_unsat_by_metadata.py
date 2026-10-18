"""R5 prospectively frozen original Certora 2024 UNSAT transfer, NO new theorem logic.
Registered Issue #228 BEFORE any of the 41 new source bodies or source statuses read.
Program selects first 8 UNSAT originals among ALL 41 via original :status metadata only,
no solver/task difficulty or content selection. 1 independent-origin run then STOP.
"""
import collections,hashlib,importlib.util,json,re,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path("/tmp/r5_certora2024_first");ROOT.mkdir(exist_ok=True,parents=True)
OUT=Path("/tmp/r5_certora2024_frozen_unsat8_first.json")
SOURCE_COMMIT="02e00a1ad661405c438059820d82a5cf5ef11569"
FAMILY="non-incremental/QF_UFNIA/20240410-certora/nia-splits"
SOURCE_BASE=f"https://raw.githubusercontent.com/SMT-LIB/benchmark-submission-2024/{SOURCE_COMMIT}/{FAMILY}/"
SOURCE_DIR_API=(f"https://api.github.com/repos/SMT-LIB/benchmark-submission-2024/contents/"
                f"{FAMILY}?ref={SOURCE_COMMIT}")
R3_COMMIT="01acd8153f3268754a7a01e93509259bb97696bc"
R3_PATH="research/evidence/r3-exact-ast-gate-36/one_shot_old_vs_token_vs_exact_ast.py"
R3_BLOB="7e378010ac671e34bf7784b83a4a7cf37354769a"
OLD_PROVER_BLOB="ff493a21b626733e2797487974388fa6e93b56ec"
EXPECTED_DIRECTORY_MEMBERS=41
REQUIRED_UNSAT_COHORT=8
Z3_WALL=3
CVC5_WALL=3
OLD_STAGE_WALL=5

Z3_SCRIPT=r"""
import json,sys,z3
try:
 solver=z3.Solver()
 solver.from_file(sys.argv[1])
 solver.set(timeout=2700)
 ans=solver.check()
 print(json.dumps({"answer":str(ans),
   "reason":solver.reason_unknown()[:100] if ans==z3.unknown else ""}))
except Exception as ex:
 print(json.dumps({"answer":"ERROR","error_type":type(ex).__name__}))
"""

def fetch(url,file):
 request=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R5-prospective-UNSAT-2024",
  "Accept":"application/vnd.github+json"})
 with urllib.request.urlopen(request,timeout=60) as inp,open(file,"wb") as out:
  import shutil
  shutil.copyfileobj(inp,out)
 return Path(file).read_bytes()
def blob(file):
 return subprocess.run(["git","hash-object",str(file)],capture_output=True,
                       text=True,timeout=10,check=True).stdout.strip()
def import_file(path):
 spec=importlib.util.spec_from_file_location("neumann_r5_unchanged_r3_original",str(path))
 mod=importlib.util.module_from_spec(spec)
 sys.modules[spec.name]=mod
 spec.loader.exec_module(mod)
 return mod

def child(name,mode,cmd,max_wall):
 peak=ROOT/("rss_"+mode+"_"+name.replace(".","_")+".txt")
 start=time.perf_counter()
 try:
  p=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak)]+cmd,
     capture_output=True,text=True,timeout=max_wall)
  if mode=="cvc5":
   answers=[x.strip() for x in p.stdout.splitlines() if x.strip() in ("sat","unsat","unknown")]
   answer=answers[0] if answers else "NO_USABLE_ANSWER"
   parsed={}
  else:
   try: parsed=json.loads(p.stdout.splitlines()[-1])
   except (ValueError,IndexError):parsed={}
   answer=parsed.get("answer","NO_USABLE_ANSWER")
  row={"answer":answer,"error_type":parsed.get("error_type"),
       "return_code":p.returncode,"outer_timeout":False,
       "stderr_sha256":hashlib.sha256(p.stderr.encode()).hexdigest()}
 except subprocess.TimeoutExpired:
  row={"answer":"OUTER_WALL_TIMEOUT","return_code":None,"outer_timeout":True}
 row["wall_s"]=round(time.perf_counter()-start,6)
 row["peak_rss_kib"]=int(peak.read_text().strip()) if (
    peak.exists() and peak.read_text().strip().isdigit()) else None
 return row

def main():
 start=time.perf_counter()
 receipt={"status":"R5_FIRST_NOT_COMPLETE",
  "issue":"https://github.com/yoonsj0305/NEUMANN/issues/228",
  "original_repo":"SMT-LIB/benchmark-submission-2024",
  "original_source_commit":SOURCE_COMMIT,"source_family":FAMILY,
  "expected_directory_members":EXPECTED_DIRECTORY_MEMBERS,
  "selection":"first eight source-header UNSAT in lexicographic order over ALL 41",
  "eligibility_only_source_status_read_before_all_solver_arms":True,
  "frozen_r3_commit":R3_COMMIT,"frozen_r3_git_blob_sha1":R3_BLOB,
  "frozen_old_math_git_blob_sha1":OLD_PROVER_BLOB,
  "G0_GLOBAL":"OPEN","G1":"HOLD_LEARNING","G2":"BLOCKED",
  "Q1_Q7_GLOBAL":"OPEN","neural_forwards":0,"gpu_or_paid_model_calls":0,
  "directory_manifest":[],"chosen_originals":[],"tasks":[]}
 def save():OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 save()
 try:
  engine_begin=time.perf_counter()
  r3path=ROOT/"fixed_r3_router.py"
  raw=fetch(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{R3_COMMIT}/{R3_PATH}",r3path)
  if blob(r3path)!=R3_BLOB:raise RuntimeError("FROZEN_R3_CODE_CHANGED")
  R3=import_file(r3path)
  receipt["r3_source_sha256"]=hashlib.sha256(raw).hexdigest()
  oldpath=ROOT/"old_theorem.py"
  oldraw=fetch(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/"
              f"{R3.PROVER_SHA}/{R3.PROVER_PATH}",oldpath)
  if blob(oldpath)!=OLD_PROVER_BLOB:raise RuntimeError("FROZEN_MATHEMATICAL_PROVER_CHANGED")
  receipt["old_prover_source_sha256"]=hashlib.sha256(oldraw).hexdigest()
  receipt["hybrid_engine_fetch_init_wall_s"]=round(time.perf_counter()-engine_begin,6)
  z3version=subprocess.run([sys.executable,"-c",
     "import z3;print(z3.get_version_string())"],capture_output=True,text=True,check=True,timeout=10)
  receipt["z3_version"]=z3version.stdout.strip()
  if receipt["z3_version"]!="4.15.4":raise RuntimeError("Z3_WRONG_VERSION")
  cvc5version=subprocess.run(["cvc5","--version"],capture_output=True,text=True,timeout=8)
  if cvc5version.returncode:raise RuntimeError("CVC5_NOT_AVAILABLE")
  receipt["cvc5_version"]=cvc5version.stdout.strip().splitlines()[0]

  directory_begin=time.perf_counter()
  listing=json.loads(fetch(SOURCE_DIR_API,ROOT/"original_directory.json"))
  members=sorted((x for x in listing if x.get("type")=="file" and
                  re.fullmatch(r"\d{4}\.smt2",x.get("name",""))),
                 key=lambda x:x["name"])
  if len(members)!=EXPECTED_DIRECTORY_MEMBERS:raise RuntimeError("FROZEN_DIRECTORY_COUNT_MISMATCH")
  if len({x["name"] for x in members})!=EXPECTED_DIRECTORY_MEMBERS:
   raise RuntimeError("DIRECTORY_DUPLICATE_MEMBER")
  candidates=[]
  for meta in members:
   name=meta["name"]
   file=ROOT/("original_"+name)
   raw=fetch(SOURCE_BASE+name,file)
   if blob(file)!=meta["sha"]:raise RuntimeError("ORIGINAL_GIT_BLOB_NOT_VERIFIED:"+name)
   source=raw.decode("utf-8")
   logic=re.search(r"\(set-logic\s+(\S+)\s*\)",source)
   status=re.search(r"\(set-info\s+:status\s+(sat|unsat|unknown)\s*\)",source)
   if not logic or logic.group(1)!="QF_UFNIA" or not status:
    raise RuntimeError("ORIGINAL_REQUIRED_HEADER_OR_LOGIC_MISMATCH:"+name)
   item={"name":name,"git_blob_sha1":meta["sha"],
         "original_sha256":hashlib.sha256(raw).hexdigest(),
         "bytes":len(raw),"source_status_for_selection_ONLY":status.group(1)}
   receipt["directory_manifest"].append(item)
   if status.group(1)=="unsat":
    candidates.append((name,file,item))
   save()
  receipt["complete_41_input_fetch_wall_s"]=round(time.perf_counter()-directory_begin,6)
  receipt["source_status_distribution"]=dict(collections.Counter(
     v["source_status_for_selection_ONLY"] for v in receipt["directory_manifest"]))
  receipt["frozen_eligible_unsat_count"]=len(candidates)
  selected=candidates[:REQUIRED_UNSAT_COHORT]
  receipt["chosen_originals"]=[{"name":n,"sha256":v["original_sha256"]} for n,_,v in selected]
  save()
  if len(selected)<REQUIRED_UNSAT_COHORT:
   receipt["status"]="R5_ELIGIBILITY_FAIL_INSUFFICIENT_SOURCE_UNSAT_STOP"
   receipt["decision"]="ELIGIBILITY_FAIL_STOP"
   save()
   print("NEUMANN_R5_SOURCE_SELECTION_STOP",json.dumps({
      "status":receipt["status"],"source_statuses":receipt["source_status_distribution"]}),flush=True)
   return
  if len({n for n,_,_ in selected})!=8:raise RuntimeError("COHORT_DUPLICATE")
  # DO NOT pass metadata expected answer into any original solver, only file path.
  for i,(name,src,identity) in enumerate(selected):
   row={"source_name":name,"source_sha256":identity["original_sha256"],
        "source_bytes":identity["bytes"],
        "task_selection_rank":i,
        "execution_order":["z3","cvc5","hybrid"] if i%3==0 else
                         (["cvc5","hybrid","z3"] if i%3==1 else ["hybrid","z3","cvc5"])}
   for arm in row["execution_order"]:
    if arm=="z3":
     row["z3"]=child(name,"z3",[sys.executable,"-c",Z3_SCRIPT,str(src)],Z3_WALL)
    elif arm=="cvc5":
     row["cvc5"]=child(name,"cvc5",
        ["cvc5","--lang=smt2","--tlimit=2700",str(src)],CVC5_WALL)
    elif arm=="hybrid":
     begin=time.perf_counter()
     proof=R3.child("certora2024",name,src,"ast",oldpath)
     source_cert=(proof.get("cert") is True and
          proof.get("status")=="ORIGINAL_UNSAT_CERTIFIED" and
          not proof.get("timeout") and proof.get("exit_code")==0)
     fallback=None
     if not source_cert:
      fallback=child(name,"fallback",
        [sys.executable,"-c",Z3_SCRIPT,str(src)],Z3_WALL)
     row["hybrid"]={"frozen_proof_stage":proof,
         "original_sound_UNSAT_certificate":source_cert,
         "fallback":fallback,"accepted_answer":"unsat" if source_cert else fallback["answer"],
         "full_case_wall_s":round(time.perf_counter()-begin,6)}
    else:raise RuntimeError("UNREGISTERED_ARM")
   receipt["tasks"].append(row)
   save()
  if len(receipt["tasks"])!=8:raise RuntimeError("NOT_ALL_EIGHT")
  rows=receipt["tasks"]
  sourceproofs=[r for r in rows if r["hybrid"]["original_sound_UNSAT_certificate"]]
  extra=[r for r in sourceproofs if
     r["z3"]["answer"]!="unsat" and r["cvc5"]["answer"]!="unsat"]
  z3correct=sum(r["z3"]["answer"]=="unsat" for r in rows)
  cvc5correct=sum(r["cvc5"]["answer"]=="unsat" for r in rows)
  hybridcorrect=sum(r["hybrid"]["accepted_answer"]=="unsat" for r in rows)
  z3wall=sum(r["z3"]["wall_s"] for r in rows)
  cvc5wall=sum(r["cvc5"]["wall_s"] for r in rows)
  hybridwall=sum(r["hybrid"]["full_case_wall_s"] for r in rows)+receipt["hybrid_engine_fetch_init_wall_s"]
  if sourceproofs and extra and hybridcorrect>max(z3correct,cvc5correct) and
      hybridwall<=min(z3wall,cvc5wall):
   outcome="RESTRICTED_NEW_SOURCE_MATH_PROOF_AND_TWO_BASELINE_COST_GO"
  elif not sourceproofs:outcome="FAIL_NO_NEW_SOURCE_EXACT_CERTIFICATE_STOP"
  elif not extra:outcome="NO_GO_NO_UNIQUE_EXTRA_VS_TWO_BASELINES"
  else:outcome="NO_GO_NO_ALL_IN_COST_GAP"
  receipt["metrics"]={
    "tested_original_unsat":8,
    "source_sound_UNSAT_proofs":len(sourceproofs),
    "source_sound_certificate_filenames":[r["source_name"] for r in sourceproofs],
    "new_source_sound_proofs_unsolved_by_both_z3_and_cvc5":len(extra),
    "z3_return_unsat_claims":z3correct,"cvc5_return_unsat_claims":cvc5correct,
    "hybrid_return_unsat_or_sound_cert":hybridcorrect,
    "z3_wall_sum_s":round(z3wall,6),"cvc5_wall_sum_s":round(cvc5wall,6),
    "hybrid_wall_including_source_fetch_and_import_s":round(hybridwall,6),
    "all_41_input_fetch_common_wall_s":receipt["complete_41_input_fetch_wall_s"],
    "preregistered_single_family_decision":outcome,
    "strongest_2026_specialist_or_frontier_claim":False}
  receipt["status"]="R5_FIRST_EIGHT_2024_UNSAT_ALL_ARMS_COMPLETE"
  receipt["overall_elapsed_wall_s"]=round(time.perf_counter()-start,6)
  save()
  print("NEUMANN_R5_PROSPECTIVE_UNSAT_FINAL",json.dumps(receipt["metrics"],sort_keys=True),flush=True)
 except Exception as e:
  receipt["status"]="R5_FIRST_REGISTERED_EVIDENCE_EXECUTION_FAILED"
  receipt["error_type"]=type(e).__name__;receipt["error"]=str(e)[:250]
  receipt["overall_elapsed_wall_s"]=round(time.perf_counter()-start,6)
  save()
  print("NEUMANN_R5_FIRST_EXECUTION_FAILURE",receipt["error_type"],receipt["error"],flush=True)
  raise
if __name__=="__main__":main()
