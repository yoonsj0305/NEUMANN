"""Prospective original-program certificate transfer to unseen pinned source mutations.

All source checks use original Z3+cvc5 independent native semantic equivalence
and full original Pre/Trans/Post certification. Cache is *never* an oracle:
a cached invariant must pass fresh full original 3VC on mutated source.
Matched strong Direct owns all identical cache rights and solver tools.

No neural learning, Q3 novel discovery, frontier or global 10x claim.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3

from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,native_pdr,original_syguS,verified_3vc
)
from research.evidence.q3_affine_unopened_transfer_20261021.dragon4_spacer_extracted_dual_3vc import (
    from_spacer_answer
)
from research.evidence.q34_safety_triage_six_20261021.first_six_general_reachable_unsafety_and_full_safe_3vc import (
    bounded_original_bad_path
)
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import sha

REV="13c8deb68a873635879c9a69bc78caebd340f646"
FROZEN_COMMIT="11ecb5691116bd3953b0dd5e69afe9b58839aaf0"

def ms(start):
    return (time.perf_counter_ns()-start)/1e6

def source_spacer_base_invariant(src,native):
    now,nxt=src["now"],src["next"]
    name=f"base_reach_{len(now)}"
    reach=z3.Function(name,*[v.sort() for v in now],z3.BoolSort())
    bad=z3.Function(f"base_bad_{len(now)}",z3.BoolSort())
    used=z3.z3util.get_vars(z3.And(native["pre"],native["trans"],native["post"]))
    variables=list(used)
    names={str(v) for v in variables}
    for v in now+nxt:
        if str(v) not in names:variables.append(v);names.add(str(v))
    fp=z3.Fixedpoint()
    fp.set(engine="spacer",timeout=15000)
    fp.register_relation(reach,bad)
    fp.declare_var(*variables)
    fp.rule(reach(*now),native["pre"])
    fp.rule(reach(*nxt),z3.And(reach(*now),native["trans"]))
    fp.rule(bad(),z3.And(reach(*now),z3.Not(native["post"])))
    r=fp.query(bad())
    if r!=z3.unsat:
        return {"status":"ABSTAIN_BASE_SPACER_NOT_UNSAT","spacer":str(r)},None
    answer=fp.get_answer()
    invs=from_spacer_answer(answer,reach,now)
    checks=[]
    for inv in invs:
        ok,proofs=verified_3vc(src,native,inv)
        checks.append({"formula_sha256":sha(inv.sexpr().encode()),
                       "original_source_full_dual_3VC":proofs,"pass":ok})
        if ok:
            return {"status":"SOURCE_BASE_INDUCTIVE_CACHE_DUAL_PROVED",
                    "candidate_count":len(invs),"real_original_dual_source_proofs":checks,
                    "actual_cached_SMT_AST_SHA256":sha(inv.sexpr().encode())},inv
    return {"status":"ABSTAIN_BASE_NO_DUAL_CERTIFIED_CANDIDATE",
            "candidate_count":len(invs),"original_dual_certification_trials":checks},None

def build_bases(root,items):
    out={}
    cache={}
    for item in items:
        t=time.perf_counter_ns()
        rec={"source":item["path"],"group":item["group"],
             "original_source_git_blob":item["git_blob"],
             "cached_invariant_ready":False}
        try:
            raw,parsed,native,evidence=prepare(root,item)
            rec["genuine_source_dual_parity"]=evidence
            cand_receipt,cand=source_spacer_base_invariant(parsed,native)
            rec["source_original_structure_discovery"]=cand_receipt
            if cand is not None:
                rec["cached_invariant_ready"]=True
                cache[item["group"]]={"formula":cand,
                         "parsed":parsed,"original_path":item["path"]}
        except Exception as e:
            rec["error"]=type(e).__name__+":"+str(e)[:340]
        rec["base_inductive_cache_creation_wall_ms"]=ms(t)
        out[item["group"]]=rec
        print("REAL_SOURCE_BASE_CACHE",item["group"],
              rec["cached_invariant_ready"],"COST",round(rec["base_inductive_cache_creation_wall_ms"],2),
              "ERROR",rec.get("error"),flush=True)
    return out,cache

def baseline_native_pdr_with_fallback(raw,parsed,native):
    steps=[]
    t=time.perf_counter_ns()
    pdr=native_pdr(parsed,native)
    steps.append({"method":"unmodified_original_SPACER","receipt":pdr})
    if pdr["certified"]:
        return "SAFE",steps,ms(t)
    syn=original_syguS(raw,parsed,native,0.75)
    steps.append({"method":"original_source_cvc5_SyGuS_750ms","receipt":syn})
    if syn["certified"]:
        return "SAFE",steps,ms(t)
    trace=bounded_original_bad_path(parsed,native)
    steps.append({"method":"full_original_grounded_BMC_depth3","receipt":trace})
    if trace["true_bounded_original_safety_refuted"]:
        return "UNSAFE",steps,ms(t)
    return "UNKNOWN",steps,ms(t)

def transfer_or_fallback(raw,parsed,native,cached):
    start=time.perf_counter_ns()
    steps=[]
    if cached is not None:
        previous=cached["parsed"]
        if previous["states"]==parsed["states"]:
            # Source-target state names may differ in internal Z3 representation;
            # substitute all previous STATE VARIABLES into actual target source.
            formula=z3.substitute(cached["formula"],
                    *list(zip(previous["now"],parsed["now"])))
            ok,proof=verified_3vc(parsed,native,formula)
            steps.append({
               "method":"base_sourced_canonical_inductive_invariant_with_fresh_original_dual_3VC",
               "original_source_dual_3VC":proof,
               "candidate_smt_sha256":sha(formula.sexpr().encode()),
               "proves_actual_mutant_source":ok
            })
            if ok:
                return "SAFE",steps,ms(start),True
        else:
            steps.append({"method":"SOURCE_STATE_SIGNATURE_MISMATCH_NO_UNVERIFIED_REUSE"})
    verdict,fallback,paid=baseline_native_pdr_with_fallback(raw,parsed,native)
    steps+=fallback
    return verdict,steps,ms(start),False

def per_mutant(root,item,cached):
    start=time.perf_counter_ns()
    row={"source":item["path"],"group":item["group"],
         "original_git_blob":item["git_blob"],
         "status":"UNKNOWN",
         "has_all_original_source_evidence":False}
    try:
        a=time.perf_counter_ns()
        raw,parsed,native,identity=prepare(root,item)
        parse_ms=ms(a)
        row["original_source_parity_dual_proven"]=identity
        row["has_all_original_source_evidence"]=True
        cold,steps,cost=baseline_native_pdr_with_fallback(raw,parsed,native)
        warm,twarm,costwarm,reused=transfer_or_fallback(raw,parsed,native,cached)
        row["cold_direct_baseline"]={
            "original_verdict":cold,"attempts":steps,
            "source_parsing_and_semantic_validation_ms":parse_ms,
            "full_actual_wall_including_original_parsing_ms":parse_ms+cost,
        }
        row["verified_reused_source_candidate_then_direct_fallback"]={
            "original_verdict":warm,"attempts":twarm,
            "proof_reused_and_dual_reverified":reused,
            "source_parsing_and_semantic_validation_ms":parse_ms,
            "full_actual_wall_including_original_parsing_ms":parse_ms+costwarm,
        }
        row["verdict_agreement_if_both_originals_resolved"]=(
            cold==warm if cold!="UNKNOWN" and warm!="UNKNOWN" else None)
        row["paired_direct_over_verified_cache_wall_ratio_if_equal_quality"]=(
            (parse_ms+cost)/(parse_ms+costwarm)
            if cold==warm and cold!="UNKNOWN" else None)
        row["status"]="COMPLETE_DUAL_VERIFIED_BOTH_ARMS" if cold==warm and cold!="UNKNOWN" else "UNKNOWN_OR_CONFLICT"
    except Exception as e:
        row["error"]=type(e).__name__+":"+str(e)[:340]
    row["whole_study_wall_ms"]=ms(start)
    print("REAL_MUTANT_FIRST",row["source"],row["status"],
          "COLD",row.get("cold_direct_baseline",{}).get("original_verdict"),
          "REUSE",row.get("verified_reused_source_candidate_then_direct_fallback",{}).get("original_verdict"),
          "REUSABLE",row.get("verified_reused_source_candidate_then_direct_fallback",{}).get("proof_reused_and_dual_reverified"),
          "RATIO",row.get("paired_direct_over_verified_cache_wall_ratio_if_equal_quality"),
          "ERROR",row.get("error"),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    f=json.loads(args.freeze.read_text())
    if f["upstream_commit"]!=REV or len(f["mutants"])!=8 or len(f["baseline_origins"])!=3:
        raise RuntimeError("SOURCE_ORIGINAL_MUTANT_COHORT_CHANGED")
    base,caches=build_bases(args.root,f["baseline_origins"])
    rows=[per_mutant(args.root,m,caches.get(m["group"])) for m in f["mutants"]]
    cold=[x["cold_direct_baseline"] for x in rows if "cold_direct_baseline" in x]
    warm=[x["verified_reused_source_candidate_then_direct_fallback"] for x in rows
          if "verified_reused_source_candidate_then_direct_fallback" in x]
    basecost=sum(x["base_inductive_cache_creation_wall_ms"] for x in base.values())
    costcold=sum(x["full_actual_wall_including_original_parsing_ms"] for x in cold)
    costwarm=sum(x["full_actual_wall_including_original_parsing_ms"] for x in warm)
    equals=[x for x in rows if x["status"]=="COMPLETE_DUAL_VERIFIED_BOTH_ARMS"]
    report={
        "schema":"neumann.q34.pre_registered_eight_original_mutants_incremental_certification.v1",
        "first_mutant_freeze_commit":FROZEN_COMMIT,
        "all_eight_first_mutant_source_rows_preserved":len(rows)==8,
        "genuine_source_dual_parity_and_original_sha_count":sum(x["has_all_original_source_evidence"] for x in rows),
        "base_certified_cache_count":sum(x["cached_invariant_ready"] for x in base.values()),
        "exact_previous_source_original_dual_proven_invariant_reuses":sum(
          x.get("verified_reused_source_candidate_then_direct_fallback",{}).get("proof_reused_and_dual_reverified",False)
          for x in rows),
        "paired_both_resolved_equal_verdict_count":len(equals),
        "cold_direct_full_actual_wall_ms":costcold,
        "warm_original_certified_cost_excluding_initial_base_investment_ms":costwarm,
        "base_certificate_original_full_discovery_investment_ms":basecost,
        "warm_including_initial_certificate_investment_full_wall_ms":costwarm+basecost,
        "amortized_warm_over_direct_wall_ratio_for_this_eight_source_cohort":(
            (costwarm+basecost)/costcold if len(equals)==8 and costcold else None),
        "per_group_base_original_evidence":base,
        "first_mutant_cases":rows,
        "strongest_direct_can_equally_reuse_identical_source_certificates":True,
        "this_is_not_neural_invention_or_superior_equal_authority_direct":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("CERTIFIED_MUTANT_REUSE_COUNT",report["exact_previous_source_original_dual_proven_invariant_reuses"],"/8")
    print("SOURCE_INDEPENDENT_PAIRED_VERDICT_EQUAL",len(equals),"/8")
    print("COLD_WALL_MS",costcold,"WARM_MS",costwarm,
          "WARM_WITH_PAID_CACHE_CREATION_MS",costwarm+basecost)
    print("AMORTIZED_8_MUTANTS_COST_RATIO",report["amortized_warm_over_direct_wall_ratio_for_this_eight_source_cohort"])
    print("GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
