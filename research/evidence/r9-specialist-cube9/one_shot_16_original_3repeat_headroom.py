"""R9 first fixed same-host three-repeat classical specialist headroom audit.
Exact source manifest is the FIRST R8 original evidence, 16 previously opened
originals (NOT fresh). One program is exact R8 frozen general Z3+SymPy modulus
certificate. Other is an appropriate Python stdlib dedicated original SMT
3-cube mod9 arithmetic certificate. True control for algorithmic overhead.
"""
import collections,hashlib,json,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path("/tmp/neumann_r9_specialist");ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path("/tmp/neumann_r9_specialist_first_repeated.json")
SOURCE_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
SOURCE_PREFIX="https://raw.githubusercontent.com/SMT-LIB/benchmark-submission-2022/"+SOURCE_COMMIT+"/non-incremental/QF_NIA/20220315-MathProblems/"
GENERIC_COMMIT="17c127dde4b477edf0a93ca041ae53150dc97e93"
GENERIC_PATH="research/evidence/r8-modular-obstruction/exact_polynomial_remainder_certificate.py"
GENERIC_BLOB="e6e8682bbc87def7921d13954331e1ab66ac9267"
SPECIALIST_COMMIT="e53b00c110b7528050de42c9f0b7facdb595e9b6"
SPECIALIST_PATH="research/evidence/r9-specialist-cube9/specialist_original_smt_cube9.py"
SPECIALIST_BLOB="fd2fdbda8637b3ba0150cc22257d73c9dfcc22cb"
FILES={
"STC_0013.smt2":"5f75567ac02a13814e5d47e9f83c1b82ff8c3b06e537e168fa25895873914169",
"STC_0058.smt2":"6bba5a9c64715ea1e9ebf777686136f06b2c723e0e225c5e52c21f79eaff6e83",
"STC_0095.smt2":"5348e6a7c06e58e2df50cf0684cb243d56b3ec79b0c09ff0fffc8d0cad2c5cbc",
"STC_0139.smt2":"e4006a2fb2f38707fcba0d91bf574f6857ee56fa69640f05e8c15f009c63947b",
"STC_0185.smt2":"3b036fa377f057276364437f84642b0abdedf0cbca2379eaf56ced97fe1bcb2f",
"STC_0238.smt2":"fa28f54b7f4fc271bb0013006e1a6d113ae52b08b3b7f1fee0d533596cb8e377",
"STC_0284.smt2":"ba5f619c1102a910ee46565272301893d49218c94c6010e75681b301d764d93f",
"STC_0292.smt2":"1ac02bb92a353ed1937a2df8ae84bf9af7be4b6a735974a06e2db20c5ecbbf8d",
"STC_0382.smt2":"bde16cb062e3ef106638ca8921ac2b82e00a946035170b0f425c1b7bb2b056b9",
"STC_0428.smt2":"0ea5b932d1067c7474d3711a5ad9c48b4ea5e0518827de2cf8804715bcabf2b5",
"STC_0437.smt2":"88ec8e55efb2dcf02dbfe43e9765f8532f7244c7f3fa15db40f019978a42ca33",
"STC_0644.smt2":"c3cb4366083ce00fb282021e1ff8f082fdda4eb962af41d9fa613bf33293f9e1",
"STC_0652.smt2":"734326f9d6f21fccecaa801ce96475f334228e5c43c938b2ca28a83e48cb9ddf",
"STC_0671.smt2":"5fa6cb7be8f592331a0b874fb456caefe39dd96e54852596a1e0a395e45b0487",
"STC_0698.smt2":"678665f8fa935527b1b93cd8db19fdba34554594d1035520fdf8f21e9aed1c15",
"STC_0707.smt2":"9b32fd7a206f75aa8fd53abff7207cf4e026ea368dc1bea7b52246282af03845"}
assert len(FILES)==16
TRIALS=3
PROOF_STATUS="INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE"

def download(url,path):
 req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R9-preregistered-relevant-specialist"})
 with urllib.request.urlopen(req,timeout=50) as src,path.open("wb") as dst:
  import shutil
  shutil.copyfileobj(src,dst)
 return path.read_bytes()

def blobsha(path):
 return subprocess.run(["git","hash-object",str(path)],capture_output=True,
                       text=True,check=True,timeout=10).stdout.strip()

def execute(src_name,round_index,arm,script,orig):
 peak=ROOT/("maxrss_"+str(round_index)+"_"+arm+"_"+src_name.replace(".","_"))
 start=time.perf_counter()
 try:
  r=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak),
     sys.executable,str(script),str(orig)],capture_output=True,text=True,timeout=10)
  try:record=json.loads(r.stdout.splitlines()[-1])
  except (IndexError,ValueError):record={"status":"NO_PROOF_JSON"}
  record["exit_code"]=r.returncode
  record["timed_out"]=False
  record["stderr_sha256"]=hashlib.sha256(r.stderr.encode()).hexdigest()
 except subprocess.TimeoutExpired:
  record={"status":"EXTERNAL_10S_TIMEOUT","exit_code":None,"timed_out":True}
 record["cold_subprocess_wall_s"]=round(time.perf_counter()-start,6)
 record["peak_rss_kib"]=(int(peak.read_text().strip()) if
   peak.exists() and peak.read_text().strip().isdigit() else None)
 return record

def test_specialist_must_not_certify_sat_remainder(script):
 # Unit correctness controls are NOT original cohort evidence.
 controls={}
 for n in range(9):
  path=ROOT/("synthetic_control_"+str(n)+".smt2")
  path.write_text("(set-logic QF_NIA)\n"+
    "(declare-fun x () Int)\n(declare-fun y () Int)\n(declare-fun z () Int)\n"+
    f"(assert (= (+ (* x x x) (* y y y) (* z z z)) {n}))\n(check-sat)\n")
  result=execute("control_"+str(n),0,"specialist_control",script,path)
  cert=result.get("status")==PROOF_STATUS
  if cert != (n in (4,5)):
   raise RuntimeError("NEGATIVE_CONTROL_MATHEMATICAL_REGRESSION_"+str(n))
  controls[str(n)]={"cert":cert,"response_status":result.get("status")}
 # A false source mention inside an OR is not a required asserted equality.
 path=ROOT/"synthetic_disjunctive.smt2"
 path.write_text("(set-logic QF_NIA)\n"+
  "(declare-fun x () Int)\n(declare-fun y () Int)\n(declare-fun z () Int)\n"+
  "(assert (or (= (+ (* x x x) (* y y y) (* z z z)) 4) true))\n")
 outside=execute("control_or",0,"specialist_control",script,path)
 if outside.get("status")==PROOF_STATUS:
  raise RuntimeError("UNSOUND_DISJUNCTION_FALSE_POSITIVE")
 controls["disjunction_does_not_trigger"]=True
 return controls

def main():
 t0=time.perf_counter()
 receipt={"status":"R9_FIRST_BENCHMARK_INCOMPLETE","issue":232,
 "source_repo":"SMT-LIB/benchmark-submission-2022","source_commit":SOURCE_COMMIT,
 "originals_from_first_r8_immutable_sha":FILES,
 "generic_commit":GENERIC_COMMIT,"generic_git_blob":GENERIC_BLOB,
 "specialist_commit":SPECIALIST_COMMIT,"specialist_git_blob":SPECIALIST_BLOB,
 "three_repeats":TRIALS,"corpus_exposed_after_r8":True,
 "no_learned_model":True,"no_gpu_or_paid_model":True,
 "G0_FULL":"OPEN","G1":"HOLD_LEARNING","G2":"BLOCKED","Q1_Q7_GLOBAL":"OPEN",
 "original_sources":[],"measurements":[]}
 def save():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
 save()
 try:
  programs={}
  for arm,commit,p,expected in [
    ("generic",GENERIC_COMMIT,GENERIC_PATH,GENERIC_BLOB),
    ("specialist",SPECIALIST_COMMIT,SPECIALIST_PATH,SPECIALIST_BLOB)]:
   start=time.perf_counter()
   path=ROOT/(arm+"_frozen_exact_source.py")
   raw=download("https://raw.githubusercontent.com/yoonsj0305/NEUMANN/"+commit+"/"+p,path)
   if blobsha(path)!=expected:raise RuntimeError("SOURCE_PROGRAM_SHA_MISMATCH_"+arm)
   receipt[arm+"_source_fetch_wall_s"]=round(time.perf_counter()-start,6)
   receipt[arm+"_source_sha256"]=hashlib.sha256(raw).hexdigest()
   programs[arm]=path
  original_download_start=time.perf_counter()
  originals=[]
  for name,sha in FILES.items():
   path=ROOT/name
   raw=download(SOURCE_PREFIX+name,path)
   actual=hashlib.sha256(raw).hexdigest()
   if actual!=sha:raise RuntimeError("EXACT_R8_ORIGINAL_SOURCE_SHA_CHANGED_"+name)
   blob=blobsha(path)
   originals.append((name,path,sha,blob))
   receipt["original_sources"].append({"name":name,"sha256":sha,"upstream_git_blob":blob})
  receipt["shared_16_source_download_wall_s"]=round(time.perf_counter()-original_download_start,6)
  receipt["correctness_unit_controls"]=test_specialist_must_not_certify_sat_remainder(programs["specialist"])
  save()
  for trial in range(TRIALS):
   for i,(name,path,sha,blob) in enumerate(originals):
    order=("generic","specialist") if ((i+trial)%2==0) else ("specialist","generic")
    row={"original_name":name,"original_sha256":sha,"trial":trial+1,"execution_order":order}
    for arm in order:
     result=execute(name,trial+1,arm,programs[arm],path)
     if result.get("status")!=PROOF_STATUS or result.get("exit_code")!=0 or result.get("timed_out"):
      row[arm]=result;receipt["measurements"].append(row);save()
      raise RuntimeError("ORIGINAL_PROOF_NOT_REPRODUCED_"+arm+"_"+name)
     if result.get("source_sha256")!=sha:raise RuntimeError("PROOF_ORIGINAL_HASH_MISMATCH")
     if result.get("modulus")!=9:raise RuntimeError("EXPECTED_ORIGINAL_MOD9_PROOF_NOT_FROZEN")
     if arm=="generic":
      if not result.get("independent_verifier",{}).get("zero_excluded"):
       raise RuntimeError("R8_ORIGINAL_SECOND_PROOF_VERIFIER_MISSING")
     else:
      if not result.get("target_residue_absent") or not result.get("crosscheck_different_enumeration"):
       raise RuntimeError("R9_SPECIALIST_INDEPENDENT_RESIDUE_CHECK_FAILED")
      if result.get("independent_full_residue_checks")!=729:
       raise RuntimeError("NOT_ALL_NINE_CUBED_REMAINDER_ASSIGNMENTS")
     row[arm]=result
    receipt["measurements"].append(row)
    save()
  if len(receipt["measurements"])!=16*TRIALS:raise RuntimeError("NOT_48_PAIRS")
  totals={}
  for arm in ("generic","specialist"):
   times=[r[arm]["cold_subprocess_wall_s"] for r in receipt["measurements"]]
   total=sum(times)+receipt[arm+"_source_fetch_wall_s"]
   totals[arm]={"certified_original_runs":len(times),"unique_originals":16,
    "median_cold_case_wall_s":round(sorted(times)[len(times)//2],6),
    "sum_cold_48_cases_s":round(sum(times),6),
    "pinned_program_fetch_s":receipt[arm+"_source_fetch_wall_s"],
    "total_48_including_program_fetch_s":round(total,6),
    "peak_original_rss_kib":max(r[arm]["peak_rss_kib"] or 0 for r in receipt["measurements"]),
    "per_round_16_case_wall_s":[round(sum(r[arm]["cold_subprocess_wall_s"]
      for r in receipt["measurements"] if r["trial"]==j),6) for j in (1,2,3)]}
  better=totals["specialist"]["total_48_including_program_fetch_s"]<totals["generic"]["total_48_including_program_fetch_s"]
  receipt["summary"]={"input_originals":16,"trials":3,
   "all_original_certificates_reproduced_in_both_algorithms":True,
   "original_16_competition_correctness_grounded_in_R8":True,
   "generic":totals["generic"],"specialist":totals["specialist"],
   "specialist_matched_total_wall_less":better,
   "specialist_cost_reduction_pct":round(100*(
     totals["generic"]["total_48_including_program_fetch_s"]-
     totals["specialist"]["total_48_including_program_fetch_s"])/
     totals["generic"]["total_48_including_program_fetch_s"],4),
   "judgement":"R9_CLASSICAL_SPECIALIST_HEADROOM_DOMINATES_GENERIC_DEV_PASS" if better
     else "R9_SPECIALIST_NOT_PROVEN_CHEAPER_ORIGINAL_DEV",
   "not_independent_cross_generator_or_learned_transfer":True,
   "strongest_mathematically_optimal_general_solver_claim":False}
  receipt["status"]="R9_FIRST_16_ORIGINALS_THREE_ROUNDS_COMPLETE"
  receipt["total_wall_excluding_shared_CI_setup_s"]=round(time.perf_counter()-t0,6)
  save()
  print("NEUMANN_R9_CLASSICAL_SPECIALIST_VERDICT",json.dumps(receipt["summary"],sort_keys=True),flush=True)
 except Exception as exc:
  receipt["status"]="R9_FIRST_EXECUTION_FAILED"
  receipt["failure"]=type(exc).__name__+":"+str(exc)[:250]
  receipt["whole_wall_s"]=round(time.perf_counter()-t0,6)
  save()
  print("NEUMANN_R9_FIRST_FAILURE",receipt["failure"],flush=True)
  raise

if __name__=="__main__":main()
