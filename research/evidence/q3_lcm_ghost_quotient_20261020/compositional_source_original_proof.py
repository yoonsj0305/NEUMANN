"""Source-linked, decomposed and independently checkable proof of genuine
LoopInvGen lcm original safety. 4 source-mined mod invariants are lifted
to integer ghost quotients, with branch-specific updates derived algebraically.
All sublemmas Z3+cvc5; original monolithic 3VC may remain UNKNOWN.
NOT neural, NOT first-blind, NOT frontier.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,subprocess,time
from pathlib import Path
import sympy as sp
import z3
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,
 check_formula,all_exact_branch_updates)
from research.evidence.q3_lcm_modular_lattice_20261020.second_exact_integer_lattice import (
 fixed_source_only_lattice,signed_linear_template)
from research.evidence.q3_lcm_modular_lattice_20261020.source_only_modular_houdini import (
 REL,BLOB,SRC_SHA,exact_git_blob,query)

def wall(t):return round((time.perf_counter_ns()-t)/1e6,3)
def external_cvc5(smt2,seconds=8):
 t=time.perf_counter_ns()
 try:
  z=subprocess.run(["cvc5","--lang=smt2","--decision=internal",
          "--tlimit-per="+str(seconds*1000),"-"],input=smt2,
          text=True,capture_output=True,timeout=seconds+4,check=False)
  lines=[line.strip() for line in z.stdout.splitlines() if line.strip()]
  return {"result":lines[-1] if lines else "EMPTY",
    "exit_code":z.returncode,"wall_ms":wall(t),
    "stderr_excerpt":z.stderr[:100]}
 except Exception as exc:
  return {"result":"NO_RESULT","error":str(exc)[:120],"wall_ms":wall(t)}

def dual(name,contradiction,seconds=8):
 t=time.perf_counter_ns()
 z=z3.Solver();z.set(timeout=seconds*1000);z.add(contradiction)
 z3result=str(z.check())
 cvc=external_cvc5(z.to_smt2(),seconds=seconds) if z3result=="unsat" else {"result":"NOT_RUN"}
 return {"name":name,"Z3":z3result,"cvc5":cvc,
   "both_unsat":z3result=="unsat" and cvc.get("result")=="unsat"
     and cvc.get("exit_code")==0,"Z3_wall_ms":wall(t)}

def dnf(expr):
 if z3.is_or(expr):return [row for q in expr.children() for row in dnf(q)]
 if z3.is_and(expr):
  rows=[[]]
  for ch in expr.children():
   rows=[a+b for a in rows for b in dnf(ch)]
   if len(rows)>8:raise RuntimeError("TOO_MANY_ORIGINAL_BRANCHES")
  return rows
 if z3.is_true(expr):return [[]]
 if z3.is_false(expr):return []
 return [[expr]]

def vec_formula(vec,values):
 return z3.Sum(*[int(c)*x for c,x in zip(vec,values) if int(c)]) if sum(int(c)!=0 for c in vec)>1 else next((int(c)*v for c,v in zip(vec,values) if int(c)),z3.IntVal(0))

def derive_integer_coeffs(columns,target):
 mat=sp.Matrix.hstack(*[sp.Matrix(v) for v in columns])
 sol,free=mat.gauss_jordan_solve(sp.Matrix(target))
 if free.rows:raise RuntimeError("NON_UNIQUE_INTEGER_BASIS")
 if any(not bool(x.is_Integer) for x in sol):raise RuntimeError("NON_INTEGER_COEFFICIENT")
 got=tuple(int(v) for v in mat*sol)
 if got!=tuple(target):raise RuntimeError("INTEGER_CERTIFICATE_REPLAY_FAIL")
 return [int(x) for x in sol]

def run(source_root):
 whole=time.perf_counter_ns()
 path=source_root/REL
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SRC_SHA or exact_git_blob(raw)!=BLOB:
  raise RuntimeError("ORIGINAL_GIT_BLOB_SHA_MISMATCH")
 forms=sexprs(raw);src=extract_mixed_original(forms)
 native=native_original_relations(forms,src)
 native.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,native)
 if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
  raise RuntimeError("CUSTOM_NATIVE_ORIGINAL_PARITY_NOT_VALID")
 if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
  raise RuntimeError("VACUOUS_ORIGINAL")
 mined,_=fixed_source_only_lattice(src,native)
 labels=set(mined["final_modular_candidates"])
 sta=[];mut=[]
 for i,(v,vp) in enumerate(zip(src["now"],src["next"])):
  if query(native["trans"],v!=vp)[0]=="unsat":
   if query(native["pre"],z3.Not(v>0))[0]=="unsat":sta.append(i)
  else:mut.append(i)
 if len(sta)!=2 or len(mut)!=4:raise RuntimeError("SCOPE_STATIC_MUTABLE_MISMATCH")
 groups=[]
 for m in sta:
  selected=[(label,tuple(c),f) for label,c,f in signed_linear_template(src,m,mut)
        if label in labels]
  if len(selected)!=2:raise RuntimeError("EXPECTED_TWO_SOURCE_MINED_RELATIONS_PER_MODULUS")
  groups.append((m,selected))
 state=src["now"];nextstate=src["next"]
 n=len(state)
 ghosts=[[z3.Int(f"q3ghost_now_{g}_{j}") for j in range(2)] for g in range(2)]
 positives=[v>0 for v in state]
 eqs=[vec_formula(v,state)==state[m]*ghosts[g][j]
  for g,(m,selected) in enumerate(groups) for j,(_,v,_) in enumerate(selected)]
 lifted_inv=z3.And(*positives,*eqs)

 checks=[]
 source_exhaustion=dual("ORIGINAL_TRANS_EXHAUSTED_BY_ALL_DNF_BRANCHES",
       z3.Xor(native["trans"],z3.Or(*[
           z3.And(*row) for row in dnf(native["trans"])])),seconds=5)
 checks.append(source_exhaustion)
 branch_atoms=dnf(src["trans"])
 updates=all_exact_branch_updates(src)
 if len(branch_atoms)!=len(updates) or len(updates)!=2:
  raise RuntimeError("EXACT_UPDATE_BRANCH_COUNT_MISMATCH")
 source_update_checks=[]
 ghosts_updates=[]
 for k,(atoms,(A,b)) in enumerate(zip(branch_atoms,updates)):
  original_branch=z3.And(*atoms)
  for i in range(n):
   update=vec_formula([int(x) for x in A.row(i)],state)+int(b[i])
   item=dual(f"ORIGINAL_BRANCH_{k}_NEXT_{i}_EXACT_SOURCE_UPDATE",
       z3.And(original_branch,nextstate[i]!=update),seconds=6)
   checks.append(item);source_update_checks.append(item)
  if any(int(q)!=0 for q in b):raise RuntimeError("UNHANDLED_AFFINE_OFFSET")
  group_updates=[]
  for g,(m,selected) in enumerate(groups):
   if any(int(A[m,i])!=int(i==m) for i in range(n)):
    raise RuntimeError("ORIGINAL_MODULUS_NOT_PRESERVED")
   columns=[tuple(int(i==m) for i in range(n)),
     *[v for label,v,f in selected]]
   neww=[]
   for j,(label,direction,formula) in enumerate(selected):
    updated=tuple(int(t) for t in sp.Matrix([direction])*A)
    coeff=derive_integer_coeffs(columns,updated)
    qnext=z3.IntVal(coeff[0])+z3.Sum(*[
        z3.IntVal(coeff[h+1])*ghosts[g][h] for h in range(2)])
    # Verify a branch's actual SOURCE next variable expression modulo
    # explicit old ghost witnesses; this is a local first-order theorem.
    after=vec_formula(direction,nextstate)
    lemma=z3.And(lifted_inv,original_branch,
         after !=nextstate[m]*qnext)
    check=dual(f"GHOST_INDUCTIVE_BRANCH{k}_MODGROUP{g}_FORM{j}",lemma,seconds=8)
    checks.append(check)
    neww.append({"name":label,"int_lattice_coords":coeff,
      "computed_next_quotient_smt":qnext.sexpr(),
      "certificate":check})
   group_updates.append(neww)
  ghosts_updates.append(group_updates)
  for i in range(n):
   item=dual(f"ORIGINAL_BRANCH{k}_PRESERVES_POSITIVE_STATE_{i}",
      z3.And(lifted_inv,original_branch,z3.Not(nextstate[i]>0)),seconds=6)
   checks.append(item)

 # Original Pre yields one explicit group of witness constants; their
 # search reads PRE and mined formulas, never the published post.
 initials=[]
 for g,(m,selected) in enumerate(groups):
  for j,(_,vec,_) in enumerate(selected):
   possible=[]
   for q in range(-4,5):
    if query(native["pre"],vec_formula(vec,state)!=state[m]*q)[0]=="unsat":
     possible.append(q)
   if len(possible)!=1:raise RuntimeError("SOURCE_PRE_GHOST_NOT_UNIQUE")
   initials.append((g,j,possible[0]))
 initializer=z3.And(*[ghosts[g][j]==val for g,j,val in initials])
 checks.append(dual("REAL_ORIGINAL_PRE_HAS_EXPLICIT_INITIAL_GHOST_WITNESSES",
  z3.And(native["pre"],initializer,z3.Not(lifted_inv)),seconds=7))

 # Unmodified original goal: post says if x==y, u/v positive and u+v
 # both divisible by source-positive constant a and b. Validate this exact
 # presentation semantically against ORIGINAL parsed native Post.
 a,b,x,y,u,v=state
 goal=z3.Or(x!=y,z3.And(u>0,v>0,
   ((u+v)%a)==0,((u+v)%b)==0))
 checks.append(dual("ORIGINAL_PUBLISHED_POST_HAS_EXACT_LCM_GOAL",
    z3.Xor(native["post"],goal),seconds=7))
 target=(0,0,0,0,1,1)
 exiting=(0,0,1,-1,0,0)
 termination_lemmas=[]
 for g,(m,selected) in enumerate(groups):
  columns=[v for _,v,f in selected]+[exiting]
  coeff=derive_integer_coeffs(columns,target)
  Q=z3.Sum(*[int(coeff[j])*ghosts[g][j] for j in range(2)])
  item=dual(f"ORIGINAL_EXIT_MODULUS_{g}_HAS_INTEGER_QUOTIENT",
     z3.And(lifted_inv,x==y,(u+v)!=state[m]*Q),seconds=7)
  checks.append(item)
  termination_lemmas.append({"modulus":str(state[m]),
     "source_mined_form_coefficients":coeff[:2],
     "original_exit_difference_coefficient":coeff[2],
     "integer_witness_expression":Q.sexpr(),
     "check":item})
  # Independently certify universal (m*K) mod m = 0 for all m>0
  # with no candidate-specific hidden assumptions or witness values.
  mm,qq=z3.Ints(f"q3_universal_modulus_{g} q3_universal_quotient_{g}")
  check=dual(f"UNIVERSAL_EUCLIDEAN_REMAINDER_MULTIPLE_{g}",
      z3.And(mm>0, ((mm*qq)%mm)!=0),seconds=10)
  checks.append(check)

 # These verified pieces imply the unchanged original Post for any
 # original transition path. No unsafe assumption about existential
 # witness availability: source PRE explicit quotient constants and
 # deterministic branch ghost updates provide total witness lifting.
 ok=all(c["both_unsat"] for c in checks)
 return {"schema":"neumann.q3.original_lcm.compositional_ghost_certificate.v1",
   "source":"LoopInvGen/"+REL,"upstream_rev":"6ac90265b11431c9477dfbd33e3e3380234c0499",
   "original_sha256":SRC_SHA,"original_git_blob":BLOB,
   "original_native_custom_parser_parity":parity,
   "selected_modular_relations":[v[0] for m,group in groups for v in group],
   "source_only_integer_lattice_old_certificate":mined["final_exact_source_induction_certificate"],
   "explicit_initial_integer_witness_values":[{"group":g,"index":j,"value":k}
       for g,j,k in initials],
   "source_derived_original_branch_integer_ghost_updates":ghosts_updates,
   "original_exit_quotient_witnesses":termination_lemmas,
   "compositional_sublemmas":checks,
   "total_sublemmas":len(checks),
   "dual_independently_unsat_sublemmas":sum(c["both_unsat"] for c in checks),
   "full_compositional_original_safety_certificate":ok,
   "monolithic_original_3VC_unchanged_status":{"initial":"unsat","consecution":"unknown","post":"unknown"},
   "genuine_unseen_original_source":False,"neural_trained_new_structure":False,
   "same_information_classical_method":True,
   "full_neural_Q3_invention":"NOT_PROVEN",
   "Q3_global":"OPEN","Q1_Q7_global":"OPEN","gpu_calls":0,"paid_api_calls":0,
   "whole_study_wall_ms":wall(whole)}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source-root",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args(); result=run(a.source_root)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print("SOURCE",result["source"],"CHECKS",result["total_sublemmas"])
 print("DUAL_INDEPENDENT_CHECKS",result["dual_independently_unsat_sublemmas"])
 print("DECOMPOSED_REAL_ORIGINAL_SAFETY",result["full_compositional_original_safety_certificate"])
 for c in result["compositional_sublemmas"]:
  if not c["both_unsat"]:print("NOT_PROVEN_LEMMA",c["name"],c["Z3"],c["cvc5"])
 print("Q3_GLOBAL",result["Q3_global"])
if __name__=="__main__":main()
