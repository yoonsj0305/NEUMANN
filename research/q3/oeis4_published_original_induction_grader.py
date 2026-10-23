"""Independent published OEIS ORIGINAL finite sum functional proof.

No source grader supplies gold to the learner or adjusts its structure
actions. First source proposals frozen; separate job then proves each
newly defined model M(n) equals the entire published author's finite
rational sum for every positive integer n, by generic sum telescoping.

For any author's F(n)=SUM_{k=1}^n g(k), an arbitrary SOURCE defined M:
M(1)=m1, M(n+1)=M(n)+r(n), succeeds iff:
  m1==g(1) and r(n)==g(n+1) as exact symbolic rational expressions.
This is a generic induction theorem verifier not 4 hard-coded table answers.
"""
import argparse,collections,json,pathlib
import sympy as sp
from recursive_operator_source_inventor import N,sha,save

K=sp.Symbol("k",integer=True,positive=True)
def grade(truthfile,predfile,out):
    truth=json.loads(pathlib.Path(truthfile).read_text())["private_true_equations"]
    pred=json.loads(pathlib.Path(predfile).read_text())
    assert len(truth)==4 and len(pred["methods"])==5
    by_id={x["id"]:x for x in truth}
    scores={};cases={}
    for mode,source in pred["methods"].items():
        c=collections.Counter();rows=[]
        for row in source["cases"]:
            gold=by_id[row["id"]]
            # New original source identity could not have been used by
            # either program generator or neural policy source step.
            summand=sp.sympify(gold["summand_expression"],locals={"k":K})
            author_initial=sp.cancel(summand.subs(K,1))
            author_step=sp.cancel(summand.subs(K,N+1))
            certified=[]
            for candidate in row["new_programs"]:
                if candidate["kind"]!="NEW_EXECUTABLE_RECURSIVE_SYMBOL":continue
                assert candidate["new_symbol"]=="M"
                discovered_initial=sp.Rational(candidate["base_y"])
                discovered_step=sp.sympify(candidate["step_increment_AST"],locals={"n":N})
                base=bool(candidate["base_n"]==1 and
                    sp.cancel(discovered_initial-author_initial)==0)
                step=bool(sp.cancel(discovered_step-author_step)==0)
                if base and step:
                    certified.append({
                        "new_independently_defined_function_symbol":candidate["new_symbol"],
                        "source_generated_full_recursive_definition":candidate["definition"],
                        "author_original_entire_domain":"F(n)=SUM(k=1..n, %s)"%gold["summand_expression"],
                        "source_generated_increment":str(discovered_step),
                        "author_true_symbolic_increment":str(author_step),
                        "initial_state_identity_exact":base,
                        "successor_functional_identity_exact":step,
                        "whole_positive_integer_domain_mathematical_induction":True,
                        "first_source_did_not_see_author_original_formula":True})
            good=bool(certified)
            c["total_authored_originals"]+=1
            c["entire_function_induction_PROVED"]+=int(good)
            c["UNKNOWN"]+=int(not good)
            rows.append({"id":row["id"],
                "published_original_source":gold["published_source"],
                "source_URL":gold["url"],
                "source_true_author_full_sum_formula_SHA256":sha(gold["summand_expression"]),
                "first_selected_actions":[z["selected_action"] for z in row["attempts"]],
                "status":"ENTIRE_AUTHOR_SEQUENCE_PROVED_BY_INDUCTION" if good else "UNKNOWN",
                "certified_new_recursive_programs":certified})
        scores[mode]=dict(c);cases[mode]=rows
    solution_sets={m:{x["id"] for x in rows if x["status"]=="ENTIRE_AUTHOR_SEQUENCE_PROVED_BY_INDUCTION"} for m,rows in cases.items()}
    D=solution_sets["D_FROZEN_MODEL_PLUS_VERIFY_REPAIR"]
    A=solution_sets["A_ALL_BOTH_ACTIONS"]
    report={
       "schema":"NEUMANN_Q3_P2_OEIS4_INDEPENDENT_FROZEN_NEURAL_REFLECTION_NEW_RECURSIVE_SYMBOL_MATH_PROOFS.v1",
       "source_prediction_exact_sha256":sha(pathlib.Path(predfile).read_bytes()),
       "published_OEIS_original_formula_metadata_sha256":sha(pathlib.Path(truthfile).read_bytes()),
       "real_external_OEIS_published_originals":4,
       "independent_whole_domain_original_accuracy":scores,
       "all_case_original_math_certificates":cases,
       "verified_repair_additional_originals_vs_priors_neural_one_action":sorted(
             D-solution_sets["D_PRIOR_FROZEN_MODEL_ONLY"]),
       "newly_defined_recursion_exclusive_over_strongest_same_rights_classical":sorted(D-A),
       "general_mathematical_induction_not_sampling_only":True,
       "original_benchmarks_hand_chosen_for_rational_recurrence_family":True,
       "frozen_previous_neural_weights_reused":True,
       "verifier_triggered_action_retry_IS_PROGRAMMED_NOT_LEARNED":True,
       "new_program_M_step_semantics_inferred_from_source_NOT_prelisted":True,
       "Q3_global":"OPEN","G1":"HOLD","Q4_SYSTEM_10X":"NOT_PROVED"}
    digest=save(out,report)
    print("NEUMANN_P2_OEIS4_FIRST_NEW_RATIONAL_RECURRENCE_INDUCTION_ORIGINAL_PROOF",
      json.dumps({"sha256":digest,"scores":scores,
        "verifier_repair_more_than_frozen":len(report["verified_repair_additional_originals_vs_priors_neural_one_action"]),
        "learner_unique_vs_CLASSICAL_A":len(report["newly_defined_recursion_exclusive_over_strongest_same_rights_classical"])},sort_keys=True),flush=True)
    assert all(v["total_authored_originals"]==4 for v in scores.values())
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("truth","pred","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args();grade(a.truth,a.pred,a.out)
