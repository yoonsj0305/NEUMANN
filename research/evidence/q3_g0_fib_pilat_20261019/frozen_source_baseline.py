"""Q3 G0 first fresh-author-source BASELINE ONLY. Frozen target identities preregistered
docs/research/Q3_G0_FIB_PILAT_ORIGINAL_PRE_SOURCE_FREEZE_20261019.md
Neither neural training nor source-specific classical algorithm tuning permitted here.
"""
from __future__ import annotations
import argparse,hashlib,json,time,traceback
from pathlib import Path
import z3

from experiments.q3_source_prove import (
    sexprs,extract_mixed_original,native_original_relations,check_parity,
    check_formula,source_proof,measured_solve,houdini,
    all_exact_branch_updates,common_kernels,actual_relation,
    prove_candidate_relation
)
from first_proof_gated_lazy_fallback import independent_native_bad_query
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

REV="6ac90265b11431c9477dfbd33e3e3380234c0499"
FROZEN=(
  ("2016.ATVA_PILAT","benchmarks/NIA/2016.ATVA_PILAT/mannadiv.sl",
   "8530c3a189403f14db1f505820a65e92ba876193"),
  ("2017.ASE_FiB","benchmarks/LIA/2017.ASE_FiB/fib_01.sl",
   "480ddf9d1ddb0c2c3e6d2aabf6af2e38f8f26f09"),
  ("2017.ASE_FiB","benchmarks/LIA/2017.ASE_FiB/fib_04.sl",
   "92cf26303dd2fd754a28f532e2333bcaaaf4634c"),
)
def blob(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()
def ms(start):
 return round((time.perf_counter_ns()-start)/1e6,3)
def candidate_from_source(selected,src,native):
 if selected=="POST_ONLY":return native["post"]
 if selected=="OCTAGON_HOUDINI":
  if src["num_bool"]:raise ValueError("OCTAGON_BOOL_UNSUPPORTED")
  inv,*_=houdini(native["pre"],native["trans"],src["now"],src["next"])
  return inv
 if selected=="BRANCH_AFFINE_NULLSPACE":
  branches=all_exact_branch_updates(src)
  terms=[]
  for rel in common_kernels(branches,src):
   p=actual_relation(rel,src["now"])
   if prove_candidate_relation(src,native,p)["source_certified"]:terms.append(p)
  return z3.And(native["post"],*terms)
 raise ValueError("NO_CANDIDATE_FOR_NATIVE_SPACER")

def one(root,group,rel,expect):
 path=root/rel;raw=path.read_bytes()
 got=blob(raw)
 if expect!=got:raise ValueError("FROZEN_GIT_BLOB_MISMATCH "+rel)
 receipt={"origin_group":group,"source":rel,"git_blob":got,
          "source_sha256":hashlib.sha256(raw).hexdigest(),
          "bytes":len(raw),"original_validity":"UNDETERMINED",
          "classical":{},"g0":"NOT_ASSESSED"}
 t0=time.perf_counter_ns()
 try:
  forms=sexprs(raw)
  src=extract_mixed_original(forms)
  native=native_original_relations(forms,src)
  native.update({"now":src["now"],"next":src["next"]})
  receipt["state_int_count"]=len(src["now"])
  receipt["state_bool_count"]=src["num_bool"]
  parity=check_parity(src,native)
  receipt["native_source_pre_trans_post_xor_parity"]=parity
  if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
   receipt["original_validity"]="ORIGINAL_PARSER_MISMATCH"
   return receipt
  pre=check_formula(native["pre"])
  not_post=check_formula(z3.Not(native["post"]))
  trans=check_formula(native["trans"])
  receipt["nonvacuity"]={"pre_sat":pre,"some_state_violates_post":not_post,"trans_sat":trans}
  if pre!="sat" or not_post!="sat":
   receipt["original_validity"]="ORIGINAL_VACUOUS_OR_UNKNOWN"
   return receipt
  receipt["original_validity"]="NONVACUOUS_PARSED_PARITY_PASS"

  t=time.perf_counter_ns()
  result=measured_solve(src,native)
  receipt["classical"]["full_frozen_source_only_portfolio"]=result
  receipt["classical"]["full_portfolio_measured_wall_ms"]=ms(t)

  t=time.perf_counter_ns()
  try:
   spac=independent_native_bad_query(native,src["now"],src["next"])
   receipt["classical"]["direct_strong_z3_spacer"]={
      "status":spac["status"],
      "native_solver_wall_ms":spac.get("native_solver_wall_ms"),
      "whole_python_wall_ms":ms(t)}
  except Exception as exc:
   receipt["classical"]["direct_strong_z3_spacer"]={
      "status":"ERROR","reason":type(exc).__name__+":"+str(exc)[:250],
      "whole_python_wall_ms":ms(t)}

  selected=result.get("selected")
  original_vcs=result.get("original_three_vc")
  receipt["classical"]["original_Z3_certified"]=(selected is not None and
      selected!="NONE" and original_vcs=={"initial":"unsat","consecution":"unsat","post":"unsat"})
  receipt["classical"]["independent_cvc5_attempted"]=False
  if receipt["classical"]["original_Z3_certified"]:
   t=time.perf_counter_ns()
   try:
    cand=candidate_from_source(selected,src,native)
    ext=check_original_candidate(path,cand.sexpr(),
       expected_source_sha256=hashlib.sha256(raw).hexdigest())
    cv=ext.get("cvc5_original_three_vc") or {}
    receipt["classical"]["independent_cvc5_attempted"]=True
    receipt["classical"]["independent_cvc5_three_vc"]=cv
    receipt["classical"]["independent_cvc5_certified"] = (
       ext.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5" and
       set(cv)=={"initial","consecution","post"} and
       all(x.get("status")=="unsat" and x.get("returncode")==0 for x in cv.values()))
   except Exception as e:
    receipt["classical"]["independent_cvc5_error"]=type(e).__name__+":"+str(e)[:250]
   receipt["classical"]["independent_wall_ms"]=ms(t)
  if (receipt["classical"]["original_Z3_certified"] or
       receipt["classical"]["direct_strong_z3_spacer"]["status"]=="unsat"):
   receipt["g0"]="NO_GO_CLASSICAL_ALREADY_CERTIFIED"
  else:
   receipt["g0"]="UNRESOLVED_HEADROOM_CANDIDATE_NOT_PROOF_OF_SAFE_PROGRAM"
 except Exception as exc:
  receipt["original_validity"]="CLASSICAL_BASELINE_ERROR_OR_UNSUPPORTED"
  receipt["error"]=type(exc).__name__+":"+str(exc)[:350]
  receipt["g0"]="UNSUPPORTED_NO_G0_HEADROOM_INFERENCE"
 receipt["whole_case_wall_ms"]=ms(t0)
 return receipt

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args()
 results=[]
 for group,rel,expect in FROZEN:
  t=time.perf_counter_ns()
  try:
   result=one(args.root,group,rel,expect)
  except Exception as e:
   result={"origin_group":group,"source":rel,"git_blob":expect,
    "g0":"FAIL_CLOSED_SOURCE_IDENTITY_OR_IO",
    "error":type(e).__name__+":"+str(e)[:300]}
  result["runner_case_wall_ms"]=ms(t)
  results.append(result)
  print("CASE",rel,"ORIGINAL",result.get("original_validity"),
        "G0",result["g0"],"CLASSIC",result.get("classical",{}).get("full_frozen_source_only_portfolio",{}).get("selected"))
 all_hash_verified=all(r.get("git_blob")==expect and "source_sha256" in r
                   for r,(_,_,expect) in zip(results,FROZEN))
 valid=[r for r in results if r.get("original_validity")=="NONVACUOUS_PARSED_PARITY_PASS"]
 unresolved=[r for r in valid if r["g0"]=="UNRESOLVED_HEADROOM_CANDIDATE_NOT_PROOF_OF_SAFE_PROGRAM"]
 no_go=[r for r in valid if r["g0"]=="NO_GO_CLASSICAL_ALREADY_CERTIFIED"]
 out={"schema":"neumann.q3.g0.fib-pilat.classical-first.v1",
 "frozen_source_upstream_revision":REV,
 "global_Q1_Q7":"OPEN","global_Q3":"OPEN",
 "neural_training_on_frozen_sources":False,
 "source_identity_all_verified":all_hash_verified,
 "valid_originals":len(valid),"classical_certified":len(no_go),
 "headroom_candidates_not_safe_proofs":len(unresolved),
 "g0_decision":"UNRESOLVED_NEEDS_SEMANTIC_SPECIALIST_PROOF" if unresolved else
              "NO_GO_LEARNING_ON_CLASSICALLY_SOLVED" if valid and len(no_go)==len(valid) else
              "INVALID_OR_INSUFFICIENT_G0_EVIDENCE",
 "all_cohort_rows_included":len(results)==3,"cases":results}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print("FIRST_G0_ALL_SHA_MATCH",all_hash_verified)
 print("FIRST_G0",out["g0_decision"])
 print("GLOBAL_Q3",out["global_Q3"])

if __name__=="__main__":main()
