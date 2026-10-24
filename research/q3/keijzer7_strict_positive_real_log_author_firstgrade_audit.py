"""First source first gold whole-real-domain positive-log correction audit.

On first original Keijzer-7 ("log(x)") there may be real-domain symbol
identities the naïve SymPy unconstrained-complex symbolic equality rejects.
Do not re-select or change FIRST frozen model predictions. Prove positivity
of EVERY logarithm argument on x>0, combine whole expression via exact
multiplicative rational algebra, and prove equality for all positive real x.

First author source grid for Keijzer7 is positive; real valid benchmark
domain is x>0. Any AST without a fully machine-certified positive log
argument is categorically UNKNOWN, NOT rescued by force=True.

Original grade SHA persists. A corrected domain-aware forensic grade is
AFTER-GRADE and must NEVER be represented as FIRST predeclared blind score.
"""
import argparse,hashlib,json,pathlib,collections
import sympy as sp
LOCKS={
    "source":"e22b82e4cfb47fe605e1b049e01359d1752d7bbb26146d421faf08e71696ba32",
    "truth":"560843ae60804dc5356f1215687707f76908291bfb424210d35b9238d1f94580",
    "pred":"d6a0d41e5f58f50fbf563aa5d7aabe0e760bbaa63d473c5205b8f2f29bc327b0",
    "grade":"f3ad4c51c4ef35e576e56feebdb59d8b3ad4041e0acd99737edbe0a8025e8995"
}
def checksum(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def log_ratio(expr,x):
    # C = Σ n_i log(g_i(x)), n_i integer. Each g_i(x)>0 for x>0
    # is an independently necessary premise. Ratio=Π g_i**n_i
    # proves exp(C) exactly, then real-log injectivity establishes C=log(x).
    items=sp.Add.make_args(expr)
    ratio=sp.Integer(1);atoms=[]
    for term in items:
        coeff,rest=term.as_coeff_Mul()
        if not coeff.is_Integer or rest.func is not sp.log:
            return {"status":"UNKNOWN_NON_INTEGRAL_LOG_SUM","term":str(term)}
        g=sp.factor(rest.args[0])
        if g.is_positive is not True:
            return {"status":"UNKNOWN_ARG_NOT_PROVEN_POSITIVE","argument":str(g)}
        ratio*=g**coeff
        atoms.append({"argument":str(g),"integer_log_coefficient":str(coeff),
                      "positive_for_all_x_positive":True})
    return {"status":"ALL_REAL_LOG_ARGUMENTS_POSITIVE","ratio":str(sp.cancel(ratio)),
            "ratio_sym":sp.cancel(ratio),"log_atoms":atoms}
def main(a):
    for k,v in LOCKS.items():
        assert checksum(getattr(a,k))==v,(k,"ORIGINAL_FIRST_FOUR_ARTIFACTS_MUTATED")
    source=json.loads(pathlib.Path(a.source).read_text())["source_numeric_without_equations"]
    truth=json.loads(pathlib.Path(a.truth).read_text())["private_true_equations"]
    predictions=json.loads(pathlib.Path(a.pred).read_text())["methods"]
    first=json.loads(pathlib.Path(a.grade).read_text())
    dsource=next(r for r in source if r["task_ID"]=="Keijzer-7")
    gold=next(r for r in truth if r["task_ID"]=="Keijzer-7")
    assert dsource["id"]==gold["id"]
    assert min(dsource["fixed_author_train_domain"])>0
    x=sp.Symbol("x",positive=True,real=True)
    true=sp.sympify(gold["author_full_expression_sympy"],locals={"x":x})
    assert sp.simplify(true-sp.log(x))==0,("AUTHOR_NOT_LOG_X",str(true))
    assert len(dsource["x"])==len(dsource["y"])==48
    by_arm={}
    corrections={}
    for name,arm in predictions.items():
        proposal=next(r for r in arm["cases"] if r["id"]==gold["id"])
        first_result=next(r for r in first["all_original_cases"][name] if r["id"]==gold["id"])
        certified=[]
        rejected=[]
        for m in proposal["source_valid_defined_macros"]:
            h=sp.sympify(m["defined_operator_AST"],locals={"x":x})
            test=log_ratio(h,x)
            if test["status"]=="ALL_REAL_LOG_ARGUMENTS_POSITIVE" and sp.cancel(test["ratio_sym"]-x)==0:
                certified.append({"source_generated_expression":m["named_lambda"],
                    "all_log_atoms_proven_positive":test["log_atoms"],
                    "rational_multiplicative_ratio_exactly_x":True,
                    "whole_log_expression_exact_on_all_x_positive":True,
                    "first_action_origin":m.get("structural_action_family")})
            else:
                rejected.append({"lambda":m["named_lambda"],"why":test["status"]})
        by_arm[name]={
            "first_complex_unconstrained_symbolic_grade":first_result["status"],
            "source_original_candidate_count":len(proposal["source_valid_defined_macros"]),
            "strict_valid_all_real_positive_domain_log_proofs":certified,
            "unproved_or_non_log_candidates":rejected
        }
        corrections[name]=int(first_result["status"]=="UNKNOWN" and bool(certified))
    raw={k:v["author_full_exact"] for k,v in first["method_full_author_symbolic_exact"].items()}
    enhanced={k:raw[k]+corrections[k] for k in raw}
    result={
      "schema":"NEUMANN_Q3_KEIJZER7_STRICT_POSITIVE_REAL_DOMAIN_LOG_AUTHOR_CORRECTION.v1",
      "FIRST_all_source_truth_pred_and_first_grade_SHA256":LOCKS,
      "original_Keijzer7_author_task_ID":"Keijzer-7",
      "published_original_function_on_domain":str(true),
      "published_positive_real_training_domain":dsource["fixed_author_train_domain"],
      "positivity_premise_required_for_every_log_argument":True,
      "symbolic_log_identity_rule":"for every positive g_i and integer n_i, Σ n_i ln(g_i)=ln(Π g_i**n_i); if ratio equals x positive, equals ln(x)",
      "original_FIRST_grader_counts_UNCHANGED":raw,
      "strict_aftergrade_REAL_domain_corrected_counts":enhanced,
      "aftergrade_new_domain_certified_original_per_method":corrections,
      "first_pregrade_source_macro_witnesses":by_arm,
      "NO_CHANGE_TO_FIRST_SOURCE_CANDIDATE_MODEL_OR_WEIGHTS":True,
      "postgrade_label":"AFTERGOLD_FORENSIC_MATH_VERIFIER_CORRECTION_NOT_FIRST_BLIND_SCORE",
      "G1":"HOLD","Q3_global":"OPEN","Q4_10x":"NOT_PROVED"}
    path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3_ORIGINAL_KEIJZER7_REAL_DOMAIN_PROVEN_LOG_REPAIR_FIRST_OUTPUT_INTACT",
       json.dumps({"original_first_grade":raw,
         "corrected_real_domain_grade":enhanced,
         "new_entire_author_log_exact_per_method":corrections,
         "original_source_macros":{k:[p["source_generated_expression"] for p in q["strict_valid_all_real_positive_domain_log_proofs"]] for k,q in by_arm.items()},
         "SHA256":checksum(path)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in LOCKS:p.add_argument("--"+k,required=True)
    p.add_argument("--out",required=True)
    main(p.parse_args())
