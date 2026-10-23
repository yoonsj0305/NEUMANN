"""SHA-lock all first Livermore source, original truth, constructed candidates,
independent grade BEFORE classifying which external original families improved.

POSTGRADE diagnostic only. Never retunes, reorders, reruns source generator,
or presents opened author originals as future blind tasks.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
X=sp.Symbol("x")
LOCKS={
 "source":"8a73b34d3e4a02deb1037fd29eeeb6a66fcbbed344bcbbdd223481b5ba204a88",
 "truth":"2d5f91ce33fe400b3a8330cef255a4ff4b599a628316e46607ea23e5c2b8e34f",
 "pred":"bf3dc33fbfb475277e42af0415f765355007810b77e0a48cee401d5da584f625",
 "grade":"d34fa5b3580ddff103f591ab380ca660014ae21d9a59b07b0e6bb7ef43335527"}
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def inspect(a):
    for k,expected in LOCKS.items():
        actual=sha(getattr(a,k))
        assert actual==expected,(k,"FIRST_AUTHOR_SOURCE_RECEIPT_CHANGED",actual,expected)
    source=json.loads(pathlib.Path(a.source).read_text())
    original=json.loads(pathlib.Path(a.truth).read_text())
    pred=json.loads(pathlib.Path(a.pred).read_text())
    grade=json.loads(pathlib.Path(a.grade).read_text())
    truth={r["id"]:r for r in original["private_true_equations"]}
    assert len(truth)==len(source["source_numeric_without_equations"])==8
    methods=grade["methods"]
    assert methods["B_NEW_DYNAMIC_TYPED_AST_COMPOSITION"]["exact_author_function"]==4
    assert methods["C_OLD_SAFE_GRAPH_GRAMMAR"]["exact_author_function"]==0
    assert methods["C_RECURSIVE_POLYNOMIAL_ONLY"]["exact_author_function"]==2
    bymethod={k:{r["id"]:r for r in rows} for k,rows in grade["all_original_cases"].items()}
    observed=[]
    typecount=collections.Counter()
    for id,record in truth.items():
        true=sp.sympify(record["original_expression_sympy"],locals={"x":X})
        if true.is_polynomial(X):
            kind="POLYNOMIAL_DEGREE_"+str(sp.Poly(true,X).degree())
        elif true.is_rational_function(X):
            kind="RATIONAL_NONPOLYNOMIAL"
        else:kind="NONRATIONAL"
        typecount[kind]+=1
        row={"id":id,"name":record["task_ID"],
          "public_source_author_formula":record["original_expression"],
          "canonical_author_function":str(true),
          "author_mathematical_class":kind,
          "whole_original_exact_by_each_method":{
              m:bymethod[m][id]["true_full_analytic_author_equal"] for m in bymethod},
          "first_source_constructed_exact_executable_macro":(
              bymethod["B_NEW_DYNAMIC_TYPED_AST_COMPOSITION"][id]["source_only_created_macro"]
          )}
        if row["first_source_constructed_exact_executable_macro"]:
            program=row["first_source_constructed_exact_executable_macro"]
            constructed=sp.sympify(program["defined_operator_AST"],locals={"x":X})
            assert sp.simplify(true-constructed)==0,(
                  "MATH_IDENTICAL_FULL_AUTHOR_FORMULA_NOT_ACTUALLY_TRUE",record["task_ID"])
        observed.append(row)
    action=pred["methods"]
    report={"schema":"NEUMANN_Q3_FIRST_LIVERMORE_OTHER_AUTHOR_DYNAMIC_DAG_HEADROOM_AND_FULL_FUNCTION_EVIDENCE.v1",
      "immutable_FIRST_four_evidence_receipts_SHA256":LOCKS,
      "original_benchmark":"Livermore13/15/16/18/19/20/21/22 public DSO corpus",
      "original_class_distribution":dict(typecount),
      "all_eight_public_original_cases_after_only_first_grade":observed,
      "native_full_author_mathematical_exact_grades":methods,
      "measured_source_CPU_s":{k:v["cpu_process_s"] for k,v in action.items()},
      "numeric_verifier_calls":{k:v["source_work"]["source_calls"] for k,v in action.items()},
      "actually_constructed_graph_nodes":{k:v["source_work"]["constructed_graph_nodes"] for k,v in action.items()},
      "new_dynamic_grammar_beyond_old_safe_originals_count":4,
      "all_original_cases_registered_and_no_retuning":True,
      "truth_not_available_to_first_source_program_job":True,
      "new_AST_semantics_human_given":True,
      "model_learned_graph_edit_policy":"NO",
      "G0_REPRESENTATION_SPACE_HEADROOM":"SCOPED_PASS_4_8_VS_OLD_0_8",
      "G1":"HOLD","Q3_GLOBAL":"OPEN","Q4_TOTAL_10X":"NOT_PROVED"}
    path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_LIVERMORE_FIRST_SOURCE_SHA_LOCKED_ORIGINAL_MACROS_AND_REAL_FUNCTION_HEADROOM",
          json.dumps({"sha256":sha(path),"counts":dict(typecount),
           "each":[{"author":z["name"],"true":z["canonical_author_function"],
            "new_exact":z["whole_original_exact_by_each_method"]["B_NEW_DYNAMIC_TYPED_AST_COMPOSITION"],
            "old_exact":z["whole_original_exact_by_each_method"]["C_OLD_SAFE_GRAPH_GRAMMAR"],
            "source_generated":(z["first_source_constructed_exact_executable_macro"] or {}).get("named_lambda")
            } for z in observed]},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in LOCKS:p.add_argument("--"+key,required=True)
    p.add_argument("--out",required=True)
    inspect(p.parse_args())
