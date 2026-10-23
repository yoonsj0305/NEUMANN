"""Postgrade structural and cost audit on immutable FIRST seventh32 exact original.
Never modifies prediction/grade. Checks whether learned macro is functionally
outside prior arithmetic-only grammar, and full lifecycle CPU vs classical.
"""
import argparse,json,hashlib,pathlib,collections
import sympy as sp
from erbench_original_seventh import allowed_formula,calc,SYM
X=sp.Symbol("x")
LOCK={
"original":"d946d7de32edfad3740b0cba580323b80fa215349812b1b9e1f87eb6ceaacf07",
"source":"27f7111f8d751cbe0ad36eb0b58d75a58564346605cf65491ee92eab04d3a65e",
"pred":"13561690066b6d9f47471df5ae7d801fe5534c66ead03a3113a074e144cc34cb",
"grade":"6fbfdead8f4d5bbc9090d55c0e2bf8a453f9e2bfef742f7765940074822c3cf5"
}
def sig(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def run(a):
    for k in LOCK:assert sig(getattr(a,k))==LOCK[k],("MUTATED_FROZEN_ORIGINAL",k)
    p=json.loads(pathlib.Path(a.pred).read_text())
    t=json.loads(pathlib.Path(a.original).read_text())["private_true_equations"]
    g=json.loads(pathlib.Path(a.grade).read_text())
    assert len(t)==32
    studies={}
    for method,receipts in g["per_original_receipts"].items():
        studies[method]={row["id"]:row for row in receipts}
    categories=collections.Counter();correct=[]
    for v in t:
        node,var=allowed_formula(v["original_expression"])
        expr=calc(node,{var:X},SYM)
        # strict symbolic shape test: rational function of x
        try:cr=sp.cancel(sp.together(expr))
        except Exception:cr=expr
        rational=bool(cr.is_rational_function(X))
        categories["original_rational_function" if rational else "original_nonrational"]+=1
        rr={k:studies[k][v["id"]] for k in studies}
        if rr["D_learned_recursive_macro"]["original_truth"]=="FULL_AUTHOR_EXACT":
            examples=rr["D_learned_recursive_macro"]["new_named_macro_exact_matches"]
            correct.append({"id":v["id"],"task_ID":v["task_ID"],
                "category":"RATIONAL" if rational else "NONRATIONAL",
                "true_expression_sha256":hashlib.sha256(v["original_expression"].encode()).hexdigest(),
                "self_rewarded_learned_macro_definitions":examples,
                "present_in_complete_same_language":rr["A_full_recursive_4913"]["original_truth"]=="FULL_AUTHOR_EXACT",
                "present_in_random_same256":rr["C_uniform_same256"]["original_truth"]=="FULL_AUTHOR_EXACT"})
    tr=p["training"]
    methods=p["all_methods"]
    counters={"all":32,**dict(categories),
        "learned_exact_from_nonrational":sum(x["category"]=="NONRATIONAL" for x in correct),
        "learned_exact_from_rational":sum(x["category"]=="RATIONAL" for x in correct)}
    corpus=[{"method":k,"macro_candidates":v["source_cases_with_candidate"],
              "candidate_program_calls":v["total_AST_programs_tested"],
              "test_CPU_s":v["model_and_numeric_source_CPU_s"]} for k,v in methods.items()]
    known_training=float(tr["training_source_reward_cpu_s"])+float(tr["neural_training_cpu_s"])
    learned_total=known_training+methods["D_learned_recursive_macro"]["model_and_numeric_source_CPU_s"]
    classical=methods["A_full_recursive_4913"]["model_and_numeric_source_CPU_s"]
    result={"schema":"NEUMANN_Q3_FIRST_SEVENTH32_IMMUTABLE_AFTERGRADE_LANGUAGE_EXPRESSIVITY_AND_COST.v1",
     "original_SOURCES_ALL_SHA_LOCKED":LOCK,"first_original_task_count":32,
     "first_original_true_formula_categories":counters,
     "all_actual_learned_original_exact_macro_definitions":correct,
     "comparators":corpus,
     "training_source_reward_CPU_s":tr["training_source_reward_cpu_s"],
     "actual_neural_training_CPU_s":tr["neural_training_cpu_s"],
     "known_learning_plus_test_source_CPU_s":learned_total,
     "classical_complete_same_grammar_source_CPU_s":classical,
     "learning_to_classical_known_CPU_ratio":learned_total/classical,
     "unknown_lifecycle_overhead":"package_installs_and_source_numeric_data_prep_excluded",
     "note":"Original source author formulas are visible ONLY in this AFTERGRADED diagnostic; cannot tune seventh32 as pristine again",
     "human_predefined_sin_cos_exp_log_sqrt_semantics":True,
     "learned_macro_from_known_base_operations_is_NOT_new_atomic_semantics":True,
     "learned_exclusive_source_win_over_A":0,
     "Q3_global":"OPEN","G1":"HOLD"}
    dst=pathlib.Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3_SEVENTH32_IMMUTABLE_FIRST_SCORE_STRUCTURAL_COST_AUDIT",json.dumps({
     "receipt_sha256":sig(dst),"category_counts":counters,"exact_programs":correct,
     "known_train_plus_D_cpu":learned_total,"A_complete_cpu":classical},sort_keys=True),flush=True)
    assert len(correct)==2 and g["all_method_exact_originals"]["D_learned_recursive_macro"]["original_exact"]==2
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for k in LOCK:parser.add_argument("--"+k,required=True)
    parser.add_argument("--out",required=True)
    run(parser.parse_args())
