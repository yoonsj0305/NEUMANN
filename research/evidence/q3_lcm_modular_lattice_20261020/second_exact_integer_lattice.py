"""Exact integer congruence closure without solver-timeout-induced lost atoms.
Previous source-only Houdini first-failure receipt kept IMMUTABLE; its key 4
atoms received Z3 UNKNOWN (not SAT), so algebraic source-affine proof is used.
Post is kept entirely untouched and absent from learned-free candidate selection.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,time
from pathlib import Path
import sympy as sp
from sympy.matrices.normalforms import hermite_normal_form
import z3
from research.evidence.q3_lcm_modular_lattice_20261020.source_only_modular_houdini import (
  REL,BLOB,SRC_SHA,EXPECTED,now_ms,exact_git_blob,query,
  generate_candidates,source_bad_vcs,cvc5_on_vc)
from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,
  check_formula,source_proof,all_exact_branch_updates)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

def signed_linear_template(source,mod,variables):
 n=len(source["now"]);state=source["now"]
 for i in variables:
  c=tuple(1 if x==i else 0 for x in range(n))
  yield (f"{state[i]} mod {state[mod]} = 0",c,state[i]%state[mod]==0)
 for i,j in itertools.combinations(variables,2):
  for sign in (1,-1):
   c=tuple((1 if x==i else sign if x==j else 0) for x in range(n))
   f=state[i]+sign*state[j]
   yield (f"({state[i]} {'+' if sign==1 else '-'} {state[j]}) mod {state[mod]} = 0",
     c,f%state[mod]==0)

def integer_lattice_membership(columns,required):
 """Exact integer span (NOT rational span) by canonical HNF."""
 try:
  M=sp.Matrix.hstack(*[sp.Matrix(v) for v in columns])
  H=hermite_normal_form(M)
  vals,params=H.gauss_jordan_solve(sp.Matrix(required))
  if params.rows>0:return False,None
  if any(not bool(z.is_Integer) for z in vals):return False,None
  if H*vals !=sp.Matrix(required):raise RuntimeError("HNF_CHECK_BROKEN")
  return True,[int(x) for x in vals]
 except ValueError:return False,None

def fixed_source_only_lattice(source,native):
 statics,mutable,ignored_candidates,positives=generate_candidates(source,native)
 branches=all_exact_branch_updates(source)
 for A,b in branches:
  if A.shape!=(len(source["now"]),len(source["now"])):
   raise RuntimeError("BAD_EXACT_SOURCE_BRANCH_SHAPE")
  if any(v!=0 for v in b):
   raise RuntimeError("NONZERO_AFFINE_OFFSET_NOT_SUPPORTED")
  if any(not val.is_Integer for val in A):
   raise RuntimeError("NONINTEGRAL_BRANCH_TRANSITION_MATRIX")
 n=len(source["now"])
 assert len(statics)==2 and len(mutable)==4,"SOURCE_TYPED_CAP_EXPECTED"
 groups=[];pre_cases=[]
 for m in statics:
  good=[]
  for label,c,p in signed_linear_template(source,m,mutable):
   verdict=query(native["pre"],z3.Not(p))[0]
   pre_cases.append({"modulus_idx":m,"name":label,"pre_bad":verdict})
   if verdict=="unsat":good.append((label,c,p))
  groups.append((m,good))
 initial_count=sum(len(g) for _,g in groups)
 iteration_ledger=[]
 for iteration in range(initial_count+1):
  removed_any=False
  for group_index,(m,group) in enumerate(groups):
   base=[u[1] for u in group]
   modulus_dir=tuple(1 if q==m else 0 for q in range(n))
   bases=[modulus_dir,*base]
   keep=[];reject=[]
   for label,vector,pred in group:
    proofs=[]
    good=True
    for branch,A_and_b in enumerate(branches):
     A,b=A_and_b
     updated=sp.Matrix([vector])*A
     v=tuple(int(q) for q in updated.row(0))
     included,coeff=integer_lattice_membership(bases,v)
     proofs.append({"branch":branch,"updated_linear_direction":v,
          "in_integer_modular_lattice":included,"integer_hnf_certificate":coeff})
     if not included:good=False
    if good:keep.append((label,vector,pred))
    else:reject.append({"candidate":label,"modulus":str(source["now"][m]),
         "branch_checks":proofs})
   if reject:
    removed_any=True
    groups[group_index]=(m,keep)
   iteration_ledger.append({"iteration":iteration,"modulus":str(source["now"][m]),
       "started":len(group),"removed":reject,"left":len(keep)})
  if not removed_any:break
 else:raise RuntimeError("SOURCE_LATTICE_CLOSURE_NONTERMINATING")
 # Complete algebraic subcertificate for *each* survivor relative to final bases.
 exact_certificate=[]
 for m,group in groups:
  base=[tuple(1 if x==m else 0 for x in range(n))]+[c for _,c,_ in group]
  for label,vec,p in group:
   for idx,(A,b) in enumerate(branches):
    vv=tuple(int(x) for x in (sp.Matrix([vec])*A).row(0))
    good,coeff=integer_lattice_membership(base,vv)
    if not good:raise RuntimeError("FINAL_INTEGER_MODULE_CERTIFICATE_MISMATCH")
    recomputed=tuple(sum(int(coeff[j])*int(base[j][i])
       for j in range(len(base))) for i in range(n))
    assert recomputed==vv
    exact_certificate.append({"candidate":label,"modulus_idx":m,
      "source_branch":idx,"updated_vector":vv,
      "modulus_plus_surviving_vectors":base,
      "exact_integer_coefficients":coeff,
      "replay_identity_verified":True})
 final_mod=[(label,c,p) for m,group in groups for label,c,p in group]
 final_formula=z3.And(*[p for label,c,p in final_mod],
   *[p for label,p,mod in positives])
 return {"source_constant_positive_moduli":[str(source["now"][i]) for i in statics],
   "source_mutable_variables":[str(source["now"][i]) for i in mutable],
   "initial_mod_candidates":2*(len(mutable)+2*len(mutable)*(len(mutable)-1)//2),
   "pre_filter_decisions":pre_cases,
   "initial_pre_satisfied_candidates":initial_count,
   "source_affine_exact_branch_count":len(branches),
   "lattice_rounds":iteration_ledger,
   "final_modular_candidates":[x[0] for x in final_mod],
   "positive_source_helpers":[x[0] for x in positives],
   "final_exact_source_induction_certificate":exact_certificate,
   "all_hnf_certificates_exact":all(x["replay_identity_verified"] for x in exact_certificate)}, final_formula

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source-root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args()
 start=time.perf_counter_ns()
 raw=(args.source_root/REL).read_bytes()
 if exact_git_blob(raw)!=BLOB or hashlib.sha256(raw).hexdigest()!=SRC_SHA:
  raise RuntimeError("ORIGINAL_SOURCE_SHA_BLOB_MISMATCH")
 s=sexprs(raw);source=extract_mixed_original(s)
 native=native_original_relations(s,source)
 native.update({"now":source["now"],"next":source["next"]})
 parity=check_parity(source,native)
 if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
  raise RuntimeError("ORIGINAL_SOURCE_PARITY_NOT_VALID")
 if query(native["pre"])[0]!="sat" or query(z3.Not(native["post"]))[0]!="sat":
  raise RuntimeError("ORIGINAL_SOURCE_VACUOUS")
 t=time.perf_counter_ns()
 result,inv=fixed_source_only_lattice(source,native)
 discovery_wall=now_ms(t)
 vc=source_bad_vcs(inv,source,native)
 native_three={k:query(pred,timeout=12000)[0] for k,pred in vc.items()}
 source_cert=source_proof(inv,native)
 postonly=source_proof(native["post"],native)
 positive_only=source_proof(z3.And(*[
   source["now"][i]>0 for i in range(len(source["now"]))]),native)
 first_check=check_original_candidate(args.source_root/REL,inv.sexpr(),
   expected_source_sha256=SRC_SHA) if native_three==EXPECTED else {}
 ext_first=first_check.get("cvc5_original_three_vc") or {}
 ext_first_pass=(first_check.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5")
 ext_second={}
 if native_three==EXPECTED and not ext_first_pass:
  for name,bad in vc.items():ext_second[name]=cvc5_on_vc(bad,timeout=15)
 ext_accepted=ext_first_pass or (set(ext_second)==set(EXPECTED) and
  all(x.get("result")=="unsat" and x.get("exit_code")==0 for x in ext_second.values()))
 proof_first=source_cert["accepted"] and native_three==EXPECTED
 out={"schema":"neumann.q3.real_lcm.source_exact_modular_lattice_HNF.v1",
   "scope":"POSTHOC_ALREADY_OPENED_REAL_ORIGINAL_CLASSICAL_ONLY",
   "original_path":REL,"source_sha256":SRC_SHA,"git_blob":BLOB,
   "original_parser_semantic_parity":parity,
   "source_only_grammar_mining":result,
   "source_only_lattice_wall_ms":discovery_wall,
   "generated_invariant_SMT_sexpr":inv.sexpr(),
   "original_source_no_Post_used_in_generation":True,
   "original_Z3_native_3VC":native_three,
   "original_Z3_induction_checker":source_cert["vcs"],
   "original_post_only_control":postonly["vcs"],
   "source_positive_only_control":positive_only["vcs"],
   "cvc5_original_existing_3s":ext_first,
   "cvc5_original_explicit_15s":ext_second,
   "independent_original_cvc5_all_3VC":ext_accepted,
   "full_real_original_3VC_dual_solver":proof_first and ext_accepted,
   "no_neural_training_and_no_neural_new_operator":True,
   "learned_only_advantage_over_matched_classical":False,
   "genuinely_new_blind_origin":False,"GPU_calls":0,"paid_API_calls":0,
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "total_wall_ms":now_ms(start)}
 args.out.parent.mkdir(exist_ok=True,parents=True)
 args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
 print("EXACT_LATTICE",result["final_modular_candidates"])
 print("ALGEBRA_CERTIFICATES",len(result["final_exact_source_induction_certificate"]))
 print("ORIGINAL_Z3",native_three)
 print("CVC5_3S",ext_first,"CVC5_15S",ext_second)
 print("FULL_REAL_ORIGINAL_DUAL_3VC_PASS",out["full_real_original_3VC_dual_solver"])
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
