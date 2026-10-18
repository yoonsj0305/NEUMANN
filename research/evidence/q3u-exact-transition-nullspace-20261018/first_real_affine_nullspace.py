"""Q3U - exact linear algebra source-transition relation invention (classical).

No learned neural operator is involved. SymPy computes actual primitive integer
left-nullspace coefficients from unchanged ORIGINAL SyGuS trans source
equations; Z3 checks the actual unchanged ORIGINAL 3 VCs via two source
parsing implementations. The entire first frozen 8 FiB + 2 other actual
source cases (not blind) is recorded, including unsupported/failed outcomes.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import sympy as sp
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3t-mixed-original-20261018"))
sys.path.insert(0,str(HERE.parent/"q3t2-native-original-20261018"))

from mixed_sygus_original import (
    extract_mixed_original, sexprs, blobhash, check_formula,
    check_cover
)
from native_smtlib_source_parity import (
    native_original_relations, independent_native_bad_query
)

REV="6ac90265b11431c9477dfbd33e3e3380234c0499"
LICENSE_GIT_BLOB="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"
FIB="benchmarks/LIA/2017.ASE_FiB"
CONTROLS=(
    "benchmarks/LIA/2016.SyGuS-Comp/array.sl",
    "benchmarks/LIA/others/inria-00615623_4.sl"
)
MAX_VARS=8
MAX_CANDIDATES=12
PARITY_TIMEOUT_MS=2500
PROVEN="ORIGINAL_FULL_3VC_CERTIFIED"

class UnsupportedTransition(Exception):pass

def flat_and(node):
    if z3.is_and(node):
        for x in node.children():yield from flat_and(x)
    else:
        yield node

def affine(expr,variables):
    """Exact affine integer decomposition; reject nonlinear/unknown safely."""
    expr=z3.simplify(expr)
    n=len(variables)
    if z3.is_int_value(expr):
        return sp.zeros(n,1),sp.Integer(expr.as_long())
    for i,v in enumerate(variables):
        if z3.eq(expr,v):
            basis=sp.zeros(n,1);basis[i]=1
            return basis,sp.Integer(0)
    if not z3.is_app(expr):
        raise UnsupportedTransition("AFFINE_NOT_AN_APP")
    kind=expr.decl().kind()
    args=list(expr.children())
    if kind in (z3.Z3_OP_ADD,z3.Z3_OP_SUB):
        if not args:raise UnsupportedTransition("EMPTY_ARITHMETIC")
        acc,b=affine(args[0],variables)
        for term in args[1:]:
            ac,bc=affine(term,variables)
            if kind==z3.Z3_OP_ADD:acc,b=acc+ac,b+bc
            else:acc,b=acc-ac,b-bc
        return acc,b
    if kind==z3.Z3_OP_UMINUS and len(args)==1:
        c,b=affine(args[0],variables)
        return -c,-b
    if kind==z3.Z3_OP_MUL:
        literals=sp.Integer(1)
        variable_factor=[]
        for v in args:
            if z3.is_int_value(v):
                literals*=int(v.as_long())
            else:
                variable_factor.append(v)
        if len(variable_factor)>1:
            raise UnsupportedTransition("SOURCE_NONLINEAR_MULTIPLICATION")
        if len(variable_factor)==0:return sp.zeros(n,1),literals
        c,b=affine(variable_factor[0],variables)
        return literals*c,literals*b
    raise UnsupportedTransition("ORIGINAL_NONAFFINE_EXPRESSION_"+str(kind))

def exact_update_matrix(original):
    now,nxt=original["now"],original["next"]
    if len(now)<2 or len(now)>MAX_VARS or original["num_bool"]!=0:
        raise UnsupportedTransition("ONLY_2_TO_8_INT_STATES_IN_FIRST_STUDY")
    updates={}
    for part in flat_and(original["trans"]):
        if not z3.is_eq(part):
            continue # Original guard retained for the Z3 proof obligations.
        a,b=part.children()
        for i,t in enumerate(nxt):
            if z3.eq(a,t) and not z3.eq(b,t):
                rhs=b
            elif z3.eq(b,t) and not z3.eq(a,t):
                rhs=a
            else:
                continue
            if i in updates:
                raise UnsupportedTransition("AMBIGUOUS_DOUBLE_NEXT_STATE_EQUATION")
            if any(v in z3.z3util.get_vars(rhs) for v in nxt):
                raise UnsupportedTransition("NEXT_STATE_VARIABLE_ON_RHS")
            updates[i]=affine(rhs,now)
    if len(updates)!=len(nxt):
        raise UnsupportedTransition("ORIGINAL_TRANSITION_NOT_FULLY_EXPLICIT_AFFINE")
    # A[i,j] is coefficient of current x_j in original next x'_i.
    A=sp.Matrix([[updates[i][0][j] for j in range(len(now))]
                 for i in range(len(now))])
    b=sp.Matrix([updates[i][1] for i in range(len(now))])
    return A,b

def primitive_int_vector(vec):
    vals=[sp.Rational(x) for x in vec]
    lcm=sp.ilcm(*[int(x.q) for x in vals])
    scaled=[int(x*lcm) for x in vals]
    nz=[abs(x) for x in scaled if x]
    if not nz:raise ValueError("ZERO_NULLSPACE_VECTOR")
    gcd=math.gcd(*nz)
    scaled=[x//gcd for x in scaled]
    if next(x for x in scaled if x)<0:scaled=[-x for x in scaled]
    return tuple(scaled)

def linear_term(coeff,now):
    return z3.Sum(*[z3.IntVal(int(c))*v
                    for c,v in zip(coeff,now) if c!=0])

def uniquely_pre_forced_value(pre,term):
    smt=z3.Solver();smt.set(timeout=1200);smt.add(pre)
    if smt.check()!=z3.sat:return None
    value=smt.model().eval(term,model_completion=True)
    if not z3.is_int_value(value):return None
    proposed=int(value.as_long())
    smt.push();smt.add(term!=proposed)
    unique=smt.check()==z3.unsat
    smt.pop()
    return proposed if unique else None

def relation_candidates(A,b,original):
    n=A.rows
    found=[];seen=set()
    # Reset: c^T A == 0, c^T b == k; relation true in EVERY successor.
    # Conserved: c^T (A-I)==0, c^T b ==0; source Pre must fix k.
    for name,left in (("RESET",A.T),("CONSERVATION",(A-sp.eye(n)).T)):
        for vector in left.nullspace():
            coeff=primitive_int_vector(vector)
            if name=="RESET":
                k=sum(int(coeff[i])*int(b[i]) for i in range(n))
            else:
                shift=sum(int(coeff[i])*int(b[i]) for i in range(n))
                if shift!=0:continue
                k=uniquely_pre_forced_value(
                    original["pre"],linear_term(coeff,original["now"])
                )
                if k is None:continue
            key=(coeff,int(k))
            if key in seen:continue
            seen.add(key)
            c={"coefficients":coeff,"constant":int(k),"mechanism":name,
               "equation_sha256":hashlib.sha256(
                   json.dumps(key).encode()).hexdigest()}
            found.append(c)
            if len(found)>=MAX_CANDIDATES:break
        if len(found)>=MAX_CANDIDATES:break
    return found

def actual_relation(expr,now):
    return linear_term(expr["coefficients"],now)==int(expr["constant"])

def prove_candidate_relation(original,native,relation):
    before=check_formula(z3.And(native["pre"],z3.Not(relation)))
    nxt=z3.substitute(relation,*list(zip(native["now"],native["next"])))
    induction=check_formula(z3.And(
        native["trans"],relation,z3.Not(nxt)
    ))
    return {
       "original_pre_implies_relation":before,
       "original_inductive_relation":induction,
       "source_certified":before=="unsat" and induction=="unsat"
    }

def check_parity(a,b):
    return {key:check_formula(z3.Xor(a[key],b[key]),PARITY_TIMEOUT_MS)
            for key in ("pre","trans","post")}

def synthetic_controls():
    x,y=z3.Ints("q3u_ctrl_x q3u_ctrl_y")
    xp,yp=z3.Ints("q3u_ctrl_xp q3u_ctrl_yp")
    base={"now":[x,y],"next":[xp,yp],
          "num_bool":0,"num_int":2,
          "pre":z3.And(x==1,y==1),
          "trans":z3.And(xp==x+y,yp==x+y),
          "post":y>=1}
    A,b=exact_update_matrix(base)
    candidates=relation_candidates(A,b,base)
    certified=[]
    for c in candidates:
        pred=actual_relation(c,base["now"])
        if prove_candidate_relation(base,base,pred)["source_certified"]:
            certified.append((c,pred))
    chosen=[(c,pred) for c,pred in certified if c["coefficients"]==(1,-1)
            and c["constant"]==0]
    if len(chosen)!=1:
        raise RuntimeError("SYNTHETIC_1_MINUS_1_AUTOMATIC_INVARIANT_NOT_FOUND")
    R=chosen[0][1]
    full=check_cover(z3.And(base["post"],R),base)
    post=check_cover(base["post"],base)
    false=check_cover(x-y==1,base)
    mutated={**base,"trans":z3.And(xp==x+y,yp==y)}
    mutated_proof=check_cover(z3.And(base["post"],R),mutated)
    independent={**base,"trans":z3.And(xp==x+1,yp==y+2)}
    A2,b2=exact_update_matrix(independent)
    # No nonzero exact constant invariant for arbitrary state under +[1,2].
    # The vector [2,-1] IS actually conserved, but source Pre sets it to 1;
    # it must NOT be admitted as a false reset. Conserved candidates are
    # legitimate if exactly proven; all are still checked by original Z3.
    independent_candidates=relation_candidates(A2,b2,independent)
    accepted=[
       c for c in independent_candidates
       if prove_candidate_relation(independent,independent,
                     actual_relation(c,independent["now"]))["source_certified"]
    ]
    ok=(
        full["status"]==PROVEN
        and post["status"]!=PROVEN
        and false["status"]!=PROVEN
        and mutated_proof["status"]!=PROVEN
        and len(chosen)==1
    )
    return {"pass":ok,
       "reset_relation_coefficient_computed":[1,-1],
       "control_post_alone_3vc":post["status"],
       "control_post_plus_derived_relation_3vc":full["status"],
       "control_invalid_relation_3vc":false["status"],
       "control_mutated_original_step_3vc":mutated_proof["status"],
       "control_conserved_candidates_each_original_checked":len(accepted)}

def sample(root):
    fib_dir=root/FIB
    chosen=sorted(fib_dir.glob("*.sl"))[:8]
    if len(chosen)!=8:raise RuntimeError("NOT_EXACT_EIGHT_PREDECLARED_REAL_FIB")
    return chosen+[root/x for x in CONTROLS]

def evaluate_one(path,root):
    data=path.read_bytes()
    original_path=path.relative_to(root).as_posix()
    record={
       "original_path":original_path,
       "git_blob":blobhash(data),
       "status":"NOT_RUN",
       "source_family":"/".join(path.relative_to(root).parts[:3]),
       "all_source_certified_relations":[],
       "original_full_relation_safety":False
    }
    began=time.perf_counter_ns()
    try:
        original=extract_mixed_original(sexprs(data))
        native=native_original_relations(sexprs(data),original)
        native.update({
            "now":original["now"],
            "next":original["next"]
        })
        par=check_parity(original,native)
        record["independent_source_parsing_parity"]=par
        if any(v!="unsat" for v in par.values()):
            record["status"]="ABSTAIN_SOURCE_PARSER_SEMANTICS_NOT_PROVED"
            return record
        record["original_int_state_count"]=original["num_int"]
        record["original_bool_state_count"]=original["num_bool"]
        pre=check_formula(native["pre"])
        notpost=check_formula(z3.Not(native["post"]))
        record["original_pre_sat"]=pre
        record["original_not_post_sat"]=notpost
        if pre!="sat" or notpost!="sat":
            record["status"]="ABSTAIN_EMPTY_OR_UNKNOWN_ORIGINAL_GOAL"
            return record
        baseline=check_cover(native["post"],native)
        record["source_post_alone_original_3vc"]=baseline["status"]
        strong=independent_native_bad_query(native,native["now"],native["next"])
        record["source_only_direct_spacer_bad_exit"]=strong["status"]
        record["source_only_spacer_wall_ms"]=strong["native_solver_wall_ms"]
        A,b=exact_update_matrix(original)
        record["exact_original_affine_state_variables"]=A.rows
        # Only SHA identities of source-derived transition matrices leave CI.
        record["exact_affine_transition_sha256"]=hashlib.sha256(
           (str(A)+str(b)).encode()).hexdigest()
        candidates=relation_candidates(A,b,original)
        cert=[]
        for item in candidates:
            relation=actual_relation(item,native["now"])
            proof=prove_candidate_relation(original,native,relation)
            rec={**item,**proof}
            if proof["source_certified"]:
                cert.append((item,relation))
            record["all_source_certified_relations"].append(rec)
        record["original_relation_certified_count"]=len(cert)
        # Deduce I from source-given post and independently proved equations.
        # Avoid declaring any benefit when Post alone is already inductive.
        target=z3.And(native["post"],*[r for c,r in cert])
        final=check_cover(target,native)
        record["full_original_3vc_with_derived_relations"]=final["status"]
        record["full_original_3vc_statuses"]={
            k:final.get(k) for k in ("initial","consecution","post")}
        record["original_full_relation_safety"]=final["status"]==PROVEN
        record["source_relation_proof_not_post_alone"]=(
            record["original_full_relation_safety"]
            and baseline["status"]!=PROVEN and bool(cert)
        )
        record["strong_specialist_also_solved"]=strong["status"]=="unsat"
        record["status"]="ORIGINAL_AFFINE_RELATION_FULL_VC_CHECK_COMPLETE"
        return record
    except Exception as e:
        record["status"]="ABSTAIN_ORIGINAL_SOURCE_OR_AFFINE_NOT_SUPPORTED"
        record["reason_type"]=type(e).__name__
        record["reason_category"]=str(e).split(":")[0][:110]
        return record
    finally:
        record["total_case_wall_ms"]=round((time.perf_counter_ns()-began)/1e6,3)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if blobhash((a.root/"LICENSE.md").read_bytes())!=LICENSE_GIT_BLOB:
        raise RuntimeError("UPSTREAM_LICENSE_GIT_BLOB_CHANGED")
    controls=synthetic_controls()
    if not controls["pass"]:
        raise RuntimeError("SYNTHETIC_ADVERSARIAL_NULLSPACE_PROOF_FAILED")
    result=[evaluate_one(path,a.root) for path in sample(a.root)]
    if len(result)!=10 or len({x["git_blob"] for x in result})!=10:
        raise RuntimeError("FIRST_10_ACTUAL_SOURCE_COHORT_IDENTITY_CHANGED")
    totals={
      "actual_original_source_count":len(result),
      "actual_origins":len({r["source_family"] for r in result}),
      "source_affine_extracted":sum(r["status"]=="ORIGINAL_AFFINE_RELATION_FULL_VC_CHECK_COMPLETE" for r in result),
      "exact_source_derived_relations_original_inductive":sum(r.get("original_relation_certified_count",0) for r in result),
      "original_safety_fully_proven_by_nullspace_plus_post":sum(r["original_full_relation_safety"] for r in result),
      "proved_beyond_source_post_alone":sum(r.get("source_relation_proof_not_post_alone",False) for r in result),
      "direct_classical_spacer_success":sum(r.get("source_only_direct_spacer_bad_exit")=="unsat" for r in result)
    }
    report={
      "study":"Q3U_SOURCE_TRANSITION_EXACT_COEFFICIENT_NULLSPACE_REAL_ORIGINAL_SAFETY",
      "status":"FIRST_FROZEN_ORIGINAL_TRANSITION_NULLSPACE_AND_THREE_VC_STUDY_COMPLETE",
      "upstream_revision":REV,
      "math_method":"EXACT_CLASSICAL_LEFT_NULLSPACE_WITH_ORIGINAL_INDUCTION",
      "coefficients_hardcoded_per_target":False,
      "new_neural_model_training_or_inference":0,
      "global_q1_q7":"OPEN",
      "q3f_two_original_escrow_bodies_opened":False,
      "externally_copied_source_or_smt_formula_text":False,
      "first_controls":controls,
      "first_actual_source_summary":totals,
      "all_first_original_source_records":result
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3U_SOURCE_DERIVED_MATH_CONTROLS",controls)
    print("Q3U_ACTUAL_REAL_SOURCE_RESULTS",totals)
    print("Q3U_FROZEN_FULL_PROGRAMS",[(x["original_path"],x["status"],x.get("original_relation_certified_count"),x.get("source_relation_proof_not_post_alone")) for x in result])
    print("Q3U_ALL_Q1_Q7",report["global_q1_q7"])

if __name__=="__main__":
    main()
