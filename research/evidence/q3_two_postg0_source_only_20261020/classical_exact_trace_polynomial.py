"""Original real source-only classical algebra generators, after immutable G0.
NEITHER learned nor prospectively blind. Source queries BEFORE reading Post
for candidate selection; actual published native Pre/Trans/Post check in 3VC.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math,time,subprocess
from pathlib import Path
from functools import reduce
from operator import mul
import sympy as sp
import z3
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,
 check_formula,source_proof)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
COHORT=(
 ("quadratic_accumulator","benchmarks/NIA/other/mul.sl",
   "f6291a03edee61b5624bd5b394913988d4c5af9a"),
 ("polynomial_clock","benchmarks/NIA/2018.CHI_InvGame/sorin04.desugared.sl",
   "565795c4792ead110b65aad27fa5657bbbee074e")
)
EXPECTED={"initial":"unsat","consecution":"unsat","post":"unsat"}
def now_ms(t):return round((time.perf_counter_ns()-t)/1e6,3)
def blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def z3check(*args,timeout=2400):
 s=z3.Solver();s.set(timeout=timeout);s.add(*args)
 result=s.check()
 return str(result),s.model() if result==z3.sat else None
def original_source_episodes(src,native,domain=range(-3,8),max_init=100):
 """Diversify Pre using general pair constraints; never inspect original Post.
 All next states are actual source Trans Z3 models, proven unique per step."""
 now,nxt=src["now"],src["next"]
 state_by_pre={}
 checks={"pre_queries":0,"successor_unique_z3_unsat":0,
    "real_original_transitions":0,"transition_unknown":0}
 for u,v in itertools.combinations(range(len(now)),2):
  for a,b in itertools.product(domain,repeat=2):
   checks["pre_queries"]+=1
   result,model=z3check(native["pre"],now[u]==a,now[v]==b)
   if result!="sat":continue
   state=tuple(int(model.eval(x,model_completion=True).as_long()) for x in now)
   state_by_pre[state]=None
   if len(state_by_pre)>=max_init:break
  if len(state_by_pre)>=max_init:break
 if not state_by_pre:
  status,model=z3check(native["pre"])
  if status!="sat":raise RuntimeError("CANNOT_SAMPLE_SOURCE_PRE")
  state=tuple(int(model.eval(x,model_completion=True).as_long()) for x in now)
  state_by_pre[state]=None
 states=set()
 for pre_state in state_by_pre:
  state=pre_state
  for step in range(28):
   states.add(state)
   conds=[x==v for x,v in zip(now,state)]
   result,model=z3check(native["trans"],*conds)
   if result=="unsat":break
   if result!="sat":
    checks["transition_unknown"]+=1
    raise RuntimeError("ORIGINAL_NEXT_SOURCE_UNKNOWN")
   successor=tuple(int(model.eval(x,model_completion=True).as_long()) for x in nxt)
   diff=z3.Or(*[x!=v for x,v in zip(nxt,successor)])
   uresult,_=z3check(native["trans"],*conds,diff)
   if uresult!="unsat":raise RuntimeError("SOURCE_SUCCESSOR_NOT_UNIQUE_"+str(uresult))
   checks["successor_unique_z3_unsat"]+=1
   checks["real_original_transitions"]+=1
   state=successor
  else:
   raise RuntimeError("BOUND_EXCEEDED_28_STEPS")
 checks["initial_models"]=len(state_by_pre)
 checks["unique_reachable_states"]=len(states)
 return sorted(states),checks

def expr_integer_from_fraction_polynomial(raw,now):
 """Build exact integer equation using the LCM denominators, no truncation."""
 polynomial=sp.Poly(raw, *now,domain=sp.QQ) if False else sp.Poly(raw,domain=sp.QQ)
 denom=sp.ilcm(*[int(x.q) for x in polynomial.coeffs()]) if polynomial.coeffs() else 1
 eq=sp.expand(denom*raw)
 def convert(term):
  if term.is_Integer:return z3.IntVal(int(term))
  if term.is_Symbol:return z3.Int(str(term))
  if term.is_Add:return z3.Sum(*[convert(v) for v in term.args])
  if term.is_Mul:return reduce(mul,(convert(v) for v in term.args),z3.IntVal(1))
  if term.is_Pow and term.exp.is_Integer and term.exp>=0:return convert(term.base)**int(term.exp)
  raise RuntimeError("UNSUPPORTED_SYMBOLIC_EXPRESSION_"+str(term))
 if any(x.q!=1 for x in sp.Poly(eq).coeffs()):
  raise RuntimeError("RATIONAL_INVARIANT_NOT_INTEGERIZED")
 return convert(eq)==0, str(sp.Eq(eq,0))

def exact_nullspace_candidate(states,now):
 n=len(now)
 if n!=4:raise RuntimeError("FOUR_STATE_VARS_REQUIRED")
 tuples=[()]+[(i,) for i in range(n)]+list(itertools.combinations_with_replacement(range(n),2))
 assert len(tuples)==15
 t=time.perf_counter_ns()
 M=sp.Matrix([[reduce(mul,(sp.Integer(s[k]) for k in mon),sp.Integer(1))
          for mon in tuples] for s in states])
 basis=M.nullspace()
 if not basis:raise RuntimeError("NO_NONTRIVIAL_DEG2_EXACT_NULLSPACE")
 possible=[]
 symbols=sp.symbols(' '.join(str(v) for v in now))
 for v in basis:
  mulden=sp.ilcm(*[int(c.q) for c in v])
  ci=[int(mulden*c) for c in v]
  gcd=math.gcd(*ci)
  ci=[x//max(gcd,1) for x in ci]
  nonzero=sum(x!=0 for x in ci)
  # primitive L1/sparsity selection independent of original Post
  magnitude=sum(abs(x) for x in ci)
  raw=sum(sp.Integer(w)*reduce(mul,(symbols[z] for z in mon),sp.Integer(1))
          for w,mon in zip(ci,tuples))
  candidate,display=expr_integer_from_fraction_polynomial(sp.expand(raw),symbols)
  possible.append((nonzero,magnitude,display,candidate,ci))
 possible.sort(key=lambda x:(x[0],x[1],x[2]))
 _,_,chosen,formula,coeff=possible[0]
 return {"candidate":formula,
    "expression":chosen,"degree2_monomials":len(tuples),
    "exact_trace_row_rank":int(M.rank()),
    "exact_nullspace_dimension":len(basis),
    "chosen_monomial_coefficients":coeff,
    "whole_symbolic_discovery_ms":now_ms(t)},formula

def exact_clock_polynomials(states,src,native):
 now,nxt=src["now"],src["next"]
 # Clock is source-Trans-proven +1 without looking at target Post.
 choices=[i for i,(v,vp) in enumerate(zip(now,nxt))
   if z3check(native["trans"],vp!=v+1)[0]=="unsat"]
 if not choices:raise RuntimeError("NO_ORIGINAL_SOURCE_GUARANTEED_CLOCK")
 clock=choices[0]
 symbols=sp.symbols(' '.join(str(v) for v in now))
 x=symbols[clock]
 candidates=[]
 descriptions=[]
 for j,var in enumerate(now):
  if j==clock:continue
  ordered=sorted({(t[clock],t[j]) for t in states})
  if len({v for v,_ in ordered})<4:raise RuntimeError("INSUFFICIENT_SOURCE_CLOCK_STATES")
  fitted=None
  for degree in range(0,4):
   polynomial=sp.interpolate(ordered[:degree+1],x)
   if all(polynomial.subs(x,t)==y for t,y in ordered):
    fitted=(degree,sp.expand(polynomial));break
  if fitted is None:raise RuntimeError("DEGREE3_SOURCE_FIT_FAILURE")
  degree,poly=fitted
  # Equation y - P(clock)=0 rational coefficients cleared exactly.
  assertion,readable=expr_integer_from_fraction_polynomial(symbols[j]-poly,symbols)
  candidates.append(assertion)
  descriptions.append({"source_state":str(var),
    "clock_variable":str(now[clock]),"degree":degree,
    "original_source_polynomial":str(poly),"exact_integerized_invariant":readable})
 return {"clock_chosen_from_original_trans_not_Post":str(now[clock]),
 "fitted_from_pre_trans_only":descriptions,
 "source_trajectory_samples":len(states)},z3.And(*candidates)

def one(root,kind,relative,expect):
 t=time.perf_counter_ns()
 path=root/relative
 raw=path.read_bytes()
 if blob(raw)!=expect:raise ValueError("ORIGINAL_GIT_BLOB_MISMATCH")
 forms=sexprs(raw);src=extract_mixed_original(forms)
 native=native_original_relations(forms,src)
 native.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,native)
 if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
  raise RuntimeError("ORIGINAL_PRE_TRANS_POST_SEMANTIC_PARITY_FAIL")
 if z3check(native["pre"])[0]!="sat" or z3check(z3.Not(native["post"]))[0]!="sat":
  raise RuntimeError("VACUOUS_ORIGINAL")
 states,trace=original_source_episodes(src,native,
       domain=range(-3,8),max_init=120 if kind=="quadratic_accumulator" else 2)
 if kind=="quadratic_accumulator":
  mechanism,inv=exact_nullspace_candidate(states,src["now"])
 else:
  mechanism,inv=exact_clock_polynomials(states,src,native)
 # Post is accessed ONLY AFTER source-only structures are frozen above.
 proof=source_proof(inv,native)
 raw_double={}
 if proof["accepted"]:
  raw_double=check_original_candidate(path,inv.sexpr(),
    expected_source_sha256=hashlib.sha256(raw).hexdigest())
 independent=raw_double.get("cvc5_original_three_vc") or {}
 dual=(raw_double.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
   and set(independent)==set(EXPECTED)
   and all(v.get("status")=="unsat" and v.get("returncode")==0
        for v in independent.values()))
 post_only=source_proof(native["post"],native)
 result={"source":relative,"source_sha256":hashlib.sha256(raw).hexdigest(),
    "git_blob":expect,"source_original_semantic_parity":parity,
    "source_only_trace_generator":trace,
    "source_only_math_generator":mechanism,
    "candidate_original_SMT":inv.sexpr(),
    "candidate_generated_without_original_Post":True,
    "exact_original_Z3_vcs":proof["vcs"],
    "exact_original_Z3_pass":proof["accepted"],
    "exact_original_cvc5_vcs":independent,
    "exact_original_cvc5_pass":dual,
    "original_post_only_ablation":post_only["vcs"],
    "full_original_independent_3VC_pass":dual and proof["accepted"] and
      not post_only["accepted"],
    "source_kind":"POST_G0_OPENED_CLASSICAL_ONLY",
    "no_neural_training_and_no_new_neural_operator":True,
    "whole_case_wall_ms":now_ms(t)}
 return result

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args();rows=[]
 for k,rel,sha in COHORT:
  try:result=one(args.root,k,rel,sha)
  except Exception as e:result={"source":rel,"git_blob":sha,
    "full_original_independent_3VC_pass":False,
    "error":type(e).__name__+":"+str(e)[:350],
    "status":"FAIL_CLOSED_EXCEPTION_OR_UNSUPPORTED"}
  print("ORIGINAL_CLASSIC_CASE",rel,
       "DUAL_CERT",result["full_original_independent_3VC_pass"],
       "Z3",result.get("exact_original_Z3_vcs"),
       "ERROR",result.get("error"))
  rows.append(result)
 summary={"schema":"neumann.q3.two.real.original.sourceonly.classical.afterG0.v1",
  "current_cohort_originals":2,
  "all_rows_retained":len(rows)==2,
  "total_double_certified":sum(x["full_original_independent_3VC_pass"] for x in rows),
  "first_new_origin_G0_original_portfolio_historical_UNRESOLVED":2,
  "source_was_opened_after_first_G0":True,
  "all_training_neural_calls":0,"all_paid_api_calls":0,
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN","cases":rows}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 print("NEW_ORIGINAL_CLASSICAL_CERTIFIED",summary["total_double_certified"],"/2")
 print("GLOBAL_Q3",summary["global_Q3"])
if __name__=="__main__":main()
