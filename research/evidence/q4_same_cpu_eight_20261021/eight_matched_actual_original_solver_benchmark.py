"""Same-CPU same-source PDR+dual versus original SyGuS+dual, eight
already opened/frozen real originals. This is a comparison of two existing
CLASSICAL solvers, not evidence of neural math, global Q4 or SOTA advantage.
Never convert timeout-censored evidence into fabricated speed ratio.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3

from research.evidence.q3_gater_relational_mixed_20261020.posthoc_independent_source_cvc5_invariant_3vc import (
    first_original_sygus_model,
)
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob,sha,sexprs,compile_typed_original,compile_independent_native,dual
)
from research.evidence.q3_other_origin_four_20261021.frozen_four_mixed_source_pdr_dual import evaluate_source

def original_baseline(root,target):
    start=time.perf_counter_ns()
    rec={"source":target["path"],"route":"cvc5_original_SyGuS_then_native_dual_3VC",
         "proves_original_published_Post":False,"status":"UNKNOWN"}
    try:
        raw=(root/target["path"]).read_bytes()
        if len(raw)!=target["bytes"] or blob(raw)!=target["git_blob"]:
            raise RuntimeError("FROZEN_SOURCE_MUTATED")
        original=compile_typed_original(sexprs(raw))
        native=compile_independent_native(sexprs(raw),original)
        candidate,receipt=first_original_sygus_model(raw,original)
        rec["original_sygus_solver_receipt"]=receipt
        nxt=z3.substitute(candidate,*list(zip(original["now"],original["next"])))
        checks={
            "source_initial":dual(z3.And(native["pre"],z3.Not(candidate)),"unsat",8),
            "source_step":dual(z3.And(candidate,native["trans"],z3.Not(nxt)),"unsat",8),
            "source_post":dual(z3.And(candidate,z3.Not(native["post"])),"unsat",8),
        }
        rec["independent_source_original_3VC"]=checks
        rec["proves_original_published_Post"]=all(v["dual_pass"] for v in checks.values())
        rec["status"]="PASS_DUAL_3VC" if rec["proves_original_published_Post"] else "ABSTAIN_UNPROVED"
    except Exception as e:
        rec["status"]="ABSTAIN_UNKNOWN_TIMEOUT_OR_UNSUPPORTED"
        rec["exception"]=type(e).__name__+":"+str(e)[:300]
    rec["end_to_end_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("BASELINE_REAL_SOURCE",target["path"],rec["status"],
          "WALL",round(rec["end_to_end_wall_ms"],3),flush=True)
    return rec

def pdr_route(root,target):
    start=time.perf_counter_ns()
    rec=evaluate_source(root,target)
    rec["end_to_end_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    rec["route"]="Z3_PDR_then_native_dual_3VC"
    rec["proves_original_published_Post"]=rec["source_independent_original_3VC"]
    return rec

def mutant_post_false_control(root,target):
    # An always-FALSE published property must NOT prove safe if
    # genuine unchanged original Pre is satisfiable.
    raw=(root/target["path"]).read_bytes()
    if blob(raw)!=target["git_blob"]:raise RuntimeError("MUTANT_CONTROL_WRONG_SOURCE")
    original=compile_typed_original(sexprs(raw))
    native=compile_independent_native(sexprs(raw),original)
    pre_check=dual(native["pre"],"sat",8)
    if not pre_check["dual_pass"]:
        return {"status":"ABSTAIN_NO_SOURCE_PRE"}
    reach=z3.Function("negative_reach",*[v.sort() for v in original["now"]],z3.BoolSort())
    bad=z3.Function("negative_bad",z3.BoolSort())
    used=z3.z3util.get_vars(z3.And(native["pre"],native["trans"],native["post"]))
    names={str(v) for v in used}
    vars_=list(used)
    for v in original["now"]+original["next"]:
        if str(v) not in names:
            vars_.append(v);names.add(str(v))
    f=z3.Fixedpoint()
    f.set(engine="spacer",timeout=12000)
    f.register_relation(reach,bad)
    f.declare_var(*vars_)
    f.rule(reach(*original["now"]),native["pre"])
    f.rule(reach(*original["next"]),z3.And(reach(*original["now"]),native["trans"]))
    f.rule(bad(),z3.And(reach(*original["now"]),z3.Not(z3.BoolVal(False))))
    answer=f.query(bad())
    return {"source":target["path"],"post":"MUTATED_FALSE_CONTROL_NOT_OFFICIAL",
            "reachability_outcome":str(answer),
            "status":"PASS_REJECT_FALSE_SAFETY" if answer==z3.sat else "FAIL_OR_UNKNOWN_CONTROL"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--first-freeze",type=Path,required=True)
    p.add_argument("--second-freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    old=json.loads(a.first_freeze.read_text())
    other=json.loads(a.second_freeze.read_text())
    if len(old["source_targets"])!=4 or len(other["targets"])!=4:
        raise RuntimeError("COHORT_NOT_FROZEN_EIGHT")
    if old["upstream_commit"]!="13c8deb68a873635879c9a69bc78caebd340f646" or other["upstream_commit"]!="13c8deb68a873635879c9a69bc78caebd340f646":
        raise RuntimeError("UPSTREAM_REVISION_DIFFERS")
    targets=old["source_targets"]+other["targets"]
    groups=[]
    for t in targets:
        baseline=original_baseline(a.root,t)
        proposed=pdr_route(a.root,t)
        b=baseline["proves_original_published_Post"]
        c=proposed["proves_original_published_Post"]
        paired=(baseline["end_to_end_wall_ms"]/proposed["end_to_end_wall_ms"]) if b and c else None
        groups.append({
            "source":t["path"],"source_git_blob":t["git_blob"],
            "baseline":baseline,"portfolio":proposed,
            "both_original_dual3VC_success":b and c,
            "paired_baseline_over_portfolio_wall_ratio_if_both_pass":paired,
            "timeout_censored_is_not_speed_ratio":not(b and c)
        })
    negatives=[mutant_post_false_control(a.root,targets[i]) for i in (0,4,6)]
    paired=[t["paired_baseline_over_portfolio_wall_ratio_if_both_pass"]
            for t in groups if t["both_original_dual3VC_success"]]
    all_pdr=sum(x["portfolio"]["proves_original_published_Post"] for x in groups)
    all_base=sum(x["baseline"]["proves_original_published_Post"] for x in groups)
    result={
        "schema":"neumann.q4.eight_frozen_originals.same_cpu_SyGuS_vs_PDR_dual.v1",
        "origins_eight_frozen_original_sha":True,
        "after_both_original_source_cohorts_already_open":True,
        "negative_post_false_controls":negatives,
        "mutated_post_is_never_official":True,
        "baseline_original_dual_safety_pass":all_base,
        "PDR_original_dual_safety_pass":all_pdr,
        "both_pass_count":len(paired),
        "common_solved_wall_speed_ratios":paired,
        "scoped_paired_all_at_least_10x":bool(paired) and all(q>=10 for q in paired),
        "scoped_portfolio_coverage_exceeds_this_fixed_baseline":all_pdr>all_base,
        "not_any_SOTA_or_full_Q4_10x":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","new_training":0,
        "cases":groups,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("REAL_SAME_CPU_FIRST_FROZEN_EIGHT_CVC5_SYGUS_DUAL",all_base,"/8")
    print("REAL_SAME_CPU_FIRST_FROZEN_EIGHT_PDR_DUAL",all_pdr,"/8")
    print("COMMON_SOLVED_TIME_RATIOS",paired)
    print("SCOPED_COMMON_ALL_10X",result["scoped_paired_all_at_least_10x"])
    print("NEGATIVE_MUTATED_FALSE_POST",negatives)
    print("GLOBAL_Q4",result["global_Q4"])
if __name__=="__main__":
    main()
