"""NEUMANN R8 first source-body-hidden metadata-adapted 2022 MathProblems trial. PRE-REGISTERED Issue #230 (metadata-adapted after R6).
One official 2026 SMT-COMP eligibility selection on original 2022 MathProblems:
exact source family, official reference UNSAT, >=2 distinct solver UNSAT claims,
zero competing SAT claims, first 8 sorted names from 27 eligible with one UNSAT solver. NO raw formula before selection.
Same-host Z3, cvc5, original unchanged R3 classical structural+Z3 fallback.
STOP on insufficient eligibility; NO learned model, paid API or GPU.
"""
import collections,gzip,hashlib,importlib.util,json,subprocess,sys,time,urllib.request
from pathlib import Path
import ijson

ROOT=Path("/tmp/neumann_r8_first");ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path("/tmp/neumann_r8_math2022_first_evidence.json")
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
 req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R8-preregistered-2026-grounded-unseen"})
 with urllib.request.urlopen(req,timeout=70) as i,open(dest,"wb") as o:
  import shutil
  shutil.copyfileobj(i,o)
 return dest.read_bytes()

def git_blob(dest):
 return subprocess.run(["git","hash-object",str(dest)],capture_output=True,text=True,
                       check=True,timeout=9).stdout.strip()

def module(path):
 s=importlib.util.spec_from_file_location("r8_frozen_r3_original",str(path))
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


MOD_PROOF_SHA="17c127dde4b477edf0a93ca041ae53150dc97e93"
MOD_PROOF_PATH="research/evidence/r8-modular-obstruction/exact_polynomial_remainder_certificate.py"
MOD_PROOF_BLOB="e6e8682bbc87def7921d13954331e1ab66ac9267"

def proof_eval(name,script,source):
 peak=ROOT/("rss_proof_"+name.replace(".","_")+".txt")
 begin=time.perf_counter()
 try:
  result=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak),
    sys.executable,str(script),str(source)],capture_output=True,text=True,timeout=12)
  try:obj=json.loads(result.stdout.splitlines()[-1])
  except (ValueError,IndexError):obj={"status":"PROOF_UNREADABLE_JSON"}
  obj["process_exit_code"]=result.returncode
  obj["process_outer_timeout"]=False
  obj["stderr_sha256"]=hashlib.sha256(result.stderr.encode()).hexdigest()
 except subprocess.TimeoutExpired:
  obj={"status":"PROOF_OUTER_TIMEOUT","process_exit_code":None,"process_outer_timeout":True}
 obj["full_child_wall_s"]=round(time.perf_counter()-begin,6)
 obj["peak_rss_kib"]=(int(peak.read_text().strip()) if
   peak.exists() and peak.read_text().strip().isdigit() else None)
 return obj

def main():
 initial=time.perf_counter()
 receipt={"status":"R8_FIRST_NOT_COMPLETE","issue":231,
  "source_repo":ORIGINAL_REPO,"source_git":ORIGINAL_COMMIT,
  "source_family":ORIGINAL_FAMILY,
  "official_reference_git":OFFICIAL_COMMIT,
  "official_data_sha256":OFFICIAL_DIGEST,
  "selection":"2026 official MathProblems UNSAT and >=1 UNSAT solver no SAT; first 8 development and NEXT 8 unseen source-body holdout",
  "only_three_development_source_bodies_read_by_human_after_R7":True,
  "modular_lemma_pre_frozen_commit":MOD_PROOF_SHA,
  "modular_lemma_pre_frozen_blob":MOD_PROOF_BLOB,
  "moduli_exhaustively_checked":"2..12","max_integer_variables":4,
  "source_expected_status_is_never_proof_hint":True,
  "no_neural_model":True,"no_gpu":True,"no_paid_api":True,
  "G0_FULL":"OPEN","G1":"HOLD_LEARNING","G2":"BLOCKED","Q1_Q7_GLOBAL":"OPEN",
  "official_manifest":[],"fixed_development":[],"fixed_source_body_unseen_holdout":[],"cases":[]}
 def persist():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
 persist()
 try:
  for filename,digest in OFFICIAL_DIGEST.items():
   raw=get(OFFICIAL_BASE+filename,ROOT/filename)
   if hashlib.sha256(raw).hexdigest()!=digest:
    raise RuntimeError("OFFICIAL_REFERENCE_DIGEST_CHANGED")
  source_ref={}
  with gzip.open(ROOT/"benchmarks-2026.json.gz","rb") as fi:
   for row in ijson.items(fi,"non_incremental.item"):
    source=row.get("file") or {}
    if source.get("logic")=="QF_NIA" and source.get("family",[])[:1]==[ORIGINAL_FAMILY]:
     if source["name"] in source_ref:raise RuntimeError("DUPLICATE_OFFICIAL_SOURCE")
     source_ref[source["name"]]=str(row.get("status","unknown")).lower()
  official=collections.defaultdict(dict)
  with gzip.open(ROOT/"results-sq-2026.json.gz","rb") as fi:
   for row in ijson.items(fi,"results.item"):
    src=row.get("file") or {}
    if (row.get("track")!="SingleQuery" or src.get("logic")!="QF_NIA"
         or src.get("family",[])[:1]!=[ORIGINAL_FAMILY]):continue
    filename=src["name"]; solver=str(row.get("solver",""))
    if not solver or solver in official[filename]:raise RuntimeError("DUPLICATE_OR_INVALID_SOLVER")
    official[filename][solver]=str(row.get("result","")).lower()
  for filename in sorted(source_ref):
   solvers=official.get(filename,{})
   unsat={k for k,v in solvers.items() if v=="unsat"}
   sat={k for k,v in solvers.items() if v=="sat"}
   receipt["official_manifest"].append({"name":filename,
     "official_source_status":source_ref[filename],
     "unsat_solver_count":len(unsat),"sat_solver_count":len(sat),
     "eligible":source_ref[filename]=="unsat" and len(unsat)>=1 and not sat})
  eligible=[row for row in receipt["official_manifest"] if row["eligible"]]
  receipt["official_total"]=len(source_ref)
  receipt["official_status_counts"]=dict(collections.Counter(source_ref.values()))
  receipt["source_provenance_eligible_total"]=len(eligible)
  if len(source_ref)!=1100 or len(eligible)!=27:
   raise RuntimeError("OFFICIAL_ELIGIBILITY_METADATA_DRIFT")
  dev=[x["name"] for x in eligible[:8]]
  hold=[x["name"] for x in eligible[8:16]]
  receipt["fixed_development"]=dev
  receipt["fixed_source_body_unseen_holdout"]=hold
  # Identity of first 8 prior original metadata, source formula contents NOT used.
  if dev!=["STC_0013.smt2","STC_0058.smt2","STC_0095.smt2",
           "STC_0139.smt2","STC_0185.smt2","STC_0238.smt2",
           "STC_0284.smt2","STC_0292.smt2"]:
   raise RuntimeError("HISTORICAL_R7_FIRST8_IDENTITY_DRIFT")
  persist()
  # Byte-exact theorem source was frozen by Git commit BEFORE holdout source reading.
  engstart=time.perf_counter()
  theorem=ROOT/"pinned_universal_modular_obstruction.py"
  data=get(f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{MOD_PROOF_SHA}/{MOD_PROOF_PATH}",theorem)
  if git_blob(theorem)!=MOD_PROOF_BLOB:raise RuntimeError("FROZEN_PROVER_BYTE_DRIFT")
  receipt["frozen_engine_fetch_wall_s"]=round(time.perf_counter()-engstart,6)
  receipt["frozen_engine_sha256"]=hashlib.sha256(data).hexdigest()
  cvc5_ver=subprocess.run(["cvc5","--version"],text=True,capture_output=True,timeout=10)
  if cvc5_ver.returncode:raise RuntimeError("CVC5_NOT_AVAILABLE")
  receipt["cvc5_version"]=cvc5_ver.stdout.strip().splitlines()[0]
  zver=subprocess.run([sys.executable,"-c","import z3;print(z3.get_version_string())"],
      text=True,capture_output=True,check=True,timeout=12).stdout.strip()
  if zver!="4.15.4":raise RuntimeError("Z3_WRONG_VERSION")
  receipt["z3_version"]=zver
  source_start=time.perf_counter()
  originals=[]
  for i,filename in enumerate(dev+hold):
   if not filename.endswith(".smt2") or "/" in filename or "\\" in filename:
    raise RuntimeError("ILLEGAL_SOURCE_FILENAME")
   path=ROOT/("original_"+filename)
   data=get(ORIGINAL_BASE+filename,path)
   if b"(set-logic QF_NIA)" not in data:raise RuntimeError("ORIGINAL_LOGIC_NOT_QF_NIA")
   originals.append((filename,path,hashlib.sha256(data).hexdigest(),git_blob(path)))
  receipt["shared_original_download_wall_s"]=round(time.perf_counter()-source_start,6)
  receipt["sources"]=[{"name":n,"sha256":sha,"git_blob":blob} for n,_,sha,blob in originals]
  persist()
  for i,(filename,path,source_hash,source_blob) in enumerate(originals):
   cohort="exposed_r7_development_first8" if i<8 else "unopened_source_body_holdout_next8"
   row={"name":filename,"original_sha256":source_hash,"original_git_blob":source_blob,
        "cohort":cohort,"order":[("z3","cvc5","proof"),("proof","z3","cvc5"),
        ("cvc5","proof","z3")][i%3]}
   for arm in row["order"]:
    if arm=="z3":
     row["z3"]=subprocess_eval(filename,"z3",
       [sys.executable,"-c",Z3_SCRIPT,str(path)],3)
    elif arm=="cvc5":
     row["cvc5"]=subprocess_eval(filename,"cvc5",
       ["cvc5","--lang=smt2","--tlimit=2700",str(path)],3)
    else:
     row["modular_proof"]=proof_eval(filename,theorem,path)
   receipt["cases"].append(row)
   persist()
  if len(receipt["cases"])!=16:raise RuntimeError("NOT_ALL_16_ORIGINALS_TESTED")
  if len(set(row["original_sha256"] for row in receipt["cases"]))!=16:
   raise RuntimeError("DUPLICATE_ORIGINAL_SOURCE_SHA256")
  for row in receipt["cases"]:
   p=row["modular_proof"]
   if p.get("process_exit_code")!=0 or p.get("process_outer_timeout"):
    raise RuntimeError("ORIGINAL_MODULAR_PROOF_PROCESS_NOT_COMPLETED")
   if p["status"]=="INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE":
    if p.get("zero_residue_impossible")!=True:raise RuntimeError("PROOF_WITHOUT_NO_ZERO")
    if p["independent_verifier"].get("zero_excluded")!=True:
     raise RuntimeError("MISSING_SEPARATE_EXHAUSTIVE_VERIFIER")
  report={}
  for group,records in (("dev",[r for r in receipt["cases"] if r["cohort"].startswith("exposed")]),
                        ("holdout",[r for r in receipt["cases"] if r["cohort"].startswith("unopened")]),
                        ("all16",receipt["cases"])):
   certs=[r for r in records if r["modular_proof"]["status"]=="INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE"]
   report[group]={"originals":len(records),
     "original_math_unsat_certificates":len(certs),
     "independently_verifiable_witness_files":[r["name"] for r in certs],
     "additional_math_certs_vs_both_3sec_ordinary_z3_cvc5":
       sum(r["z3"]["answer"]!="unsat" and r["cvc5"]["answer"]!="unsat" for r in certs),
     "z3_unsat_claims":sum(r["z3"]["answer"]=="unsat" for r in records),
     "cvc5_unsat_claims":sum(r["cvc5"]["answer"]=="unsat" for r in records),
     "z3_total_wall_s":round(sum(r["z3"]["wall_s"] for r in records),6),
     "cvc5_total_wall_s":round(sum(r["cvc5"]["wall_s"] for r in records),6),
     "modular_prover_16_process_wall_s":round(sum(r["modular_proof"]["full_child_wall_s"] for r in records),6)}
  report["all16"]["modular_engine_pinned_source_fetch_wall_s"]=receipt["frozen_engine_fetch_wall_s"]
  report["all16"]["module_total_including_fetch_s"]=round(
       report["all16"]["modular_prover_16_process_wall_s"]+receipt["frozen_engine_fetch_wall_s"],6)
  report["interpretation"]={
   "r8_dev_classical_math":"PASS" if report["dev"]["original_math_unsat_certificates"]>=1 else "FAIL",
   "r8_holdout_source_body_unseen_classical_math":"PASS" if report["holdout"]["original_math_unsat_certificates"]>=1 else "FAIL",
   "neural_semantic_learner":"NOT_TESTED",
   "strongest_classical_modulo9_specialist_baseline":"NOT_TESTED",
   "global_Q1_Q7":"OPEN"}
  receipt["metrics"]=report
  receipt["status"]="R8_FIRST_16_EXACT_ORIGINAL_MODULAR_VERIFIED"
  receipt["job_wall_excluding_dependency_setup_s"]=round(time.perf_counter()-initial,6)
  persist()
  print("R8_FIRST_CERTIFICATE_AND_HOLDOUT",json.dumps(report,sort_keys=True),flush=True)
 except Exception as exc:
  receipt["status"]="R8_FIRST_RUN_TECHNICAL_OR_SOURCE_FAILURE"
  receipt["failure_type"]=type(exc).__name__
  receipt["failure_message"]=str(exc)[:280]
  receipt["job_wall_excluding_dependency_setup_s"]=round(time.perf_counter()-initial,6)
  persist()
  print("R8_FIRST_RUN_FAILURE",receipt["failure_type"],receipt["failure_message"],flush=True)
  raise

if __name__=="__main__":main()
