"""Q3 proof-carrying learned nonlinear AST from RAW original source transitions.

SYNTHETIC DEVELOPMENT ONLY, not SyGuS first blind.
No positive-negative symmetry pairs, no target polynomial used by learner.
Only source transitions, output variable anchor and generic degree<=3
monomials in OTHER variables (pair products restricted to degree 2).
Train by Adam on h(s')-h(s)≈0; integerize coefficients; universal exact
sympy polynomial identity certificate on ORIGINAL source transition/Pre/Post.
Compare exact rational classical synthesis on SAME samples, basis and solver
authority. Stop at first fully proved degree, charge all prior failed fits.
"""
import argparse,hashlib,itertools,json,time
from pathlib import Path
import numpy as np
import sympy as sp
def sources():
 x,y,z=sp.symbols("x y z",integer=True)
 return [
  dict(name="quadratic_accumulator",variables=(x,y),next=(x+1,y+2*x+1),
       anchor=y,pre={x:0,y:0},post=y-x**2,N=128),
  dict(name="cubic_accumulator",variables=(x,y),next=(x+1,y+3*x*x+3*x+1),
       anchor=y,pre={x:0,y:0},post=y-x**3,N=250),
  dict(name="bilinear_running_product",variables=(x,y,z),next=(x+1,y,z+y),
       anchor=z,pre={x:0,z:0},post=z-x*y,N=400)]
def basis(V,degree,anchor):
 out=[]
 for total in range(1,degree+1):
  for power in itertools.product(range(total+1),repeat=len(V)):
   if sum(power)!=total or power[V.index(anchor)]!=0:continue
   if total>2 and sum(bool(q) for q in power)>1:continue
   out.append(sp.prod(v**q for v,q in zip(V,power)))
 return out+[anchor]
def observations(P,seed):
 rg=np.random.default_rng(seed)
 s=np.stack([rg.integers(-8,9,P["N"]) if v==P["anchor"]
              else rg.integers(-5,6,P["N"]) for v in P["variables"]],axis=1)
 nxt=np.column_stack([np.broadcast_to(sp.lambdify(P["variables"],f,"numpy")(*s.T),(P["N"],))
                      for f in P["next"]])
 return s,nxt
def differences(P,states,nexts,B):
 fun=[sp.lambdify(P["variables"],expr,"numpy") for expr in B]
 def phi(s):return np.column_stack([np.broadcast_to(f(*s.T),(len(s),))
                                           for f in fun]).astype(float)
 return phi(nexts)-phi(states)
def fit(D,seed):
 rg=np.random.default_rng(seed);A=D[:,:-1].copy();rhs=-D[:,-1].copy()
 norm=np.maximum(np.sqrt(np.mean(A*A,axis=0)),1e-8);A/=norm
 w=rg.normal(0,.02,A.shape[1]);m=np.zeros_like(w);v=np.zeros_like(w)
 start=time.perf_counter_ns()
 for t in range(1,6501):
  res=A@w-rhs;g=(2/len(A))*(A.T@res)+1e-5*w
  m=.9*m+.1*g;v=.999*v+.001*g*g
  w-=.035*(m/(1-.9**t))/(np.sqrt(v/(1-.999**t))+1e-8)
 c=np.r_[w/norm,1.]
 return c,(time.perf_counter_ns()-start)/1e6,float(np.max(np.abs(D@c)))
def prove(P,I):
 after=I.xreplace(dict(zip(P["variables"],P["next"])))
 init=sp.factor(I.subs(P["pre"],simultaneous=True))
 step=sp.factor(after-I)
 goal=sp.factor(I-P["post"])
 return dict(init_exact=str(init),step_exact=str(step),goal_difference_exact=str(goal),
             fully_inductive_and_original_Post=(init==step==goal==0))
def classical(D,B):
 t=time.perf_counter_ns()
 M=sp.Matrix(np.rint(D).astype(int).tolist())
 v=sp.symbols("a:"+str(M.cols))
 eqs=list(M*sp.Matrix(v))+[v[-1]-1]
 answer=sp.linsolve(eqs,v)
 if not answer:return None,(time.perf_counter_ns()-t)/1e6
 vals=list(next(iter(answer)))
 free=set().union(*(q.free_symbols for q in vals))
 vals=[q.subs({s:0 for s in free}) for q in vals]
 return sp.expand(sum(c*b for c,b in zip(vals,B))),(time.perf_counter_ns()-t)/1e6
def run(P,seed):
 states,nexts=observations(P,seed);trials=[];chosen=None
 rng=np.random.default_rng(90000+seed)
 allB=basis(P["variables"],3,P["anchor"])
 weights=rng.integers(-5,6,len(allB));weights[-1]=1
 untrained=sp.expand(sum(int(c)*b for c,b in zip(weights,allB)))
 negative=prove(P,untrained)
 for degree in (1,2,3):
  B=basis(P["variables"],degree,P["anchor"]);D=differences(P,states,nexts,B)
  params,ms,residual=fit(D,seed+37)
  rounded=np.rint(params).astype(int)
  can_round=np.max(np.abs(params-rounded))<.07
  I=sp.expand(sum(int(c)*b for c,b in zip(rounded,B))) if can_round else None
  certificate=prove(P,I) if I is not None else None
  reference,exactms=classical(D,B)
  exactcertificate=prove(P,reference) if reference is not None else None
  ok=bool(certificate and certificate["fully_inductive_and_original_Post"])
  trial=dict(degree=degree,monomial_operator_count=len(B),actual_fit_wall_ms=ms,
             numeric_training_residual=residual,numeric_coefficients=params.tolist(),
             learned_composed_AST=str(I) if I is not None else None,
             learned_universal_original_source_certificate=certificate,
             learned_full_original_PASS=ok,
             classical_exact_polynomial_AST=str(reference) if reference is not None else None,
             classical_exact_original_source_certificate=exactcertificate,
             classical_full_original_PASS=bool(exactcertificate and
                                                 exactcertificate["fully_inductive_and_original_Post"]),
             classical_exact_synthesis_wall_ms=exactms)
  trials.append(trial)
  if ok:chosen=degree;break
 return dict(task=P["name"],seed=seed,source_transition_AST=list(map(str,P["next"])),
             source_pre={str(k):v for k,v in P["pre"].items()},
             original_source_post_AST=str(P["post"]),positive_target_labels_during_fit=0,
             passed_degree=chosen,without_gradient_fit_PASS=negative["fully_inductive_and_original_Post"],
             all_degree_trials=trials)
def counterexample():
 x,y=sp.symbols("x y",integer=True)
 f=y+2*x+1;g=f+x*(x-1)*(x-2)
 before=[bool(sp.simplify(f.subs({x:j,y:0})-g.subs({x:j,y:0}))==0) for j in (0,1,2)]
 I=y-x*x;delta=sp.factor(I.xreplace({x:x+1,y:g})-I)
 assert all(before) and delta==x*(x-1)*(x-2)
 return dict(first_three_observed_source_transitions_indistinguishable=True,
             symbolic_mutated_original_source_residual=str(delta),
             exact_violating_source_x=3,exact_violation=int(delta.subs(x,3)),
             unchanged_learned_candidate_must_be_rejected=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);a=ap.parse_args()
 t=time.perf_counter_ns()
 rows=[run(P,seed) for P in sources() for seed in range(8)]
 success=sum(r["passed_degree"] is not None for r in rows)
 classic=sum(r["all_degree_trials"][-1]["classical_full_original_PASS"] for r in rows
             if r["passed_degree"] is not None)
 fitted_ms=sum(sum(t["actual_fit_wall_ms"] for t in r["all_degree_trials"]) for r in rows)
 classic_ms=sum(sum(t["classical_exact_synthesis_wall_ms"] for t in r["all_degree_trials"]) for r in rows)
 result=dict(schema="neumann.q3.source_transition_nonlinear_learned_AST_synthetic_v1",
    scope="SYNTHETIC_POSTHOC_DEVELOPMENT_NOT_EXTERNAL_FIRSTBLIND",
    actual_unlabeled_transition_training=True,
    supervised_operator_input="goal variable anchor; generic polynomial degree<=3",
    task_families=3,seed_repetitions_per_family=8,total_runs=len(rows),
    learned_quadratic_cubic_cross_term_original_proofs=success,
    strong_same_data_exact_polynomial_baseline_proofs=classic,
    linear_only_learned_proofs=sum(r["passed_degree"]==1 for r in rows),
    untrained_random_anchor_ablation_proofs=sum(r["without_gradient_fit_PASS"] for r in rows),
    model_fit_ms_sum=fitted_ms,strong_classical_exact_synthesis_ms_sum=classic_ms,
    total_experiment_wall_ms=(time.perf_counter_ns()-t)/1e6,
    training_cost_not_amortized=True,
    finite_source_sample_no_free_lunch=counterexample(),
    manually_given_correct_nonlinear_expression_in_training=False,
    designed_fixed_polynomial_primitive_grammar=True,
    autonomously_invented_new_primitive=False,
    learned_advantage_over_strong_classical=False,
    proven_ten_x_over_strongest_classical=False,
    real_source_family_generalization_unproven=True,
    global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
    all_original_source_trials=rows)
 path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 for key in ("total_runs","learned_quadratic_cubic_cross_term_original_proofs",
             "strong_same_data_exact_polynomial_baseline_proofs","linear_only_learned_proofs",
             "untrained_random_anchor_ablation_proofs","model_fit_ms_sum",
             "strong_classical_exact_synthesis_ms_sum"):
  print("Q3_NONLINEAR_LEARNED_STRUCTURE",key,result[key],flush=True)
 print("EXACT_SOURCE_MUTATION_REJECT",result["finite_source_sample_no_free_lunch"]["exact_violation"],flush=True)
 print("RAW_REPORT_SHA256",hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
 assert success==classic==24 and result["linear_only_learned_proofs"]==0
 assert result["untrained_random_anchor_ablation_proofs"]==0
if __name__=="__main__":main()
