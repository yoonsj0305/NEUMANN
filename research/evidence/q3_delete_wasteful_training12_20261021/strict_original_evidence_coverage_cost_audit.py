"""Immutable actual original 12 receipt audit; compare complete native proofs
and candidate-search wall of actual fitted model versus SAME-DATA no-fit OR.

No rerun, synthetic task, simulated timing or posthoc source manipulation.
One exact SHA256 for prior real CI JSON, each genuine original SHA prelocked,
and each SAFE accepted only if original Z3+cvc5 three VCs dual_pass.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
EXPECTED_REPORT_SHA="f6c1ace2921bfb1fae511982cc0e657ad57187acce813b4a1ce3aa32cd1ccd68"
def check(cond,msg):
    if not cond:raise AssertionError(msg)
def main():
    p=argparse.ArgumentParser()
    for n in ("report","freeze","out"):p.add_argument("--"+n,required=True)
    a=p.parse_args()
    b=Path(a.report).read_bytes()
    check(hashlib.sha256(b).hexdigest()==EXPECTED_REPORT_SHA,"HISTORIC_ACTUAL_CI_JSON_SHA_CHANGED")
    q=json.loads(b);f=json.loads(Path(a.freeze).read_text())
    check(q["schema"]=="neumann.q3.12_originals_exact_minimum_semantic_feature_then_actual_trained_DNF.v1",
          "ACTUAL_RESEARCH_RECEIPT_SCHEMA_WRONG")
    original={x["path"]:x["git_blob"] for x in f["cases"]}
    check(len(original)==12 and len(q["cases"])==12,"NOT_ORIGINAL_TWELVE")
    classified=[]
    for x in q["cases"]:
        check(original[x["source"]]==x["real_original_blob"],"NOT_HISTORIC_ORIGINAL_GIT_ID")
        t=bool(x.get("trivial_zero_model_original_3VC_certified",False))
        adapted=x.get("automatically_selected_semantic_interface",{})
        fixed=x.get("previous_frozen_two_slot_interface",{})
        learned=bool(adapted.get("learned_disjunction_full_original_inductive",False))
        classical=bool(adapted.get("no_fit_disjunction_full_original_inductive",False))
        if t:
            check(all(v["dual_pass"] for v in x["trivial_original_all_dual_3VC"].values()),
                  "TAUTOLOGY_NOT_FULL_SOURCE_INDUCTIVE")
        for r in (adapted,fixed):
            for kind in ("learned_disjunction","no_fit_disjunction"):
                if r.get(kind+"_full_original_inductive",False):
                    certificates=r[kind+"_original_dual_3VC"]
                    check(set(certificates)=={"init","consecution","goal"} and
                          all(v["dual_pass"] for v in certificates.values()),
                          "ORIGINAL_THREE_SOURCE_VCS_NOT_DUAL")
        if not t and adapted:
            minimum=x["fully_independent_original_minimal_feature_proof"]
            check(minimum["status"]=="MINIMUM_ORIGINAL_SOURCE_INFO_PROVED_BY_BOTH_SOLVERS",
                  "MINIMUM_INPUT_NOT_DUAL_CERTIFIED")
            if adapted.get("actual_trained"):
                check(isinstance(adapted.get("training_ms"),(int,float)) and
                      adapted.get("trained_calibration_ms") is not None and
                      adapted.get("exact_no_fit_search_ms") is not None,
                      "INSTRUMENTED_MODEL_AND_CLASSICAL_COST_MISSING")
        classified.append({"source":x["source"],"real_git_blob":x["real_original_blob"],
                           "no_training_direct_original_proof":t,
                           "adaptive_learned_original_full_safe":learned,
                           "adaptive_classical_original_full_safe":classical,
                           "nonlearned_proof_including_tautology":t or classical,
                           "learned_proof_including_tautology":t or learned,
                           "model_fit":bool(adapted.get("actual_trained",False)),
                           "model_training_and_calibration_ms":
                               (adapted["training_ms"]+adapted["trained_calibration_ms"])
                               if adapted.get("actual_trained") else None,
                           "same_input_exact_no_fit_search_ms":
                               adapted.get("exact_no_fit_search_ms") if adapted.get("actual_trained") else None})
    check(len({x["real_git_blob"] for x in classified})==12,
          "DUPLICATE_REAL_SOURCE_BLOB")
    a_l=[x for x in classified if x["learned_proof_including_tautology"]]
    a_c=[x for x in classified if x["nonlearned_proof_including_tautology"]]
    dominated=[x for x in classified if x["learned_proof_including_tautology"] and
               not x["nonlearned_proof_including_tautology"]]
    paired=[x for x in classified if x["model_fit"]]
    model_search_ms=sum(x["model_training_and_calibration_ms"] for x in paired)
    baseline_search_ms=sum(x["same_input_exact_no_fit_search_ms"] for x in paired)
    # Reconstructed conditional policies from individually measured search times.
    # No live dispatcher or new solver execution is claimed.
    learned_first_fallback_ms=(model_search_ms+
        sum(q["same_input_exact_no_fit_search_ms"] for q in paired
            if not q["adaptive_learned_original_full_safe"]))
    classical_first_fallback_ms=(baseline_search_ms+
        sum(q["model_training_and_calibration_ms"] for q in paired
            if not q["adaptive_classical_original_full_safe"]))
    learned_first_covered=sum(
        q["adaptive_learned_original_full_safe"] or q["adaptive_classical_original_full_safe"]
        for q in paired)
    check(learned_first_covered==sum(q["adaptive_classical_original_full_safe"] for q in paired),
          "FALLBACK_CHANGED_VALIDATED_PROOF_COVERAGE")
    check(len(dominated)==0,"MODEL_FOUND_NEW_PROOF_NOT_COVERED_BY_CLASSICAL_DO_NOT_DELETE")
    check(len(a_l)==4 and len(a_c)==6 and len(paired)==6,"ORIGINAL_RESULT_COUNTS_CHANGED")
    output={
        "schema":"neumann.q3.immutable_original12_matched_model_vs_exact_proof_first_delete_training.v1",
        "official_full_prior_12_source_CI":39599100942,
        "official_json_SHA256":EXPECTED_REPORT_SHA,
        "source_prebody_locked_genuine_original_count":12,
        "actual_model_fit_count":len(paired),
        "learned_or_tautology_complete_original_3VC":len(a_l),
        "no_fit_OR_or_tautology_complete_original_3VC":len(a_c),
        "learned_unique_beyond_equal_rights_classical":len(dominated),
        "actual_training_and_symbolic_calibration_sum_ms_on_paired_6":model_search_ms,
        "exact_no_fit_OR_symbolic_candidate_search_sum_ms_on_paired_6":baseline_search_ms,
        "estimated_learning_first_then_exact_fallback_candidate_search_ms_from_individual_measurements":
            learned_first_fallback_ms,
        "estimated_exact_first_then_learning_fallback_candidate_search_ms_from_individual_measurements":
            classical_first_fallback_ms,
        "learning_first_fallback_proved_source_count_on_six":learned_first_covered,
        "exact_classical_only_proved_source_count_on_six":
            sum(q["adaptive_classical_original_full_safe"] for q in paired),
        "measured_candidate_search_nofit_to_reconstructed_learning_first_ratio":
            baseline_search_ms/learned_first_fallback_ms if learned_first_fallback_ms else None,
        "counterfactual_routing_not_live_dispatched_or_end_to_end":True,
        "measured_model_to_nofit_candidate_search_wall_ratio":
            model_search_ms/baseline_search_ms if baseline_search_ms>0 else None,
        "cost_measurement_excludes_shared_data_collection_and_final_dual_3VC":True,
        "safe_to_delete_all_model_fits_for_THIS_COHORT_WITHOUT_LOSING_ANY_PRIOR_PROVED_SAFE":True,
        "does_not_imply_model_never_useful_on_OTHER_TASKS":True,
        "does_not_establish_end_to_end_10x_speedup":True,
        "no_new_training_or_solver_executed":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "per_real_original":classified}
    Path(a.out).write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    for k in ("actual_model_fit_count","learned_or_tautology_complete_original_3VC",
              "no_fit_OR_or_tautology_complete_original_3VC",
              "learned_unique_beyond_equal_rights_classical",
              "actual_training_and_symbolic_calibration_sum_ms_on_paired_6",
              "exact_no_fit_OR_symbolic_candidate_search_sum_ms_on_paired_6",
              "measured_model_to_nofit_candidate_search_wall_ratio",
              "estimated_learning_first_then_exact_fallback_candidate_search_ms_from_individual_measurements",
              "estimated_exact_first_then_learning_fallback_candidate_search_ms_from_individual_measurements",
              "measured_candidate_search_nofit_to_reconstructed_learning_first_ratio"):
        print("ACTUAL_ORIGINAL_PROOF_FIRST_MODEL_DELETION",k,output[k],flush=True)
    print("GLOBAL_Q3_OPEN",flush=True)
if __name__=="__main__":main()
