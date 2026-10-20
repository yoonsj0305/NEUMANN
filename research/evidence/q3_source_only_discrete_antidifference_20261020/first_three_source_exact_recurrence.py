"""Q3: post-BMC original-source ONLY discrete polynomial antidifference.
Source initial/transition derive candidate; real published Post is not used
until after candidate is frozen. CLASSICAL, not novel neural learning.
"""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,time
from pathlib import Path
import sympy as sp
import z3
from experiments.q3_source_prove import sexprs,extract_mixed_original,native_original_relations,check_parity,check_formula

COHORT=(
 ("benchmarks/NIA/other/pottsumm3.sl","e0734e4358956b3ca66d280c9d4f8282b18d29b4"),
 ("benchmarks/NIA/2018.CHI_InvGame/s9.desugared.sl","36234fd712b21a9111f834058e8371b10e3de191"),
 ("benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-3.desugared.sl","728ee7e03686db111e47b429e3d584ad3ed668db"))
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def ms(t):return round((time.perf_counter_ns()-t)/1e6,3)
def zcheck(expr,secs=6):
 t=time.perf_counter_ns();s=z3.Solver();s.set(timeout=1000*secs);s.add(expr)
 return str(s.check()),ms(t)
def cvc(expr,secs=12):
 t=time.perf_counter_ns();s=z3.Solver();s.add(expr)
 try:
  r=subprocess.run(["cvc5","--lang=smt2","--decision=internal",
      "--tlimit-per="+str(secs*1000),"-"],input=s.to_smt2(),
      text=True,capture_output=True,timeout=secs+4)
  vals=[x.strip() for x in r.stdout.splitlines() if x.strip()]
  return {"status":vals[-1] if vals else "EMPTY","exit_code":r.returncode,
    "wall_ms":ms(t),"stderr":r.stderr[:100]}
 except Exception as ex:return {"status":"EXCEPTION","error":str(ex)[:160],"wall_ms":ms(t)}
def atoms(e):
 if z3.is_and(e):return [a for x in e.children() for a in atoms(x)]
 return [] if z3.is_true(e) else [e]
def sym(e):
 if z3.is_int_value(e):return sp.Integer(e.as_long())
 k=e.decl().kind()
 if k==z3.Z3_OP_UNINTERPRETED and e.num_args()==0:
  return sp.Symbol(str(e),integer=True)
 cs=list(map(sym,e.children()))
 if k==z3.Z3_OP_ADD:return sp.Add(*cs)
 if k==z3.Z3_OP_SUB:return cs[0]-sum(cs[1:])
 if k==z3.Z3_OP_UMINUS:return -cs[0]
 if k==z3.Z3_OP_MUL:return sp.Mul(*cs)
 raise ValueError("NONPOLYNOMIAL_SOURCE_UPDATE:"+str(e))
def zexpr(e):
 if e.is_Integer:return z3.IntVal(int(e))
 if e.is_Symbol:return z3.Int(str(e))
 if e.is_Add:return z3.Sum(*list(map(zexpr,e.args)))
 if e.is_Mul:
  out=z3.IntVal(1)
  for v in e.args:out*=zexpr(v)
  return out
 if e.is_Pow and e.exp.is_Integer and e.exp>=0:
  return zexpr(e.base)**int(e.exp)
 raise ValueError("UNHANDLED_SYMPY_EXPR:"+str(e))
def integer_eq(e,syms):
 poly=sp.Poly(sp.expand(e),*syms,domain=sp.QQ)
 denominator=math.lcm(*[int(c.q) for c in poly.coeffs()]) if poly.coeffs() else 1
 value=sp.expand(e*denominator)
 assert all(c.q==1 for c in sp.Poly(value,*syms).coeffs())
 return zexpr(value)==0,{"expression":str(sp.Eq(value,0)),
   "exact_integer_denominator":denominator,
   "polynomial_degree":sp.Poly(value,*syms).total_degree()}
def derive_updates(src,native):
 now,nxt=src["now"],src["next"]
 assignments={}
 for e in atoms(native["trans"]):
  if not z3.is_eq(e):continue
  l,r=e.children()
  for future in nxt:
   if l.eq(future):assignments[str(future)]=r
   elif r.eq(future):assignments[str(future)]=l
 if len(assignments)!=len(nxt):raise ValueError("NEXT_COORDINATE_MISSING")
 for iteration in range(len(nxt)+2):
  start=[assignments[str(x)].sexpr() for x in nxt]
  for future in nxt:
   replacements=[(u,assignments[str(u)]) for u in nxt if not u.eq(future)]
   assignments[str(future)]=z3.simplify(z3.substitute(assignments[str(future)],*replacements))
  if start==[assignments[str(x)].sexpr() for x in nxt]:break
 if any(any(z3.eq(x,u) for u in nxt) for x in []):raise ValueError("IMPOSSIBLE")
 all_new=z3.Or(*[x!=assignments[str(x)] for x in nxt])
 validity,t=zcheck(z3.And(native["trans"],all_new),secs=8)
 if validity!="unsat":raise ValueError("EXTRACTED_SOURCE_TRANS_NOT_PROVED_"+validity)
 return {str(v):sp.expand(sym(assignments[str(vp)])) for v,vp in zip(now,nxt)},t
def discover(src,native):
 t=time.perf_counter_ns()
 now,nxt=src["now"],src["next"]
 upd,proof_time=derive_updates(src,native)
 names=[str(v) for v in now]
 ss={name:sp.Symbol(name,integer=True) for name in names}
 stat={v for v in names if upd[v]==ss[v]}
 clocks={v for v in names if sp.expand(upd[v]-ss[v])==1}
 accepted=[];rejected=[];parts=[]
 for clock in sorted(clocks):
  for var in names:
   if var==clock or var in stat:continue
   delta=sp.expand(upd[var]-ss[var])
   if delta==0 or ss[var] in delta.free_symbols:continue
   if not delta.free_symbols.issubset({ss[clock],*[ss[v] for v in stat]}):continue
   tau=sp.Symbol("_discrete_index",integer=True)
   poly=sp.expand(sp.summation(delta.subs(ss[clock],tau),(tau,0,ss[clock]-1)))
   if not bool(poly.is_polynomial(*ss.values())):continue
   residual=sp.expand(poly.subs(ss[clock],ss[clock]+1)-poly-delta)
   if residual!=0:raise ValueError("DISCRETE_ANTIDIFFERENCE_NOT_EXACT")
   candidate,meta=integer_eq(ss[var]-poly,list(ss.values()))
   pre_bad,pre_time=zcheck(z3.And(native["pre"],z3.Not(candidate)),secs=5)
   meta.update({"clock":clock,"accumulator":var,
     "delta":str(delta),"antidifference":str(poly),
     "source_pre_bad":pre_bad,"source_pre_ms":pre_time,
     "finite_difference_proven":True})
   if pre_bad=="unsat":accepted.append(meta);parts.append(candidate)
   else:rejected.append(meta)
 for name in sorted(clocks|stat):
  fact=z3.Int(name)>=0
  res,_=zcheck(z3.And(native["pre"],z3.Not(fact)),secs=3)
  if res=="unsat":parts.append(fact);accepted.append({"source_domain":str(fact)})
 for guard in atoms(native["trans"]):
  if guard.decl().kind()!=z3.Z3_OP_LT:continue
  lo,hi=guard.children()
  if str(lo) not in clocks:continue
  if not(z3.is_int_value(hi) or str(hi) in stat):continue
  fact=lo<=hi
  res,_=zcheck(z3.And(native["pre"],z3.Not(fact)),secs=3)
  if res=="unsat":parts.append(fact);accepted.append({"source_guard_bound":str(fact)})
 if not parts:raise ValueError("NO_SOURCE_ONLY_INVARIANT_FOUND")
 return z3.And(*parts),{"source_only_generated":accepted,
  "source_pre_rejected":rejected,
  "source_exact_updates":{k:str(v) for k,v in upd.items()},
  "source_increment_clocks":sorted(clocks),"source_constant_parameters":sorted(stat),
  "source_transition_entailment_Z3_ms":proof_time,
  "source_only_generation_ms":ms(t)}
def one(root,path,expect):
 start=time.perf_counter_ns()
 result={"source":path,"expected_git_blob":expect,"full_original_Z3_cvc5_3VC":False}
 try:
  raw=(root/path).read_bytes()
  if blob(raw)!=expect:raise ValueError("ORIGINAL_GIT_SHA_MISMATCH")
  result["original_source_sha256"]=sha(raw)
  forms=sexprs(raw);s=extract_mixed_original(forms)
  n=native_original_relations(forms,s);n.update({"now":s["now"],"next":s["next"]})
  parity=check_parity(s,n);result["original_parser_parity"]=parity
  if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
   raise ValueError("ORIGINAL_NATIVE_CUSTOM_PARITY_MISMATCH")
  if check_formula(n["pre"])!="sat" or check_formula(z3.Not(n["post"]))!="sat":
   raise ValueError("ORIGINAL_VACUITY")
  candidate,mechanism=discover(s,n)
  result["pre_trans_only_generated"]=mechanism
  result["original_candidate_SMT"]=candidate.sexpr()
  # Source Post is FIRST touched for candidate proof AFTER synthesis above.
  nxt=z3.substitute(candidate,*list(zip(s["now"],s["next"])))
  proof={"initial":z3.And(n["pre"],z3.Not(candidate)),
    "consecution":z3.And(candidate,n["trans"],z3.Not(nxt)),
    "post":z3.And(candidate,z3.Not(n["post"]))}
  result["Z3_native_original_3VC"]={}
  result["cvc5_native_original_3VC"]={}
  for key,f in proof.items():
   st,t=zcheck(f,secs=10)
   result["Z3_native_original_3VC"][key]={"status":st,"wall_ms":t}
   result["cvc5_native_original_3VC"][key]=cvc(f,secs=12) if st=="unsat" else {"status":"NOT_RUN"}
  result["full_original_Z3_cvc5_3VC"]=(all(v["status"]=="unsat"
     for v in result["Z3_native_original_3VC"].values()) and all(
     v.get("status")=="unsat" and v.get("exit_code")==0
     for v in result["cvc5_native_original_3VC"].values()))
  result["status"]="POSTHOC_CLASSICAL_ORIGINAL_DUAL_PASS" if result["full_original_Z3_cvc5_3VC"] else "PARTIAL_NONLINEAR_SOLVER_UNKNOWN_OR_COUNTEREXAMPLE"
 except Exception as exc:
  result["status"]="ABSTAIN_SOURCE_OR_ALGORITHM_ERROR"
  result["error"]=type(exc).__name__+":"+str(exc)[:320]
 result["source_wall_ms"]=ms(start)
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 rows=[one(a.root,*row) for row in COHORT]
 for r in rows:print("EXACT_SOURCE_ANTIDIFFERENCE",r["source"],r.get("status"),
   "Z3",r.get("Z3_native_original_3VC"),"ERR",r.get("error"),flush=True)
 result={"schema":"neumann.q3.three.source_exact.discrete_antidifference.v1",
   "source_sha_originally_frozen_before_bmc":True,
   "this_source_already_opened_after_BMC":True,
   "three_source_rows_preserved":len(rows)==3,
   "independent_original_full_3VC_pass_count":sum(x["full_original_Z3_cvc5_3VC"] for x in rows),
   "classical_only_no_neural_calls":True,
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN","sources":rows}
 a.out.parent.mkdir(exist_ok=True,parents=True)
 a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print("CLASSICAL_ORIGINAL_3VC",result["independent_original_full_3VC_pass_count"],"/3 GLOBAL_Q3 OPEN")
if __name__=="__main__":main()
