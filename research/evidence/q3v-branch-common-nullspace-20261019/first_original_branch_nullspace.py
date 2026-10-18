"""Q3V: Source-conditioned CLASSICAL common affine nullspace across every branch.

Actual original SyGuS sources are unchanged. Exact integer coefficients are
computed from the intersection of linear constraints across ALL transition
branches. Verifier checks each candidate and full source invariant with Z3.
No learned neural model nor claim of novel neural math operator invention.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,sys,time
from pathlib import Path
import sympy as sp
import z3
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3u-exact-transition-nullspace-20261018"))
from first_real_affine_nullspace import (
    affine,primitive_int_vector,linear_term,uniquely_pre_forced_value,
    actual_relation,prove_candidate_relation,check_parity,sample,
    LICENSE_GIT_BLOB,REV,PROVEN
)
from first_real_affine_nullspace import blobhash,sexprs,check_formula,check_cover
from first_real_affine_nullspace import extract_mixed_original,native_original_relations,independent_native_bad_query

MAX_BRANCHES=32
MAX_BRANCH_ATOMS=200
MAX_RELATIONS=16

class BranchSourceUnsupported(Exception):pass

def dnf(expr):
    """Structure-preserving bounded DNF. NEVER omit a source branch."""
    if z3.is_true(expr):return [[]]
    if z3.is_false(expr):return []
    if z3.is_or(expr):
        out=[]
        for term in expr.children():
            out.extend(dnf(term))
            if len(out)>MAX_BRANCHES:raise BranchSourceUnsupported("SOURCE_BRANCH_CAP")
        return out
    if z3.is_and(expr):
        result=[[]]
        for term in expr.children():
            sub=dnf(term)
            if len(result)*len(sub)>MAX_BRANCHES:
                raise BranchSourceUnsupported("DISTRIBUTED_SOURCE_BRANCH_CAP")
            result=[p+q for p in result for q in sub]
            if any(len(branch)>MAX_BRANCH_ATOMS for branch in result):
                raise BranchSourceUnsupported("SOURCE_BRANCH_LITERAL_CAP")
        return result
    return [[expr]]

def all_exact_branch_updates(source):
    state,nextstate=source["now"],source["next"]
    if len(state)<2 or len(state)>8 or source["num_bool"]:
        raise BranchSourceUnsupported("FIRST_BRANCH_CLASSICAL_ONLY_2_8_INT_STATE")
    rawbranches=dnf(source["trans"])
    if not rawbranches:raise BranchSourceUnsupported("NO_TRANSITION_BRANCHES")
    out=[]
    for branch in rawbranches:
        updates={}
        for literal in branch:
            if not z3.is_eq(literal):
                continue
            lhs,rhs=literal.children()
            for idx,target in enumerate(nextstate):
                if z3.eq(lhs,target) and not z3.eq(rhs,target):
                    expression=rhs
                elif z3.eq(rhs,target) and not z3.eq(lhs,target):
                    expression=lhs
                else:continue
                if idx in updates:
                    raise BranchSourceUnsupported("REPEATED_UPDATE_OF_SAME_NEXT_STATE")
                if any(z3.eq(v,n) for v in z3.z3util.get_vars(expression)
                       for n in nextstate):
                    raise BranchSourceUnsupported("NEXT_STATE_DEPENDENCY_IN_RHS")
                updates[idx]=affine(expression,state)
        if len(updates)!=len(state):
            raise BranchSourceUnsupported("NOT_ALL_NEXT_STATES_EXPLICITLY_UPDATED_PER_BRANCH")
        A=sp.Matrix([[updates[i][0][j] for j in range(len(state))]
                     for i in range(len(state))])
        b=sp.Matrix([updates[i][1] for i in range(len(state))])
        out.append((A,b))
    return out

def common_kernels(branches,original):
    n=len(original["now"])
    eye=sp.eye(n)
    conservation=sp.Matrix.vstack(*(
        matrix for A,b in branches for matrix in
        (A.T-eye,b.T)
    ))
    reset=sp.Matrix.vstack(*(
        [A.T for A,b in branches]+
        [(b-branches[0][1]).T for A,b in branches[1:]]
    ))
    candidates=[];seen=set()
    for name,linear in (("CONSERVATION_ALL_BRANCHES",conservation),
                        ("RESET_ALL_BRANCHES",reset)):
        for vector in linear.nullspace():
            coeff=primitive_int_vector(vector)
            term=linear_term(coeff,original["now"])
            if name=="CONSERVATION_ALL_BRANCHES":
                k=uniquely_pre_forced_value(original["pre"],term)
                if k is None:continue
            else:
                k=sum(int(coeff[i])*int(branches[0][1][i])
                      for i in range(n))
                if check_formula(z3.And(original["pre"],term!=k))!="unsat":
                    continue
            identity=(coeff,int(k))
            if identity in seen:continue
            seen.add(identity)
            candidates.append({
                "coefficients":coeff,
                "constant":int(k),
                "mechanism":name,
                "equation_sha256":hashlib.sha256(
                    json.dumps(identity).encode()).hexdigest()
            })
            if len(candidates)>=MAX_RELATIONS:
                return candidates
    return candidates

def synthetic_branch_controls():
    i,n,a,b=z3.Ints("q3v_i q3v_n q3v_a q3v_b")
    ip,np,ap,bp=z3.Ints("q3v_ip q3v_np q3v_ap q3v_bp")
    pre=z3.And(i==0,n==1,a==0,b==0)
    branch1=z3.And(i<n,ip==i+1,np==n,ap==a+1,bp==b+2)
    branch2=z3.And(i<n,ip==i+1,np==n,ap==a+2,bp==b+1)
    stutter=z3.And(i>=n,ip==i,np==n,ap==a,bp==b)
    post=z3.Implies(i>=n,a+b==3*n)
    original={"now":[i,n,a,b],"next":[ip,np,ap,bp],
              "num_int":4,"num_bool":0,"pre":pre,
              "trans":z3.Or(branch1,branch2,stutter),
              "post":post}
    branches=all_exact_branch_updates(original)
    candidates=common_kernels(branches,original)
    cert=[]
    for item in candidates:
        predicate=actual_relation(item,original["now"])
        status=prove_candidate_relation(original,original,predicate)
        if status["source_certified"]:
            cert.append((item,predicate))
    allpreds=z3.And(post,*[p for c,p in cert])
    full=check_cover(allpreds,original)
    postonly=check_cover(post,original)
    bad=check_cover(a+b-3*i==1,original)
    corrupted={**original,"trans":z3.Or(
        branch1,z3.And(i<n,ip==i+1,np==n,ap==a+2,bp==b+3),stutter
    )}
    stale=check_cover(allpreds,corrupted)
    expected=sum(any(
        x in c["coefficients"] for c,p in cert
    ) for x in (1,3)) # informational, not success assertion
    found_relation=any(
        tuple(x["coefficients"])==(3,0,-1,-1) and x["constant"]==0
        for x,p in cert
    )
    valid=found_relation and len(branches)==3 and (
        full["status"]==PROVEN and postonly["status"]!=PROVEN
        and bad["status"]!=PROVEN and stale["status"]!=PROVEN)
    return {
        "pass":valid,"original_source_branch_count":len(branches),
        "derived_expected_inductive_coefficients":[3,0,-1,-1],
        "expected_candidate_certified":found_relation,
        "original_post_alone":postonly["status"],
        "original_post_plus_common_branch_relations":full["status"],
        "invalid_relation_full_vc":bad["status"],
        "corrupt_one_branch_invalidates_stale_original_certificate":stale["status"],
        "source_original_certified_relation_count":len(cert)
    }

def evaluate(path,root):
    raw=path.read_bytes()
    rec={"source_path":path.relative_to(root).as_posix(),
         "source_git_blob":blobhash(raw),
         "status":"UNDETERMINED",
         "mathematical_relations":[]}
    start=time.perf_counter_ns()
    try:
        src=extract_mixed_original(sexprs(raw))
        native=native_original_relations(sexprs(raw),src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        rec["actual_original_pre_trans_post_native_parser_parity"]=parity
        if any(q!="unsat" for q in parity.values()):
            rec["status"]="ABSTAIN_SOURCE_SEMANTIC_PARITY_NOT_PROVEN"
            return rec
        rec["original_pre_sat"]=check_formula(native["pre"])
        rec["original_not_post_sat"]=check_formula(z3.Not(native["post"]))
        if rec["original_pre_sat"]!="sat" or rec["original_not_post_sat"]!="sat":
            rec["status"]="ABSTAIN_ORIGINAL_GOAL_VACUOUS_OR_UNKNOWN"
            return rec
        direct=independent_native_bad_query(native,src["now"],src["next"])
        rec["strong_source_only_SPACER_bad_exit"]=direct["status"]
        rec["strong_spacer_ms"]=direct["native_solver_wall_ms"]
        rec["source_post_only_3vc"]=check_cover(native["post"],native)["status"]
        branches=all_exact_branch_updates(src)
        rec["original_transition_dnf_branch_count"]=len(branches)
        rec["transition_all_branch_A_b_sha256"]=hashlib.sha256(
            "|".join(str(A)+";"+str(b) for A,b in branches).encode()
        ).hexdigest()
        proposed=common_kernels(branches,src)
        rec["proposed_common_exact_nullspace_coefficients"]=len(proposed)
        cert=[]
        for relation in proposed:
            expression=actual_relation(relation,src["now"])
            status=prove_candidate_relation(src,native,expression)
            item={**relation,**status}
            rec["mathematical_relations"].append(item)
            if status["source_certified"]:
                cert.append(expression)
        rec["original_two_vc_certified_relations"]=len(cert)
        full=check_cover(z3.And(native["post"],*cert),native)
        rec["full_source_original_3vc_status"]=full["status"]
        rec["full_source_original_3vc_checks"]={
            k:full.get(k) for k in ("initial","consecution","post")}
        rec["full_original_safe_by_branch_nullspace"]=full["status"]==PROVEN
        rec["original_new_relation_essential_beyond_post"] = (
            bool(cert) and rec["full_original_safe_by_branch_nullspace"]
            and rec["source_post_only_3vc"]!=PROVEN)
        rec["status"]="COMPLETE_ORIGINAL_BRANCH_NULLSPACE_CHECK"
    except Exception as e:
        rec["status"]="ABSTAIN_ORIGINAL_BRANCH_NOT_SUPPORTED"
        rec["reason_type"]=type(e).__name__
        rec["reason_category"]=str(e).split(":")[0][:120]
    finally:
        rec["case_full_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    return rec

def run(root):
    if blobhash((root/"LICENSE.md").read_bytes())!=LICENSE_GIT_BLOB:
        raise ValueError("UPSTREAM_LICENSE_CHANGED")
    controls=synthetic_branch_controls()
    if not controls["pass"]:
        raise ValueError("FIRST_BRANCHING_ORIGINAL_NEGATIVE_CONTROL_FAIL")
    cases=[evaluate(p,root) for p in sample(root)]
    if len(cases)!=10 or len({r["source_git_blob"] for r in cases})!=10:
        raise ValueError("Q3V_EXACT_TEN_ORIGINAL_IDENTITY_CHANGED")
    summar={
       "original_files":len(cases),
       "original_family_groups":len({"/".join(r["source_path"].split("/")[:3]) for r in cases}),
       "source_transition_exact_branch_affine_extracted":sum(
          r["status"]=="COMPLETE_ORIGINAL_BRANCH_NULLSPACE_CHECK" for r in cases),
       "source_original_two_vc_proven_candidate_relations":sum(
          r.get("original_two_vc_certified_relations",0) for r in cases),
       "full_original_safety_proven_by_post_and_common_branch_nullspace":sum(
          r.get("full_original_safe_by_branch_nullspace",False) for r in cases),
       "new_nontrivial_full_original_proofs_beyond_source_post":sum(
          r.get("original_new_relation_essential_beyond_post",False) for r in cases),
       "source_only_specialist_proved_originals":sum(
          r.get("strong_source_only_SPACER_bad_exit")=="unsat" for r in cases)
    }
    return {
       "study":"Q3V_FIRST_BRANCH_COMMON_SOURCE_TRANSITION_EXACT_NULLSPACE",
       "status":"FIRST_FROZEN_ORIGINAL_BRANCH_NULLSPACE_STUDY_RECORDED",
       "source_repo_git_revision":REV,
       "deterministic_classical_source_transition_coefficients_only":True,
       "neural_training_calls":0,
       "new_mathematical_primitive_learned":False,
       "q3f_sealed_chc_original_bodies_opened":False,
       "source_and_invariant_text_not_redistributed":True,
       "first_synthetic_branch_adversarial_controls":controls,
       "first_fixed_authentic_original_summary":summar,
       "first_all_original_records":cases,
       "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    r=run(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3V_ADVERSARIAL_ALL_BRANCH_CONTROLS",r["first_synthetic_branch_adversarial_controls"])
    print("Q3V_FIRST_REAL_ORIGINAL_RESULT",r["first_fixed_authentic_original_summary"])
    print("Q3V_CASES",[(x["source_path"],x["status"],x.get("original_transition_dnf_branch_count"),x.get("original_new_relation_essential_beyond_post"),x.get("reason_category")) for x in r["first_all_original_records"]])
    print("Q3V_GLOBAL_Q1_Q7",r["global_q1_q7"])
