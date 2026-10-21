"""Official PR433 source-real eight immutable cost/proof audit.

No new training, no body view, no benchmark tuning, no false online routing.
Checks certified original triple VCs for learned, exact classical and PDR.
The portfolio union is **retrospective coverage**, NOT deployed optimized
online wall-time. We explicitly separate candidate fit/synthesis from
independent proof, syntax/setup, failed attempts and amortization.
"""
import argparse,hashlib,json
from pathlib import Path
SHA="24695f8d8fec77d90eada2475011ba40332bf36696d65c03bd3043e2f07b67cc"
def demand(cond,msg):
    if not cond:raise AssertionError(msg)
def verify_proof(p):
    demand(p is not None and p["exactly_full_source_3VC_proved"],"NOT_PROVED_CANDIDATE")
    rec=p["full_original_independent_Z3_cvc5_3VC"]
    demand(set(rec)=={"init","consecution","goal"},"MISSING_ACTUAL_ORIGINAL_3VC")
    demand(all(q["dual_pass"] for q in rec.values()),"INDEPENDENT_ORIGINAL_SOLVER_VETO")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    raw=Path(a.source).read_bytes()
    demand(hashlib.sha256(raw).hexdigest()==SHA,"OFFICIAL_RAW_JSON_SHA_CHANGED")
    j=json.loads(raw)
    demand(j["schema"]=="neumann.q3.posthoc_original8_Pre_plus_Trans_numeric_structure_ablated_v1","ORIGINAL_SOURCE_SCHEMA_CHANGED")
    demand(j["exact_original_sources_sha_verified"]==8,"NOT_8_SOURCE_ORIGINALS")
    rows=j["all_cases"]
    demand(len(rows)==8 and len({x["original_git_blob"] for x in rows})==8,"ORIGINAL_DUPLICATE")
    result=[];learn_fit_ms=0;trans_only_fit_ms=0;exact_synthesis_ms=0
    for row in rows:
        demand(row["status"]=="EXECUTED_REAL_EXTERNAL_ORIGINAL_ALL_METHODS","DROPPED_ORIGINAL_ERROR")
        demand(all(p["dual_pass"] for p in row["original_source_native_parity"].values()),"BAD_SOURCE_NATIVE_PARITY")
        ml=bool(row["learned_whole_program_safe"])
        exact=bool(row["classical_same_grammar_whole_program_safe"])
        spacer=bool(row["original_Z3_SPACER"]["certified"])
        sygus=bool(row["original_cvc5_SyGuS_2s"]["certified"])
        baseline_ablated=bool(row["transition_only_ablation_original_safe"])
        learned_evidence=[];exact_evidence=[];trans_evidence=[]
        candidates=row["source_generic_gradient_and_exact_classical_candidates"]
        for trial in candidates:
            learn_fit_ms+=trial["fitted_gradient_wall_ms"]
            trans_only_fit_ms+=trial["transition_only_model_ablation_fit_ms"]
            exact_synthesis_ms+=trial["classical_exact_synthesis_wall_ms"]
            for key,dst in (
               ("learned_candidate_original_proof",learned_evidence),
               ("classical_exact_original_proof",exact_evidence),
               ("transition_only_model_ablation",trans_evidence)):
                c=trial.get(key)
                if c and c["exactly_full_source_3VC_proved"]:
                    verify_proof(c);dst.append({"anchor":trial["anchor_index"],"degree":trial["max_basis_degree"],
                                               "candidate_AST":c["original_typed_compiled_AST"]})
        demand(ml==bool(learned_evidence),"LEARNED_HEADER_NOT_CERTIFIED")
        demand(exact==bool(exact_evidence),"EXACT_HEADER_NOT_CERTIFIED")
        demand(baseline_ablated==bool(trans_evidence),"KNOCKOUT_HEADER_NOT_CERTIFIED")
        if spacer:
            demand(any(x["certified"] and all(y["dual_pass"] for y in x["original_full_dual_3VC"].values())
                       for x in row["original_Z3_SPACER"]["original_independently_certified_candidates"]),
                   "SPACER_CANDIDATE_UNPROVEN")
        result.append({
            "source":row["source"],"original_git_blob":row["original_git_blob"],
            "learned_source_full_3VC":ml,"same_data_exact_source_full_3VC":exact,
            "original_SPACER_full_3VC":spacer,"original_cvc5_2s_full_3VC":sygus,
            "transition_only_learning_ablation_full_3VC":baseline_ablated,
            "combined_learned_plus_SPACER_retrospective_coverage":bool(ml or spacer),
            "combined_exact_plus_SPACER_retrospective_coverage":bool(exact or spacer),
            "learned_unique_not_recoverable_by_exact_or_SPACER":bool(ml and not exact and not spacer),
            "learned_original_verified_AST":learned_evidence,
            "matched_classical_verified_AST":exact_evidence,
            "all_source_path_wall_ms_including_all_methods":row["all_original_source_work_wall_ms"]})
    n=lambda k:sum(bool(x[k]) for x in result)
    demand(n("combined_learned_plus_SPACER_retrospective_coverage")==8,"LEARNED_PORTFOLIO_COVERAGE_NOT_8")
    demand(n("combined_exact_plus_SPACER_retrospective_coverage")==8,"CLASSICAL_PORTFOLIO_COVERAGE_NOT_8")
    demand(n("learned_unique_not_recoverable_by_exact_or_SPACER")==0,"ACTUAL_NEURAL_NOVELTY_EXISTS_RECHECK")
    report={
      "schema":"neumann.q3.real_external8_official_immutable_full_original_proof_cost_audit.v1",
      "official_action_run":39616621609,
      "official_raw_JSON_SHA256":SHA,
      "posthoc_after_failed_source_first_training_run":True,
      "external_genuine_originals":8,
      "source_native_verified_learned":n("learned_source_full_3VC"),
      "source_native_verified_matched_classical_exact":n("same_data_exact_source_full_3VC"),
      "source_native_verified_SPACER":n("original_SPACER_full_3VC"),
      "transition_only_model_knockout_source_full_3VC":n("transition_only_learning_ablation_full_3VC"),
      "retrospective_learned_plus_SPACER_coverage":n("combined_learned_plus_SPACER_retrospective_coverage"),
      "retrospective_EXACT_plus_SPACER_coverage":n("combined_exact_plus_SPACER_retrospective_coverage"),
      "source_native_learned_unique_over_exact_and_SPACER":n("learned_unique_not_recoverable_by_exact_or_SPACER"),
      "fitted_learned_coefficients_candidate_generation_wall_ms_sum":learn_fit_ms,
      "repeated_transition_only_learner_ablation_fit_wall_ms_sum":trans_only_fit_ms,
      "same_math_rational_classical_candidate_synthesis_wall_ms_sum":exact_synthesis_ms,
      "all_methods_original_parse_and_proof_wall_ms_sum":sum(q["all_source_path_wall_ms_including_all_methods"] for q in result),
      "retrospective_oracle_portfolio_is_NOT_actual_online_routed_runtime":True,
      "total_training_cost_and_amortization_NOT_MEASURED":True,
      "no_proof_of_learned_superiority_or_10x":True,
      "learned_unique_primitive_created":False,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "per_genuine_original":result}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("retrospective_learned_plus_SPACER_coverage",
              "retrospective_EXACT_plus_SPACER_coverage",
              "source_native_learned_unique_over_exact_and_SPACER",
              "fitted_learned_coefficients_candidate_generation_wall_ms_sum",
              "same_math_rational_classical_candidate_synthesis_wall_ms_sum"):
        print("Q3_REAL_ORIGINAL_CERTIFICATE_COST_AUDIT",k,report[k])
    print("Q3_GLOBAL_OPEN")
if __name__=="__main__":main()
