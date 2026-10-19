"""Q3 prod-bin exact-original learned nonaffine conserved relation.
This is post-G0 developmental work. Learned coefficients share the exact same
monomial grammar and source evidence as a strong exact classical control.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,time,subprocess
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import z3
from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,
  check_formula,source_proof,_obligations)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

SOURCE="benchmarks/NIA/2018.CHI_InvGame/prod-bin.desugared.sl"
BLOB="b720f5e7556e1486d77ef65ae8f35b7bace20485"
def ms(t):return round((time.perf_counter_ns()-t)/1e6,3)
def git_blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def features(records,terms):
 return np.asarray([[int(np.prod([v[i] for i in term])) for term in terms] for v in records],dtype=float)
def product_z3(term,states):
 result=z3.IntVal(1)
 for j in term:result*=states[j]
 return result
def plus(ts):
 return z3.Sum(*ts) if len(ts)>1 else (ts[0] if ts else z3.IntVal(0))
def candidate(weights,terms,states):
 a,b,x,y,z=states
 pieces=[z-a*b]
 pieces.extend(int(w)*product_z3(t,states) for w,t in zip(weights,terms) if int(w))
 return z3.simplify(plus(pieces)==0)

def actual_original_episodes(native,src,parameters):
 now,nxt=src["now"],src["next"]
 full=[]
 unique=0
 for aa,bb in parameters:
  pre=z3.Solver();pre.set(timeout=1500)
  pre.add(native["pre"],now[0]==aa,now[1]==bb)
  if pre.check()!=z3.sat:raise RuntimeError("EXPECTED_SOURCE_PRE_SAT")
  m=pre.model()
  state=tuple(m.eval(v,model_completion=True).as_long() for v in now)
  trajectory=[state]
  for step in range(35):
   s=z3.Solver();s.set(timeout=1500)
   s.add(native["trans"],*[v==k for v,k in zip(now,state)])
   verdict=s.check()
   if verdict==z3.unsat:break
   if verdict!=z3.sat:raise RuntimeError("ORIGINAL_SOURCE_TRANS_UNKNOWN")
   model=s.model()
   nxt_state=tuple(model.eval(v,model_completion=True).as_long() for v in nxt)
   proof=z3.Solver();proof.set(timeout=1500)
   proof.add(native["trans"],*[v==k for v,k in zip(now,state)],
     z3.Or(*[v!=k for v,k in zip(nxt,nxt_state)]))
   if proof.check()!=z3.unsat:raise RuntimeError("SOURCE_NEXT_NOT_UNIQUE")
   unique+=1
   state=nxt_state;trajectory.append(state)
  else:raise RuntimeError("ORIGINAL_TRACE_OVER_LIMIT")
  full.append(trajectory)
 return full,unique

def matrices(episodes,terms):
 states=[t for trajectory in episodes for t in trajectory]
 old=[t for trajectory in episodes for t in trajectory[:-1]]
 new=[t for trajectory in episodes for t in trajectory[1:]]
 U=features(states,terms)
 V=features(new,terms)-features(old,terms)
 def anchor(s):return float(s[4]-s[0]*s[1])
 yy=-np.asarray([anchor(s) for s in states]+
   [anchor(t)-anchor(s) for s,t in zip(old,new)],dtype=float)
 return np.vstack([U,V]),yy,len(states),len(old),states

def gradient_coefficients(X,y):
 scaling=np.maximum(np.max(np.abs(X),axis=0),1.)
 ys=max(float(np.max(np.abs(y))),1.)
 A=X/scaling;target=y/ys
 def fn(w):
  diff=A@w-target
  return float(np.mean(diff**2)),2*(A.T@diff)/len(diff)
 start=time.perf_counter_ns()
 model=minimize(fn,np.zeros(A.shape[1]),jac=True,method="L-BFGS-B",
   options={"maxiter":3500,"ftol":1e-18,"gtol":1e-12,"maxls":50})
 raw=model.x*ys/scaling
 coeff=np.rint(raw).astype(int)
 return coeff,{"optimizer":"CPU SciPy L-BFGS-B differentiable neural linear readout",
    "truly_optimized":model.nit>0,"optimizer_iterations":int(model.nit),
    "learned_parameters":int(A.shape[1]),
    "round_coefficients":coeff.tolist(),
    "raw_float_coefficients":[round(float(v),7) for v in raw],
    "train_reconstruction_exact":bool(np.array_equal(X@coeff,y)),
    "learning_component_ms":ms(start)}
def exact_classical_coefficients(X,y):
 start=time.perf_counter_ns()
 raw,res,rank,sing=np.linalg.lstsq(X,y,rcond=None)
 coeff=np.rint(raw).astype(int)
 return coeff,{"algorithm":"same-feature source-data exact linear-system baseline",
   "rank":int(rank),"matched_features":int(X.shape[1]),
   "round_coefficients":coeff.tolist(),
   "train_reconstruction_exact":bool(np.array_equal(X@coeff,y)),
   "classical_component_ms":ms(start)}
def cvc5_vc(script):
 t=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=smt2","--decision=internal","--tlimit-per=15000","-"],
   input=script, text=True,capture_output=True,timeout=19)
  out=p.stdout.strip().splitlines()
  return {"status":out[-1].strip() if out else "EMPTY",
     "returncode":p.returncode,"component_ms":ms(t),
     "stderr_excerpt":p.stderr[:140]}
 except Exception as exc:return {"status":"NO_RESULT","reason":str(exc)[:200],"component_ms":ms(t)}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source-root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args()
 raw=(args.source_root/SOURCE).read_bytes()
 if git_blob(raw)!=BLOB:raise ValueError("EXACT_ORIGINAL_GIT_BLOB_MISMATCH")
 forms=sexprs(raw);src=extract_mixed_original(forms)
 native=native_original_relations(forms,src)
 native.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,native)
 if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
  raise ValueError("SOURCE_NATIVE_PARITY_INCORRECT")
 if len(src["now"])!=5 or src["num_bool"]!=0:raise ValueError("SOURCE_TYPED_SHAPE_MISMATCH")
 if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
  raise ValueError("UNSOUND_VACUOUS_SOURCE")
 monomials=[()]+[(i,) for i in range(5)]+list(itertools.combinations_with_replacement(range(5),2))
 exclude={(),(4,),(0,1)}
 terms=[t for t in monomials if t not in exclude]
 assert len(terms)==18
 train_keys=list(itertools.product(range(8),range(11)))
 heldout_keys=list(itertools.product(range(8,11),range(11,15)))
 train,train_trans=actual_original_episodes(native,src,train_keys)
 heldout,test_trans=actual_original_episodes(native,src,heldout_keys)
 X,y,nstates,nsteps,states=matrices(train,terms)
 H,hy,nhstates,nhsteps,holdstates=matrices(heldout,terms)
 learned,learnmeta=gradient_coefficients(X,y)
 classical,classmeta=exact_classical_coefficients(X,y)
 relation=candidate(learned,terms,src["now"])
 classical_relation=candidate(classical,terms,src["now"])
 no_bilinear=learned.copy()
 for k,t in enumerate(terms):
  if len(t)==2 and t==(2,3):no_bilinear[k]=0
 no_product_proof=source_proof(candidate(no_bilinear,terms,src["now"]),native)
 postonly=source_proof(native["post"],native)
 lproof=source_proof(relation,native)
 cproof=source_proof(classical_relation,native)
 source_sha=hashlib.sha256(raw).hexdigest()
 certified=check_original_candidate(args.source_root/SOURCE,relation.sexpr(),
   expected_source_sha256=source_sha)
 cv=certified.get("cvc5_original_three_vc") or {}
 independently_verified=certified.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
 independent_extension=None
 if not independently_verified and lproof["accepted"]:
  indep={}
  for name,bad in _obligations(relation,src,native).items():
   s=z3.Solver();s.set(timeout=3000);s.add(bad)
   if s.check()!=z3.unsat:raise RuntimeError("INVALID_Z3_NATIVE_OBLIGATION")
   indep[name]=cvc5_vc(s.to_smt2())
  independent_extension=indep
  independently_verified=(set(indep)=={"initial","consecution","post"} and
    all(x["status"]=="unsat" and x["returncode"]==0 for x in indep.values()))
 checks={
   "authentic_original_sha_and_pre_trans_post_parity":True,
   "actual_original_deterministic_successors_all_verified":True,
   "real_gradient_training_nonzero_iterations":learnmeta["truly_optimized"],
   "train_real_source_state_constraints_reconstructed":learnmeta["train_reconstruction_exact"],
   "unseen_initial_condition_heldout_exact":bool(np.array_equal(H@learned,hy)),
   "learned_bilinear_hidden_delta_gamma":int(learned[terms.index((2,3))])==1,
   "source_post_only_NOT_inductive":not postonly["accepted"],
   "bilinear_ablation_does_not_inductively_prove":not no_product_proof["accepted"],
   "generated_candidate_original_Z3_3VC":lproof["accepted"],
   "independent_original_cvc5_3VC":independently_verified,
   "equal_info_strong_classical_exact_regression_also_solves":(
     classmeta["train_reconstruction_exact"] and
     bool(np.array_equal(H@classical,hy)) and cproof["accepted"])}
 result={
  "schema":"neumann.q3.prod-bin.posthoc.dev.source-trained.bilinear.v1",
  "source":SOURCE,"original_git_blob":BLOB,"original_sha256":source_sha,
  "original_semantics_XOR":parity,
  "train_episodes":len(train),"train_states":nstates,"train_original_transitions":train_trans,
  "heldout_episodes":len(heldout),"heldout_states":nhstates,
  "heldout_original_transitions":test_trans,
  "public_post_given_only_as_goal_anchor_not_a_gold_invariant":True,
  "source_only_full_degree_two_grammar_predeclared":True,
  "neural_feature_monomials":[list(t) for t in terms],
  "learned":learnmeta,"classical":classmeta,
  "learned_equal_matched_classical_coefficients":bool(np.array_equal(learned,classical)),
  "learned_candidate_sexpr":relation.sexpr(),
  "post_only_z3_bad_conditions":postonly["vcs"],
  "bilinear_ablated_original_z3_bad_conditions":no_product_proof["vcs"],
  "learned_native_original_Z3_bad_conditions":lproof["vcs"],
  "classical_native_original_Z3_bad_conditions":cproof["vcs"],
  "first_unmodified_original_cvc5_checker":cv,
  "independent_cvc5_15s_internal_original":independent_extension,
  "checks":checks,"scoped_posthoc_pass":all(checks.values()),
  "trained_neural_invents_new_primitive_outside_given_monomial_vocabulary":False,
  "learned_unique_vs_classical_same_features":False,
  "g0_proof_of_best_classical_impossibility":False,
  "true_G1_blind_family_generalization":False,
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "gpu_calls":0,"paid_API_calls":0}
 args.out.parent.mkdir(exist_ok=True,parents=True)
 args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("FIRST_PRODBIN_SOURCE_ORIGINAL",SOURCE)
 print("GRADIENT_TRAIN",nstates,"HOLDOUT",nhstates)
 print("LEARNED_TERMS",[(list(t),int(k)) for t,k in zip(terms,learned) if k])
 print("CLASSICAL_TERMS",[(list(t),int(k)) for t,k in zip(terms,classical) if k])
 print("ORIGINAL_Z3",lproof["vcs"])
 print("INDEPENDENT_CVC5_CERTIFIED",independently_verified)
 print("SCOPED_POSTHOC_PASS",result["scoped_posthoc_pass"])
 print("GLOBAL_Q3",result["global_Q3"])
if __name__=="__main__":main()
