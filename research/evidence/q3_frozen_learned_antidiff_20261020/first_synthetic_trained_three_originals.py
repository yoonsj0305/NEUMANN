"""Q3 learned 42-weight coefficient-producing operator, FIRST real unseen source.
Synthetic numeric recurrence traces only for training, no actual source labels.
Pre/source-blob identities frozen in previous commit b300aa21. CLASSICAL control
gets exactly same Pre/Trans and same native Z3/cvc5 original proof budgets.
G1/global Q3 remain OPEN because grammar is fixed and exact classical is stronger.
"""
from __future__ import annotations
import argparse,hashlib,json,math,time
from pathlib import Path
import numpy as np
import sympy as sp
import z3
from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import (
 blob,sha,ms,atoms,derive_updates,zexpr,integer_eq,zcheck,cvc,discover)
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,check_formula)

COHORT=(
 ("benchmarks/NIA/other/pottsumm2.sl","81eda39a343064ade00393afc3b7ac85f296dddf"),
 ("benchmarks/NIA/other/pottsumm4.sl","58e7abf2b607dafefaacd8f3007a1cc6e2cbe399"),
 ("benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-4.desugared.sl","7981b1ebef61779043278aabc250d17eab3d3a1b"))
TRAIN_SEED=20261020
HOLDOUT_SEED=20261021
TRAIN_SIZE=384
HOLDOUT_SIZE=64
DEG_DELTA=5
DEG_F=6
SCALE=5040
NUMERIC_EXACT_TOL=1e-6

def generate_recurrence_data(seed,count):
 rng=np.random.default_rng(seed)
 rows=rng.integers(-3,4,size=(count,DEG_DELTA+1),dtype=np.int64)
 polyvar=sp.Symbol("t",integer=True)
 targets=np.zeros((count,DEG_F+1),dtype=np.int64)
 for j,coeff in enumerate(rows):
  delta=[sum(int(coeff[k])*u**k for k in range(DEG_DELTA+1)) for u in range(DEG_F)]
  prefix=[0]
  for d in delta:prefix.append(prefix[-1]+d)
  polynomial=sp.Poly(sp.interpolate([(t,int(prefix[t])) for t in range(DEG_F+1)],polyvar),polyvar,domain="QQ")
  for power in range(DEG_F+1):
   num=sp.Rational(polynomial.nth(power))*SCALE
   if not num.is_Integer:raise RuntimeError("FROZEN_SCALE_INVALID")
   targets[j,power]=int(num)
 return rows,targets

def train_frozen_operator():
 start=time.perf_counter_ns()
 X,Y=generate_recurrence_data(TRAIN_SEED,TRAIN_SIZE)
 solution,resid,rank,singular=np.linalg.lstsq(X.astype(float),Y.astype(float),rcond=None)
 rounded=np.rint(solution).astype(np.int64)
 if np.max(np.abs(solution-rounded))>NUMERIC_EXACT_TOL:
  raise RuntimeError("WEIGHTS_COULD_NOT_BE_EXACTLY_INTEGERIZED")
 train_ok=np.array_equal(X@rounded,Y)
 testX,testY=generate_recurrence_data(HOLDOUT_SEED,HOLDOUT_SIZE)
 held_ok=np.all(testX@rounded==testY,axis=1)
 ablated_X=generate_recurrence_data(TRAIN_SEED,TRAIN_SIZE)[0]
 ablated_Y=Y[np.random.default_rng(TRAIN_SEED+1).permutation(TRAIN_SIZE)]
 scrambled=np.rint(np.linalg.lstsq(ablated_X.astype(float),ablated_Y.astype(float),rcond=None)[0]).astype(np.int64)
 shuffled_success=int(np.sum(np.all(testX@scrambled==testY,axis=1)))
 zero_success=int(np.sum(np.all(testY==0,axis=1)))
 if not train_ok or int(held_ok.sum())!=HOLDOUT_SIZE or shuffled_success==HOLDOUT_SIZE:
  raise RuntimeError("FROZEN_TRAINING_OR_ABLATION_CONTRACT_FAIL")
 weight_sha=hashlib.sha256(rounded.astype(">i8").tobytes()).hexdigest()
 return rounded,{"training_random_synthetic_recurrences":TRAIN_SIZE,
  "target_generation":"source numeric prefix traces and exact rational interpolation",
  "maximum_increment_degree":DEG_DELTA,"maximum_result_degree":DEG_F,
  "frozen_coefficient_denominator":SCALE,
  "learned_trainable_linear_weights":int(rounded.size),
  "lstsq_rank":int(rank),"lstsq_singular_values":[round(float(v),7) for v in singular],
  "training_full_coefficients_exact":train_ok,
  "heldout_64_full_integer_coefficient_predictions_exact":int(held_ok.sum()),
  "shuffled_train_labels_holdout_success":shuffled_success,
  "zero_weights_holdout_success":zero_success,
  "frozen_trained_weights_sha256":weight_sha,
  "frozen_learned_weight_matrix":rounded.tolist(),
  "whole_synthetic_training_and_audits_ms":ms(start)}

def learned_pre_trans_generator(src,native,weights):
 start=time.perf_counter_ns()
 original,extraction_ms=derive_updates(src,native)
 n=src["now"];symbols={str(x):sp.Symbol(str(x),integer=True) for x in n}
 st={var for var in original if original[var]==symbols[var]}
 clocks={var for var in original if sp.expand(original[var]-symbols[var])==1}
 generated=[];dropped=[];components=[]
 for clock in sorted(clocks):
  t=symbols[clock]
  for variable in original:
   if variable==clock or variable in st:continue
   delta=sp.expand(original[variable]-symbols[variable])
   if not delta.free_symbols.issubset({t,*[symbols[s] for s in st]}):
    continue
   if delta==0:continue
   try:dp=sp.Poly(delta,t,domain="ZZ["+','.join(sorted(st))+"]") if st else sp.Poly(delta,t,domain=sp.ZZ)
   except Exception:
    try:dp=sp.Poly(delta,t)
    except Exception:continue
   if dp.degree()>DEG_DELTA or dp.degree()<0:continue
   vector=[sp.expand(dp.nth(d)) for d in range(DEG_DELTA+1)]
   values=[sp.expand(sum(sp.Integer(int(weights[k,degree]))*vector[k]
      for k in range(DEG_DELTA+1))/SCALE) for degree in range(DEG_F+1)]
   F=sp.expand(sum(values[d]*t**d for d in range(DEG_F+1)))
   # The proposed coefficient vector comes from FROZEN learned weights.
   # Sympy here verifies the proposal, not generates the antiderivative.
   arithmetic_residual=sp.expand(F.subs(t,t+1)-F-delta)
   formula,desc=integer_eq(symbols[variable]-F,list(symbols.values()))
   status,time_ms=zcheck(z3.And(native["pre"],z3.Not(formula)),secs=3)
   receipt={"clock":clock,"accumulator":variable,"source_delta":str(delta),
     "frozen_learned_integrated_polynomial":str(F),
     "learned_symbolic_finite_difference_exact":arithmetic_residual==0,
     "original_pre_bad":status,
     "pre_check_ms":time_ms,**desc}
   if status=="unsat" and arithmetic_residual==0:
    components.append(formula);generated.append(receipt)
   else:dropped.append(receipt)
 for name in sorted(clocks|st):
  f=z3.Int(name)>=0
  status,_=zcheck(z3.And(native["pre"],z3.Not(f)),secs=3)
  if status=="unsat":
   components.append(f);generated.append({"source_pre_proven_domain":str(f)})
 for guard in atoms(native["trans"]):
  if guard.decl().kind()!=z3.Z3_OP_LT:continue
  l,r=guard.children()
  if str(l) not in clocks:continue
  if not(z3.is_int_value(r) or str(r) in st):continue
  f=l<=r
  status,_=zcheck(z3.And(native["pre"],z3.Not(f)),secs=3)
  if status=="unsat":
   components.append(f);generated.append({"original_transition_guard_clock":str(f)})
 if not components:raise ValueError("NO_FROZEN_LEARNED_SOURCE_ONLY_CANDIDATE")
 return z3.And(*components),{"frozen_learned_coeff_generator":generated,
   "source_only_candidate_rejects":dropped,
   "source_original_increment_clocks":sorted(clocks),
   "source_original_static_symbols":sorted(st),
   "source_transition_update_entailment_ms":extraction_ms,
   "learned_generation_and_source_precheck_ms":ms(start)}

def proof(inv,src,native):
 substitute=z3.substitute(inv,*list(zip(src["now"],src["next"])))
 vcs={"initial":z3.And(native["pre"],z3.Not(inv)),
   "consecution":z3.And(inv,native["trans"],z3.Not(substitute)),
   "post":z3.And(inv,z3.Not(native["post"]))}
 rows={}
 for key,bad in vcs.items():
  v,elapsed=zcheck(bad,secs=10)
  ext=cvc(bad,secs=12) if v=="unsat" else {"status":"NOT_RUN"}
  rows[key]={"Z3":v,"native_original_cvc5":ext,
    "dual_independent_UNSAT":v=="unsat" and ext.get("status")=="unsat" and ext.get("exit_code")==0,
    "Z3_wall_ms":elapsed}
 return rows,all(row["dual_independent_UNSAT"] for row in rows.values())

def one(root,path,expect,weights):
 t=time.perf_counter_ns()
 rec={"source":path,"git_blob_frozen_before_original_inspection":expect,
   "frozen_learned_full_original_dual_3VC":False,"strong_classical_full_original_dual_3VC":False}
 try:
  raw=(root/path).read_bytes()
  if blob(raw)!=expect:raise RuntimeError("PINNED_SOURCE_IDENTITY_MISMATCH")
  rec["original_byte_sha256"]=sha(raw)
  parsed=sexprs(raw);src=extract_mixed_original(parsed)
  native=native_original_relations(parsed,src)
  native.update({"now":src["now"],"next":src["next"]})
  parity=check_parity(src,native)
  rec["original_native_custom_semantic_parity"]=parity
  if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
   raise RuntimeError("UNTRUSTED_SOURCE_SEMANTIC_PARITY")
  if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
   raise RuntimeError("VACUOUS_ORIGINAL")
  candidate,learned_receipt=learned_pre_trans_generator(src,native,weights)
  rec["learned_first_proposal_invariant_SMT"]=candidate.sexpr()
  rec["learned_source_only_mechanism"]=learned_receipt
  # Strong source-only exact SymPy discrete summation independent classical;
  # this must get the exact same input and unchanged native source goal.
  classical,classical_receipt=discover(src,native)
  rec["strong_classical_invariant_SMT"]=classical.sexpr()
  rec["strong_classical_source_only_mechanism"]=classical_receipt
  rec["frozen_learned_original_3VC"],rec["frozen_learned_full_original_dual_3VC"]=proof(candidate,src,native)
  rec["strong_classical_original_3VC"],rec["strong_classical_full_original_dual_3VC"]=proof(classical,src,native)
  rec["verdict"]="LEARNED_TRANSFER_DUAL_3VC_AND_CLASSICAL_TIE" if (
      rec["frozen_learned_full_original_dual_3VC"] and
      rec["strong_classical_full_original_dual_3VC"]) else "NO_UNIQUE_LEARNED_SUCCESS_OR_ABSTAIN"
 except Exception as exc:
  rec["verdict"]="ABSTAIN_OR_GENERATION_FAILURE"
  rec["error"]=type(exc).__name__+":"+str(exc)[:320]
 rec["case_wall_ms"]=ms(t)
 return rec

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",type=Path,required=True)
 parser.add_argument("--out",type=Path,required=True)
 args=parser.parse_args()
 full=time.perf_counter_ns()
 weights,training=train_frozen_operator()  # BEFORE opening actual original bodies
 print("TRAINED_LINEAR_OPERATOR_SHA",training["frozen_trained_weights_sha256"],
       "HELDOUT_EXACT",training["heldout_64_full_integer_coefficient_predictions_exact"],flush=True)
 rows=[one(args.root,name,sha,weights) for name,sha in COHORT]
 for row in rows:
  print("FIRST_FROZEN_LEARNED_SOURCE",row["source"],row["verdict"],
    "NEURAL_ORIGINAL",row["frozen_learned_full_original_dual_3VC"],
    "STRONG_CLASSIC",row["strong_classical_full_original_dual_3VC"],
    "ERROR",row.get("error"),flush=True)
 report={"schema":"neumann.q3.synthetic_cpu_learned_linear_polynomial_antidifference.v1",
   "science_scope":"FIRST_SHA_FROZEN_ORIGINAL_SAME_UPSTREAM_AUTHOR; fixed grammar learning, NOT global Q3",
   "trained_operator":training,
   "model_training_before_any_target_source_body_parsed":True,
   "three_target_originals_pinned_before_content_read":True,
   "distinct_upstream_author_origin_groups":1,
   "three_source_rows_retained":len(rows)==3,
   "learned_first_proposals_dual_original_3VC":sum(
       bool(r["frozen_learned_full_original_dual_3VC"]) for r in rows),
   "same_information_strong_classical_dual_original_3VC":sum(
       bool(r["strong_classical_full_original_dual_3VC"]) for r in rows),
   "learned_new_mathematical_primitive_outside_predeclared_polynomial_grammar":False,
   "learned_superior_to_complete_exact_classical":False,
   "learned_10x_over_classical_all_in":False,
   "GPU_calls":0,"paid_API_calls":0,
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "whole_study_wall_ms":ms(full),"cases":rows}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("LEARNED_FIRST_UNSEEN_ORIGINAL_DUAL_PROOFS",
    report["learned_first_proposals_dual_original_3VC"],"/3")
 print("STRONG_CLASSICAL_ORIGINAL_DUAL_PROOFS",
    report["same_information_strong_classical_dual_original_3VC"],"/3")
 print("GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":main()
