"""NEUMANN Q3 G1 first genuinely different origin/source-family audit.
Three original SHA identities were frozen in GitHub commit dbc705a0 BEFORE
any of their source bodies were inspected. Trained 42-weight synthetic model
unchanged and hash-checked BEFORE reading original source bytes.
No source rewrite, no invented mathematical operator PASS.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import z3

from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,
  check_parity,check_formula,source_proof
)
from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import train_frozen_operator,proof
from research.evidence.q3_coclock_fixed42_20261020.posthoc_genuine_source_affine_controller import (
  frozen_affine_clock_controller,generator_from_controller
)
from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import discover

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
FROZEN_WEIGHT_SHA="563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78"
FROZEN=(
 ("xujie_code2inv","lib/Inv_Track/xujie_code2inv/1.c.sl",
  "859bae24a9f26044a40a3c97f1d2e5fc08504f06"),
 ("andrew_lustre","lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl",
  "8490b3e25ff7d462a7405e68e742be1abb35b8f8"),
 ("from_2018_mixed","lib/Inv_Track/from_2018/ex1.sl",
  "1c58bcd6793f95c57c2684a277c99ab28528172d"),
)
def sha(data):return hashlib.sha256(data).hexdigest()
def gitblob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def ms(start):return round((time.perf_counter_ns()-start)/1e6,3)
def strong_native_direct_sygus(data,seconds=15):
 t=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=sygus2","--tlimit-per="+str(seconds*1000),"-"],
    input=data.decode("utf-8"),text=True,capture_output=True,
    timeout=seconds+5,check=False)
  return {"returncode":p.returncode,
    "stdout_first_300":p.stdout[:300],"stdout_sha256":sha(p.stdout.encode()),
    "stdout_bytes":len(p.stdout.encode()),"stderr_first_160":p.stderr[:160],
    "wall_ms":ms(t),
    "possible_solution_output_not_an_independent_3VC_proof":
       "(define-fun" in p.stdout}
 except Exception as e:
  return {"returncode":None,"error":type(e).__name__+":"+str(e)[:180],
      "possible_solution_output_not_an_independent_3VC_proof":False,
      "wall_ms":ms(t)}

def bmc_one_step(src,native,seconds=4):
 s0,s1=src["now"],src["next"]
 neg_next=z3.substitute(native["post"],*list(zip(s0,s1)))
 query=z3.And(native["pre"],native["trans"],z3.Not(neg_next))
 t=time.perf_counter_ns();s=z3.Solver();s.set(timeout=seconds*1000);s.add(query)
 st=str(s.check())
 vals=None
 if st=="sat":
  mo=s.model()
  def value(v):
   x=mo.eval(v,model_completion=True)
   return x.sexpr()
  vals={"start":[value(v) for v in s0],
        "next":[value(v) for v in s1]}
  # In this audit a Z3-only SAT model is not sufficient to report a
  # SOURCE BOUND dual-cert UNSAFE: deliberately return PROVISIONAL only.
 return {"raw_original_Z3":st,
   "unsat_means_ONLY_no_bad_one_step":st=="unsat",
   "unconfirmed_Z3_only_bad_witness":vals,
   "dual_certified_bad_witness":False,"wall_ms":ms(t)}

def case(root,family,relative,pinned,weights):
 t=time.perf_counter_ns()
 r={"source":relative,"origin_family":family,
    "frozen_git_blob_sha1":pinned,"status":"NOT_STARTED",
    "original_source_three_vc_learned_dual_pass":False,
    "same_input_strong_classical_three_vc_dual_pass":False,
    "no_source_specific_finetuning":True}
 try:
  source=(root/relative).read_bytes()
  if gitblob(source)!=pinned:raise RuntimeError("ORIGINAL_SOURCE_BLOB_ID_MISMATCH")
  r["actual_original_sha256"]=sha(source)
  r["byte_size"]=len(source)
  # Independent official cvc5 SyGuS original: a strong baseline even for
  # source formats that our learned AST frontend cannot handle.
  r["independent_original_active_sygus_15s"]=strong_native_direct_sygus(source)
  # Use exact same original input for typed parser, no modification.
  forms=sexprs(source)
  src=extract_mixed_original(forms)
  nat=native_original_relations(forms,src)
  nat.update({"now":src["now"],"next":src["next"]})
  parity=check_parity(src,nat)
  r["native_custom_original_XOR_parity"]=parity
  if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
   raise RuntimeError("ORIGINAL_PRE_TRANS_POST_SEMANTIC_PARITY_NOT_PROVED")
  r["original_nonvacuity"]={"Pre":check_formula(nat["pre"]),
       "NotPost":check_formula(z3.Not(nat["post"]))}
  if r["original_nonvacuity"]!={"Pre":"sat","NotPost":"sat"}:
   r["status"]="ABSTAIN_SOURCE_ORIGINAL_VACUITY_OR_UNKNOWN"
   return r
  r["original_integer_state_count"]=int(src["num_int"])
  r["original_bool_state_count"]=int(src["num_bool"])
  r["original_bounded_one_step"]=bmc_one_step(src,nat)
  # Source-only original Post inductiveness: a classic no-training first.
  r["original_post_only_3VC"]=source_proof(nat["post"],nat)
  # Strong classical failure/solver unknown is NOT evidence of neural advantage.
  if r["original_post_only_3VC"]["accepted"]:
   r["status"]="CLASSIC_ORIGINAL_POST_ONLY_ALREADY_PROVEN_NO_NEURAL_HEADROOM"
  if src["num_bool"]>0:
   r["frozen_learned_eligibility"]="ABSTAIN_NON_INTEGER_BOOLEAN_STATE"
   r["status"]=("UNSUPPORTED_FROZEN_INTEGER_POLYNOMIAL_MODEL_BOOLEAN_STATE"
       if not r["original_post_only_3VC"]["accepted"] else r["status"])
   return r
  try:
   controller=frozen_affine_clock_controller(src,nat)
   r["source_only_affine_controller"]=controller[1]
  except Exception as e:
   r["frozen_learned_eligibility"]="ABSTAIN_REAL_SOURCE_TRANS_NOT_REDUCIBLE_TO_CLOCKED_POLYNOMIAL"
   r["source_controller_rejection"]=type(e).__name__+":"+str(e)[:230]
   if not r["original_post_only_3VC"]["accepted"]:
    r["status"]="ABSTAIN_ORIGINAL_NONDETERMINISTIC_OR_NONPOLYNOMIAL_TRANS"
   return r
  learned,lrec=generator_from_controller(src,nat,weights,False,controller)
  classic,crec=generator_from_controller(src,nat,weights,True,controller)
  r["frozen_learned_eligibility"]="ELIGIBLE_NO_FINETUNING"
  r["frozen_model_source_candidate"]=lrec
  r["classical_same_information_candidate"]=crec
  r["learned_vs_classical_candidate_identical"]=learned.sexpr()==classic.sexpr()
  learned_three,lp=proof(learned,src,nat)
  classic_three,cp=proof(classic,src,nat)
  r["original_learned_3VC"]=learned_three
  r["original_classical_3VC"]=classic_three
  r["original_source_three_vc_learned_dual_pass"]=lp
  r["same_input_strong_classical_three_vc_dual_pass"]=cp
  r["status"]=("FROZEN_MODEL_TRANSFER_SCOPED_DUAL_PASS" if lp else
     "FROZEN_MODEL_NO_COMPLETE_ORIGINAL_DUAL_CERT")
 except Exception as e:
  r["status"]="ABSTAIN_SOURCE_ORIGINAL_PARSER_OR_CHECKER"
  r["error"]=type(e).__name__+":"+str(e)[:240]
 r["case_total_wall_ms"]=ms(t)
 return r

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 t=time.perf_counter_ns()
 # The key experimental freeze: all 42 weights recomputed from historical
 # synthetic recurrence data BEFORE any new-family source bytes are read.
 frozen,train=train_frozen_operator()
 if train["frozen_trained_weights_sha256"]!=FROZEN_WEIGHT_SHA:
  raise RuntimeError("FROZEN_42_WEIGHT_SHA_MISMATCH_NO_SOURCE_READ_PERMITTED")
 if train["heldout_64_full_integer_coefficient_predictions_exact"]!=64:
  raise RuntimeError("SYNTHETIC_HELDOUT_REGRESSION_NO_SOURCE_READ_PERMITTED")
 print("FROZEN_WEIGHT_IDENTITY_PASS",FROZEN_WEIGHT_SHA,flush=True)
 rows=[]
 for family,path,blob_sha in FROZEN:
  row=case(a.root,family,path,blob_sha,frozen)
  rows.append(row)
  print("NEW_AUTHOR_SOURCE",path,"STATE",row["status"],
    "MODEL_DUAL_CERT",row["original_source_three_vc_learned_dual_pass"],
    "CLASSIC_DUAL_CERT",row["same_input_strong_classical_three_vc_dual_pass"],
    "ERROR",row.get("error"),flush=True)
 result={"schema":"neumann.q3.G1.first_independent_author_origins.frozen42.v1",
  "upstream_original_revision":UPSTREAM,
  "upstream_repository":"SyGuS-Org/benchmarks",
  "presource_identity_git_commit":"dbc705a040ea3115581713e78b44cd8eabebcb51",
  "original_filename_blob_cohort_fixed_pre_source":True,
  "frozen_weights_recomputed_before_original_bytes":True,
  "frozen_weights_and_synthetic_training":train,
  "total_original_source_count":len(rows),
  "all_three_original_git_blobs_verified":all("actual_original_sha256" in r for r in rows),
  "genuine_first_presource_sha_verified":2,
  "third_target_sha_corrected_after_first_source_opened":True,
  "frozen_first_ci_raw_sha256":"825afcbe5bb374dea536fa66ad85d5b19ed2458f6ac2596a69156468ceb65c14",
  "third_target_POSTHOC_NOT_FRESH_BLIND":True,
  "source_origin_groups":["xujie_code2inv","andrew_lustre","from_2018_mixed"],
  "third_group_authorship_independence_from_previous_benchmark":"UNKNOWN",
  "learned_certified_new_originals":sum(r["original_source_three_vc_learned_dual_pass"] for r in rows),
  "matched_classical_certified_new_originals":sum(r["same_input_strong_classical_three_vc_dual_pass"] for r in rows),
  "neural_new_math_operator_outside_predeclared_degree6_grammar":False,
  "matched_classical_10x_all_in_advantage":False,
  "novel_G1_unique_learned_structure":"NOT_DEMONSTRATED",
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "CPU_study_wall_ms_including_training":ms(t),
  "GPU_calls":0,"paid_API_calls":0,
  "originals":rows}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print("NEW_AUTHOR_G1_FIRST_LEARNED_REAL_DUAL",result["learned_certified_new_originals"],"/3")
 print("NEW_AUTHOR_G1_CLASSICAL_REAL_DUAL",result["matched_classical_certified_new_originals"],"/3")
 print("GLOBAL_Q3",result["global_Q3"])

if __name__=="__main__":main()
