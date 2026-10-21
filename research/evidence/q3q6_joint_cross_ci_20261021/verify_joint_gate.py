"""Read-only, fail-closed audit of three immutable NEUMANN official runs.
No solver re-execution, no new original solutions, no ML or Q3/Q6 PASS.
"""
import argparse,hashlib,json
from pathlib import Path

HASHES={
"q3":"9d4821bb5ea59858bdf04b23b904dbeae7c0843a16af143d9c2ac28482f2823d",
"eight":"a98ff77cda62762d5e74c27eb8490b1fd2803ef5ee2e774385f8f6bd6a4f3b69",
"twelve":"5ec0d54585fe0843a18ad9fa5b2d50b1645b7172b2e7295d28796b031e4f0819"
}
def need(ok,msg):
    if not ok: raise AssertionError(msg)
def load(path,key):
    b=Path(path).read_bytes()
    need(hashlib.sha256(b).hexdigest()==HASHES[key],"OFFICIAL_UNCHANGED_JSON_HASH_REQUIRED:"+key)
    return json.loads(b)
def dual(d,want):
    need(isinstance(d,dict) and d.get("expected")==want,"EXPECTED_NOT_FROZEN")
    need(d.get("Z3")==want and d.get("cvc5")==want and d.get("cvc5_exit")==0 and d.get("dual_pass") is True,
         "DUAL_SOLVER_RECEIPT_FALSE")
def one(row):
    name=row["source"]
    need(row.get("actual_original_SHA_authenticated") is True,"NOT_AUTHENTIC:"+name)
    need(row.get("dynamic_arity_original_canonical_success") is True,"NOT_PROVED:"+name)
    need(row.get("original_source_dynamic_arity") in (2,3,4,5,6),"UNSUPPORTED_ARITY")
    need(row.get("all_three_alpha_signature_digests_identical_to_original") is True,"FALSE_CANON_HASH")
    need(row.get("original_source_and_renamed_3x_full_dual_equivalence_tests_passed")==9,"FALSE_RECORDED_COUNT")
    tests=row["three_synthetic_renamed_semantic_source_test_cases"]
    need(len(tests)==3 and {t["renaming_seed"] for t in tests}=={1,2,3},"WRONG_VARIANTS")
    for t in tests:
        need(t["source_canonical_alpha_name_order_sha_equal"] is True,"WRONG_ALPHA_SIGNATURE")
        need(t["independent_dual_original_Pre_Trans_Post_pass_count"]==3,"WRONG_FORMULA_COUNT")
        obligations=t["independent_source_3_math_grammars_semantics_dual_equivalence"]
        need(set(obligations)=={"pre","trans","post"},"MISSING_FORMULA")
        for q in obligations.values():
            need(q["original_vs_alpha_native_XOR_dual_proved_UNSAT"] is True,"NO_SOURCE_EQUIVALENCE")
            dual(q["independent_z3_cvc5_original_source_receipt"],"unsat")
    need(row.get("negative_post_mutation_real_semantics_dual_SAT") is True,"NEGATIVE_NOT_DETECTED")
    need(row.get("negative_post_mutation_canonical_sha_differs") is True,"NEGATIVE_NOT_DIFFERENT")
    dual(row["negative_original_source_dual_check_receipt"],"sat")
    return 9
def audit(q3,eight,twelve):
    need(q3["schema"]=="neumann.q3.official_18_originals_cross_CI_authority_audited.v1","WRONG_Q3_SCHEMA")
    need(eight["schema"]=="neumann.q6.real_eight_original_dynamic_alpha_semantic_skeleton_independently_proved.v1","WRONG_EIGHT_SCHEMA")
    need(twelve["schema"]=="neumann.q6.fixed_classical_alpha_representation_on_12_first_originals.v1","WRONG_TWELVE_SCHEMA")
    originals=q3["frozen_source_18_real_results"]
    names=[r["original_git_blob"] for r in originals]
    need(len(names)==len(set(names))==18,"Q3_DUPLICATE_OR_MISSING_ORIGINAL")
    labs=[r["final_source_mathematical_authority"] for r in originals]
    for label,count in {
        "ORIGINAL_FULL_SMT_SOLVER_FIRST_EXPERT":13,
        "POSTHOC_INDEPENDENT_ORIGINAL_DUAL_CERTIFIED":4,
        "POSTHOC_EXTERNAL_WINOGRAD_1971_THEOREM_CONDITIONAL":1
    }.items(): need(labs.count(label)==count,"Q3_WRONG_AUTHORITY_"+label)
    need(q3["cumulative_true_original_solver_or_original_dual_proven_SAT_UNSAT"]==17,"Q3_FALSE_TOTAL")
    need(q3["some_initial_13_positive_source_outcomes_ONLY_SINGLE_original_solver_observation"] is True,"Q3_SINGLE_SOLVER_LIMIT_HIDDEN")
    need(q3["Winograd_original_6product_to_rank7_external_theorem_not_machine_proven"] is True,"EXTERNAL_THEOREM_MISLABELED")
    need(q3["learned_model_structure_unique_NOT_PROVEN"] is True and q3["full_original_unseen_model_Q3"]=="OPEN","FAKE_Q3_LEARNED_PASS")
    a=eight["real_originals"];b=twelve["originals"]
    need(len(a)==8 and len(b)==12,"Q6_SOURCE_COUNT")
    need(eight["true_native_3xdifferent_names_per_original_semantics_dual_pass"]==72,"Q6_EIGHT_COUNT")
    need(twelve["independent_native_source_pre_trans_post_dual_proofs"]==108,"Q6_TWELVE_COUNT")
    need(twelve["fully_verified_source_programs"]==12 and twelve["original_source_abstention_count"]==0,"Q6_TWELVE_PASS")
    need(twelve["source_body_opened_only_after_original_GitSHA_registration"] is True,"Q6_SOURCE_LEAK")
    need(twelve["model_gradient_updates"]==twelve["trained_model_inference_calls"]==0,"FALSE_LEARNED_CALLS")
    need(twelve["best_classical_direct_with_same_normalizer_equal_rights"] is True,"CLASSICAL_BASELINE_UNFAIR")
    need(twelve["family_verdicts"]=={
        "fib_related":{"authentic":6,"fully_verified":6},
        "other_2018_math_program":{"authentic":6,"fully_verified":6}},"BAD_FAMILY_COUNTS")
    allrows=a+b
    need(len({x["true_source_git_blob"] for x in allrows})==20,"REPEATED_SHA_INFLATION")
    need(len({x["source"] for x in allrows})==20,"REPEATED_SOURCE_INFLATION")
    need(all(x.get("independent_exact_git_blob_matches_frozen") is True for x in b),"FIRST_SOURCE_NOT_SHA_FROZEN")
    count=sum(one(x) for x in allrows)
    need(count==180,"WRONG_NESTED_DUAL_COUNT")
    need(all(x.get(k)=="OPEN" for x in (eight,twelve) for k in
             ("global_Q3","global_Q4","global_Q5","global_Q6")),"FALSE_GLOBAL_CLOSURE")
    return {
      "source_runs":[39569042369,39573707830,39574325055],
      "q3_authentic_originals":18,"q3_internally_original_resolved":17,
      "q3_external_theorem_conditional":1,
      "q6_distinct_original_programs":20,
      "q6_presource_frozen_new_originals":12,
      "q6_native_z3_cvc5_formula_equivalence_pairs_reaudited":count,
      "q6_dual_negative_semantic_mutation_pairs_reaudited":20,
      "q6_alpha_source_variants_reaudited":60,
      "model_unique_structure":"OPEN_NOT_PROVEN",
      "full_equal_cost_frontier_gap":"OPEN_NOT_MEASURED",
      "source_original_problem_solving_is_NOT_alpha_transformation":True,
      "NO_NEW_SOLVER_CALLS":True
    }
def main():
    p=argparse.ArgumentParser()
    for arg in ("q3","eight","twelve","out"):p.add_argument("--"+arg,required=True)
    a=p.parse_args()
    x=audit(load(a.q3,"q3"),load(a.eight,"eight"),load(a.twelve,"twelve"))
    Path(a.out).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print("Q3_TRUE_ORIGINAL_RESOLVED",x["q3_internally_original_resolved"])
    print("Q3_EXTERNAL_PUBLISHED_CONDITIONAL",x["q3_external_theorem_conditional"])
    print("Q6_DISTINCT_ORIGINAL_SOURCE_PROGRAMS",x["q6_distinct_original_programs"])
    print("Q6_DOUBLE_SOLVER_SEMANTIC_PROOF_PAIRS",x["q6_native_z3_cvc5_formula_equivalence_pairs_reaudited"])
    print("Q6_DOUBLE_SOLVER_NEGATIVE_CONTROLS",x["q6_dual_negative_semantic_mutation_pairs_reaudited"])
    print("GLOBAL_Q3_Q6_LEARNED_UNIQUE","OPEN")
if __name__=="__main__":main()
