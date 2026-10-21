"""Strict read-only audit of 44 ORIGINAL Q3 tasks across two source collections.
Two original source corpora: 26 integer/math, 18 real geometry/matrix.
The 44-task collection is posthoc; no source-first learning or model claim.
"""
import argparse,hashlib,json
from pathlib import Path
HASH={
"q26":"de6581a04c7dd9fa1760c3722bc152a48ab07763ac15da3fc0064dfa11ebda8c",
"q18":"9d4821bb5ea59858bdf04b23b904dbeae7c0843a16af143d9c2ac28482f2823d",
"prior":"9fa0b058749e0fe0858891f04b5529e4c1278d5e13abf8e29d024c78f90a382e"}
PRIOR_SHA="01a8e86521634d522ee0a6b62024dc26e7ee5ac7"
def guard(ok,m):
    if not ok:raise AssertionError(m)
def load(path,key):
    raw=Path(path).read_bytes()
    guard(hashlib.sha256(raw).hexdigest()==HASH[key],"IMMUTABLE_ACTIONS_JSON_SHA_MISMATCH:"+key)
    return json.loads(raw)
def audit(a,b,c):
    guard(a["schema"]=="neumann.q3.true_authentic_26_originals_three_classical_routes_published_theorem_ablation.v1","26_SCHEMA")
    guard(b["schema"]=="neumann.q3.official_18_originals_cross_CI_authority_audited.v1","18_SCHEMA")
    guard(c["schema"]=="neumann.q3.real_original_STC367_external_prior_reference_genuine_full_smt_sat.v1","PRIOR_SCHEMA")
    rows=a["same_source_originals"]
    guard(len(rows)==a["true_original_26_source_count"]==26,"NOT_26_REAL_ORIGINALS")
    guard(a["actual_original_source_git_sha_authenticated_count"]==26,"26_SOURCE_SHA_FAIL")
    guard(a["any_known_true_source_misclassification_or_authentication_failure"]==0,"26_MISCLASSIFICATION")
    guard(a["genuine_original_internal_machine_proved_sat_or_unsat"]==20,"26_INTERNAL_PROOF_COUNT")
    guard(a["genuine_original_EXTERNAL_PUBLISHED_THEOREM_conditional_unsat"]==3,"26_EXTERNAL_THEOREM_NOT_SEPARATED")
    guard(a["integrated_original_classified_total_internal_plus_trusted_literature"]==23,"26_FALSE_TOTAL")
    guard(a["matched_raw_original_strong_generic_Z3_OR_cvc5_solved_count"]==8,"26_FALSE_DIRECT")
    guard(a["learned_unique_structure_bonus_vs_equal_authority_classical"]==0,"26_FALSE_LEARNED_GAP")
    guard(a["external_published_number_theory_theorem_NOT_independently_formally_proved"] is True,"HIDDEN_EXTERNAL_THEOREM")
    guard(a["accepted_comparator_equal_authority_specialist_can_copy_exact_same_algorithm"] is True,"DIRECT_RIGHTS_WITHHELD")
    names26={};blobs26=set()
    for r in rows:
        guard(r.get("source_Git_blob_authenticated") is True,"SOURCE_SHA_NOT_VALID")
        guard(r.get("status")=="VALID_TRUE_ORIGINAL_SOURCE_CHECK","INVALID_ORIGINAL_TRUTH")
        source=r["source"];blob=r["original_expected_git_blob"]
        guard(source not in names26 and blob not in blobs26,"DUPLICATE_26")
        names26[source]=r;blobs26.add(blob)
    internal=sum(r.get("gold_free_math_broker_solved_internal_only") is True for r in rows)
    conditional=sum(r.get("ablation_external_theorem_off_loses_accepted_classification") is True for r in rows)
    unknown=[r for r in rows if not r.get("gold_free_math_broker_certified")]
    guard((internal,conditional,len(unknown))==(20,3,3),"INCORRECT_26_CASE_BY_CASE")
    cases18=b["frozen_source_18_real_results"]
    guard(len(cases18)==18 and len({r["original_git_blob"] for r in cases18})==18,"DUPLICATE_18")
    guard(set(r["original_git_blob"] for r in cases18).isdisjoint(blobs26),"CROSS_CORPUS_REUSED_SOURCE")
    guard(len({r["source_path"] for r in cases18}|set(names26))==44,"CROSS_CORPUS_REUSED_PATH")
    labs=[r["final_source_mathematical_authority"] for r in cases18]
    guard(labs.count("ORIGINAL_FULL_SMT_SOLVER_FIRST_EXPERT")==13,"18_FIRST_SOLVED_MISMATCH")
    guard(labs.count("POSTHOC_INDEPENDENT_ORIGINAL_DUAL_CERTIFIED")==4,"18_DUAL_CERT_MISMATCH")
    guard(labs.count("POSTHOC_EXTERNAL_WINOGRAD_1971_THEOREM_CONDITIONAL")==1,"18_WINOGRAD_ONLY_CONDITIONAL")
    guard(b["cumulative_true_original_solver_or_original_dual_proven_SAT_UNSAT"]==17,"18_INTERNAL_COUNT")
    guard(b["some_initial_13_positive_source_outcomes_ONLY_SINGLE_original_solver_observation"] is True,"18_SINGLE_SOLVER_LIMIT")
    guard(b["Winograd_original_6product_to_rank7_external_theorem_not_machine_proven"] is True,"18_MACHINE_PROOF_FALSE")
    prior=c["source_genuine_original_checked"]
    guard(c["externally_retrieved_existing_public_witness_NOT_NEUMANN_created"] is True,"PRIOR_ANSWER_LAUNDERED")
    guard(c["not_authenticated_as_learner_hidden_structure_discovery"] is True,"PRIOR_MISATTRIBUTED_LEARNING")
    guard(prior["genuine_source_SHA_authenticated"] is True and prior["original_full_SMT2_independent_Z3_cvc5_SAT"] is True,"PRIOR_NOT_DUAL_CERTIFIED")
    guard(prior["status"]=="KNOWN_PUBLISHED_PRIOR_WITNESS_TRUE_ORIGINAL_SAT_DUAL","PRIOR_FALSE_STATUS")
    guard(prior["arbitrary_precision_integer_cubic_sum"]==367,"PUBLIC_WITNESS_MATH_FALSE")
    guard(prior["external_reference_witness_inference_has_privileged_answer"] is True,"PRIVILEGED_EXTERNAL_ORACLE_HIDDEN")
    known=[r for r in unknown if r["source"].endswith("/STC_0367.smt2") and r["original_expected_git_blob"]==PRIOR_SHA]
    guard(len(known)==1,"PRIOR_ANSWER_DOES_NOT_MATCH_ONE_OF_26_UNSOLVED_ORIGINALS")
    guard(not known[0]["gold_free_math_broker_certified"],"EXTERNAL_ANSWER_DOUBLE_COUNTED_AS_INTERNAL")
    guard(all(d.get("global_Q3")=="OPEN" and d.get("global_Q4")=="OPEN" for d in (a,b,c)),"FALSE_Q3_Q4_CLOSED") if "global_Q3" in b else guard(a["global_Q3"]==c["global_Q3"]=="OPEN" and b["full_original_unseen_model_Q3"]=="OPEN","FALSE_Q3")
    ledger={
     "schema":"neumann.q3.44_authentic_originals_five_distinct_authority_levels.v1",
     "original_evidence_runs":[39546097948,39546751137,39569042369],
     "distinct_original_source_count":44,
     "source_first_expert_or_internal_math_resolved":37,
     "previously_known_published_EXTERNAL_witness_verified_source_count":1,
     "EXTERNAL_published_theorem_conditional_count":4,
     "still_original_unresolved_count":2,
     "raw_generic_first_expert_on_26":8,
     "first_expert_on_other18":13,
     "not_matched_strong_math_specialist_advantage":True,
     "new_neural_training_calls":0,
     "all_Q1_to_Q7_global_status":"OPEN",
     "preopen_prior_source_exposure_recorded":True,
     "final_verdicts_26":[{"source":r["source"],"git_blob":r["original_expected_git_blob"],
       "status":("INTERNAL_SOURCE_PROVED" if r.get("gold_free_math_broker_solved_internal_only") else
         "EXTERNAL_PUBLISHED_THEOREM_CONDITIONAL" if r.get("ablation_external_theorem_off_loses_accepted_classification") else
         "EXTERNAL_CURATED_PUBLIC_SAT_WITNESS_DUAL" if r is known[0] else "UNKNOWN")}
       for r in rows],
     "final_verdicts_18":cases18
    }
    guard(ledger["source_first_expert_or_internal_math_resolved"]+ledger["previously_known_published_EXTERNAL_witness_verified_source_count"]+ledger["EXTERNAL_published_theorem_conditional_count"]+ledger["still_original_unresolved_count"]==44,"BROKEN_PARTITION")
    return ledger
def main():
    p=argparse.ArgumentParser()
    for k in ("q26","q18","prior","out"):p.add_argument("--"+k,required=True)
    x=p.parse_args()
    result=audit(load(x.q26,"q26"),load(x.q18,"q18"),load(x.prior,"prior"))
    Path(x.out).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3_CROSS_CORPUS_TRUE_SOURCE_ORIGINALS",result["distinct_original_source_count"])
    print("Q3_CROSS_CORPUS_INTERNAL_SOURCE_RESOLVED",result["source_first_expert_or_internal_math_resolved"])
    print("Q3_CROSS_CORPUS_EXTERNAL_PUBLISHED_CERTIFIED_SAT",result["previously_known_published_EXTERNAL_witness_verified_source_count"])
    print("Q3_CROSS_CORPUS_PUBLISHED_THEOREM_CONDITIONAL",result["EXTERNAL_published_theorem_conditional_count"])
    print("Q3_CROSS_CORPUS_GENUINELY_UNKNOWN",result["still_original_unresolved_count"])
    print("Q3_LEARNED_UNIQUE_GLOBAL_OPEN")
if __name__=="__main__":main()
