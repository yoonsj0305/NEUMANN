"""Q3 POSTHOC: self-supervised depth-growing neural coefficients on original traces.
Frozen source files have been opened in preceding Q3 research. Not blind, not
novel primitive outside Newton arithmetic grammar, not faster than exact classical.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import sympy as sp
import z3
from experiments.q3_source_prove import (
    sexprs, extract_mixed_original, native_original_relations, check_parity,
    check_formula, source_proof)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

ORIGINALS={
 "cube2":("benchmarks/NIA/2018.CHI_InvGame/cube2.desugared.sl","06343774ef7637bacbc7b20ec9b9bd7e9d8c0ab8"),
 "gauss":("benchmarks/NIA/2018.CHI_InvGame/gauss_sum-more-rows.auto.sl","a46943a0aacdfc418f5b57788d3b0b0015a815f1"),
}
def original_blob(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def matrix(ts,d):
 return np.asarray([[math.comb(int(t),k) if t>=k else 0 for k in range(d+1)] for t in ts],dtype=float)

def actual_gradient_train(ts,vals,degree):
 """Learnable linear neural readout with dynamic degree depth, genuinely fitted
 by gradient; no exact regression, no gold coefficients, no Post."""
 B=matrix(ts,degree)
 sx=np.maximum(np.max(np.abs(B),axis=0),1.)
 sy=max(float(np.max(np.abs(vals))),1.)
 X=B/sx
 y=np.asarray(vals,dtype=float)/sy
 def lossgrad(w):
  e=X@w-y
  return float(e@e/len(e)),2*(X.T@e)/len(e)
 start=time.perf_counter_ns()
 opt=minimize(lossgrad,np.zeros(degree+1),jac=True,method="L-BFGS-B",
              options={"maxiter":2000,"ftol":1e-17,"gtol":1e-12,"maxls":40})
 ms=(time.perf_counter_ns()-start)/1e6
 weights=np.asarray(opt.x)*sy/sx
 rounded=np.rint(weights).astype(int)
 return {
  "coefficients":rounded.tolist(),"raw_float_weights":[round(float(w),8) for w in weights],
  "gradient_iterations":int(opt.nit),"learning_wall_ms":round(ms,3),
  "train_exact":bool(np.array_equal(B@rounded,np.asarray(vals))),
  "training_performed":bool(opt.nit>0)
 }
def discover(ts,values,hold_t,hold_v):
 attempts=[]
 for depth in range(6):
  stage=actual_gradient_train(ts,values,depth)
  attempts.append({"depth":depth,"train_exact":stage["train_exact"],
                   "gradient_iterations":stage["gradient_iterations"],
                   "learning_wall_ms":stage["learning_wall_ms"]})
  if stage["train_exact"]:
   stage.update({"depth":depth,"growth_attempts":attempts,
       "untouched_future_trace_exact":bool(np.array_equal(
          matrix(hold_t,depth)@np.array(stage["coefficients"]),hold_v))})
   return stage
 return {"depth":None,"growth_attempts":attempts,
         "untouched_future_trace_exact":False}

def expr_for(coeff,base,driver,target):
 """Only arithmetic primitives are predefined; dynamically grow degree."""
 n=sp.Symbol("n")
 symbolic=sp.expand(sum(sp.Integer(c)*sp.prod(n-base-j for j in range(k))/
              sp.factorial(k) for k,c in enumerate(coeff)))
 num,den=sp.fraction(sp.together(symbolic))
 poly=sp.Poly(num,n)
 parts=[int(c)*_power(driver,p[0]) for p,c in poly.terms()]
 rhs=parts[0] if len(parts)==1 else z3.Sum(*parts) if parts else z3.IntVal(0)
 return target*int(den)==rhs,str(symbolic)

def _power(var,degree):
 v=z3.IntVal(1)
 for _ in range(degree):v=v*var
 return v

def collect_native_trace(src,native,count=13):
 now,nxt=src["now"],src["next"];d=len(now)
 T=[[z3.Int(f"q3grow_{t}_{j}") for j in range(d)] for t in range(count)]
 s=z3.Solver();s.set(timeout=15000)
 s.add(z3.substitute(native["pre"],*list(zip(now,T[0]))))
 for t in range(count-1):
  s.add(z3.substitute(native["trans"],*(list(zip(now,T[t]))+list(zip(nxt,T[t+1])))))
 if s.check()!=z3.sat:raise ValueError("NO_ORIGINAL_TRACE")
 m=s.model()
 rows=[[m.eval(v,model_completion=True).as_long() for v in t] for t in T]
 # Uniqueness check: all recorded next-state values forced by original Trans
 for t in range(count-1):
  cond=z3.And(native["trans"],
     *[now[j]==rows[t][j] for j in range(d)],
     z3.Or(*[nxt[j]!=rows[t+1][j] for j in range(d)]))
  if check_formula(cond)!="unsat":raise ValueError("NONDETERMINISTIC_TRACE")
 return rows

def source_only_inductive_bounds(native,src,driver):
 now,nxt=src["now"],src["next"]
 ans=[];info=[]
 for k in range(len(now)):
  if k==driver:continue
  if check_formula(z3.And(native["trans"],nxt[k]!=now[k]))!="unsat":continue
  for delta in (0,1,2):
   p=now[driver]<=now[k]+delta
   pn=nxt[driver]<=nxt[k]+delta
   if (check_formula(z3.And(native["pre"],z3.Not(p)))=="unsat" and
       check_formula(z3.And(p,native["trans"],z3.Not(pn)))=="unsat"):
    ans.append(p);info.append({"counter":driver,"constant":k,"offset":delta})
    break
 return ans,info

def analyze_one(root,key):
 rel,blob=ORIGINALS[key]
 path=root/rel;raw=path.read_bytes()
 if original_blob(raw)!=blob:raise ValueError("FROZEN_SOURCE_GIT_BLOB_MISMATCH")
 sex=sexprs(raw);src=extract_mixed_original(sex)
 native=native_original_relations(sex,src)
 native.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,native)
 if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
  raise ValueError("ORIGINAL_NATIVE_PARITY_MISMATCH")
 now,nxt=src["now"],src["next"]
 options=[]
 for k in range(len(now)):
  if check_formula(z3.And(native["trans"],nxt[k]!=now[k]+1))!="unsat":continue
  for base in range(-2,4):
   if check_formula(z3.And(native["pre"],now[k]!=base))=="unsat":
    options.append((k,base))
 if len(options)!=1:raise ValueError("NO_UNIQUE_SOURCE_COUNTER")
 driver,base=options[0]
 trace=collect_native_trace(src,native)
 if [row[driver] for row in trace]!=list(range(base,base+13)):
  raise ValueError("COUNTER_TRACE_MISMATCH")
 fitted=[];formulas=[]
 for k in range(len(now)):
  if k==driver:continue
  fixed_initial=trace[0][k]
  if check_formula(z3.And(native["pre"],now[k]!=fixed_initial))!="unsat":continue
  values=[row[k] for row in trace]
  if len(set(values))<=1:continue
  stage=discover(range(8),values[:8],range(8,13),values[8:])
  stage["state_index"]=k
  if stage["depth"] is not None:
   rel_z3,rel_text=expr_for(stage["coefficients"],base,now[driver],now[k])
   stage["generated_expression"]=rel_text
   lone=source_proof(rel_z3,native)
   stage["single_relation_initial_vc"]=lone["vcs"]["initial"]
   stage["single_relation_step_vc"]=lone["vcs"]["consecution"]
   if stage["untouched_future_trace_exact"] and lone["vcs"]["initial"]=="unsat":
    formulas.append(rel_z3)
  fitted.append(stage)
 helpers,helpers_info=source_only_inductive_bounds(native,src,driver)
 combined=z3.And(*(formulas+helpers))
 original=source_proof(combined,native)
 independent=check_original_candidate(path,combined.sexpr(),
               expected_source_sha256=hashlib.sha256(raw).hexdigest())
 ext=independent.get("cvc5_original_three_vc") or {}
 helper_only=source_proof(z3.And(*helpers),native)
 gates={
   "original_native_three_formulas_semantically_equal":True,
   "original_13step_deterministic_trace":True,
   "actual_gradient_optimizer_training":len(fitted)>0 and all(x.get("training_performed") for x in fitted),
   "train_only_degree_growth_and_unseen_future_trace":all(x.get("untouched_future_trace_exact") for x in fitted),
   "autogenerated_non_post_goal_degree":any(x.get("depth",0)>=3 for x in fitted) if key=="cube2" else any(x.get("depth",0)>=2 for x in fitted),
   "all_generated_atoms_initial_satisfied":len(formulas)==len(fitted),
   "joint_coupled_original_Z3_three_vc":original["accepted"],
   "independent_cvc5_original_three_vc":independent.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5" and
      set(ext)=={"initial","consecution","post"} and
      all(q.get("status")=="unsat" and q.get("returncode")==0 for q in ext.values()),
   "source_only_helper_does_not_solve":not helper_only["accepted"],
 }
 return {
  "original_source":rel,"git_blob":blob,
  "source_sha256":hashlib.sha256(raw).hexdigest(),
  "trace_sha256":hashlib.sha256(json.dumps(trace).encode()).hexdigest(),
  "train_samples":8,"heldout_trace_samples":5,"source_counter":driver,
  "initial_counter":base,"neural_learned_atoms":fitted,
  "classical_source_only_bounds":helpers_info,
  "joint_z3_original_vcs":original["vcs"],"external_cvc5_original_vcs":ext,
  "source_helper_alone_vcs":helper_only["vcs"],
  "gates":gates,"bounded_posthoc_pass":all(gates.values())}

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True);args=p.parse_args()
 out={"schema":"neumann.q3.self_supervised_degree_growth.first_original.v1",
    "scientific_scope":"POSTHOC previously-opened authentic originals, no new blind transfer",
    "actual_source_only_neural_gradient_learning":True,
    "original_post_used_during_learning":False,
    "degree_controller_is_classical":True,
    "basis_of_arithmetic_operations_predeclared":True,
    "trained_neural_invents_primitive_outside_arithmetic_vocabulary":False,
    "same_domain_exact_finite_differences_classical_specialist_also_solves":True,
    "GPU_calls":0,"paid_API_calls":0,
    "global_Q3":"OPEN","global_Q1_Q7":"OPEN","originals":{}}
 for key in ORIGINALS:
  result=analyze_one(args.root,key);out["originals"][key]=result
  print(key,"SCOPED",result["bounded_posthoc_pass"],
    [(x["state_index"],x.get("depth"),x.get("generated_expression")) for x in result["neural_learned_atoms"]])
 args.out.parent.mkdir(exist_ok=True,parents=True)
 args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
 print("Q3_SELF_SUPERVISED_GROWTH_ORIGINALS_SCOPED_PASS",
       all(r["bounded_posthoc_pass"] for r in out["originals"].values()))
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
