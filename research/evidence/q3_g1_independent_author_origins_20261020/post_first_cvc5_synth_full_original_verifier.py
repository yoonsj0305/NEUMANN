"""Post-first-G1 independent audit of cvc5's original synthesized invariant.
The SHA-frozen learned first result remains 0 eligible/2 valid-blind sources.
One third SHA typo was repaired after contents were opened; not a blind win.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
import z3
from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,check_formula
)
from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import proof

MIXED=Path(__file__).resolve().parents[3]/"research/evidence/q3t-mixed-original-20261018"
sys.path.insert(0,str(MIXED))
from mixed_sygus_original import compile_original,parse_signature

COHORT=(
 ("BLIND_VALID_ORIGINAL","lib/Inv_Track/xujie_code2inv/1.c.sl",
   "859bae24a9f26044a40a3c97f1d2e5fc08504f06"),
 ("BLIND_VALID_ORIGINAL","lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl",
   "8490b3e25ff7d462a7405e68e742be1abb35b8f8"),
 ("POSTHOC_CORRECTED_SHA","lib/Inv_Track/from_2018/ex1.sl",
   "1c58bcd6793f95c57c2684a277c99ab28528172d"),
)
REV="13c8deb68a873635879c9a69bc78caebd340f646"
FIRST_RAW_SHA="825afcbe5bb374dea536fa66ad85d5b19ed2458f6ac2596a69156468ceb65c14"
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def elapsed(t):return round((time.perf_counter_ns()-t)/1e6,3)
def cvc5_synth(data):
 t=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=sygus2","--tlimit-per=15000","-"],
   input=data.decode("utf-8"),capture_output=True,text=True,timeout=20)
  return p.stdout,{"returncode":p.returncode,"wall_ms":elapsed(t),
    "stderr_excerpt":p.stderr[:160],"stdout_sha256":sha(p.stdout.encode()),
    "stdout_bytes":len(p.stdout.encode()),
    "candidate_emitted_not_independent_proof":"(define-fun " in p.stdout}
 except Exception as exc:
  return "",{"returncode":None,"wall_ms":elapsed(t),"error":str(exc)[:200],
    "candidate_emitted_not_independent_proof":False}
def solution_expr(stdout,raw,src):
 forms=sexprs(stdout.encode("utf-8"))
 invspec=next(x for x in sexprs(raw) if isinstance(x,list) and x and x[0]=="synth-inv")
 signature=parse_signature(invspec[2])
 all_forms=[]
 def visit(node):
  if not isinstance(node,list):return
  if node and node[0]=="define-fun":all_forms.append(node)
  else:
   for c in node:visit(c)
 for f in forms:visit(f)
 sol=[f for f in all_forms if f[1]==invspec[1]]
 if len(sol)!=1:raise ValueError("SYNTHESIZED_SOURCE_INV_MISSING_OR_AMBIGUOUS")
 if parse_signature(sol[0][2])!=signature:raise ValueError("SYNTH_SOURCE_FORMAL_SIGNATURE_DIFFERS")
 if sol[0][3]!="Bool":raise ValueError("SYNTH_NOT_BOOL")
 env={name:src["now"][i] for i,(name,sort) in enumerate(signature)}
 expr,calls=compile_original(sol[0][4],env,{})
 if not z3.is_bool(expr):raise ValueError("SYNTH_NOT_BOOL_FORMULA")
 return expr

def case(root,kind,relative,expected):
 t=time.perf_counter_ns()
 r={"source":relative,"source_presolve_sha_role":kind,
    "original_git_blob_sha1":expected,"status":"INITIALIZED",
    "source_original_cvc5_generated_invariant_dual_3VC":False}
 try:
  source=(root/relative).read_bytes()
  if blob(source)!=expected:raise ValueError("GIT_BLOB_MISMATCH")
  r["original_bytes_sha256"]=sha(source)
  stdout,cli=cvc5_synth(source)
  r["original_cvc5_sygus_synthesis"]=cli
  if not cli["candidate_emitted_not_independent_proof"] or cli["returncode"]!=0:
   r["status"]="NO_ACTIVE_SYGUS_SOLUTION_WITHIN_15S"
   return r
  try:
   parsed=sexprs(source);src=extract_mixed_original(parsed)
   original=native_original_relations(parsed,src)
   original.update({"now":src["now"],"next":src["next"]})
   parity=check_parity(src,original)
   r["original_native_custom_parity"]=parity
   if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
    raise ValueError("ORIGINAL_SOURCE_XOR_PARITY_NOT_PROVEN")
   if check_formula(original["pre"])!="sat" or check_formula(z3.Not(original["post"]))!="sat":
    raise ValueError("ORIGINAL_NONVACUITY_NOT_PROVEN")
   proposed=solution_expr(stdout,source,src)
   r["synthesized_invariant_z3_smt"]=proposed.sexpr()
   r["synthesized_candidate_sha256"]=sha(proposed.sexpr().encode())
   original_3vc,dual=proof(proposed,src,original)
   r["actual_published_original_3VC_Z3_independent_cvc5"]=original_3vc
   r["source_original_cvc5_generated_invariant_dual_3VC"]=bool(dual)
   r["status"]="SOURCE_SYGUS_CLASSICAL_DUAL_ORIGINAL_3VC_CERTIFIED" if dual else "INDEPENDENT_ORIGINAL_PROOF_UNKNOWN_OR_FAIL"
  except Exception as exc:
   r["status"]="CVC5_SOLUTION_EMITTED_BUT_INDEPENDENT_NATIVE_VERIFIER_UNSUPPORTED"
   r["verifier_error"]=type(exc).__name__+":"+str(exc)[:220]
 except Exception as exc:
  r["status"]="ORIGINAL_SOURCE_FETCH_OR_HASH_OR_RUN_ERROR"
  r["error"]=type(exc).__name__+":"+str(exc)[:200]
 r["case_wall_ms"]=elapsed(t)
 return r

def main():
 a=argparse.ArgumentParser()
 a.add_argument("--root",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 args=a.parse_args()
 t=time.perf_counter_ns()
 rows=[case(args.root,*x) for x in COHORT]
 for q in rows:
  print("NEW_SOURCE_CLASSICAL_PROOF",q["source"],q["status"],
   "DUAL_ORIGINAL_3VC",q["source_original_cvc5_generated_invariant_dual_3VC"],flush=True)
 out={"schema":"neumann.q3.g1.external_origins.cvc5_generated_invariant.native3VC.v1",
 "external_upstream_git_rev":REV,"first_G1_raw_JSON_preserved":FIRST_RAW_SHA,
 "first_valid_blind_source_count":2,"third_SHA_corrected_POSTHOC_not_blind":True,
 "all_three_original_sources_sha_authenticated":all("original_bytes_sha256" in q for q in rows),
 "external_valid_blind_cvc5_dual_native_original_3VC":sum(
   q["source_original_cvc5_generated_invariant_dual_3VC"] for q in rows[:2]),
 "posthoc_third_classical_dual_native_original_3VC":int(
   rows[2]["source_original_cvc5_generated_invariant_dual_3VC"]),
 "original_dual_certified_cvc5_synthesized_count":sum(
   q["source_original_cvc5_generated_invariant_dual_3VC"] for q in rows),
 "G1_unique_learned_new_operator":"NOT_DEMONSTRATED",
 "learned_frozen42_first_external_dual_certified":0,
 "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
 "GPU_calls":0,"paid_API_calls":0,"wall_ms":elapsed(t),"cases":rows}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
 print("EXTERNAL_CVC5_SYNTH_ACTUAL_NATIVE_DUAL_3VC",
    out["original_dual_certified_cvc5_synthesized_count"],"/3")
 print("GLOBAL_Q3",out["global_Q3"])

if __name__=="__main__":main()
