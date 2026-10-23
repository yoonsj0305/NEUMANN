"""Postgrade immutable Ninth32 authentic original functional algebraic audit.

Never revises first source macro outputs or matches. All input SHA receipts
from run 39923380389 are verified before original author true formulas read.
Proof-carrying separate classification of GENUINE nonrational and nonaffine
target functions, versus mere syntactic two-term branch output.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_ninth import allowed_formula,calc,SYM
X=sp.Symbol('x')
EXPECTED={
 "source":"3640eeb5b460746b0d96dbc0b448a563d5810ee630e88c9aa28d6b4803d73efd",
 "truth":"70177035c01d16a7c0ed0da003ee3049bc3d605ea282a16bf927ba22a80206e1",
 "pred":"d00edb5e3ecb019286f8c18dc2f660613e20315854e966f7f1bc222251b147de",
 "grade":"9f4235b00a706db6edeb4232bc51c03290f6d2439b75f54c1f7a2125d02accc7"}
def checksum(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def classify(expr):
    try:
        f=sp.cancel(sp.together(expr))
        if not f.is_rational_function(X):return "NONRATIONAL_FULL_ORIGINAL_FUNCTION",None
        p,q=sp.fraction(f)
        pn,pq=sp.Poly(p,X),sp.Poly(q,X)
        if not all(v.is_Rational for v in list(pn.all_coeffs())+list(pq.all_coeffs())):
            return "RATIONAL_NON_Q_COEFFICIENTS",None
        d=(int(pn.degree()),int(pq.degree()))
        if d[0]<=1 and d[1]==0:return "AFFINE_RATIONAL_ORIGINAL",d
        return "NONAFFINE_RATIONAL_ORIGINAL",d
    except Exception as e:return "UNKNOWN_CLASSIFICATION_"+type(e).__name__,None
def main(a):
    for k,expected in EXPECTED.items():
        got=checksum(getattr(a,k))
        assert got==expected,(k,"IMMUTABLE_FIRST_ORIGINAL_SHA_CHANGED",got,expected)
    source=json.loads(pathlib.Path(a.source).read_text())["source_numeric_without_equations"]
    truth=json.loads(pathlib.Path(a.truth).read_text())["private_true_equations"]
    grade=json.loads(pathlib.Path(a.grade).read_text())
    prediction=json.loads(pathlib.Path(a.pred).read_text())
    assert len(source)==len(truth)==32
    first={k:{r["id"]:r for r in v} for k,v in grade["cases"].items()}
    methods=sorted(first)
    original_exact_ids={k:{r["id"] for r in v.values() if r["status"]=="FULL_AUTHOR_ORIGINAL_EXACT"} for k,v in first.items()}
    learner=original_exact_ids["D_learned_macro_top80"]
    assert all(len(ids)==5 for ids in original_exact_ids.values())
    assert len(learner)==5
    totals=collections.Counter();cases=[]
    for row in truth:
        id=row["id"]
        try:
            node,var=allowed_formula(row["original_expression"])
            expression=calc(node,{var:X},SYM)
            cls,degrees=classify(expression)
        except Exception as e:cls,degrees="UNKNOWN_AUTHOR_EXPR_"+type(e).__name__,None
        totals["all"]+=1;totals[cls]+=1
        exact=first["D_learned_macro_top80"][id]["certified_named_macros"]
        if exact:
            totals["learned_exact_total"]+=1
            totals["learned_exact_"+cls]+=1
        report={
           "id":id,"collection":row["collection"],"task_ID":row["task_ID"],
           "author_formula_SHA256":hashlib.sha256(row["original_expression"].encode()).hexdigest(),
           "mathematical_author_original_category":cls,
           "author_rational_numerator_denominator_degrees":degrees,
           "original_exact_grade":{k:id in v for k,v in original_exact_ids.items()},
           "learned_certified_named_macro_expressions":[v["named_lambda"] for v in exact],
           "learned_certified_two_branch_MACROS":
               sum(v["new_macro_definition_with_two_terms"] for v in exact),
           "learned_certified_nonrational_base_branch_macros":
               sum(v["contains_nonlinear_primitive"] for v in exact)}
        cases.append(report)
    complete={k:sorted(v) for k,v in original_exact_ids.items()}
    costs={k:v["cpu_s"] for k,v in prediction["Arms"].items()}
    learner_cpu=costs["D_learned_macro_top80"]
    train=prediction["training"]
    fullknown=learner_cpu+train["train_reward_verifier_cpu_s"]+train["neural_fit_cpu_s"]
    result={
      "schema":"NEUMANN_Q3_FIRST_NINTH32_SHA_LOCKED_POSTGRADE_TRUE_EXPRESSION_CATEGORIES.v1",
      "first_run_SHA_LOCKS":EXPECTED,
      "all_32_true_original_mathematical_categories":dict(totals),
      "all_first_original_cases":cases,
      "all_method_exact_original_ids":complete,
      "learned_only_over_union_four_classical":sorted(
          learner-set.union(*(ids for k,ids in original_exact_ids.items() if k!="D_learned_macro_top80"))),
      "known_training_learner_plus_test_CPU_s":fullknown,
      "method_eval_CPU_s":costs,
      "strong_baseline_annotation":"All-basis greedy OMP is NOT exhaustive 2-term synthesis nor external PySR/Operon",
      "numerically_rewarded_103_training_macros_are_NOT_independently_author_exact_grade":True,
      "no_new_author_orig_pred_after_true_label_exposure":True,
      "Q3_learned_atomic_new_semantics":"UNPROVED",
      "G1":"HOLD","Q4_all_in_10x":"UNPROVED"}
    path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3_FIRST_NINTH32_TRUE_ORIGINAL_MATH_CLASS_POSTGRADE_AUDIT",
        json.dumps({"counts":dict(totals),
           "known_train_and_eval_cpu":fullknown,
           "exact5_learner_ids":complete["D_learned_macro_top80"],
           "new_exclusive":len(result["learned_only_over_union_four_classical"]),
           "sha256":checksum(path)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in EXPECTED:p.add_argument("--"+k,required=True)
    p.add_argument("--out",required=True)
    main(p.parse_args())
