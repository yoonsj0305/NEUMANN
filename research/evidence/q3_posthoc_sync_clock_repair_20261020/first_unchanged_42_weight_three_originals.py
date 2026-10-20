"""Q3 original learned 42-weight discrete integrator, POSTHOC affine-clock repair.
Same frozen training sample, weights SHA and original source identity as PR #310.
All newly proposed source relations from REAL ORIGINAL Pre+Trans, no Post labels.
Each original proof independently Z3 and cvc5; exact classical receives same
affine normalized source recurrence. NOT a fresh blind G1 nor novel primitive.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import sympy as sp
import z3
from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import (
 COHORT,DEG_DELTA,DEG_F,SCALE,train_frozen_operator,proof,blob,sha,ms)
from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import (
 derive_updates,atoms,integer_eq,zcheck)
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,check_formula)

FROZEN_SHA="563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78"

def pre_unique_integer(native,expr):
 q=z3.Solver();q.set(timeout=5000);q.add(native["pre"])
 result=q.check()
 if result!=z3.sat:raise ValueError("ORIGINAL_PRE_NOT_SAT_OR_UNKNOWN")
 value=q.model().eval(expr,model_completion=True)
 if not z3.is_int_value(value):raise ValueError("PRE_VALUE_NOT_INTEGER")
 k=int(value.as_long())
 status,_=zcheck(z3.And(native["pre"],expr!=k),secs=5)
 if status!="unsat":raise ValueError("SOURCE_PRE_VALUE_NOT_UNIQUE")
 return k

def derive_synchronized_clock_context(src,native,updates):
 state=src["now"];new=src["next"]
 variables={str(q):q for q in state}
 symbols={name:sp.Symbol(name,integer=True) for name in variables}
 stat={q for q in variables if updates[q]==symbols[q]}
 clocks={q for q in variables if sp.expand(updates[q]-symbols[q])==1}
 if not clocks:raise ValueError("NO_SOURCE_VERIFIED_UNIT_CLOCK")
 starts={q:pre_unique_integer(native,variables[q]) for q in clocks}
 pivot=min(clocks,key=lambda q:(starts[q],q))
 other=[q for q in sorted(clocks) if q!=pivot]
 master=symbols[pivot]
 offsets={}
 identities=[]
 for other_clock in other:
  offset=starts[other_clock]-starts[pivot]
  w=variables[other_clock]-variables[pivot]==offset
  pre,statuspre=zcheck(z3.And(native["pre"],z3.Not(w)),secs=5)
  wp=z3.substitute(w,*list(zip(state,new)))
  conserved,statuscon=zcheck(z3.And(native["trans"],w,z3.Not(wp)),secs=8)
  if pre!="unsat" or conserved!="unsat":
   raise ValueError("SOURCE_CLOCK_DIFFERENCE_INDUCTION_NOT_CERTIFIED")
  offsets[other_clock]=offset
  identities.append({"other_clock":other_clock,"canonical_clock":pivot,
   "offset":offset,"original_Pre_bad":pre,
   "original_Trans_induction_bad":conserved,
   "source_precheck_ms":statuspre,"source_consecution_ms":statuscon})
 substitutions={symbols[q]:master+delta for q,delta in offsets.items()}
 facts=[variables[q]-variables[pivot]==delta for q,delta in offsets.items()]
 return symbols,stat,clocks,pivot,starts,substitutions,facts,identities

def models_before_post(src,native,weights):
 start=time.perf_counter_ns()
 updates,extraction_ms=derive_updates(src,native)
 symbols,stat,clocks,pivot,initials,substitutions,clock_facts,ledger=(
   derive_synchronized_clock_context(src,native,updates))
 master=symbols[pivot]
 first_learned=list(clock_facts)
 sameinfo_classical=list(clock_facts)
 produced=[];abstained=[]
 for variable in sorted(symbols):
  if variable in stat or variable in clocks:continue
  expr=sp.expand(updates[variable]-symbols[variable])
  normalized=sp.expand(expr.subs(substitutions,simultaneous=True))
  if normalized==0:continue
  if not normalized.free_symbols.issubset({master,*[symbols[q] for q in stat]}):
   abstained.append({"variable":variable,"reason":"DELTA_NONLOCAL_AFTER_CLOCK_CANONICALIZATION",
       "delta":str(expr)});continue
  try:
   delta_poly=sp.Poly(normalized,master)
  except Exception:
   abstained.append({"variable":variable,"reason":"DELTA_NONPOLYNOMIAL",
       "delta":str(normalized)});continue
  if delta_poly.degree()>DEG_DELTA: # frozen model expressive bound
   abstained.append({"variable":variable,"reason":"POLY_DEGREE_EXCEEDS_FROZEN_GRAMMAR",
     "degree":int(delta_poly.degree())});continue
  before_delta=z3.Int(variable)
  original_semantics=sp.expand(expr-normalized)
  # The arithmetic normalization must follow formally from proved
  # synchronized-clock relational invariants, not from a guess.
  from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import zexpr
  if clock_facts:
   normalization_bad=z3.And(*clock_facts,zexpr(original_semantics)!=0)
   status,_=zcheck(normalization_bad,secs=8)
   if status!="unsat":raise ValueError("SOURCE_CLOCK_NORMALIZATION_NOT_PROVED")
  base_coeffs=[sp.expand(delta_poly.nth(k)) for k in range(DEG_DELTA+1)]
  learned_coeffs=[
    sp.expand(sum(int(weights[k,p])*base_coeffs[k] for k in range(DEG_DELTA+1))/SCALE)
    for p in range(DEG_F+1)]
  F=sp.expand(sum(c*master**p for p,c in enumerate(learned_coeffs)))
  tau=sp.Symbol("_source_index_",integer=True)
  exact=sp.expand(sp.summation(normalized.subs(master,tau),
                     (tau,0,master-1)))
  if sp.expand(F.subs(master,master+1)-F-normalized)!=0:
   raise ValueError("FROZEN_WEIGHT_MATRIX_FAILED_DISCRETE_CERT")
  if sp.expand(exact.subs(master,master+1)-exact-normalized)!=0:
   raise ValueError("CLASSICAL_SYMBOLIC_ANTIDIFFERENCE_FAILED")
  acc0=pre_unique_integer(native,z3.Int(variable))
  clock0=initials[pivot]
  learned_term=sp.expand(symbols[variable]-acc0-(F-F.subs(master,clock0)))
  baseline_term=sp.expand(symbols[variable]-acc0-(exact-exact.subs(master,clock0)))
  syms=list(symbols.values())
  learned_formula,learned_desc=integer_eq(learned_term,syms)
  class_formula,class_desc=integer_eq(baseline_term,syms)
  learned_pre,_=zcheck(z3.And(native["pre"],z3.Not(learned_formula)),secs=4)
  class_pre,_=zcheck(z3.And(native["pre"],z3.Not(class_formula)),secs=4)
  if learned_pre!="unsat" or class_pre!="unsat":
   raise ValueError("SOURCE_ANCHORED_CANDIDATE_PRE_BAD")
  first_learned.append(learned_formula)
  sameinfo_classical.append(class_formula)
  produced.append({"canonical_clock":pivot,"clock_initial_value":clock0,
    "accumulator":variable,"accumulator_initial_value":acc0,
    "delta_as_original":str(expr),"delta_after_proved_clock_normalization":str(normalized),
    "frozen_learned_polynomial":str(F),"learned_source_equation":learned_desc,
    "exact_classical_polynomial":str(exact),"classical_source_equation":class_desc,
    "algebraic_frozen_discrete_delta_certificate":True,
    "classical_discrete_delta_certificate":True})
 # Source only Pre and Trans guard facets identical in both arms.
 for q in sorted(clocks|stat):
  f=z3.Int(q)>=0
  st,_=zcheck(z3.And(native["pre"],z3.Not(f)),secs=4)
  if st=="unsat":first_learned.append(f);sameinfo_classical.append(f)
 for g in atoms(native["trans"]):
  if g.decl().kind()!=z3.Z3_OP_LT:continue
  lhs,rhs=g.children()
  if str(lhs) not in clocks:continue
  if not(z3.is_int_value(rhs) or str(rhs) in stat):continue
  f=lhs<=rhs
  st,_=zcheck(z3.And(native["pre"],z3.Not(f)),secs=4)
  if st=="unsat":first_learned.append(f);sameinfo_classical.append(f)
 if not produced:raise ValueError("NO_UNAMBIGUOUS_POLYNOMIAL_ACCUMULATOR")
 learned_inv=z3.And(*first_learned)
 strong_inv=z3.And(*sameinfo_classical)
 return learned_inv,strong_inv,{"canonical_master_clock":pivot,
   "all_plus_one_clocks":sorted(clocks),
   "all_exact_static_parameters":sorted(stat),
   "source_initial_unit_clock_values":initials,
   "all_original_initial_and_trans_inductive_clock_offsets":ledger,
   "learned_unseen_polynomials":produced,
   "unsupported_accumulators":abstained,
   "source_only_rewrite_and_generation_ms":ms(start),
   "source_update_original_exact_entailment_ms":extraction_ms}

def run(root,path,identity,weights):
 t=time.perf_counter_ns()
 row={"source":path,"expected_original_git_blob":identity,
   "frozen_learned_original_dual_3VC":False,
   "equal_info_exact_classical_original_dual_3VC":False}
 try:
  raw=(root/path).read_bytes()
  if blob(raw)!=identity:raise ValueError("SOURCE_IDENTITY_MISMATCH")
  row["original_source_sha256"]=sha(raw)
  forms=sexprs(raw);src=extract_mixed_original(forms)
  native=native_original_relations(forms,src)
  native.update({"now":src["now"],"next":src["next"]})
  parity=check_parity(src,native)
  row["native_original_semantic_xor_parity"]=parity
  if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
   raise ValueError("ORIGINAL_SEMANTIC_XOR_FAIL")
  if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
   raise ValueError("UNPROVEN_SOURCE_NONVACUITY")
  learned,classical,extract=models_before_post(src,native,weights)
  row["source_only_affine_clock_normalization"]=extract
  row["learned_candidate_SMT"]=learned.sexpr()
  row["exact_classical_candidate_SMT"]=classical.sexpr()
  row["learned_published_original_3VC"],row["frozen_learned_original_dual_3VC"]=proof(learned,src,native)
  row["classical_published_original_3VC"],row["equal_info_exact_classical_original_dual_3VC"]=proof(classical,src,native)
  row["status"]="POSTHOC_FEATURE_ADAPTER_DUAL_PASS_CLASSICAL_TIE" if (
    row["frozen_learned_original_dual_3VC"] and
    row["equal_info_exact_classical_original_dual_3VC"]) else "NO_FULL_DUAL_ORIGINAL_PROOF"
 except Exception as exc:
  row["status"]="ABSTAIN_SOURCE_OR_PROOF_UNSUPPORTED"
  row["error"]=type(exc).__name__+":"+str(exc)[:320]
 row["case_wall_ms"]=ms(t)
 return row

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 args=p.parse_args()
 beginning=time.perf_counter_ns()
 weights,original_training=train_frozen_operator()
 if original_training["frozen_trained_weights_sha256"]!=FROZEN_SHA:
  raise RuntimeError("PREVIOUS_42_TRAINED_WEIGHT_IDENTITY_CHANGED")
 assert original_training["heldout_64_full_integer_coefficient_predictions_exact"]==64
 rows=[run(args.root,path,identity,weights) for path,identity in COHORT]
 for row in rows:print("POSTHOC_SYNCHRONOUS_CLOCK_ORIGINAL",row["source"],
   "LEARNED",row["frozen_learned_original_dual_3VC"],
   "CLASSICAL",row["equal_info_exact_classical_original_dual_3VC"],
   "STATUS",row["status"],"ERROR",row.get("error"),flush=True)
 report={"schema":"neumann.q3.fixed42w.posthoc_source_affine_clock_lifting.v1",
   "attribution":"POSTHOC after previous original 2/3; not prospective G1",
   "original_immutable_first_learned_real_3VC_was_2_of_3":True,
   "frozen_trained_operator":original_training,
   "new_source_adapter_retrained_any_weights":False,
   "all_original_Git_blobs_unchanged":len(rows)==3 and all("original_source_sha256" in r for r in rows),
   "original_lifted_full_dual_3VC_count":sum(r["frozen_learned_original_dual_3VC"] for r in rows),
   "original_equal_info_classical_full_dual_3VC_count":sum(
      r["equal_info_exact_classical_original_dual_3VC"] for r in rows),
   "outside_fixed_degree6_polynomial_grammar":False,
   "first_blind_new_third_source_success":False,
   "learned_unique_superiority_over_classical":False,
   "G1_real_source_family_blind":"OPEN",
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "GPU_calls":0,"paid_API_calls":0,
   "whole_study_wall_ms":ms(beginning),"cases":rows}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("POSTHOC_SOURCE_AFFINE_CROSS_CLOCK_DUAL",report["original_lifted_full_dual_3VC_count"],"/3")
 print("SAMEINFO_EXACT_CLASSICAL_DUAL",report["original_equal_info_classical_full_dual_3VC_count"],"/3")
 print("GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":main()
