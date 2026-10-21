"""Read-only auditor of four OFFICIAL and already-completed GitHub Actions.
Does NOT re-solve benchmarks or change historical experimental status.

The initial actual source-body-opened expert screen stays 13/18.
Four additional original-source proofs used independent true source
Z3+cvc5/or algebraic certificates after source body inspection.
One remaining original is conditional on a verified source-to-six-product
bridge plus external published Winograd 1971 lower-bound theorem.

Not new training, learned innovation, or apples-to-apples 10x.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

MANIFEST_SHA="f834190e2907d4e484b1bf312ea3385ed56c6bfb"

def original_filename(s):
    return s.rsplit("/",1)[-1]

def load_actual(manifest,root):
    documents={}
    for item in manifest["evidence"]:
        file=root/item["kind"]/item["filename"]
        documents[item["kind"]]=json.loads(file.read_text())
    return documents

def audit(freeze,config,artifact_root):
    assert config["schema"]=="neumann.q3.new_18_source_audit_immutable_official_CI.v1"
    assert config["first_source_body_git_sha_freeze"]=="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
    assert freeze["schema"]=="neumann.q3.new_author_nra_original_18_before_source_body.v1"
    original={p["path"]:p for p in freeze["cases"]}
    assert len(original)==18
    D=load_actual(config,artifact_root)
    baseline=D["first_baseline"]
    assert baseline["first_source_body_opened_only_after_original_git_metadata_freeze_commit"]==config["first_source_body_git_sha_freeze"]
    assert baseline["authenticated_native_original_source_sha_count"]==18
    assert baseline["strongest_three_original_solver_arms_resolved_total"]==13
    assert baseline["original_source_remaining_candidate_hard_unsolved_total"]==5
    assert baseline["actual_original_classification_conflicts"]==0
    assert len(baseline["all_exact_original_sources"])==18
    base={}
    for row in baseline["all_exact_original_sources"]:
        path=row["path"]
        assert path in original and path not in base
        assert row["original_Git_blob_authenticated"]
        assert row["registered_original_git_blob"]==original[path]["git_blob"]
        assert len(row["source_solver_execution_receipts"])==3
        assert not row["source_solver_possibly_contradictory_original_status"]
        base[path]=row
    baseline_solved={p for p in base if base[p]["strong_classical_original_task_resolved"]}
    baseline_unsolved=set(original)-baseline_solved
    assert len(baseline_solved)==13 and len(baseline_unsolved)==5
    # All posthoc source achievements must be actual observed baseline UNKNOWN,
    # not items repeated or cherry-picked from easy original cases.
    target_names={"strassen-linear.smt2","strassen-hard.smt2",
                  "cut-out-1.smt2","cut-out-2.smt2","strassen-impossible.smt2"}
    residual_names={original_filename(p) for p in baseline_unsolved}
    assert residual_names==target_names,("source cohort drift",residual_names)

    strassen=D["strassen"]
    assert strassen["source_original_all_three_authentic"]==3
    assert strassen["source_linear_complete_original_SAT_algebraic"]
    assert strassen["source_hard_complete_original_SAT_algebraic"]
    assert strassen["source_impossible_classification_external_rank7_theorem_only"]
    assert strassen["model_training_and_neural_forwards"]==0
    assert not strassen["learned_unique_Q3_proven"]
    assert len(strassen["original_three"])==3
    strassen_true_internal=set()
    for row in strassen["original_three"][:2]:
        source=row["source_identity"]["source"]
        assert source in baseline_unsolved
        assert row["source_identity"]["authentic"]
        assert row["source_identity"]["git_blob"]==original[source]["git_blob"]
        assert row["source_complete_real_mathematical_identity_valid"]
        assert row["original_source_full_real_quantified_identity_coefficient_proof"]["all_actual_original_output_input_basis_coefficients_exact"]==64
        assert row["independent_genuine_original_Z3_cvc5_universal_witness"]["both_independent_Z3_cvc5_prove_ORIGINAL_FORALL_TRUE"]
        strassen_true_internal.add(source)
    assert len(strassen_true_internal)==2
    imp=strassen["original_three"][2]
    imp_path=imp["source_identity"]["source"]
    assert imp_path in baseline_unsolved and original_filename(imp_path)=="strassen-impossible.smt2"
    assert imp["source_identity"]["git_blob"]==original[imp_path]["git_blob"]
    bridge=imp["original_native_rank_six_external_theorem_premises"]
    assert bridge["actual_original_all_four_outputs_six_active_rank_one_products"]
    assert bridge["actual_original_seventh_weight_exactly_literal_zero"]
    assert bridge["this_source_bridge_NOT_a_formal_proof_of_Winograd_theorem"]
    assert "Winograd" in bridge["known_1971_Winograd_minimum_tensor_rank_seven_EXTERNAL_THEOREM"]

    c2=D["circles2"]
    assert c2["source_git_sha_before_first_original_content_commit"]==config["first_source_body_git_sha_freeze"]
    assert c2["source_body_opened_in_parent_historical_FIRST_CI"]
    assert c2["not_neural_or_learned_new_structure"]
    c2row=c2["actual_original_source_evidence"]
    assert c2row["original_source_Git_SHA_authenticated"]
    assert c2row["original_forall_actually_refuted"]
    assert c2row["ALL_actual_original_antecedent_conjuncts_TRUE"]
    assert c2row["actual_original_consequent_FALSE"]
    assert c2row["original_full_native_SMT2_dual_Z3_cvc5"]["both_Z3_and_cvc5_full_source_ground_counterexample_SAT"]
    circle2_path=next(p for p in baseline_unsolved if original_filename(p)=="cut-out-2.smt2")
    assert c2row["real_source_SHA256"]==base[circle2_path]["true_original_source_sha256"]

    c1=D["circles1"]
    assert c1["posthoc_same_original_source_already_opened"]
    assert not c1["learned_model_training"]
    assert c1["direct_matched_with_same_scipy_has_exact_algorithm_access"]
    c1row=c1["real_original_numeric_and_exact_evidence"]
    assert c1row["actual_original_source_git_sha_verified"]
    assert c1row["all_39_original_true_source_assertions_preserved"]
    assert c1row["actual_original_SAT_dual_verified"]
    assert c1row["source_status"]=="CERTIFIED_TRUE_ORIGINAL_SAT"
    witness=c1row["true_original_full_source_exact_rational_witness"]
    assert witness["all_original_source_native_constraints_satisfied_with_Fraction"]
    assert witness["independent_original_full_SMT2_SAT_Z3_cvc5"]["independent_real_original_full_Z3_cvc5_SAT"]
    circle1_path=next(p for p in baseline_unsolved if original_filename(p)=="cut-out-1.smt2")

    later_self_contained=strassen_true_internal|{circle1_path,circle2_path}
    assert len(later_self_contained)==4 and later_self_contained<=baseline_unsolved
    assert {original_filename(p) for p in later_self_contained}==set(
        config["frozen_expected"]["source_genuinely_original_proof_additional_dual_4"])
    assert set(original)==baseline_solved|later_self_contained|{imp_path}
    total_internal=baseline_solved|later_self_contained
    result={
      "schema":"neumann.q3.official_18_originals_cross_CI_authority_audited.v1",
      "official_evidence_manifest_git_commit":MANIFEST_SHA,
      "authentic_originals":len(original),
      "historical_frozen_FIRST_original_screen_solved_originals":len(baseline_solved),
      "historical_first_original_screen_unsolved_originals":len(baseline_unsolved),
      "POSTHOC_TRUE_ORIGINAL_Z3_CVC5_dual_certificate_new_case_count":len(later_self_contained),
      "cumulative_true_original_solver_or_original_dual_proven_SAT_UNSAT":len(total_internal),
      "additional_external_published_theorem_CONDITIONAL_original_unsat_count":1,
      "originals_with_sat_unsat_conditional_on_external_literature":len(total_internal)+1,
      "strong_equal_authority_classical_specialist_can_use_every_same_algorithm_and_reference":True,
      "learned_model_structure_unique_NOT_PROVEN":True,
      "model_training_for_new_four":0,
      "some_initial_13_positive_source_outcomes_ONLY_SINGLE_original_solver_observation":True,
      "Winograd_original_6product_to_rank7_external_theorem_not_machine_proven":True,
      "source_18_originals_originally_first_SHA_frozen_not_a_fresh_learned_model_test":True,
      "all_18_originals_reported":True,
      "full_original_unseen_model_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "frozen_source_18_real_results":[
        {"source_path":p,"original_git_blob":original[p]["git_blob"],
         "first_raw_expert_status":"SOLVED" if p in baseline_solved else "UNKNOWN",
         "final_source_mathematical_authority":(
           "ORIGINAL_FULL_SMT_SOLVER_FIRST_EXPERT" if p in baseline_solved else
           "POSTHOC_INDEPENDENT_ORIGINAL_DUAL_CERTIFIED" if p in later_self_contained else
           "POSTHOC_EXTERNAL_WINOGRAD_1971_THEOREM_CONDITIONAL")}
        for p in sorted(original)
      ],
      "primary_historical_runs":[{"kind":q["kind"],"run_id":q["run_id"],"artifact":q["artifact"]}
                                 for q in config["evidence"]]
    }
    assert result["cumulative_true_original_solver_or_original_dual_proven_SAT_UNSAT"]==17
    assert result["originals_with_sat_unsat_conditional_on_external_literature"]==18
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--original-freeze",type=Path,required=True)
    p.add_argument("--artifact-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    data=audit(json.loads(a.original_freeze.read_text()),
               json.loads(a.manifest.read_text()),a.artifact_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print("Q3_CROSS_ORIGINAL_EVIDENCE_AUTHENTIC",data["authentic_originals"])
    print("Q3_CROSS_FIRST_REAL_ORIGINAL_STRONG_DIRECT",data["historical_frozen_FIRST_original_screen_solved_originals"])
    print("Q3_CROSS_ADDITIONAL_ORIGINAL_DUAL",data["POSTHOC_TRUE_ORIGINAL_Z3_CVC5_dual_certificate_new_case_count"])
    print("Q3_CROSS_TOTAL_INDEPENDENT_SOURCE_OR_SOLVER",data["cumulative_true_original_solver_or_original_dual_proven_SAT_UNSAT"])
    print("Q3_CROSS_PUBLISHED_WINOGRAD_CONDITIONAL_1",data["additional_external_published_theorem_CONDITIONAL_original_unsat_count"])
    print("Q3_CROSS_PUBLIC_THEOREM_AUGMENTED_TOTAL",data["originals_with_sat_unsat_conditional_on_external_literature"])
    print("Q3_GLOBAL_LEARNED_UNIQUE_STILL_OPEN",data["full_original_unseen_model_Q3"])
if __name__=="__main__":
    main()
