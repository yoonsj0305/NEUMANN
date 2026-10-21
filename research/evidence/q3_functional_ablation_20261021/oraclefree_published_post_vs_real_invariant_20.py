"""20 pre-existing, SHA-frozen REAL SyGuS original-source Q3 diagnostic.

An unmodified strong classic solver (Z3 SPACER) discovers an inductive
invariant without oracle labels. Exact published Post alone is a no-
discovery ablation. Both are certified on original Pre/Trans/Post by two
independent solvers. This is NOT evidence of NEUMANN-specific invention
or a trained learner; matched Direct owns the same SPACER. Historical
already-opened study, not first-source unseen transfer.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,native_pdr,verified_3vc
)
from research.evidence.q34_safety_triage_six_20261021.first_six_general_reachable_unsafety_and_full_safe_3vc import (
    bounded_original_bad_path,
)

REVISION="13c8deb68a873635879c9a69bc78caebd340f646"

def load_four_freezes(root,files):
    records=[]
    keys=["source_targets","targets","sources","targets"]
    expected_counts=[4,4,6,6]
    for name,key,count in zip(files,keys,expected_counts):
        meta=json.loads((root/name).read_text())
        cases=meta[key]
        if len(cases)!=count:raise RuntimeError("HISTORIC_COHORT_SIZE_CHANGED:"+name)
        for case in cases:
            records.append({**case,"freeze_file":name})
    if len(records)!=20 or len({q["path"] for q in records})!=20:
        raise RuntimeError("NONUNIQUE_OR_INCOMPLETE_20_REAL_SOURCE_COHORT")
    return records

def evaluate(root,item):
    start=time.perf_counter_ns()
    rec={"source":item["path"],"git_blob":item["git_blob"],"historical_freeze_file":item["freeze_file"],
         "status":"ABSTAIN_FIRST_UNASSESSED","classical_origin":True,
         "was_original_source_already_opened":True}
    try:
        raw,src,native,identity=prepare(root,item)
        rec["original_authentic_source_and_independent_parity"]=identity
        # SOURCE Post as an invariant directly, no solver inference. This is
        # a restricted naive ablation, NOT the strongest classical Direct.
        rec["post_alone_attempt"]=None
        t=time.perf_counter_ns()
        post_good,postproof=verified_3vc(src,native,native["post"])
        rec["post_alone_attempt"]={
            "native_original_published_Post_itself_is_inductive":post_good,
            "original_dual_Z3_cvc5_3VC":postproof,
            "complete_post_only_wall_ms":(time.perf_counter_ns()-t)/1e6
        }
        # This is an OFF-THE-SHELF STRONG CLASSICAL algorithm available to
        # the Direct comparator; not a newly learned NEUMANN structure.
        rec["full_original_spacer_discovery_and_independent_proof"]=native_pdr(src,native)
        certified=rec["full_original_spacer_discovery_and_independent_proof"]["certified"]
        rec["extra_inductive_structure_necessary_vs_post_only_restricted_ablation"]=certified and not post_good
        if certified:
            rec["status"]="CLASSICAL_DISCOVERY_ORIGINAL_SAFE_DUAL_3VC"
            rec["classification"]="SAFE"
        elif post_good:
            rec["status"]="PUBLISHED_POST_ALONE_INDUCTIVE_DUAL_3VC"
            rec["classification"]="SAFE"
        else:
            # Not guessing SAFE from a missing invariant; attempt an actual
            # short original counterexample independently grounded by both.
            trace=bounded_original_bad_path(src,native)
            rec["genuine_original_short_bad_path_check"]=trace
            if trace["true_bounded_original_safety_refuted"]:
                rec["status"]="ACTUAL_SOURCE_UNSAFE_REPLAYED_BOTH_SOLVERS"
                rec["classification"]="UNSAFE"
            else:
                rec["status"]="UNKNOWN_NO_ORIGINAL_COMPLETE_CERTIFICATE"
                rec["classification"]="UNKNOWN"
    except Exception as e:
        rec["status"]="ABSTAIN_SOURCE_ORIGINAL_EXCEPTION"
        rec["classification"]="UNKNOWN"
        rec["exception"]=type(e).__name__+":"+str(e)[:360]
    rec["whole_case_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_ORACLEFREE_20",rec["source"],rec["status"],
          "POST_ONLY",rec.get("post_alone_attempt",{}).get("native_original_published_Post_itself_is_inductive"),
          "SPACER",rec.get("full_original_spacer_discovery_and_independent_proof",{}).get("certified"),
          "STRUCTURE_NEEDED_VS_POST",rec.get("extra_inductive_structure_necessary_vs_post_only_restricted_ablation"),
          "ERROR",rec.get("exception"),flush=True)
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--repo",type=Path,default=Path("."))
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    opts=ap.parse_args()
    c=json.loads(opts.contract.read_text())
    if c["schema"]!="neumann.Q3.no_oracle.structural_discovery_vs_post_only.20_real_originals.preregistered.v1":
        raise RuntimeError("CONTRACT_IDENTITY_CHANGED")
    targets=load_four_freezes(opts.repo,c["historical_cohorts"])
    results=[evaluate(opts.root,target) for target in targets]
    counts={k:sum(r["classification"]==k for r in results)
            for k in ("SAFE","UNSAFE","UNKNOWN")}
    seen=sum("original_authentic_source_and_independent_parity" in r for r in results)
    postpass=sum(r.get("post_alone_attempt",{}).get("native_original_published_Post_itself_is_inductive",False)
                 for r in results)
    pdrpass=sum(r.get("full_original_spacer_discovery_and_independent_proof",{}).get("certified",False)
                for r in results)
    necessity=sum(r.get("extra_inductive_structure_necessary_vs_post_only_restricted_ablation",False)
                  for r in results)
    report={
        "schema":"neumann.q3.20_real_source_classical_hidden_structure_causal_ablation.v1",
        "scientific_scope":"posthoc_previously_opened_source_only",
        "all_real_original_source_ids_preserved":len(results)==20,
        "authentic_git_sha_and_original_dual_pre_trans_post_count":seen,
        "original_native_post_alone_inductive_count":postpass,
        "actual_original_source_PDR_invariant_independently_dual_3VC_count":pdrpass,
        "SOURCE_POST_ALONE_ABLATION_FAILED_BUT_PDR_DISCOVERY_PROVED":necessity,
        "full_source_results":counts,
        "was_any_gold_hidden_label_passed_to_proposer":False,
        "SPACER_IS_STRONG_DIRECT_CLASSICAL_COMPARATOR":True,
        "NEW_NEUMANN_SPECIFIC_ALGORITHM_CAUSAL_ADVANTAGE":"NOT_DEMONSTRATED",
        "NEW_LEARNED_STRUCTURE":"NOT_DEMONSTRATED",
        "no_neural_training_or_forward":True,
        "not_a_valid_runtime_advantage_vs_strong_direct":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
        "results":results
    }
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("SOURCE_SHA_DUAL_AUTHENTIC",seen,"/20")
    print("POST_ONLY_DUAL_INDUCTIVE",postpass,"/20")
    print("CLASSICAL_ORACLEFREE_PDR_DISCOVERY_DUAL",pdrpass,"/20")
    print("EXTRA_STRUCTURE_NEEDED_AGAINST_POST_ONLY_ABLATION",necessity,"/20")
    print("FULL_ORIGINAL_CLASSIFICATIONS",counts)
    print("GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":
    main()
