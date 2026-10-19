"""Q3 MANNADIV post-first-G0 development: self-supervised learned cross-variable
polynomial relation from only publicly verified source transitions.
NOT a new blind origin after baseline source opened; matched exact classical
same-basis expert included with zero unique neural capability.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import z3
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,
 check_formula,source_proof,houdini)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

FILE="benchmarks/NIA/2016.ATVA_PILAT/mannadiv.sl"
GIT_BLOB="8530c3a189403f14db1f505820a65e92ba876193"

def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def elapsed(t):return round((time.perf_counter_ns()-t)/1e6,3)
def join_add(terms):
 if len(terms)==0:return z3.IntVal(0)
 if len(terms)==1:return terms[0]
 return z3.Sum(*terms)
def monomials(predictor_indices):
 return ((),)+tuple((j,) for j in predictor_indices)+tuple(
  (j,k) for j,k in itertools.combinations_with_replacement(predictor_indices,2))
def features(rows,monos):
 return np.asarray([[int(np.prod([state[j] for j in monomial]))
   for monomial in monos] for state in rows],dtype=np.float64)
def polynomial(weights,variables,monos):
 terms=[]
 for coeff,monomial in zip(weights,monos):
  if not int(coeff):continue
  v=z3.IntVal(int(coeff))
  for idx in monomial:v=v*variables[idx]
  terms.append(v)
 return join_add(terms)
def original_episode(native,src,static,target,other):
 now,nxt=src["now"],src["next"]
 state_solver=z3.Solver();state_solver.set(timeout=3000)
 state_solver.add(native["pre"],now[static[0]]==target,now[static[1]]==other)
 if state_solver.check()!=z3.sat:raise ValueError("ORIGINAL_INIT_MUST_BE_SAT")
 m=state_solver.model()
 cur=tuple(m.eval(k,model_completion=True).as_long() for k in now)
 states=[cur]
 for step in range(42):
  step_solver=z3.Solver();step_solver.set(timeout=3000)
  step_solver.add(native["trans"],
      *[now[i]==cur[i] for i in range(len(now))])
  q=step_solver.check()
  if q==z3.unsat:return states
  if q!=z3.sat:raise ValueError("ORIGINAL_TRANS_MODEL_UNKNOWN")
  model=step_solver.model()
  following=tuple(model.eval(k,model_completion=True).as_long() for k in nxt)
  # Never accept an arbitrary or unverified synthesized transition.
  check=z3.Solver();check.set(timeout=3000)
  check.add(native["trans"],
      *[now[i]==cur[i] for i in range(len(now))],
      z3.Or(*[nxt[i]!=following[i] for i in range(len(now))]))
  if check.check()!=z3.unsat:raise ValueError("UNIQUE_ORIGINAL_NEXT_STATE_NOT_PROVEN")
  cur=following;states.append(cur)
 raise ValueError("ORIGINAL_TRACE_EXCEEDED_BOUND")

def source_traces(native,src,static,a_range,b_range):
 grouped=[]
 for a in a_range:
  for b in b_range:
   e=original_episode(native,src,static,a,b)
   grouped.append((a,b,e))
 return grouped
def flatten(grouped):
 return [s for _,_,states in grouped for s in states]
def learn_coeffs(train,target,monos):
 X=features(train,monos)
 y=np.asarray([row[target] for row in train],dtype=float)
 scale=np.maximum(np.max(np.abs(X),axis=0),1.0)
 target_scale=max(float(np.max(np.abs(y))),1.0)
 A=X/scale
 b=y/target_scale
 def objective(w):
  e=A@w-b
  return float(np.mean(e*e)), 2*(A.T@e)/len(e)
 start=time.perf_counter_ns()
 fitted=minimize(objective,np.zeros(len(monos)),method="L-BFGS-B",
   jac=True,options={"maxiter":3500,"ftol":1e-17,"gtol":1e-12,"maxls":50})
 raw=fitted.x*target_scale/scale
 rounded=np.rint(raw).astype(np.int64)
 return {
 "source_self_supervised_gradient_fitted":bool(fitted.nit>0),
 "optimizer_iterations":int(fitted.nit),
 "float_before_round":[round(float(v),7) for v in raw],
 "coefficients":rounded.tolist(),
 "train_exact":bool(np.array_equal(X@rounded,y)),
 "trained_model_parameter_count":len(monos),
 "training_wall_ms":elapsed(start),
 "source_only_samples":len(train)},rounded

def exact_classical_control(train,target,monos):
 X=features(train,monos);y=np.asarray([s[target] for s in train],dtype=float)
 start=time.perf_counter_ns()
 coeff,_,rank,_=np.linalg.lstsq(X,y,rcond=None)
 rounded=np.rint(coeff).astype(np.int64)
 return {"trained":False,"coefficients":rounded.tolist(),
  "rank":int(rank),"n_columns":len(monos),
  "train_exact":bool(np.array_equal(X@rounded,y)),
  "source_only_matched_basis":True,
  "numerical_control_wall_ms":elapsed(start)},rounded

def verify_source(root):
 path=root/FILE
 raw=path.read_bytes()
 if blob(raw)!=GIT_BLOB:raise ValueError("PINNED_ORIGINAL_GIT_BLOB_MISMATCH")
 forms=sexprs(raw);src=extract_mixed_original(forms)
 native=native_original_relations(forms,src)
 native.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,native)
 if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
  raise ValueError("NATIVE_CUSTOM_PRE_TRANS_POST_PARITY_MISMATCH")
 if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
  raise ValueError("ORIGINAL_PRE_POST_VACUOUS_OR_UNKNOWN")
 if src["num_bool"]!=0:raise ValueError("ORIGINAL_INTEGERS_ONLY_EXPECTED")
 static=[j for j,(a,b) in enumerate(zip(src["now"],src["next"])) if
     check_formula(z3.And(native["trans"],a!=b))=="unsat"]
 if len(static)!=2:raise ValueError("REQUIRES_TWO_INDEPENDENT_STATIC_STATE_VALUES")
 return src,native,parity,static,path,hashlib.sha256(raw).hexdigest()

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",type=Path,required=True)
 parser.add_argument("--out",type=Path,required=True)
 args=parser.parse_args()
 src,native,parity,static,path,sha=verify_source(args.root)
 now,nxt=src["now"],src["next"]
 goal=static[0]
 predictor=[j for j in range(len(now)) if j!=goal]
 mons=monomials(predictor)
 # SHARED fixed source-only first 2 stable variables as episode parameters.
 train_ep=source_traces(native,src,static,range(0,13),range(1,7))
 future_ep=source_traces(native,src,static,range(13,18),range(7,10))
 train=flatten(train_ep);future=flatten(future_ep)
 learned,weights=learn_coeffs(train,goal,mons)
 exactcontrol,exactweights=exact_classical_control(train,goal,mons)
 learning_relation=(now[goal]==polynomial(weights,now,mons))
 classical_relation=(now[goal]==polynomial(exactweights,now,mons))
 learned["heldout_true_source_sample_count"]=len(future)
 learned["future_exact"]=bool(np.array_equal(features(future,mons)@weights,
                                 np.asarray([s[goal] for s in future])))
 exactcontrol["future_exact"]=bool(np.array_equal(features(future,mons)@exactweights,
                                 np.asarray([s[goal] for s in future])))
 equal_weights=bool(np.array_equal(weights,exactweights))
 # Full identical source-only classical Houdini helper for BOTH arms.
 t=time.perf_counter_ns()
 helper,atoms,n_candidates,queries=houdini(native["pre"],native["trans"],now,nxt)
 classical_helper_only=source_proof(helper,native)
 helper_ms=elapsed(t)
 original_learned=source_proof(z3.And(learning_relation,helper),native)
 original_classical=source_proof(z3.And(classical_relation,helper),native)
 lone_relation=source_proof(learning_relation,native)
 ablated=weights.copy()
 for i,mono in enumerate(mons):
  if len(mono)==2 and int(ablated[i])!=0:
   ablated[i]=0
 without_product=source_proof(z3.And(now[goal]==polynomial(ablated,now,mons),helper),native)
 strong_expert_only=classical_helper_only
 ext=check_original_candidate(path,z3.And(learning_relation,helper).sexpr(),
             expected_source_sha256=sha)
 cv=ext.get("cvc5_original_three_vc") or {}
 gates={
  "original_sha_exact":True,
  "original_pre_trans_post_native_xor_parity":True,
  "source_next_state_unique_under_all_sampled_transitions":True,
  "training_only_original_reachable_states":True,
  "true_gradient_training_not_labels_or_source_gold":learned["source_self_supervised_gradient_fitted"],
  "train_points_exact":learned["train_exact"],
  "heldout_different_initial_values_exact":learned["future_exact"],
  "cross_variable_second_degree_source_atom_learned":any(
    int(x) and len(m)==2 and len(set(m))==2 for x,m in zip(weights,mons)),
  "source_only_helper_not_original_goal_certificate":not classical_helper_only["accepted"],
  "product_term_ablation_fails_original_3VC":not without_product["accepted"],
  "learned_plus_source_only_helper_native_Z3_original_3VC":original_learned["accepted"],
  "independent_cvc5_original_3VC":ext.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5" and
     set(cv)=={"initial","consecution","post"} and
     all(z.get("status")=="unsat" and z.get("returncode")==0 for z in cv.values()),
  "matched_basis_strong_classical_also_solves":(
    exactcontrol["train_exact"] and exactcontrol["future_exact"] and original_classical["accepted"]),
 }
 out={
  "schema":"neumann.q3.mannadiv.learned_cross_term_original_posthoc.v1",
  "truthful_science_scope":"POST_G0_DEV_OPENED_ORIGINAL, not blind G1 or novelty beyond matched classical",
  "original_program":FILE,"upstream_blob":GIT_BLOB,"source_sha256":sha,
  "source_state_count":len(now),"original_native_semantics_xor":parity,
  "static_indices":static,"monomials":list(map(list,mons)),
  "predictor_variable_names":[str(now[j]) for j in predictor],
  "goal_state_variable":str(now[goal]),
  "train_initial_range":["first constant:0..12","second constant:1..6"],
  "test_initial_range":["first constant:13..17","second constant:7..9"],
  "train_episodes":len(train_ep),"test_episodes":len(future_ep),
  "source_trace_sha256":hashlib.sha256(json.dumps(train).encode()).hexdigest(),
  "learned_neural_linear_readout":learned,
  "strong_classical_exact_same_feature_control":exactcontrol,
  "learned_polynomial_z3_sexpr":learning_relation.sexpr(),
  "full_classical_helper_count":len(atoms),
  "original_houdini_candidate_count":n_candidates,"classical_helper_ms":helper_ms,
  "classical_helper_only_original_vcs":strong_expert_only["vcs"],
  "learned_cross_term_only_original_vcs":lone_relation["vcs"],
  "with_product_removed_original_vcs":without_product["vcs"],
  "learned_composed_original_Z3_three_vc":original_learned["vcs"],
  "classical_same_feature_composed_original_Z3_three_vc":original_classical["vcs"],
  "independent_original_cvc5_three_vc":cv,
  "identical_neural_classical_round_coefficients":equal_weights,
  "gates":gates,"scoped_original_pass":all(gates.values()),
  "new_mathematical_primitive_outside_monomial_degree2_vocabulary":False,
  "exclusive_neural_capability_over_exact_classical":False,
  "headroom_against_strong_specialist":"NOT_ESTABLISHED",
  "neural_g1_admitted":False,
  "global_Q1_Q7":"OPEN","global_Q3":"OPEN",
  "GPU_calls":0,"paid_API_calls":0}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print("SOURCE",FILE)
 print("TRAIN_SOURCE_STATE_COUNT",len(train),"HOLDOUT",len(future))
 print("LEARNED_COEFFS",learned["coefficients"])
 print("MATCHED_CLASSIC_COEFFS",exactcontrol["coefficients"])
 print("LEARNED_ORIGINAL_Z3",original_learned["vcs"],"CVC5",cv)
 print("GATES",json.dumps(gates,sort_keys=True))
 print("MANNADIV_POST_G0_LEARNED_COMPOSITE_ORIGINAL_SCOPED",out["scoped_original_pass"])
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
