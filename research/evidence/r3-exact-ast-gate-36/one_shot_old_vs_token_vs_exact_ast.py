"""R2 unchanged-certificate-preserving token gate on 36 OPENED originals; issue #226.
Engineering-only check. Proof engine Git blob is historically pinned and unchanged.
"""
import collections,hashlib,json,re,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path("/tmp/r3_originals");ROOT.mkdir(exist_ok=True,parents=True)
OUT=Path("/tmp/r3_frozen36_semantic_gate_receipt.json")
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
if mode in ("gate","ast") and not possible:
 print(json.dumps({"status":"SKIP_NO_CERTIFICATE_POSSIBLE","cert":False,
  "loaded_old_proof_engine":False,"necessary_tokens_all_present":False,"scan_s":scan_s}))
 sys.exit(0)
if mode=="ast":
 # This is a necessary condition for the EXACT old prover accepting a proof.
 # Parse all original assertions through the same Z3 AST library as the old
 # prover. If any scanning error occurs, FAIL OPEN and call the old prover.
 try:
  import z3
  solver=z3.Solver();solver.from_file(source)
  stack=list(solver.assertions());atoms=[]
  while stack:
   node=stack.pop()
   if z3.is_and(node):stack.extend(node.children())
   else:atoms.append(node)
  one=lambda a: z3.is_int_value(a) and a.as_long()==1
  has_neg=False;has_guard=False
  for a in atoms:
   if z3.is_not(a) and z3.is_eq(a.arg(0)):
    lhs,rhs=a.arg(0).children()
    if ((one(lhs) and rhs.decl().kind()==z3.Z3_OP_MOD) or
        (one(rhs) and lhs.decl().kind()==z3.Z3_OP_MOD)):
     has_neg=True
   if z3.is_gt(a):
    lhs,rhs=a.children()
    if (one(rhs) and z3.is_int(lhs) and lhs.num_args()==0 and
        lhs.decl().kind()==z3.Z3_OP_UNINTERPRETED):
     has_guard=True
   if has_neg and has_guard:break
  if not (has_neg and has_guard):
   print(json.dumps({"status":"SKIP_NO_REQUIRED_Z3_AST_PATTERN",
      "cert":False,"loaded_old_proof_engine":False,
      "necessary_tokens_all_present":True,"ast_target_present":has_neg,
      "ast_guard_present":has_guard,"scan_s":time.perf_counter()-beg}))
   sys.exit(0)
 except Exception as exc:
  # Unsupported inputs NEVER lead to an unsound skip.
  pass
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
    text=True,timeout=5)
  try: result=json.loads(r.stdout.splitlines()[-1])
  except (IndexError,ValueError):result={"status":"UNPARSEABLE","cert":False}
  result["exit_code"]=r.returncode
  result["stderr_sha256"]=hashlib.sha256(r.stderr.encode()).hexdigest()
  result["timeout"]=False
 except subprocess.TimeoutExpired:
  result={"status":"EXTERNAL_5S_TIMEOUT","cert":False,"timeout":True,"exit_code":None}
 result["total_wall_s"]=round(time.perf_counter()-start,6)
 result["peak_rss_kib"]=int(rss.read_text().strip()) if (
   rss.exists() and rss.read_text().strip().isdigit()) else None
 return result
def main():
 result={"status":"FIRST_RUN_INCOMPLETE","prereg":"https://github.com/yoonsj0305/NEUMANN/issues/226",
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
   order=[("old","gate","ast"),("gate","ast","old"),("ast","old","gate")][i%3]
   item={"group":group,"name":name,"source_sha256":sha,
        "expected_old_proof_positive_from_prior_receipt":group=="hoenicke" and name in HISTORIC_PROVEN,
        "execution_order":list(order)}
   for mode in order:
    item[mode]=child(group,name,path,mode,proof_file)
   result["cases"].append(item);save()
  if len(result["cases"])!=36:raise RuntimeError("MISSING_CASE")
  old_pos={r["group"]+":"+r["name"] for r in result["cases"] if r["old"]["cert"]}
  token_pos={r["group"]+":"+r["name"] for r in result["cases"] if r["gate"]["cert"]}
  ast_pos={r["group"]+":"+r["name"] for r in result["cases"] if r["ast"]["cert"]}
  wanted={"hoenicke:"+name for name in HISTORIC_PROVEN}
  if old_pos!=wanted or old_pos!=token_pos or old_pos!=ast_pos:
   raise RuntimeError("FROZEN_CERTIFICATE_PRESERVATION_REGRESSION")
  skipped_token=[r for r in result["cases"] if r["gate"]["status"].startswith("SKIP_")]
  skipped_ast=[r for r in result["cases"] if r["ast"]["status"].startswith("SKIP_")]
  if any(r["old"]["cert"] for r in skipped_ast):
   raise RuntimeError("AST_GATE_REMOVED_A_REAL_ORIGINAL_PROOF")
  bad=[r["name"] for r in result["cases"] for mode in ("old","gate","ast")
       if r[mode]["timeout"] or r[mode]["exit_code"]!=0 or
          r[mode]["status"] in ("UNPARSEABLE","PROOF_ENGINE_ERROR")]
  if bad:raise RuntimeError("BENCHMARK_ARM_ERROR:"+",".join(bad[:3]))
  old_s=sum(r["old"]["total_wall_s"] for r in result["cases"])
  tok_s=sum(r["gate"]["total_wall_s"] for r in result["cases"])
  ast_s=sum(r["ast"]["total_wall_s"] for r in result["cases"])
  result["summary"]={
   "total_cases":36,"frozen_original_source_certificates":len(wanted),
   "old_cert":len(old_pos),"r2_token_cert":len(token_pos),"r3_ast_cert":len(ast_pos),
   "r2_token_skips":len(skipped_token),"r3_total_skips":len(skipped_ast),
   "r3_new_ast_only_skips":len(skipped_ast)-len(skipped_token),
   "r3_skips_hoenicke":sum(r["group"]=="hoenicke" for r in skipped_ast),
   "r3_skips_elster":sum(r["group"]=="elster" for r in skipped_ast),
   "old_stage_wall_s":round(old_s,6),
   "r2_token_stage_wall_s":round(tok_s,6),
   "r3_exact_ast_stage_wall_s":round(ast_s,6),
   "r3_savings_over_r2_s":round(tok_s-ast_s,6),
   "r3_cost_reduction_vs_r2_pct":round(100*(tok_s-ast_s)/tok_s,4),
   "r3_preservation":"PASS_4_OF_4",
   "r3_criterion":"PASS" if ast_s<tok_s else "FAIL_NO_TOTAL_STAGE_SAVINGS",
   "all_sources_previously_opened":True,
   "no_full_fallback_or_generalization_claim":True}
  result["status"]="R3_FIRST_36_EXACT_AST_ROUTER_COMPLETE"
  result["whole_receipt_wall_s"]=round(time.perf_counter()-start,4)
  save()
  print("R3_FINAL_36_EXACT_AST_GATE",json.dumps(result["summary"],sort_keys=True),flush=True)
 except Exception as exc:
  result["status"]="FIRST_36_SOURCE_GATE_BLOCKED"
  result["first_error"]=type(exc).__name__+": "+str(exc)[:200]
  result["whole_receipt_wall_s"]=round(time.perf_counter()-start,4)
  save()
  print("R2_36_PROOF_STAGE_FIRST_FAILURE",result["first_error"],flush=True)
  raise
if __name__=="__main__":main()
