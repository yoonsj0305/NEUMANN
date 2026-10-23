"""Aftergrade ORIGINAL eighth32 evidence audit. Never opens target truth to inference.

The first native original exact predictions and grade are IMMUTABLE SHA-pinned.
Disambiguates "nested syntax" from truly NONRATIONAL mathematical novelty:
composition of exp and log may simplify to the same old affine function.
Also distinguishes learned genuine unique-vs-random/heuristic UNION.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_eighth import allowed_formula,calc,SYM
X=sp.Symbol("x")
LOCKS={
 "source":"90ccb67f27f2d951b4fa30bb583cfbf4a63fc5c90de0956a399a1361750e659b",
 "truth":"23c01a0ebaa93e4d8cf15abc15175e8bd11e9c738afd0683cfe6b986aece209f",
 "pred":"686bd782adf50caca46b6b41613cc9dc4e38dcf63d7c7f768d346ca75d4375eb",
 "grade":"14ea0bafd328a60e42f894180f58e107393d769b98cae77f02118b0616c6cacc"
}
def hash_file(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def audit(inp,out):
    for role,value in LOCKS.items():
        actual=hash_file(getattr(inp,role))
        assert actual==value,(role,actual,value)
    truth=json.loads(pathlib.Path(inp.truth).read_text())["private_true_equations"]
    score=json.loads(pathlib.Path(inp.grade).read_text())
    pred=json.loads(pathlib.Path(inp.pred).read_text())
    source=json.loads(pathlib.Path(inp.source).read_text())
    assert len(truth)==len(source["source_numeric_without_equations"])==32
    assert len(score["cases"])==4 and len(pred["methods"])==4
    count=collections.Counter()
    annotations=[]
    inds={}
    for key,records in score["cases"].items():
        inds[key]={r["id"] for r in records if r["status"]=="FULL_ORIGINAL_AUTHOR_SYMBOLICALLY_IDENTICAL"}
    learned=inds["learned_graph_edit_512"]
    union_c=inds["nolearn_random_512"]|inds["nolearn_simple_first_512"]
    comprehensive=inds["complete_3920_classical"]
    assert len(learned)==len(comprehensive)==2
    assert len(inds["nolearn_random_512"])==len(inds["nolearn_simple_first_512"])==1
    pred_lookup={k:{r["id"]:r for r in v["predictions"]} for k,v in pred["methods"].items()}
    grade_lookup={k:{r["id"]:r for r in v} for k,v in score["cases"].items()}
    for record in truth:
        ident=record["id"]
        try:
            node,name=allowed_formula(record["original_expression"])
            true=sp.cancel(sp.together(calc(node,{name:X},SYM)))
            nonrational=not true.is_rational_function(X)
            classification=("NONRATIONAL_AUTHOR_ORIGINAL" if nonrational else "RATIONAL_AUTHOR_ORIGINAL")
        except Exception as e:
            classification="UNKNOWN_SOURCE_EXACT_CATEGORY_"+type(e).__name__
            nonrational=False
        count[classification]+=1
        label={"id":ident,"collection":record["collection"],"task_ID":record["task_ID"],
               "original_expression_sha256":hashlib.sha256(record["original_expression"].encode()).hexdigest(),
               "original_symbolic_semantic_class":classification,
               "first_native_original_method_exact":{k:ident in z for k,z in inds.items()}}
        verified=grade_lookup["learned_graph_edit_512"][ident]["certified_exact_named_lambdas"]
        if verified:
            count["learned_exact"]+=1
            if nonrational:count["learned_genuine_nonlinear"]+=1
            exacts=[]
            classical_lambdas={q["named_lambda"] for q in
                pred_lookup["complete_3920_classical"][ident]["generated_macros"]}
            for cand in verified:
                assert cand["named_lambda"] in classical_lambdas,(
                    "MISSING_COMPLETE_SAME_GRAMMAR_CANDIDATE",ident,cand["named_lambda"])
                expr=sp.sympify(cand["named_lambda"].replace("lambda x: ",""),
                                  locals={"x":X})
                assert sp.simplify(expr-true)==0,("CORRUPT_FIRST_GRADE",ident)
                exacts.append({"lambda":cand["named_lambda"],
                    "actions":cand["action_graph_edits"],
                    "syntactically_two_nested_ops":cand["new_nested_macro_definition"],
                    "semantically_genuinely_nonrational":not expr.is_rational_function(X),
                    "reused_own_training_macro_graph":cand["reused_own_training_macro_graph"]})
                if cand["reused_own_training_macro_graph"]:
                    count["learned_exact_trained_macro_reused"]+=1
            label["learned_true_macro_definitions"]=exacts
        annotations.append(label)
    result={
        "schema":"NEUMANN_Q3_EIGHTH32_POSTGRADE_ORIGINAL_SEMANTICS_AND_COMPUTE.v1",
        "immutable_first_source_truth_prediction_grade_SHA256":LOCKS,
        "strictly_AFTER_GRADE_uses_author_truth":True,
        "full_32_originals_categories":dict(count),
        "all_original_rows":annotations,
        "first_orig_exact_methods":{key:sorted(z) for key,z in inds.items()},
        "learned_unique_original_vs_random":sorted(learned-inds["nolearn_random_512"]),
        "learned_unique_original_vs_fixed_heuristic":sorted(learned-inds["nolearn_simple_first_512"]),
        "learned_unique_original_vs_union_both_512_nonlearners":sorted(learned-union_c),
        "learned_unique_original_vs_complete_classical":sorted(learned-comprehensive),
        "known_neural_full_train_plus_test_CPU_s":(
           pred["training"]["verifier_source_train_CPU_s"]+
           pred["training"]["actual_MLP_fitting_CPU_s"]+
           pred["methods"]["learned_graph_edit_512"]["cpu_s"]),
        "same_rights_complete_classical_test_CPU_s":pred["methods"]["complete_3920_classical"]["cpu_s"],
        "same512_random_test_CPU_s":pred["methods"]["nolearn_random_512"]["cpu_s"],
        "same512_heuristic_test_CPU_s":pred["methods"]["nolearn_simple_first_512"]["cpu_s"],
        "bounded_same_512_number_of_attempts":True,
        "mathematical_nature":
            "Full class includes all learned graph paths: learned cannot discover an in-class function missing from full classical; only same-budget efficiency/priority can differ",
        "original_expressions_in_eval_source_no":True,
        "G1_neural_new_atomic_semantics":"NOT_PROVED",
        "Q3_global":"OPEN","Q4_full_cost_10x":"OPEN","Q6_external_independent_author_transfer":"OPEN"}
    dest=pathlib.Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    learned_verified_details=[]
    for a in annotations:
        if a.get("learned_true_macro_definitions"):
            original_row=next(v for v in truth if v["id"]==a["id"])
            expr_original=sp.cancel(sp.together(calc(allowed_formula(original_row["original_expression"])[0],
                                  {allowed_formula(original_row["original_expression"])[1]:X},SYM)))
            if expr_original.is_rational_function(X):
                num,den=sp.fraction(expr_original)
                try: is_affine=sp.degree(num,X)<=1 and sp.degree(den,X)==0
                except Exception: is_affine=False
            else: is_affine=False
            learned_verified_details.append({
                "id":a["id"],"task_ID":a["task_ID"],"category":a["original_symbolic_semantic_class"],
                "source_original_expression":str(expr_original),
                "original_function_is_affine":bool(is_affine),
                "certified_named_macros":a["learned_true_macro_definitions"]})
    print("Q3_EIGHTH_FIRST_VERIFIED_NAMED_MACRO_SEMANTIC_DETAILS",
          json.dumps(learned_verified_details,sort_keys=True),flush=True)
    print("Q3_EIGHTH_FIRST_FROZEN_AUTHOR_SEMANTIC_AUDIT",json.dumps({
       "categories":dict(count),
       "learned_originals":result["first_orig_exact_methods"]["learned_graph_edit_512"],
       "learned_unique_vs_nonlearn_union":result["learned_unique_original_vs_union_both_512_nonlearners"],
       "known_neural_cpu":result["known_neural_full_train_plus_test_CPU_s"],
       "classical_complete_cpu":result["same_rights_complete_classical_test_CPU_s"],
       "audit_SHA256":hash_file(dest)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for role in LOCKS:p.add_argument("--"+role,required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    audit(args,args.out)
