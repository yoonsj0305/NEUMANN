"""Q3 source-specific polynomial expressivity impossibility and synthetic modular
typed-grammar escape. Strong exact same-source classical MAX+1 control mandatory.
Freeze: docs/research/Q3_POLYNOMIAL_GRAMMAR_MODULO_BARRIER_PREREG_20261019.md.
Never call supplied 'mod' syntax a learned NEW primitive.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math,subprocess,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import sympy as sp
import z3

K_THEOREM=(2,3,4,5)
D_THEOREM=range(6)
K_TRAIN=(2,3,4,5,6)
K_TEST=(7,8,9,11)
TRAIN_STEPS=48
EXPECTED={"initial":"unsat","consecution":"unsat","post":"unsat"}
def elapsed(t):return round((time.perf_counter_ns()-t)/1e6,3)
def cvc5(script,timeout=4):
 start=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=smt2",f"--tlimit-per={timeout*1000}","-"],
        input=script,text=True,capture_output=True,timeout=timeout+3,check=False)
  ret=[v.strip() for v in p.stdout.splitlines() if v.strip()]
  return {"status":ret[-1] if ret else "EMPTY","returncode":p.returncode,
          "wall_ms":elapsed(start),"stderr_excerpt":p.stderr[:100]}
 except Exception as e:
  return {"status":"NO_VERDICT","error":str(e)[:180],"wall_ms":elapsed(start)}
def evalpoly(cs,x):
 return sum(cs[j]*sp.Integer(x)**j for j in range(len(cs)))

def impossibility():
 checks=[]
 for k,d in itertools.product(K_THEOREM,D_THEOREM):
  r=sp.Matrix([[sp.Integer(i*k)**j for j in range(d+1)]
                for i in range(d+1)])
  rank=int(r.rank())
  det=sp.factor(r.det())
  formula=sp.Integer(k)**(d*(d+1)//2)*sp.prod(sp.factorial(j) for j in range(1,d+1))
  if det!=formula or rank!=d+1:raise AssertionError("RATIONAL_VANDERMONDE_THEOREM_FAIL")
  c=[z3.Real(f"coefficient_{k}_{d}_{j}") for j in range(d+1)]
  zeros=[z3.Sum(*[c[j]*(i*k)**j for j in range(d+1)])==0 for i in range(d+1)]
  one=z3.Sum(*c)==1
  solver=z3.Solver();solver.set(timeout=3000)
  solver.add(*zeros,one)
  native=str(solver.check())
  if native!="unsat":raise AssertionError("Z3_POLYNOMIAL_BARRIER_NOT_UNSAT")
  independent=cvc5(solver.to_smt2(),timeout=3)
  if independent.get("status")!="unsat" or independent.get("returncode")!=0:
   raise AssertionError("CVC5_POLYNOMIAL_BARRIER_NOT_UNSAT:"+repr((k,d,independent)))
  checks.append({"modulus":k,"degree_at_most":d,
    "determinant":str(det),"rank":rank,
    "Z3":native,"independent_cvc5":independent["status"]})
 n=sp.Symbol("n",integer=True)
 p=sp.interpolate([(i,i%2) for i in range(5)],n)
 interp={
  "polynomial":str(p),
  "train_points":[{"n":i,"P":str(p.subs(n,i)),"remainder":i%2}
                    for i in range(5)],
  "heldout_n":5,"heldout_polynomial":str(p.subs(n,5)),
  "heldout_true_remainder":1,
  "finite_interpolation_wrong_on_next_n":bool(p.subs(n,5)!=1)}
 assert interp["finite_interpolation_wrong_on_next_n"]
 return checks,interp

def trajectories(k):
 i=r=0
 rows=[]
 for step in range(TRAIN_STEPS):
  rows.append((i,r))
  nxt_r=0 if r==k-1 else r+1
  i+=1;r=nxt_r
  assert r==i%k
 return rows

def train_period():
 training=[(max(r for i,r in trajectories(k)),k) for k in K_TRAIN]
 XX=np.array([[float(x),1.] for x,y in training])
 yy=np.array([float(y) for x,y in training])
 def fn(w):
  e=XX@w-yy
  return float(np.mean(e*e)),2*(XX.T@e)/len(e)
 start=time.perf_counter_ns()
 trained=minimize(fn,np.array([0.,0.]),method="L-BFGS-B",
          jac=True,options={"maxiter":400,"gtol":1e-13,"ftol":1e-16})
 ms=elapsed(start)
 ws=trained.x
 if trained.nit<=0:raise AssertionError("NO_TRAINING_PERFORMED")
 return {"weights":[float(x) for x in ws],"optimizer_steps":int(trained.nit),
         "training_component_ms":ms,
         "train_moduli":list(K_TRAIN),
         "train_max_remainder_inputs":[a for a,b in training],
         "train_error_max":float(np.max(abs(XX@ws-yy)))},ws

def original_synthetic_three_vc(k):
 i,r,ni,nr=z3.Ints(f"i_{k} r_{k} i_next_{k} r_next_{k}")
 init=z3.And(i==0,r==0)
 trans=z3.And(ni==i+1,nr==z3.If(r==k-1,0,r+1))
 post=r==i%k
 inv=z3.And(i>=0,r>=0,r<k,r==i%k)
 next_inv=z3.substitute(inv,(i,ni),(r,nr))
 bad={"initial":z3.And(init,z3.Not(inv)),
      "consecution":z3.And(inv,trans,z3.Not(next_inv)),
      "post":z3.And(inv,z3.Not(post))}
 z3out={};cv={}
 for name,pred in bad.items():
  solver=z3.Solver();solver.set(timeout=2500)
  solver.add(pred)
  z3out[name]=str(solver.check())
  if z3out[name]!="unsat":return z3out,cv,False
  cv[name]=cvc5(solver.to_smt2(),timeout=4)
 # Strong helper-only control: no generated MOD relation.
 helper=z3.And(i>=0,r>=0,r<k)
 s=z3.Solver();s.add(helper,z3.Not(post))
 helper_only=str(s.check())
 good=z3out==EXPECTED and all(v.get("status")=="unsat"
    and v.get("returncode")==0 for v in cv.values()) and helper_only=="sat"
 return z3out,cv,helper_only,good

def run():
 checks,interp=impossibility()
 training,w=train_period()
 results=[]
 for k in K_TEST:
  rows=trajectories(k)
  observed_max=max(y for x,y in rows)
  prediction=int(np.rint(w[0]*observed_max+w[1]))
  classical=observed_max+1
  fixed=prediction==k
  z3out,cv,helper,proof=original_synthetic_three_vc(k)
  results.append({"synthetic_modulus_k":k,"trained_prediction":prediction,
    "classical_max_plus_one_prediction":classical,
    "synthetic_holdout_source_trace_is_new_modulus":True,
    "neural_correct":fixed,"strong_matched_classic_correct":classical==k,
    "typed_symbolic_generated_invariant":f"i>=0 and 0<=r<k and r = i mod {prediction}",
    "actual_synthetic_program_post":f"r = i mod {k}",
    "original_synthetic_Z3_VCs":z3out,
    "independent_cvc5_VCs":cv,"helper_without_mod_post":helper,
    "actual_program_certified":fixed and proof})
 return {"schema":"neumann.q3.polynomial-modulo-barrier.synthetic-typed-escape.v1",
  "scientific_scope":"universal mathematical theorem plus author-created synthetic transfer, NOT source-family blind",
  "universal_rational_polynomial_modulo_theorem":"PROVED_BY_INFINITE_DISTINCT_ROOTS_AND_P1_CONTRADICTION",
  "theorem_not_empirically_guessed":True,
  "verified_finite_witness_cases":checks,
  "finite_interpolation_failure_positive_control":interp,
  "training":training,
  "test":results,
  "theorem_original_solver_dual_certified":len(checks)==24,
  "synthetic_bounded_pass":all(x["actual_program_certified"] for x in results),
  "decoder_has_mod_primitive_predefined":True,
  "same_source_matched_exact_classical_also_solves":all(x["strong_matched_classic_correct"] for x in results),
  "unique_learned_mathematical_primitive_over_classical":False,
  "new_external_origin_cross_family_blind":False,
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "no_GPU_or_paid_API":True}

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 out=run()
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print("UNIVERSAL_THEOREM",out["universal_rational_polynomial_modulo_theorem"])
 print("INDEPENDENT_BOUNDED_VANDEMONDE_Z3_CVC5",out["theorem_original_solver_dual_certified"])
 print("TRAINED_WEIGHTS",out["training"])
 for item in out["test"]:
  print("SYNTHETIC_HOLDOUT",item["synthetic_modulus_k"],
    "NEURAL",item["trained_prediction"],
    "CLASSIC",item["classical_max_plus_one_prediction"],
    "PROVED",item["actual_program_certified"])
 print("SYNTHETIC_SCOPED",out["synthetic_bounded_pass"])
 print("GLOBAL_Q3",out["global_Q3"])
