"""Posthoc original mannadiv independent cvc5 Post audit. Candidate and budgets
preregistered in docs/research/Q3_MANNADIV_INDEPENDENT_POST_GAP_PREREG_20261019.md.
Never falsify independent cvc5 UNKNOWN into PASS. No neural training.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, time
from pathlib import Path
import z3
from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,
  check_formula,source_proof,_obligations)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

SOURCE="benchmarks/NIA/2016.ATVA_PILAT/mannadiv.sl"
BLOB="8530c3a189403f14db1f505820a65e92ba876193"
EXPECTED={"initial":"unsat","consecution":"unsat","post":"unsat"}
def blob(x):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\x00"+x).hexdigest()
def independent_cvc5(script,args,limit):
 start=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=smt2","--tlimit-per="+str(limit*1000),*args,"-"],
          input=script,encoding="utf-8",capture_output=True,timeout=limit+7)
  lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
  return {"status":lines[-1] if lines else "EMPTY","returncode":p.returncode,
          "stderr_excerpt":p.stderr[-270:],"wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
 except Exception as exc:
  return {"status":"NO_INDEPENDENT_VERDICT","error":str(exc)[:250],
          "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--root",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 raw=(a.root/SOURCE).read_bytes()
 if blob(raw)!=BLOB:raise RuntimeError("PINNED_ORIGINAL_SOURCE_CHANGED")
 forms=sexprs(raw);src=extract_mixed_original(forms)
 nat=native_original_relations(forms,src)
 nat.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,nat)
 if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
  raise RuntimeError("ORIGINAL_NATIVE_PARITY_UNPROVEN")
 if check_formula(nat["pre"])!="sat" or check_formula(z3.Not(nat["post"]))!="sat":
  raise RuntimeError("UNTRUSTWORTHY_VACUOUS_ORIGINAL")
 if len(src["now"])!=5 or src["num_bool"]!=0:raise RuntimeError("UNEXPECTED_ORIGINAL_STATE")
 # Typed variable index is inherited from the publicly frozen source:
 # (x1,x2,y1,y2,y3). No gold solution from upstream.
 x1,x2,y1,y2,y3=src["now"]
 relation=x1==x2*y1+y2+y3
 positive=x2>0
 bounds=z3.And(y3>=0,y2>=0,y2<x2)
 invariant=z3.And(relation,positive,bounds)
 inv=simplified=z3.simplify(invariant)
 if check_formula(z3.Xor(inv,invariant))!="unsat":
  raise RuntimeError("MODEL_CANDIDATE_SERIALIZATION_NOT_EQUIVALENT")
 original=source_proof(inv,nat)
 helper_only=source_proof(z3.And(positive,bounds),nat)
 without_product=source_proof(
    z3.And(x1==y2+y3,positive,bounds),nat)
 checks={
  "source_blob_sha_pinned":True,
  "three_original_AST_XOR_UNSAT":True,
  "candidate_unchanged_by_simplifier":True,
  "minimal_candidate_original_Z3_three_VC":original["accepted"],
  "source_only_bounds_insufficient":not helper_only["accepted"],
  "product_necessary_for_this_bounded_certificate":not without_product["accepted"],
 }
 frozen=check_original_candidate(a.root/SOURCE,inv.sexpr(),
   expected_source_sha256=hashlib.sha256(raw).hexdigest())
 branches=[]
 for label,flags,limit in (
  ("default_15s",[],15),
  ("internal_15s",["--decision=internal"],15),
  ("nl_tplanes_15s",["--nl-ext-tplanes"],15)):
  v={}
  for kind,formula in _obligations(inv,src,nat).items():
   s=z3.Solver();s.set(timeout=3000);s.add(formula)
   if s.check()!=z3.unsat:raise RuntimeError("SOUND_ORIGINAL_BAD_CONDITION_NOT_UNSAT")
   v[kind]=independent_cvc5(s.to_smt2(),flags,limit)
  branches.append({"label":label,"flags":flags,"timeout_s":limit,"original_vcs":v,
                   "all_three_external_unsat":all(x["status"]=="unsat" and x["returncode"]==0
                                                 for x in v.values())})
  if branches[-1]["all_three_external_unsat"]:break
 cvc5_frozen=frozen.get("cvc5_original_three_vc") or {}
 frozen_pass=(frozen.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
              and set(cvc5_frozen)==set(EXPECTED)
              and all(x["status"]=="unsat" and x["returncode"]==0
                 for x in cvc5_frozen.values()))
 any_pass=frozen_pass or any(x["all_three_external_unsat"] for x in branches)
 out={
  "schema":"neumann.q3.mannadiv.euclid.original.native-independent.v1",
  "original_source":SOURCE,
  "original_source_sha256":hashlib.sha256(raw).hexdigest(),
  "pinned_source_git_blob":BLOB,
  "published_original_pre_trans_post_semantic_XOR":parity,
  "source_only_minimal_candidate":"x1=x2*y1+y2+y3 AND x2>0 AND y3>=0 AND 0<=y2<x2",
  "source_only_minimal_original_Z3_bad_VCs":original["vcs"],
  "source_only_bounds_original_Z3_bad_VCs":helper_only["vcs"],
  "without_product_original_Z3_bad_VCs":without_product["vcs"],
  "existing_unchanged_cvc5_3000ms":cvc5_frozen,
  "existing_cvc5_3VC_FULL_PASS":frozen_pass,
  "registered_independent_cvc5_budget_variants":branches,
  "EXTERNAL_ORIGINAL_CVC5_ALL_THREE_UNSAT":any_pass,
  "gates":checks,
  "science_verdict":"INDEPENDENT_ORIGINAL_POST_CVC5_CERTIFIED" if any_pass else
                    "INDEPENDENT_ORIGINAL_POST_CVC5_UNKNOWN_NOT_PROVEN",
  "neural_math_primitive_invention":False,
  "learning_unique_over_strong_classical":False,
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "GPU_calls":0,"paid_API_calls":0}
 a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("ORIGINAL_Z3",original["vcs"])
 print("FROZEN_CVC5",json.dumps(cvc5_frozen))
 for r in branches:print("BUDGET",r["label"],{k:x["status"] for k,x in r["original_vcs"].items()})
 print("INDEPENDENT_CVC5_ORIGINAL_POST_CERTIFIED",any_pass)
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
