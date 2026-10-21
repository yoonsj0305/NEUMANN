"""Independent, source-native replay of the actual Q3 operator bound and escape.

Immutable official CI artifacts:
 PR441: proof all 19 supplied modulo candidates fail each of 4 OOD source
 PR442: gradient-trained continuous construction generated out-of-list ASTs
 16/16, untrained 0/16, classical GCD 16/16, mutant rejected 16/16.

This audit REFRESHES exact Z3+cvc5 original source proofs. No retraining,
no revised source problem, no claim of a newly invented modulo primitive.
All claims are scoped to the controlled synthetic source family.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
from research.evidence.q3_modular_operator_selection_20261022.learn_mod_operator_and_dual_prove import certified_source
OLD_SHA="1b0de8126c687b0ab93227f63227ee8c3cfdf41638a7d3cf3f322ae79b5ee54d"
NEW_SHA="7f2f88a67215bceefd7866fc5c82e350308001e7d8f3581d29028e5f13103457"
def require(flag,detail):
    if not flag:raise AssertionError(detail)
def read(path,known):
    raw=Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==known,"ORIGINAL_CI_JSON_SHA256_DRIFT")
    return json.loads(raw)
def fresh_dual(k,m,expected):
    certificates=certified_source(k,m)
    if expected=="SAFE":
        require(all(x["independent_dual_unsat"] for x in certificates),
                "FRESH_INDEPENDENT_NATIVE_SOURCE_3VC_NOT_SAFE")
    elif expected=="BAD_STEP":
        require(certificates[1]["independent_dual_sat"],
                "FRESH_INDEPENDENT_NATIVE_SOURCE_STEP_NOT_SAT")
    else:raise AssertionError("EXPECTED_LABEL_UNSUPPORTED")
    return certificates
def main():
    p=argparse.ArgumentParser()
    for x in ("old","new","out"):p.add_argument("--"+x,required=True)
    a=p.parse_args()
    old=read(a.old,OLD_SHA)
    new=read(a.new,NEW_SHA)
    require(old["schema"]=="neumann.q3.exact_entire_fixed_mod_operator_grammar_impossibility.v1",
            "PR441_ORIGINAL_SCHEMA_CHANGED")
    require(new["schema"]=="neumann.q3.synthetic_source_meta_learned_modulus_constructor_frozen_list_ESCAPE.v1",
            "PR442_ORIGINAL_SCHEMA_CHANGED")
    require(old["total_candidate_times_original_source_checks"]==76,
            "76_ORIGINAL_FIXED_GRAMMAR_CASES_MISSING")
    require(old["every_model_of_ANY_weights_fail_original_vc"],
            "NOT_COMPLETE_FIXED_GRAMMAR_IMPOSSIBILITY")
    require(new["heldout_test_count"]==16 and new["distinct_trained_models"]==4,
            "NOT_16_ACTUAL_OUT_OF_LIST_SOURCE_TESTS")
    require(new["train_objective_hardcoded_PERIODICITY_and_max_period_bias"],
            "MISLEADING_AUTONOMOUS_DISCOVERY_CLAIM")
    old_rows=[]
    for record in old["all_fixed_operator_source_counterexamples"]:
        k=int(record["original_source_k"]);m=int(record["candidate_operator_m"])
        require(2<=m<=20 and k in (23,29,31,37),"CHANGED_PRIOR_SOURCE_OR_GRAMMAR")
        require(k%m!=0,"NOT_ACTUALLY_INDUCTIVE_WALL")
        proof=fresh_dual(k,m,"BAD_STEP")
        old_rows.append(dict(k=k,m=m,original_Z3_cvc5_independently_rerun_SAT=proof[1]["independent_dual_sat"]))
    new_rows=[]
    for record in new["all_original_source_trials"]:
        k=record["source_original_integer_step"]
        m=record["learned_candidate_parameter"]
        classical=record["strong_classical_GCD"]
        untrained=record["untrained_candidate_parameter"]
        require(k in (23,29,31,37),"UNREGISTERED_OOD_SOURCE")
        require(m==k and m>20,"FALSE_UNBOUNDED_OPERATOR_ESCAPE")
        require(classical==k,"CLASSICAL_SOURCE_CONTROL_WAS_NOT_EQUAL")
        require(untrained!=k,"INVALID_LEARNED_MODULE_KNOCKOUT")
        require(record["training_provenance"]["weight_updates"]==350,"NO_REAL_TRAINED_WEIGHTS")
        require(record["training_provenance"]["operator_target_labels_during_training"]==0,
                "TRAINING_OPERATOR_TARGETS_LEAKED")
        full=fresh_dual(k,m,"SAFE")
        negative=fresh_dual(k,untrained,"BAD_STEP")
        mutation=certified_source(k,m,mutate=True)
        require(mutation[1]["independent_dual_sat"],
                "MUTANT_SOURCE_SOURCE_ORIGINAL_NOT_REJECTED")
        new_rows.append(dict(seed=record["seed"],k=k,learned_m=m,
          frozen_19_feature_candidates_have_no_inductive_solution=True,
          exact_native_original_after_learned_generated_expression=all(
             z["independent_dual_unsat"] for z in full),
          native_rejection_untrained_source=negative[1]["independent_dual_sat"],
          native_rejection_source_mutant=mutation[1]["independent_dual_sat"],
          source_matched_exact_GCD=classical,
          learned_primitive_mod_supplied=True))
    require(len(old_rows)==76 and len(new_rows)==16,"REPLAY_OMITTED_ORIGINAL")
    result=dict(
      schema="neumann.q3.independent_native_causal_operator_dictionary_escape_audit.v1",
      official_actions={"exhaustive_fixed_vocabulary":39625778248,
                        "trained_unbounded_constructor":39687539419},
      immutable_sha256={"fixed_vocabulary":OLD_SHA,"trained_constructor":NEW_SHA},
      original_program_class="synthetic_source_xnext_equal_xplus_k",
      old_fixed_operator_candidate_count=19,
      OOD_original_k_count=4,
      original_entire_19x4_vocabulary_all_fresh_dual_SAT=76,
      new_learned_out_of_fixed_list_original_full_fresh_Z3_cvc5_3VC=16,
      untrained_same_architecture_original_consecution_fresh_dual_SAT=16,
      OOD_source_mutant_counterexamples_replayed=16,
      matched_strong_classical_exact_GCD_same_original_proofs=16,
      model_created_NEW_PARAMETER_INSTANCES=True,
      model_created_NEW_MOD_PRIMITIVE=False,
      learned_MODULE_NECESSARY_vs_UNTRAINED_INITIALIZATION=True,
      learned_MODULE_NOT_NECESSARY_vs_STRONG_EXACT_CLASSICAL=True,
      estimated_training_and_candidate_cost_from_official_source_receipt_only=True,
      learner_synthetic_posthoc_and_designer_supplied_period_prior=True,
      not_real_external_firstblind=False,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
      all_fresh_old_witnesses=old_rows,
      all_fresh_new_certificates=new_rows)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for key in ("original_entire_19x4_vocabulary_all_fresh_dual_SAT",
                "new_learned_out_of_fixed_list_original_full_fresh_Z3_cvc5_3VC",
                "untrained_same_architecture_original_consecution_fresh_dual_SAT",
                "matched_strong_classical_exact_GCD_same_original_proofs"):
        print("Q3_CAUSAL_REPRESENTATION_ADMISSION",key,result[key],flush=True)
    print("GLOBAL_Q3_UNIQUE_LEARNED_ABILITY_NOT_PROVEN",flush=True)
if __name__=="__main__":main()
