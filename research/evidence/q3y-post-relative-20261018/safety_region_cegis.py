"""Q3Y exact Post-relative affine equality CEGIS; no source gold labels.
A distinct structural hypothesis from unconditional Q3W. Original typed
source proofs are independently checked with original native SMT-LIB semantics.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
import sympy as sp
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3w-oraclefree-cegis-20261018"))
sys.path.insert(0,str(HERE.parent/"q3x-nia-20261018"))
import affine_hull_original_cegis as core
from first_nia_domain_one_shot import select_nia_only_paths

PREREG="ab67b9037be4d6da18526079b1761e05779417ee"
PROVEN=core.PROVEN

def discover_relative(pre,trans,post,now,nxt):
    """E is separately verified Pre=>E and E & Post & Trans=>E'.
    Complete I=E & Post must additionally pass original 3 VCs.
    """
    if not (len(now)==len(nxt) and 1<=len(now)<=core.MAX_STATE):
        raise core.Abstain("STATE_ARITY_OR_NEXT_STATE_MISMATCH")
    if any(x.sort()!=y.sort() for x,y in zip(now,nxt)):
        raise core.Abstain("STATE_SORT_MISMATCH")
    start=time.perf_counter_ns()
    ini=core.solver(pre)
    first,firstms=core.verdict(ini)
    if first!="sat":raise core.Abstain("PRE_UNKNOWN_OR_UNSAT_"+first)
    rows=[core.model_column(ini,now)]
    calls=1;solver_ms=firstms
    counters={"initial":0,"transition":0}
    d=len(now)+1
    result=None
    for iteration in range(min(d+2,40)):
        E,R,rank=core.formula(rows,now)
        Enext,_,_=core.formula(rows,nxt)
        initial=core.solver(pre,z3.Not(E))
        status,ms=core.verdict(initial);calls+=1;solver_ms+=ms
        if status=="sat":
            nextrow=core.model_column(initial,now)
            if sp.Matrix.hstack(*rows,nextrow).rank()!=rank+1:
                raise AssertionError("INITIAL_WITNESS_DID_NOT_GROW_RANK")
            rows.append(nextrow);counters["initial"]+=1
            continue
        if status!="unsat":raise core.Abstain("UNKNOWN_INITIAL_"+status)
        step=core.solver(E,post,trans,z3.Not(Enext))
        status,ms=core.verdict(step);calls+=1;solver_ms+=ms
        if status=="sat":
            nextrow=core.model_column(step,nxt)
            if sp.Matrix.hstack(*rows,nextrow).rank()!=rank+1:
                raise AssertionError("POST_RELATIVE_WITNESS_NOT_RANK_INCREASING")
            rows.append(nextrow);counters["transition"]+=1
            continue
        if status!="unsat":raise core.Abstain("UNKNOWN_RELATIVE_CONSECUTION_"+status)
        result=(E,R,rank)
        break
    if result is None:raise core.Abstain("FIXPOINT_NOT_CERTIFIED_WITHIN_RANK_BOUND")
    E,R,rank=result
    Eprime=z3.substitute(E,*list(zip(now,nxt)))
    pre_vc=core.check_formula(z3.And(pre,z3.Not(E)),core.TIMEOUT_MS)
    step_vc=core.check_formula(z3.And(E,post,trans,z3.Not(Eprime)),core.TIMEOUT_MS)
    if (pre_vc,step_vc)!=("unsat","unsat"):
        raise AssertionError("POST_RELATIVE_MATH_CERTIFICATE_FALSE")
    return E,{"status":"SOUND_ORIGINAL_POST_RELATIVE_EQ_HULL",
              "state_count":len(now),"witness_models":len(rows),
              "reachable_affine_span_rank":rank,
              "independent_equations":len(R),
              "equation_coefficients":R,
              "initial_counterexamples":counters["initial"],
              "step_counterexamples":counters["transition"],
              "pre_and_region_step_equation_checks":["unsat","unsat"],
              "discovery_smt_calls":calls+2,
              "discovery_solver_wall_ms":round(solver_ms,3),
              "end_to_end_discovery_wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def compare(pre,trans,post,now,nxt):
    E,evidence=discover_relative(pre,trans,post,now,nxt)
    original={"pre":pre,"trans":trans,"post":post,"now":now,"next":nxt}
    certified=core.check_cover(z3.And(post,E),original)
    alone=core.check_cover(post,original)
    status=certified["status"]
    return E,{**{k:v for k,v in evidence.items() if k!="equation_coefficients"},
      "three_original_vcs":[certified.get(k) for k in ("initial","consecution","post")],
      "original_full_goal":status,"post_alone":alone["status"],
      "useful_new_equation":status==PROVEN and alone["status"]!=PROVEN
        and evidence["independent_equations"]>0}

def controls():
    x,y=z3.Ints("q3y_x q3y_y")
    xp,yp=z3.Ints("q3y_xp q3y_yp")
    ia,a=compare(z3.And(x==3,y==5),
         z3.And(xp==8-y,yp==x+2),x>=3,[x,y],[xp,yp])
    orig={"pre":z3.And(x==3,y==5),"trans":z3.And(xp==8-y,yp==x+2),
          "post":x>=3,"now":[x,y],"next":[xp,yp]}
    single=[core.check_cover(x==3,orig)["status"],core.check_cover(y==5,orig)["status"]]
    assert a["useful_new_equation"] and a["independent_equations"]==2
    assert all(x!=PROVEN for x in single)

    pb=z3.Or(z3.And(x==1,y==1),z3.And(x==2,y==2))
    tb=z3.Or(z3.And(x>0,xp==x+y,yp==x+y),
             z3.And(x<=0,xp==x,yp==y-5))
    ib,b=compare(pb,tb,y>=1,[x,y],[xp,yp])
    assert b["useful_new_equation"] and b["initial_counterexamples"]>=1
    assert b["independent_equations"]==1

    bx=z3.Int("q3y_bool_x");xp2=z3.Int("q3y_bool_xp")
    f=z3.Bool("q3y_flag");fp=z3.Bool("q3y_flagp")
    pc=z3.And(bx==1,f)
    tc=z3.Or(z3.And(f,xp2==bx+1,fp),
             z3.And(z3.Not(f),xp2==bx-5,z3.Not(fp)))
    ic,c=compare(pc,tc,bx>=1,[bx,f],[xp2,fp])
    assert c["useful_new_equation"] and c["independent_equations"]>=1
    mutated=z3.Or(z3.And(f,xp2==bx-5,fp),
             z3.And(z3.Not(f),xp2==bx-5,z3.Not(fp)))
    reject=core.check_cover(z3.And(bx>=1,ic),
          {"pre":pc,"trans":mutated,"post":bx>=1,"now":[bx,f],"next":[xp2,fp]})
    assert reject["status"]!=PROVEN

    idd,d=compare(x==0,xp==x-1,x>=0,[x],[xp])
    assert d["original_full_goal"]!=PROVEN
    assert core.check_formula(z3.And(x==0,xp==x-1,xp<0))=="sat"
    return {"pass":True,"rotation":a,"joint_individual_failures":single,
            "guarded_two_initial_states":b,"mixed_bool":c,
            "mutated_stale_certificate_rejected":True,"unsafe_negative":d}

def evaluate(root,path,cohort):
    t=time.perf_counter_ns()
    relative=path.relative_to(root).as_posix()
    raw=path.read_bytes()
    rec={"source":relative,"source_blob":core.blobhash(raw),
         "cohort":cohort,"status":"NOT_RUN",
         "original_source_text_or_formula_reprinted":False}
    try:
        if len(raw)>500000:raise core.Abstain("SOURCE_BYTES_CAP")
        ast=core.sexprs(raw)
        obj=core.extract_mixed_original(ast)
        if len(obj["now"])>core.MAX_STATE:
            raise core.Abstain("ORIGINAL_STATE_CAP")
        native=core.native_original_relations(ast,obj)
        native.update({"now":obj["now"],"next":obj["next"]})
        parity={k:core.check_formula(z3.Xor(obj[k],native[k]),core.TIMEOUT_MS)
                for k in ("pre","trans","post")}
        rec["original_source_native_parity"]=parity
        if any(x!="unsat" for x in parity.values()):
            raise core.Abstain("NATIVE_SOURCE_PARSE_DIVERGED_OR_UNKNOWN")
        presat=core.check_formula(native["pre"],core.TIMEOUT_MS)
        nonpost=core.check_formula(z3.Not(native["post"]),core.TIMEOUT_MS)
        rec["original_pre_sat"]=presat;rec["original_not_post_sat"]=nonpost
        if presat!="sat" or nonpost!="sat":
            raise core.Abstain("EMPTY_OR_UNKNOWN_ORIGINAL_PRE_OR_POST")
        alone=core.check_cover(native["post"],native)
        rec["original_post_only"]=alone["status"]
        specialist=core.independent_native_bad_query(native,obj["now"],obj["next"])
        rec["direct_original_spacer"]=specialist["status"]
        rec["direct_original_spacer_ms"]=specialist["native_solver_wall_ms"]
        E,proof=discover_relative(native["pre"],native["trans"],native["post"],
                                  obj["now"],obj["next"])
        rec["discovery_receipt"]={k:v for k,v in proof.items()
                                  if k!="equation_coefficients"}
        rec["discovered_equations_sha256"]=hashlib.sha256(
            json.dumps(proof["equation_coefficients"],sort_keys=True).encode()).hexdigest()
        original=core.check_cover(z3.And(native["post"],E),native)
        rec["original_goal_three_vc_status"]=original["status"]
        rec["original_goal_three_vc_queries"]=[
            original.get(k) for k in ("initial","consecution","post")]
        rec["new_non_post_original_theorem"]=(original["status"]==PROVEN
           and alone["status"]!=PROVEN and proof["independent_equations"]>0)
        if original["status"]==PROVEN:
            assert rec["original_goal_three_vc_queries"]==["unsat"]*3
            assert proof["pre_and_region_step_equation_checks"]==["unsat"]*2
        rec["status"]="COMPLETE_TRUE_ORIGINAL_SOURCE_PARITY_AND_PROOF_COMPARISON"
    except Exception as ex:
        rec["status"]="ABSTAIN_ORIGINAL_NO_PROOF"
        rec["reason_type"]=type(ex).__name__
        rec["reason_code"]=str(ex).split(":")[0][:120]
        rec["new_non_post_original_theorem"]=False
    finally:
        rec["total_case_wall_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    t0=time.perf_counter_ns()
    if core.blobhash((a.root/"LICENSE.md").read_bytes())!=core.LICENSE_BLOB:
        raise ValueError("PINNED_ORIGINAL_SOURCE_LICENSE_SHA_DRIFT")
    groups,selected,groupmetadata=select_nia_only_paths(a.root)
    checks=controls()
    old=[evaluate(a.root,path,"HISTORICAL_OPENED_LIA") for path in core.historical_paths(a.root)]
    new=[evaluate(a.root,path,"PROSPECTIVE_ORIGINAL_NIA") for path in selected]
    allrec=old+new
    if len(set(x["source_blob"] for x in allrec))!=len(allrec):
        raise ValueError("ORIGINAL_SOURCE_BLOB_DUPLICATE")
    per_group={}
    for group in groups:
        cases=[x for x in new if x["source"].startswith(group+"/")]
        per_group[group]={
            "original_files":len(cases),
            "original_3vc_new_beyond_post":sum(x["new_non_post_original_theorem"] for x in cases),
            "source_parser_and_original_proof_comparison_complete":sum(
                x["status"]=="COMPLETE_TRUE_ORIGINAL_SOURCE_PARITY_AND_PROOF_COMPARISON"
                for x in cases),
            "original_specialist_safe":sum(x.get("direct_original_spacer")=="unsat"
                                        for x in cases),
            "errors":[x.get("reason_code") for x in cases]}
    admitted=(len(groups)==2 and all(per_group[g]["original_3vc_new_beyond_post"]>=1 for g in groups))
    out={"study":"Q3Y_POSTCONDITION_RELATIVE_EXACT_AFFINE_HULL_FIRST_NIA_ORIGINALS",
         "status":"FIRST_Q3Y_FROZEN_ORIGINAL_NONLINEAR_DOMAIN_STUDY_COMPLETE",
         "pre_registered_before_original_source_read_commit":PREREG,
         "source_rev":core.UPSTREAM,
         "prior_q3x_first_failed_synthetic_runs_preserved":True,
         "original_safety_not_inferred_from_equality_only":True,
         "controls":checks,
         "previously_opened_original_count":len(old),
         "fresh_original_count":len(new),
         "new_nia_source_path_only_groups":groups,
         "new_nia_filename_only_cohort":groupmetadata,
         "fresh_original_per_case_results":new,
         "historical_original_per_case_results":old,
         "fresh_two_origin_useful_Q3_candidate_gate":admitted,
         "fresh_group_disaggregated":per_group,
         "fresh_nonpost_original_proven_count":sum(x["new_non_post_original_theorem"] for x in new),
         "historical_nonpost_original_proven_count":sum(x["new_non_post_original_theorem"] for x in old),
         "trained_neural_forwards":0,
         "gold_oracle_covers_used":False,
         "sealed_Q3F_CHC_originals_opened":False,
         "global_Q1_Q7":"OPEN",
         "study_wall_ms":round((time.perf_counter_ns()-t0)/1e6,3)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print("Q3Y_FIRST_EVIDENCE",json.dumps({
      "new_families":groups,"new_cases":len(new),"fresh_nonpost_wins":out["fresh_nonpost_original_proven_count"],
      "historic_nonpost_wins":out["historical_nonpost_original_proven_count"],
      "two_family_gate":admitted,"group":per_group,"global":out["global_Q1_Q7"]},sort_keys=True))
if __name__=="__main__":main()
