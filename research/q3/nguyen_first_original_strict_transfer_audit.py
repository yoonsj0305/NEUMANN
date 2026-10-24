"""Independent FIRST Nguyen author family transfer proof audit.

Strictly checks all original FIRST SOURCE, GRADE and learned pregrade sha256
before any label-specific or case-specific analysis. This is AFTERGRADE.
Does not retune original model, redefine model weights, or reopen task sample.
Separates a genuine repeated prior-model two exact other-author originals
from neural-only wins (=0) and all-in resource costs.
"""
import argparse,hashlib,json,pathlib,collections
import sympy as sp
from erbench_original_eleventh import allowed_formula,calc,SYM

X=sp.Symbol("x")
SHA={
    "source":"4261350718c641ac0575e5d0a165a09fd02a5ba8aaa9eb5014fc82341bcbea10",
    "truth":"b4971e75b238b7525da34aab4bd4f7b7162f56a381a91e6fe667d9c651adeaaf",
    "pred":"f2d9626f0c27f3343e597e30ef6d4c3e6ed86bd107924038dd78dccc141444e9",
    "grade":"bbd4efc0f6b7f2127400d5f1d0a89bc739c133fa7545859c4a6ad61c07236fc1",
}
FROZEN="f5ce5e9ef0f53c1289a747ca72aa5f41f34c58c4b1de8848728342af3ca3fc26"
def checksum(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def audit(args):
    for k,expected in SHA.items():
        actual=checksum(getattr(args,k))
        assert actual==expected,(k,"FIRST_VERDICTS_CANNOT_BE_MODIFIED",actual,expected)
    source=json.loads(pathlib.Path(args.source).read_text())
    truth=json.loads(pathlib.Path(args.truth).read_text())
    pred=json.loads(pathlib.Path(args.pred).read_text())
    grade=json.loads(pathlib.Path(args.grade).read_text())
    assert len(source["source_numeric_without_equations"])==len(truth["private_true_equations"])==8
    assert pred["frozen_prior_weights_sha256"]==pred["current_exact_weights_sha256"]==FROZEN
    assert pred["same_prior_model_weights_AND_REWARD_TRACE"]
    methods=pred["methods"]
    assert len(methods)==5
    first={k:{r["id"]:r for r in v} for k,v in grade["all8_original_cases"].items()}
    solved={k:{id for id,row in v.items() if row["full_symbolic_original_exact"]} for k,v in first.items()}
    assert len(solved["D_learned_derived_power_top2"])==2
    assert len(solved["C_safe_add_rational"])==len(solved["A_full_same_actions"])==3
    assert len(solved["C_random_two"])==3
    assert len(solved["C_untrained_power_one_and_two"])==0
    per_case=[];types=collections.Counter()
    per_method={}
    for name,method in methods.items():
        calls=sum(z["source_verifier_calls"] for z in method["cases"])
        counts=collections.Counter()
        for row in method["cases"]:
            counts.update(row["graph_actions"])
        per_method[name]={
          "full_analytic_author_matched":len(solved[name]),
          "source_numeric_confirmed_programs":method["source_counts"].get("source_proposals",0),
          "source_only_oracle_calls":calls,
          "evaluated_graph_actions":dict(counts),
          "candidate_inference_CPU_s":method["inference_CPU_s"]}
    for item in truth["private_true_equations"]:
        name=item["task_ID"]
        assert item["collection"]=="Nguyen2021Benchmark"
        t,v=allowed_formula(item["original_expression"])
        expr=sp.cancel(sp.together(calc(t,{v:X},SYM)))
        typ="NONRATIONAL" if not expr.is_rational_function(X) else "RATIONAL"
        if expr.is_polynomial(X):
            typ="POLYNOMIAL"
            degree=int(sp.Poly(expr,X).degree())
        else:degree=None
        types[typ]+=1
        learned=first["D_learned_derived_power_top2"][item["id"]]
        if learned["full_symbolic_original_exact"]:
            assert len(learned["verified_original_programs"])>0
            for p in learned["verified_original_programs"]:
                candidate=sp.sympify(p["named_lambda"].removeprefix("lambda x: "),locals={"x":X})
                assert sp.simplify(expr-candidate)==0,(name,"FIRST_ORIGINAL_PROOF_INVALID")
        per_case.append({
          "benchmark_problem":name,
          "original_equation":item["original_expression"],
          "original_type":typ,"polynomial_degree":degree,
          "authored_original_mathematically_exact_by_each_method":{k:item["id"] in v for k,v in solved.items()},
          "learned_source_selected_actions":next(r["graph_actions"] for r in methods["D_learned_derived_power_top2"]["cases"] if r["id"]==item["id"]),
          "learned_first_source_constructed_exact_expression":[p["named_lambda"] for p in learned["verified_original_programs"]],
        })
    learning=solved["D_learned_derived_power_top2"]
    strong=solved["A_full_same_actions"]
    fixed=solved["C_safe_add_rational"]
    r={
      "schema":"NEUMANN_Q6_FIRST_NGUYEN_AUTHOR_FAMILY_ORIGINAL_FROZEN_WEIGHTS_AND_LIMITS_AUDIT.v1",
      "all_first_source_model_gold_verifier_SHA256":SHA,
      "frozen_first_prior_model_weights_SHA256":FROZEN,
      "other_author_family":"PUBLIC Nguyen1-8 symbolic-regression benchmark; 48 noiseless source samples per equation",
      "not_original_official_nguyen_benchmark_protocol":True,
      "per_original_equation":per_case,
      "original_family_math_categories":dict(types),
      "method_original_mathematical_exact_and_computation":per_method,
      "learned_exclusive_versus_full_same_rights":sorted(learning-strong),
      "learner_EXACT_originals_lost_to_simple_safe":sorted(fixed-learning),
      "successful_cross_author_transfer_original_count":len(learning),
      "trained_model_weights_identical_to_prior_replayed":True,
      "numerical_training_data_and_reward_trace_and_memory_SHA_identical":True,
      "frozen_weight_match_succeeded_on_third_job_run":True,
      "two_prior_failed_bitwise_replays_held_as_failures":True,
      "independent_research_author_group_from_train":True,
      "improvements_over_classical_same_rights":"NONE",
      "G1":"HOLD","Q3_GLOBAL":"OPEN",
      "Q6_BASIC_CROSS_AUTHOR_WEIGHTED_TRANSFER":"SCOPED_PASS_2_OF_8",
      "Q6_STRONG_GENERALIZATION":"NOT_PROVED",
      "Q4_FRONTIER_10X":"NOT_PROVED",
    }
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("Q6_FIRST_NGUYEN8_ORIGINALS_SHA_LOCKED_LEARNED_VS_CLASSICAL_REAL_TRANSFER_AUDIT",
          json.dumps({"per_original":[{"name":x["benchmark_problem"],
             "learned":x["authored_original_mathematically_exact_by_each_method"]["D_learned_derived_power_top2"],
             "safe":x["authored_original_mathematically_exact_by_each_method"]["C_safe_add_rational"],
             "classic":x["authored_original_mathematically_exact_by_each_method"]["A_full_same_actions"]}
             for x in per_case],
             "source_type_counts":dict(types),
             "method_CPU_and_math_calls":per_method,
             "SHA256":checksum(out)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in SHA:p.add_argument("--"+key,required=True)
    p.add_argument("--out",required=True)
    audit(p.parse_args())
