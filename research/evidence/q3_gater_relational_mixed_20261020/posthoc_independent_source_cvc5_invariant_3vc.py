"""Independent actual ORIGINAL 3VC for cvc5 emitted mixed Bool/Int
SyGuS candidates after Gate R source-declared 31 nondet globals support.

Posthoc CLASSICAL original proof. Does not confer neural/G1/Q3 PASS.
"""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
  COHORT,blob,sha,sexprs,parse_signature,compile_original,
  compile_typed_original,compile_independent_native,dual,elapsed)

def first_original_sygus_model(raw,src):
 t=time.perf_counter_ns()
 p=subprocess.run(["cvc5","--lang=sygus2","--tlimit-per=15000","-"],
    input=raw.decode("utf-8"),text=True,capture_output=True,timeout=20)
 out=p.stdout
 receipt={"cvc5_sygus_exit":p.returncode,
  "cvc5_sygus_stdout_sha256":sha(out.encode()),
  "cvc5_sygus_stdout_size":len(out.encode()),"cvc5_sygus_wall_ms":elapsed(t),
  "cvc5_stderr_prefix":p.stderr[:170]}
 if p.returncode!=0:raise RuntimeError("SOURCE_SYGUS_ORIGINAL_NO_SOLUTION:"+str(receipt))
 forms=sexprs(out.encode())
 original_sig=src["states"]
 specs=[q for q in sexprs(raw) if isinstance(q,list) and q and q[0]=="synth-inv"]
 if len(specs)!=1:raise ValueError("ORIGINAL_SYNTH_INV_SHAPE")
 target=specs[0][1]
 # cvc5 may return grouped responses; visit nested syntax without
 # accepting a stray define-fun of the wrong name or source signatures.
 result=[]
 def visit(q):
  if not isinstance(q,list):return
  if q and q[0]=="define-fun":result.append(q)
  else:
   for v in q:visit(v)
 for x in forms:visit(x)
 matched=[q for q in result if len(q)==5 and q[1]==target]
 if len(matched)!=1:raise ValueError("SYNTHESIZED_INV_NOT_UNIQUE_OR_MISSING")
 sol=matched[0]
 if sol[3]!="Bool" or parse_signature(sol[2])!=original_sig:
  raise ValueError("SYNTH_INV_SIGNATURE_MISMATCH")
 source_state={name:v for (name,_),v in zip(original_sig,src["now"])}
 inv,calls=compile_original(sol[4],source_state,{})
 if not z3.is_bool(inv):raise ValueError("CVC5_GENERATED_INV_NOT_BOOL")
 return inv,{**receipt,"unmodified_cvc5_synth_candidate":inv.sexpr(),
             "source_goal_frozen_not_rewritten":True}

def original_case(root,path,pinned):
 start=time.perf_counter_ns()
 out={"original":path,"pinned_git_blob":pinned,"status":"INITIALIZED","dual_original_full_3VC":False}
 try:
  raw=(root/path).read_bytes()
  if blob(raw)!=pinned:raise ValueError("SOURCE_GIT_BLOB_MISMATCH")
  out["original_sha256"]=sha(raw)
  src=compile_typed_original(sexprs(raw))
  native=compile_independent_native(sexprs(raw),src)
  out["original_dual_XOR"]={n:dual(z3.Xor(src[n],native[n]),"unsat",10)
      for n in ("pre","trans","post")}
  if not all(v["dual_pass"] for v in out["original_dual_XOR"].values()):
   raise ValueError("ORIGINAL_NATIVE_TYPED_SEMANTICS_NOT_DUAL")
  inv,receipt=first_original_sygus_model(raw,src)
  out["sygus_original"]=receipt
  nextinv=z3.substitute(inv,*list(zip(src["now"],src["next"])))
  vcs={"initial":z3.And(native["pre"],z3.Not(inv)),
   "consecution":z3.And(inv,native["trans"],z3.Not(nextinv)),
   "post":z3.And(inv,z3.Not(native["post"]))}
  out["actual_source_original_bad_3VC"]={key:dual(f,"unsat",12) for key,f in vcs.items()}
  out["dual_original_full_3VC"]=all(q["dual_pass"] for q in out["actual_source_original_bad_3VC"].values())
  out["status"]="ORIGINAL_CLASSICAL_SYGUS_INVARIANT_INDEPENDENTLY_PROVED" if out["dual_original_full_3VC"] else "CVC5_SYGUS_CANDIDATE_NOT_FULLY_CERTIFIED"
 except Exception as exc:
  out["status"]="ABSTAIN_ORIGINAL_CLASSICAL_PROOF"
  out["error"]=type(exc).__name__+":"+str(exc)[:330]
 out["wall_ms"]=elapsed(start)
 print("ORIGINAL_MIXED_CLASSICAL_3VC",path,out["status"],
      "DUAL",out["dual_original_full_3VC"],"ERROR",out.get("error"),flush=True)
 return out
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 t=time.perf_counter_ns()
 rows=[original_case(a.root,*item) for item in COHORT]
 report={"schema":"neumann.q3.GateR.classical_source_bound_original_solver_first.v1",
   "two_already_opened_originals_posthoc":True,
   "both_source_sha_verified":all("original_sha256" in r for r in rows),
   "original_independent_classical_3VC_dual_count":sum(r["dual_original_full_3VC"] for r in rows),
   "mixed_DRAGON_1_original_independent_3VC_proven":rows[1]["dual_original_full_3VC"],
   "xujie_original_independent_3VC_proven":rows[0]["dual_original_full_3VC"],
   "front_end_branch_bool_nondet_reused_not_retrained":True,
   "learned_causal_new_structure":"NOT_DEMONSTRATED",
   "gate_R_complete":"OPEN","gate_V":"OPEN",
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "GPU_calls":0,"paid_API_calls":0,
   "whole_wall_ms":elapsed(t),"rows":rows}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("POSTHOC_CLASSICAL_ORIGINAL_CERTIFIED",report["original_independent_classical_3VC_dual_count"],"/2")
 print("GATE_R_GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":main()
