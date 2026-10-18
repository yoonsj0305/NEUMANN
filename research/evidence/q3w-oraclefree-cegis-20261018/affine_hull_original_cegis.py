"""Q3W oracle-free exact affine-hull CEGIS on untouched original programs.

No gold solution, teacher, pretrained classifier, solver-produced invariant
or oracle input. Uses Z3 only for falsifying current affine-hull hypotheses.
The mathematical technique is classical; no new neural invention claim.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from collections import Counter
from pathlib import Path
import sympy as sp
import z3
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3t-mixed-original-20261018"))
sys.path.insert(0,str(HERE.parent/"q3t2-native-original-20261018"))
from mixed_sygus_original import extract_mixed_original,sexprs,blobhash,check_cover,check_formula
from native_smtlib_source_parity import native_original_relations,independent_native_bad_query

UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
LICENSE_BLOB="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"
Q3S_FIRST_SHA256="f4e290a38a44aa7ba7cd03979ea74149df5f0d4241391d5a2302ada3876b6192"
MAX_STATE=16
MAX_COEFF=10**7
TIMEOUT_MS=2500
PROVEN="ORIGINAL_FULL_3VC_CERTIFIED"
FIB="benchmarks/LIA/2017.ASE_FiB"
OPENED_CONTROLS=[
 "benchmarks/LIA/2016.SyGuS-Comp/array.sl",
 "benchmarks/LIA/others/inria-00615623_4.sl",
 "benchmarks/LIA/others/pldi18_seahorn_Fig3.sl",
 "benchmarks/LIA/others/pldi18_seahorn_Fig4.sl",
]
class Abstain(Exception): pass

def primitive(vec):
    v=[sp.Rational(z) for z in vec]
    l=math.lcm(*[int(z.q) for z in v])
    q=[int(z*l) for z in v]
    g=math.gcd(*[abs(z) for z in q])
    if not g: raise AssertionError("ZERO_NULL_VECTOR")
    q=[z//g for z in q]
    if next(z for z in q if z)<0:q=[-z for z in q]
    if max(abs(z) for z in q)>MAX_COEFF:
        raise Abstain("EXACT_CERTIFICATE_COEFFICIENT_CAP")
    return q

def enc(variables):
    return [z3.If(x, z3.IntVal(1),z3.IntVal(0)) if z3.is_bool(x)
            else x for x in variables]

def formula(rows,vars):
    d=len(vars)+1
    K=sp.Matrix.hstack(*rows)
    if K.rows!=d: raise AssertionError("AUGMENTED_DIMENSION_MISMATCH")
    annihilators=K.T.nullspace()
    R=[primitive(v) for v in annihilators]
    encoded=enc(vars)+[z3.IntVal(1)]
    inv=z3.And(*[
       z3.Sum(*[z3.IntVal(int(a))*x for a,x in zip(coeff,encoded)])==0
       for coeff in R])
    if any([len(a)!=d for a in R]):raise AssertionError("BAD_ROW")
    # Every witness is inside the exact certified affine row span.
    for a in R:
        assert (sp.Matrix([a])*K)==sp.zeros(1,K.cols)
    return inv,R,K.rank()

def model_column(s,vars):
    if s.check()!=z3.sat:raise AssertionError("EXPECTED_SAT_MODEL_NOT_AVAILABLE")
    m=s.model()
    raw=[m.eval(v,model_completion=True) for v in vars]
    vals=[]
    for x in raw:
        if z3.is_true(x): vals.append(1)
        elif z3.is_false(x): vals.append(0)
        elif z3.is_int_value(x): vals.append(int(x.as_long()))
        else: raise Abstain("UNKNOWN_MODEL_VALUE_SORT")
    return sp.Matrix(vals+[1])

def solver(*conditions):
    s=z3.Solver();s.set(timeout=TIMEOUT_MS)
    s.add(*conditions);return s

def verdict(s):
    t0=time.perf_counter_ns()
    try:
        result=str(s.check())
    except Exception:
        result="error"
    return result,(time.perf_counter_ns()-t0)/1e6

def construct(pre,trans,now,nxt):
    if len(now)!=len(nxt) or not (1<=len(now)<=MAX_STATE):
        raise Abstain("STATE_ARITY_CAP_OR_MISMATCH")
    if any(a.sort()!=b.sort() for a,b in zip(now,nxt)):
        raise Abstain("NOW_NEXT_TYPE_MISMATCH")
    start=time.perf_counter_ns()
    init=solver(pre);status,initial_ms=verdict(init)
    if status!="sat":raise Abstain("PRE_NOT_PROVEN_SAT_"+status)
    rows=[model_column(init,now)]
    calls=1
    checks_ms=initial_ms
    d=len(now)+1
    events=[]
    final=None
    for step in range(min(d+2,40)):
        I,R,rank=formula(rows,now)
        I_next,_,rank_n=formula(rows,nxt)
        assert rank_n==rank
        first=solver(pre,z3.Not(I))
        f,ms=verdict(first);calls+=1;checks_ms+=ms
        if f=="sat":
            state=model_column(first,now)
            oldrank=rank
            if sp.Matrix.hstack(*rows,state).rank()!=oldrank+1:
                raise AssertionError("INIT_COUNTEREXAMPLE_NOT_RANK_INCREASING")
            rows.append(state)
            events.append("INIT_WITNESS")
            continue
        if f!="unsat":raise Abstain("UNKNOWN_INIT_VC_"+f)
        transition=solver(I,trans,z3.Not(I_next))
        g,ms=verdict(transition);calls+=1;checks_ms+=ms
        if g=="sat":
            state=model_column(transition,nxt)
            if sp.Matrix.hstack(*rows,state).rank()!=rank+1:
                raise AssertionError("TRANS_COUNTEREXAMPLE_NOT_RANK_INCREASING")
            rows.append(state)
            events.append("STEP_WITNESS")
            continue
        if g!="unsat":raise Abstain("UNKNOWN_TRANS_VC_"+g)
        final=(I,R,rank)
        break
    if final is None:raise Abstain("MISSING_CEGIS_TERMINATION_PROOF")
    I,R,rank=final
    # Explicit final exact *original* inductive correctness checks, not samples.
    initial=check_formula(z3.And(pre,z3.Not(I)),TIMEOUT_MS)
    now_to_next=z3.substitute(I,*list(zip(now,nxt)))
    consecutive=check_formula(z3.And(I,trans,z3.Not(now_to_next)),TIMEOUT_MS)
    if (initial,consecutive)!=("unsat","unsat"):
        raise AssertionError("CEGIS_CERTIFICATE_INVALID")
    ms=(time.perf_counter_ns()-start)/1e6
    return I,{"status":"ORIGINAL_AFFINE_HULL_PROVEN",
              "state_var_count":len(now),"witnesses":len(rows),
              "affine_rank":rank,"independent_equalities":len(R),
              "relation_coefficients":R,
              "init_counterexamples":events.count("INIT_WITNESS"),
              "transition_counterexamples":events.count("STEP_WITNESS"),
              "exact_original_induction":["unsat","unsat"],
              "original_smt_calls_for_discovery":calls+2,
              "original_smt_solver_wall_ms":round(checks_ms,3),
              "total_discovery_and_proof_wall_ms":round(ms,3)}

def test_case(name,pre,trans,post,now,nxt):
    I,study=construct(pre,trans,now,nxt)
    source={"pre":pre,"trans":trans,"post":post,"now":now,"next":nxt}
    final=check_cover(z3.And(I,post),source)
    alone=check_cover(post,source)
    study["name"]=name
    study["source_goal_with_affine_hull"]=final["status"]
    study["original_post_alone"]=alone["status"]
    study["additional_hidden_structure_necessary"]=(
        final["status"]==PROVEN and alone["status"]!=PROVEN
        and study["independent_equalities"]>0)
    return I,study

def synthetic_strict_controls():
    x,y=z3.Ints("q3w_x q3w_y")
    xp,yp=z3.Ints("q3w_xp q3w_yp")
    a_pre=z3.And(x==3,y==5)
    a_trans=z3.And(xp==8-y,yp==x+2)
    ia,a=test_case("JOINT_ROTATION",a_pre,a_trans,x>=3,[x,y],[xp,yp])
    a_orig={"now":[x,y],"next":[xp,yp],"pre":a_pre,"trans":a_trans,"post":x>=3}
    individually=[check_cover(x==3,a_orig)["status"],check_cover(y==5,a_orig)["status"]]
    assert a["additional_hidden_structure_necessary"] and a["independent_equalities"]==2
    assert all(t!=PROVEN for t in individually)

    b_pre=z3.Or(z3.And(x==1,y==1),z3.And(x==2,y==2))
    b_trans=z3.Or(z3.And(x>0,xp==x+y,yp==x+y),
                  z3.And(x<=0,xp==x,yp==y))
    ib,b=test_case("BRANCHING_NON_SINGLETON_INIT",b_pre,b_trans,y>=1,[x,y],[xp,yp])
    assert b["additional_hidden_structure_necessary"]
    assert b["init_counterexamples"]>=1
    assert b["independent_equalities"]==1

    bx=z3.Int("q3w_bool_x"); bxp=z3.Int("q3w_bool_xp")
    flag=z3.Bool("q3w_flag");flagp=z3.Bool("q3w_flagp")
    c_pre=z3.And(bx==1,flag)
    c_trans=z3.Or(z3.And(flag,bxp==bx+1,flagp),
                  z3.And(z3.Not(flag),bxp==bx-5,z3.Not(flagp)))
    ic,c=test_case("GUARDED_MIXED_BOOL_INT",c_pre,c_trans,bx>=1,
                    [bx,flag],[bxp,flagp])
    assert c["additional_hidden_structure_necessary"]
    assert c["independent_equalities"]>=1
    changed=z3.Or(z3.And(flag,bxp==bx-5,flagp),
                  z3.And(z3.Not(flag),bxp==bx-5,z3.Not(flagp)))
    mutated={"pre":c_pre,"trans":changed,"post":bx>=1,
             "now":[bx,flag],"next":[bxp,flagp]}
    assert check_cover(z3.And(ic,bx>=1),mutated)["status"]!=PROVEN

    neg_pre=x==0;neg_trans=xp==x-1;neg_post=x>=0
    idd,d=test_case("TRULY_UNSAFE_NEGATIVE",neg_pre,neg_trans,
                      neg_post,[x],[xp])
    assert d["source_goal_with_affine_hull"]!=PROVEN
    # Concrete reachable violating successor.
    assert check_formula(z3.And(neg_pre,neg_trans,z3.Not(z3.substitute(
             neg_post,(x,xp)))))=="sat"
    return {"pass":True,"A_joint":a,"A_both_singletons_individually_fail":individually,
            "B_branch":b,"C_mixed_bool":c,"C_stale_certificate_rejected":True,
            "D_unsafe":d}

def historical_paths(root):
    fib=sorted((root/FIB).glob("*.sl"))[:8]
    if len(fib)!=8:raise AssertionError("MISSING_FROZEN_FIB_COHORT")
    out=fib+[root/x for x in OPENED_CONTROLS]
    if len(out)!=12:raise AssertionError("HISTORICAL_12_CHANGED")
    return out

def freeze_fresh(root,artifact_path,oldpaths):
    raw=artifact_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=Q3S_FIRST_SHA256:
        raise ValueError("FIRST_Q3S_ARCHIVE_HASH_MISMATCH")
    r=json.loads(raw)
    if r.get("study")!="Q3S_FIRST_TWO_UNUSED_SOURCE_FAMILIES_LEARNED_AFFINE_RELATIONAL_TYPED_ORIGINAL_PROOFS":
        raise ValueError("Q3S_FIRST_STUDY_IDENTITY_MISMATCH")
    chosen=set(r["newly_selected_origin_groups"])
    prior=set(r["all_excluded_previous_origin_groups"])|chosen
    prior|={"/".join(p.relative_to(root).parts[:3]) for p in oldpaths}
    possible=[g for g in r["available_previously_unused_origin_groups"] if g not in prior]
    selected=possible[:2]
    if len(selected)!=2:raise ValueError("NO_TWO_FRESH_EXCLUDED_ORIGINAL_GROUPS")
    files=[]
    for group in selected:
        original_files=sorted((root/group).glob("*.sl"))[:4]
        if len(original_files)<2:
            raise ValueError("FRESH_SELECTED_ORIGIN_NO_TWO_FILES")
        files.extend(original_files)
    assert len({p.relative_to(root).as_posix() for p in files})==len(files)
    return selected,files

def evaluate_original(root,path,kind):
    t0=time.perf_counter_ns()
    rel=path.relative_to(root).as_posix()
    raw=path.read_bytes()
    rec={"source":rel,"source_blob":blobhash(raw),"cohort":kind,"status":"NOT_RUN",
         "raw_source_or_invariant_text_exported":False}
    try:
        if len(raw)>500000:raise Abstain("ORIGINAL_SOURCE_SIZE_CAP")
        forms=sexprs(raw)
        obj=extract_mixed_original(forms)
        if len(obj["now"])>MAX_STATE:raise Abstain("ORIGINAL_STATE_CAP")
        native=native_original_relations(forms,obj)
        native.update({"now":obj["now"],"next":obj["next"]})
        parity={k:check_formula(z3.Xor(obj[k],native[k]),TIMEOUT_MS)
                for k in ("pre","trans","post")}
        rec["original_native_semantic_xor"]=parity
        if any(v!="unsat" for v in parity.values()):
            raise Abstain("SOURCE_SEMANTIC_PARITY_UNKNOWN_OR_FAIL")
        pre=check_formula(native["pre"],TIMEOUT_MS)
        notpost=check_formula(z3.Not(native["post"]),TIMEOUT_MS)
        rec["original_pre_sat"]=pre
        rec["original_not_post_sat"]=notpost
        if pre!="sat" or notpost!="sat":
            raise Abstain("VACUOUS_OR_UNKNOWN_SOURCE_GOAL")
        post_only=check_cover(native["post"],native)["status"]
        rec["original_post_alone"]=post_only
        # Strong independent source-only classical solver, never mined for gold.
        specialist=independent_native_bad_query(native,obj["now"],obj["next"])
        rec["original_specialist_spacer_status"]=specialist["status"]
        rec["original_specialist_spacer_wall_ms"]=specialist["native_solver_wall_ms"]
        I,discovery=construct(native["pre"],native["trans"],obj["now"],obj["next"])
        rec["discoverer_diagnostics"]={k:v for k,v in discovery.items()
            if k!="relation_coefficients"}
        rec["relation_coefficient_sha256"]=hashlib.sha256(
            json.dumps(discovery["relation_coefficients"],sort_keys=True).encode()).hexdigest()
        final=check_cover(z3.And(I,native["post"]),native)
        rec["original_full_three_vc_status"]=final["status"]
        rec["original_full_three_vc_components"]={
            k:final.get(k) for k in ("initial","consecution","post")}
        rec["nontrivial_source_only_discovery"]=(post_only!=PROVEN
            and discovery["independent_equalities"]>0
            and final["status"]==PROVEN)
        rec["status"]="COMPLETE_ORIGINAL_SOURCE_COMPARISON"
        if final["status"]==PROVEN:
            assert all(final.get(k)=="unsat" for k in ("initial","consecution","post"))
            assert discovery["exact_original_induction"]==["unsat","unsat"]
            assert rec["original_pre_sat"]=="sat" and rec["original_not_post_sat"]=="sat"
    except (Exception,) as exc:
        # Fail closed including unsupported; preserve case identity and reason.
        rec["status"]="ABSTAIN_ORIGINAL_NOT_CERTIFIED"
        rec["reason_type"]=type(exc).__name__
        rec["reason_code"]=str(exc).split(":")[0][:120]
        rec["nontrivial_source_only_discovery"]=False
    finally:
        rec["total_case_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--q3s-first",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    started=time.perf_counter_ns()
    if blobhash((a.root/"LICENSE.md").read_bytes())!=LICENSE_BLOB:
        raise ValueError("UPSTREAM_LICENSE_SOURCE_BLOB_CHANGED")
    historical=historical_paths(a.root)
    freshgroups,fresh=freeze_fresh(a.root,a.q3s_first,historical)
    # Frozen source identity and evidence all retained regardless of outcomes.
    controls=synthetic_strict_controls()
    oldresults=[evaluate_original(a.root,p,"PREVIOUSLY_OPENED") for p in historical]
    freshresults=[evaluate_original(a.root,p,"FRESH_PATH_ONLY_SOURCE_GROUP") for p in fresh]
    allresults=oldresults+freshresults
    assert len({x["source_blob"] for x in allresults})==len(allresults)
    by_group={}
    for group in freshgroups:
        group_cases=[r for r in freshresults if r["source"].startswith(group+"/")]
        by_group[group]={
            "originals":len(group_cases),
            "valid_source_certificates":sum(x["status"]=="COMPLETE_ORIGINAL_SOURCE_COMPARISON"
                                            for x in group_cases),
            "source_goal_proven_beyond_post_only":sum(x["nontrivial_source_only_discovery"]
                                                     for x in group_cases),
            "specialist_original_solved":sum(x.get("original_specialist_spacer_status")=="unsat"
                                             for x in group_cases)
        }
    fresh_admitted=(len(freshgroups)==2 and
         all(by_group[g]["source_goal_proven_beyond_post_only"]>=1 for g in freshgroups))
    result={
        "study":"Q3W_FIRST_ORACLE_FREE_AFFINE_CEGIS_WITH_STRICT_ORIGINAL_PARITY",
        "status":"ONE_SHOT_Q3W_ORIGINAL_STUDY_COMPLETE",
        "preregistration_commit":"93ca73e3a3b5d5abd52285eae59624464115b699",
        "upstream_revision":UPSTREAM,
        "algorithm":"exact_CEGIS_least_inductive_affine_hull_Int_Bool",
        "synthetic_controls":controls,
        "original_source_count":len(allresults),
        "previously_opened_case_count":len(oldresults),
        "newly_selected_frozen_source_groups":freshgroups,
        "newly_selected_frozen_source_count":len(freshresults),
        "fresh_group_results":by_group,
        "fresh_transfer_strict_Q3_candidate_pass":fresh_admitted,
        "historical_nontrivial_original_discoveries":sum(
            r["nontrivial_source_only_discovery"] for r in oldresults),
        "fresh_nontrivial_original_discoveries":sum(
            r["nontrivial_source_only_discovery"] for r in freshresults),
        "all_original_case_receipts":allresults,
        "trained_neural_forward_calls":0,
        "gold_labels_or_precomputed_original_solutions_used":False,
        "classical_specialist_invariant_leakage":False,
        "q3f_two_sealed_chc_originals_opened":False,
        "global_Q1_Q7":"OPEN",
        "measured_full_study_wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3W_FIRST_ALL_FROZEN_RESULTS",json.dumps({
        "status":result["status"],"source_count":result["original_source_count"],
        "historical_wins":result["historical_nontrivial_original_discoveries"],
        "fresh_wins":result["fresh_nontrivial_original_discoveries"],
        "two_family_gate":fresh_admitted,"fresh_group_results":by_group,
        "synthetic_controls":controls["pass"],"global":result["global_Q1_Q7"]},
        sort_keys=True))
if __name__=="__main__":main()
