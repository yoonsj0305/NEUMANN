"""R2 unchanged-certificate-preserving token gate on 36 OPENED originals; issue #225.
Engineering-only check. Proof engine Git blob is historically pinned and unchanged.
"""
import collections,hashlib,json,re,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path("/tmp/r2_originals");ROOT.mkdir(exist_ok=True,parents=True)
OUT=Path("/tmp/r2_frozen36_proof_stage_receipt.json")
PROVER_SHA="c051985ceb216c5e2e3685e28c5f5a0e064850e2"
PROVER_BLOB="ff493a21b626733e2797487974388fa6e93b56ec"
PROVER_PATH="research/evidence/g0-newton-hoenicke27/one_shot_integer_polynomial_proof.py"
H_SOURCE="7f993a017850ba547c6ea19a1bf3b54adf54a449"
E_SOURCE="37c6cd5d98edb46057f30cef35ba7c7250fe0161"
H_NAMES="modInv128 modInv16 modInv32 modInv64 modInv8 modInvFull modInvInitial modInvStep modInvStepSimplified modInvVar1 modSimpleTest sqrtStep1 sqrtStep1a sqrtStep2 sqrtStep2a sqrtStep3 sqrtStep3a sqrtStep4 sqrtStep4a sqrtStep5 sqrtStep5a sqrtStep6 sqrtStep6a sqrtStep7 sqrtStep7a sqrtStepFinal sqrtStepFinala".split()
E_FILES={"A_1":"d6d20f10f78e2060d7037fd5493425cc3d820587",
"B_1":"62d505ab915f7cf51f563e053552feaf50268dfe",
"B_2":"c9714bb59597ebb4e218c0c3d1ccb53700a550c7",
"C_1":"e4e1ae1731d533117f1c3b761b121ef0775f40b9",
"C_2":"b806486b03f136a02f10b7a78ddccf882544e740",
"D_1":"76289b3309508128ebd15e30207f85af739f4f93",
"D_2":"6c7f4a9d3f71687cb2b6a79185ead71eaf877628",
"E_1":"20422aba0dd9ca634833b857f8ec0123a4abd190",
"E_2":"bc25ca78c39c86e159bac59b01d29b08297889a3"}
CASES=[("hoenicke",x+".smt2",None) for x in H_NAMES]+[("elster",n+".smt2",v) for n,v in E_FILES.items()]
assert len(CASES)==36
HISTORIC_PROVEN={"modInvStep.smt2","modInvStepSimplified.smt2","modInvVar1.smt2","modSimpleTest.smt2"}
INNER=r"""
import importlib.util,json,re,sys,time
from pathlib import Path
mode,source,prover=sys.argv[1:]
raw=Path(source).read_bytes()
beg=time.perf_counter()
needed={b"not",b"mod",b"1",b">"}
seen=set()
for match in re.finditer(rb"\|[^|]*\||\(|\)|[^\s()]+",raw):
 token=match.group(0)
 if token in needed:
  seen.add(token)
  if len(seen)==4:break
possible=len(seen)==4
scan_s=time.perf_counter()-beg
if mode=="gate" and not possible:
 print(json.dumps({"status":"SKIP_NO_CERTIFICATE_POSSIBLE","cert":False,
  "loaded_old_proof_engine":False,"necessary_tokens_all_present":False,"scan_s":scan_s}))
 sys.exit(0)
try:
 sp=importlib.util.spec_from_file_location("frozen_original_exact_poly_prover",prover)
 alg=importlib.util.module_from_spec(sp);sys.modules[sp.name]=alg;sp.loader.exec_module(alg)
 result=alg.prove_one_original(source)
 cert=(result.get("status")=="ORIGINAL_UNSAT_CERTIFIED" and
       result.get("independent_original_plus_proven_lemma")=="unsat" and
       result.get("no_source_assertion_removed") is True)
 print(json.dumps({"status":result.get("status"),"cert":cert,"method":result.get("method"),
   "loaded_old_proof_engine":True,"necessary_tokens_all_present":possible,"scan_s":scan_s}))
except Exception as exc:
 print(json.dumps({"status":"PROOF_ENGINE_ERROR","cert":False,
   "error_type":type(exc).__name__,"necessary_tokens_all_present":possible,
   "loaded_old_proof_engine":True,"scan_s":scan_s}))
"""
def fetch(url,path):
 req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-R2-frozen-36-proof-gate"})
 with urllib.request.urlopen(req,timeout=45) as src,path.open("wb") as dst:
  import shutil
  shutil.copyfileobj(src,dst)
 return path.read_bytes()
def blob(path):
 return subprocess.run(["git","hash-object",str(path)],capture_output=True,text=True,check=True,timeout=8).stdout.strip()
def child(group,name,path,mode,prover):
 start=time.perf_counter()
 rss=ROOT/("rss_"+group+"_"+mode+"_"+name.replace(".","_"))
 try:
  r=subprocess.run(["/usr/bin/time","-f","%M","-o",str(rss),
    sys.executable,"-c",INNER,mode,str(path),str(prover)],capture_output=True,
    text=True,timeout=4)
  try: result=json.loads(r.stdout.splitlines()[-1])
  except (IndexError,ValueError):result={"status":"UNPARSEABLE","cert":False}
  result["exit_code"]=r.returncode
  result["stderr_sha256"]=hashlib.sha256(r.stderr.encode()).hexdigest()
  result["timeout"]=False
 except subprocess.TimeoutExpired:
  result={"status":"EXTERNAL_4S_TIMEOUT","cert":False,"timeout":True,"exit_code":None}
 result["total_wall_s"]=round(time.perf_counter()-start,6)
 result["peak_rss_kib"]=int(rss.read_text().strip()) if (
   rss.exists() and rss.read_text().strip().isdigit()) else None
 return result
def main():
 result={"status":"FIRST_RUN_INCOMPLETE","prereg":"https://github.com/yoonsj0305/NEUMANN/issues/225",
 "originals":36,"source_commits":{"hoenicke":H_SOURCE,"elster":E_SOURCE},
 "proof_sha":PROVER_SHA,"proof_blob":PROVER_BLOB,
 "no_original_source_answer_labels_passed":True,
 "originals_previously_opened_engineering_only":True,
 "neural_forwards":0,"G1":"HOLD_LEARNING","G2":"BLOCKED",
 "global_Q1_Q7":"OPEN","cases":[]}
 def save():OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 save();start=time.perf_counter()
 try:
  proof_file=ROOT/"frozen_original_exact_prover.py"
  data=fetch("https://raw.githubusercontent.com/yoonsj0305/NEUMANN/"+
      PROVER_SHA+"/"+PROVER_PATH,proof_file)
  if blob(proof_file)!=PROVER_BLOB:raise RuntimeError("ORIGINAL_PROVER_BLOB_MISMATCH")
  result["old_prover_sha256"]=hashlib.sha256(data).hexdigest()
  paths=[]
  for group,name,expected_blob in CASES:
   src=(H_SOURCE if group=="hoenicke" else E_SOURCE)
   family=("20230328-sqrtmodinv-hoenicke" if group=="hoenicke" else "20250331-elster")
   repo=("benchmark-submission-2023" if group=="hoenicke" else "benchmark-submission-2025")
   path=ROOT/(group+"_"+name)
   raw=fetch(f"https://raw.githubusercontent.com/SMT-LIB/{repo}/{src}/non-incremental/QF_NIA/{family}/{name}",path)
   if expected_blob and blob(path)!=expected_blob:
    raise RuntimeError("PINNED_SOURCE_BLOB_NOT_SAME:"+name)
   if b"(set-logic QF_NIA)" not in raw:raise RuntimeError("SOURCE_LOGIC_NOT_QF_NIA")
   paths.append((group,name,path,hashlib.sha256(raw).hexdigest()))
  for i,(group,name,path,sha) in enumerate(paths):
   item={"group":group,"name":name,"source_sha256":sha,
        "expected_old_proof_positive_from_prior_receipt":group=="hoenicke" and name in HISTORIC_PROVEN,
        "execution_order":"old_first" if i%2==0 else "gate_first"}
   if i%2==0:
    item["old"]=child(group,name,path,"old",proof_file)
    item["gate"]=child(group,name,path,"gate",proof_file)
   else:
    item["gate"]=child(group,name,path,"gate",proof_file)
    item["old"]=child(group,name,path,"old",proof_file)
   result["cases"].append(item);save()
  if len(result["cases"])!=36:raise RuntimeError("MISSING_CASE")
  old_pos={r["group"]+":"+r["name"] for r in result["cases"] if r["old"]["cert"]}
  gate_pos={r["group"]+":"+r["name"] for r in result["cases"] if r["gate"]["cert"]}
  wanted={"hoenicke:"+name for name in HISTORIC_PROVEN}
  # No silently closing if either historical positive or a new positive changed.
  if old_pos!=gate_pos or old_pos!=wanted:
   raise RuntimeError("CERTIFICATE_PRESERVATION_FAIL_OR_OLD_PROGRAM_REGRESSION")
  skipped=[r for r in result["cases"] if r["gate"]["status"]=="SKIP_NO_CERTIFICATE_POSSIBLE"]
  if any(r["old"]["cert"] for r in skipped):
   raise RuntimeError("SOUND_GATE_SKIPPED_VALID_OLD_PROOF")
  old_s=sum(r["old"]["total_wall_s"] for r in result["cases"])
  gated_s=sum(r["gate"]["total_wall_s"] for r in result["cases"])
  result["summary"]={"registered":36,"old_cert_count":len(old_pos),
   "gate_cert_count":len(gate_pos),"skipped_count":len(skipped),
   "skipped_hoenicke":sum(r["group"]=="hoenicke" for r in skipped),
   "skipped_elster":sum(r["group"]=="elster" for r in skipped),
   "old_total_cold_proof_stage_wall_s":round(old_s,6),
   "gate_total_cold_proof_stage_wall_s":round(gated_s,6),
   "net_proof_stage_wall_s_saved":round(old_s-gated_s,6),
   "engineering_gate":"PASS" if gated_s<old_s else "FAIL_NO_MEASURED_COST_GAIN",
   "all_originals_opened_not_blind":True,
   "does_not_establish_whole_hybrid_allin_on_unseen_families":True}
  result["status"]="FIRST_36_SOURCE_SOUND_NOOP_GATE_AUDIT_COMPLETE"
  result["whole_receipt_wall_s"]=round(time.perf_counter()-start,4)
  save()
  print("R2_36_PROOF_STAGE_FIRST",json.dumps(result["summary"],sort_keys=True),flush=True)
 except Exception as exc:
  result["status"]="FIRST_36_SOURCE_GATE_BLOCKED"
  result["first_error"]=type(exc).__name__+": "+str(exc)[:200]
  result["whole_receipt_wall_s"]=round(time.perf_counter()-start,4)
  save()
  print("R2_36_PROOF_STAGE_FIRST_FAILURE",result["first_error"],flush=True)
  raise
if __name__=="__main__":main()
