"""Posthoc independent mutation-invalidation guards for three already proven
base-source structural invariants. Important: these are clearly labelled
SYNTHETIC NEGATIVE CONTROLS, not extra authentic source benchmark results.

Two classes: published goal is FALSE, and transition is unconstrained TRUE.
The originally certified invariant must not be accepted blindly. Require
independent Z3+cvc5 SAT counterexamples to relevant original 3VC obligations.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import z3
from research.evidence.q34_real_source_mutant_reuse_20261021.verified_source_mutants_original_certificate_transfer import build_bases
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare,verified_3vc
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import dual

def evaluate(root,item,cached):
    raw,source,native,parity=prepare(root,item)
    cand=cached["formula"]
    now,next_state=source["now"],source["next"]
    next_cand=z3.substitute(cand,*list(zip(now,next_state)))
    if cached["parsed"]["states"]!=source["states"]:
        raise RuntimeError("UNEXPECTED_BASE_STATE_SIGNATURE_CHANGED")
    positive,passproof=verified_3vc(source,native,cand)
    no_safety={**native,"post":z3.BoolVal(False)}
    neg_status,false_post_3vc=verified_3vc(source,no_safety,cand)
    # The cached candidate is allowed to hold on all TRUE reachable source
    # states, so when Post=False the single source initial implies a
    # source-reachable proof counterexample to the safety VC.
    post_bad_sat=dual(z3.And(cand,z3.Not(no_safety["post"])),"sat",10)
    trans_any={**native,"trans":z3.BoolVal(True)}
    notstep,weak_trans_3vc=verified_3vc(source,trans_any,cand)
    candidate_step_bad=dual(z3.And(cand,z3.Not(next_cand)),"sat",10)
    row={
      "source":item["path"],"origin_group":item["group"],
      "synthetic_cases_not_original_source":True,
      "real_original_positive_full_dual_3VC":positive,
      "positive_original_source_proofs":passproof,
      "negative_1_modified_goal_FALSE_rejected":not neg_status and post_bad_sat["dual_pass"],
      "negative_1_independent_Z3_cvc5_grounded_bad_safety":post_bad_sat,
      "negative_1_original_source_pre_trans_unchanged":True,
      "negative_2_modified_transition_TRUE_rejected":not notstep and candidate_step_bad["dual_pass"],
      "negative_2_independent_Z3_cvc5_grounded_bad_step":candidate_step_bad,
      "negative_2_original_source_pre_post_unchanged":True,
      "no_silent_cache_trust":True
    }
    print("SOURCE_MUTATION_INVALIDATION",row["origin_group"],
      "SOURCE_SAFE",positive,
      "FALSE_POST_REJECT",row["negative_1_modified_goal_FALSE_rejected"],
      "ANY_TRANS_REJECT",row["negative_2_modified_transition_TRUE_rejected"],flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    o=p.parse_args()
    frozen=json.loads(o.freeze.read_text())
    if len(frozen["baseline_origins"])!=3 or len(frozen["mutants"])!=8:
        raise RuntimeError("ORIGINAL_FROZEN_BASE_IDENTITY_CHANGED")
    first,caches=build_bases(o.root,frozen["baseline_origins"])
    rows=[]
    for b in frozen["baseline_origins"]:
        if b["group"] not in caches:
            rows.append({"origin_group":b["group"],"status":"ABSTAIN_NO_CERTIFIED_BASE"})
        else:
            rows.append(evaluate(o.root,b,caches[b["group"]]))
    output={
      "schema":"neumann.q34.true_source_invariant_synthetic_invalidation_controls.v1",
      "frozen_real_mutants_first_source_evidence_immutable":True,
      "new_real_source_verification_success_claims":0,
      "synthetic_mutations_are_only_negative_controls":True,
      "original_base_count":len(rows),
      "positive_full_original_source_dual_pass":sum(r.get("real_original_positive_full_dual_3VC",False) for r in rows),
      "negative_goal_false_z3_cvc5_rejections":sum(r.get("negative_1_modified_goal_FALSE_rejected",False) for r in rows),
      "negative_trans_any_z3_cvc5_rejections":sum(r.get("negative_2_modified_transition_TRUE_rejected",False) for r in rows),
      "no_neural_forward":True,
      "global_Q3":"OPEN","global_Q4":"OPEN",
      "rows":rows,
    }
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print("ORIGINAL_BASE_DUAL_POSITIVES",output["positive_full_original_source_dual_pass"],"/3")
    print("SYNTHETIC_FALSE_POST_DUAL_REJECTS",output["negative_goal_false_z3_cvc5_rejections"],"/3")
    print("SYNTHETIC_TRUE_TRANS_DUAL_REJECTS",output["negative_trans_any_z3_cvc5_rejections"],"/3")
if __name__=="__main__":
    main()
