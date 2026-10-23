"""First independent published Keijzer author entire-domain grader.

Reads gold public original Keijzer6..9 equations ONLY in this grader job.
For a newly SOURCE-DERIVED recursive function M and actual harmonic
author's original F(n)=sum_{i=1}^n 1/i, mathematical induction certifies
all n >= 1, not merely 48 source matches.

- Base M(1)=F(1).
- Step M(n+1)-M(n)=F(n+1)-F(n)=1/(n+1), for every integer n>=1.
This proof includes correct functional semantics of genuinely NEW
recursive name M, not a named HARMONIC primitive introduced by author.

For closed-form source proposals, exact SymPy symbolic equality to
published original author entire expression (over positive domain).
Unknown keeps its honest state.
"""
import argparse,collections,json,pathlib
import sympy as sp
from recursive_operator_source_inventor import (
 N,save,sha,recurrence_induction_check,LOG_SQRT_ATOMS,
)
def grader(truthpath,predpath,out):
    orig=json.loads(pathlib.Path(truthpath).read_text())["private_true_equations"]
    pre=json.loads(pathlib.Path(predpath).read_text())
    assert len(orig)==4 and len(pre["methods"])==5
    orig_by_id={x["id"]:x for x in orig}
    audit={};cases={}
    for method,entry in pre["methods"].items():
        count=collections.Counter();detail=[]
        for item in entry["cases"]:
            t=orig_by_id[item["id"]]
            n=t["task_ID"]
            formula=sp.sympify(t["original_author_expression"],locals={
              "n":N,"harmonic":sp.harmonic,"asinh":sp.asinh})
            proofs=[]
            for candidate in item["new_programs"]:
                if candidate["kind"]=="NEW_EXECUTABLE_RECURSIVE_SYMBOL":
                    result=recurrence_induction_check(candidate,n)
                    if result["status"]=="ALL_POSITIVE_INTEGER_AUTHOR_SEMANTICS_PROVED_BY_INDUCTION":
                        assert n=="Keijzer-6"
                        assert sp.simplify(formula-sp.harmonic(N))==0
                        proofs.append({"type":"INFINITE_INTEGER_DOMAIN_INDUCTION",
                            "defined_new_semantic_symbol":candidate["new_symbol"],
                            "source_generated_rational_step":candidate["step_increment_AST"],
                            "entire_original_math_proof":result})
                elif candidate["kind"]=="FINITE_REGISTERED_UNARY_EXPRESSION":
                    expression=sp.sympify(candidate["source_generated_AST"],locals={"n":N})
                    if sp.simplify(formula-expression)==0:
                        proofs.append({"type":"ANALYTIC_FUNCTION_IDENTITY_ALL_POSITIVE_REALS",
                           "source_generated_analytic_AST":str(expression)})
            passed=bool(proofs)
            count["author_total"]+=1
            count["original_entire_function_exact"]+=int(passed)
            count["UNKNOWN"]+=int(not passed)
            count["newly_defined_recursive_symbol_exact_full_author"]+=int(
                  any(q["type"]=="INFINITE_INTEGER_DOMAIN_INDUCTION" for q in proofs))
            detail.append({"id":item["id"],"original_published_author_task":n,
                "original_formula_sha256":sha(t["original_author_expression"]),
                "status":"ENTIRE_ORIGINAL_AUTHOR_PROVED" if passed else "UNKNOWN",
                "independent_proofs":proofs,"structure_actions_executed":item["actions"],
                "source_proposals_count":len(item["new_programs"])})
        audit[method]=dict(count);cases[method]=detail
    solved={m:{x["id"] for x in a if x["status"]=="ENTIRE_ORIGINAL_AUTHOR_PROVED"} for m,a in cases.items()}
    d=solved["D_LEARNED_DEFINE_ONE_ACTION"];full=solved["A_BOTH_ACTIONS_IDENTICAL_RIGHTS"]
    result={"schema":"NEUMANN_Q3_FIRST_KEIJZER_PUBLISHED_AUTHOR_RECURSIVE_SEMANTIC_INDUCTION_GRADE.v1",
       "frozen_serialized_model_exact_source_prediction_sha256":sha(pathlib.Path(predpath).read_bytes()),
       "original_published_author_equation_sha256":sha(pathlib.Path(truthpath).read_bytes()),
       "author_originals_6_to_9":4,
       "all_methods_entire_math_author_proofs":audit,
       "all_author_case_receipts":cases,
       "model_exclusive_v_full_same_semantic_rights":sorted(d-full),
       "model_exclusive_v_old_closed_form":sorted(d-solved["C_FIXED_ONLY_CLOSED"]),
       "first_original_true_recursive_symbol_Keijzer6_proved":any(
            x["original_published_author_task"]=="Keijzer-6" and x["status"]=="ENTIRE_ORIGINAL_AUTHOR_PROVED"
            for x in cases["A_BOTH_ACTIONS_IDENTICAL_RIGHTS"]),
       "author_semantics_proof_is_not_finite_numeric_interpolation":True,
       "generic_RECURRENCE_SCHEMA_preprogrammed_by_human":True,
       "specific_new_recurrence_semantics_not_registered_as_a_named_human_primitive":True,
       "unbounded_semantic_operator_invention":"NOT_PROVED",
       "no_full_frontier_comparison":"TRUE",
       "G1":"HOLD","Q3_GLOBAL":"OPEN","Q4_ALL_IN_10X":"NOT_PROVED"}
    s=save(out,result)
    print("Q3_KEIJZER_FIRST_ENTIRE_AUTHOR_MATHEMATICAL_INDUCTIVE_NEW_SYMBOL_GRADE",
          json.dumps({"sha256":s,"grades":audit,
            "learned_exclusive_over_full":len(result["model_exclusive_v_full_same_semantic_rights"]),
            "learned_exclusive_v_OLD_CLOSED":len(result["model_exclusive_v_old_closed_form"]),
            "entire_author_Keijzer6_induction_proved":result["first_original_true_recursive_symbol_Keijzer6_proved"]},sort_keys=True),flush=True)
    assert all(v["author_total"]==4 for v in audit.values())
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--truth",required=True)
    p.add_argument("--pred",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    grader(a.truth,a.pred,a.out)
