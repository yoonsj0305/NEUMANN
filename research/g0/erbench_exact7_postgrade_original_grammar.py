"""Post-grade native mathematical audit of FIRST frozen ERBench fourth32.

NEVER revises previously sealed original input, 7-point predictions or answers.
Checks an especially important scientific invariant:
if the full author function belongs to the exact P4/Q2 grammar and has no
singularity at the probes, 7 sample theorem guarantees its equality to any
other P4/Q2 interpolation candidate.
"""
import argparse,collections,hashlib,json,pathlib,ast
import sympy as sp
from erbench_original_second import allowed_formula,calc,SYM

X=sp.Symbol("x")
SHA={
"private":"8f7bd5ed2ca2cd9c8c39e72f6a2ad830b409815d2fb7c522c820874fd56875e1",
"pred":"03eb04ca69d2630f46f122af9e26bdb73701d32f2b893e04b0a25a3de9dc3e07",
"grade":"fa22a50316b5f33ea2716048998c3d53fb6c75b296c3fd88c1634545372d9a99"}
def digest(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def grammar(original_expr):
    try:
        node,var=allowed_formula(original_expr)
        f=sp.cancel(sp.together(calc(node,{var:X},SYM)))
        if not f.is_rational_function(X):
            return {"class":"OUTSIDE_RATIONAL_FUNCTION_CLASS"}
        num,den=sp.fraction(f)
        npoly=sp.Poly(num,X);dpoly=sp.Poly(den,X)
        if not (all(c.is_Rational for c in npoly.all_coeffs()) and
                all(c.is_Rational for c in dpoly.all_coeffs())):
            return {"class":"OUTSIDE_Q_COEFFICIENT_CLASS"}
        n=int(npoly.degree());m=int(dpoly.degree())
        return {"class":("INSIDE_EXACT_P4_Q2" if n<=4 and m<=2 else
                         "OUTSIDE_P4_Q2_DEGREE"),
                "numerator_degree":n,"denominator_degree":m}
    except Exception as e:
        return {"class":"UNKNOWN_CANNOT_CLASSIFY_ORIGINAL",
                "reason":type(e).__name__+":"+str(e)[:120]}
def main(a):
    for role in SHA:
        assert digest(getattr(a,role))==SHA[role],role+"_FIRST_RUN_HASH_MISMATCH"
    gt=json.loads(pathlib.Path(a.private).read_text())["originals"]
    pp=json.loads(pathlib.Path(a.pred).read_text())["all_32_source_programs"]
    gg=json.loads(pathlib.Path(a.grade).read_text())["rows"]
    assert len(gt)==len(pp)==len(gg)==32
    pred={r["id"]:r for r in pp};grade={r["id"]:r for r in gg}
    totals=collections.Counter();out=[]
    for orig in gt:
        oid=orig["id"];p=pred[oid];g=grade[oid]
        kind=grammar(orig["original_expr"])
        actual=g["original_grade"]
        totals[kind["class"]]+=1
        totals["all"]+=1
        if actual=="FULL_ORIGINAL_SYMBOLICALLY_EQUIVALENT":totals["original_exact"]+=1
        elif actual=="NOT_ORIGINAL_EQUAL_REJECTED":totals["original_rejected"]+=1
        elif actual=="UNKNOWN_ABSTAIN":totals["abstain"]+=1
        else:totals["unsupported"]+=1
        # The strong condition is theoretical and must be reflected empirically:
        if p["status"]=="SEVEN_POINT_CONDITIONALLY_UNIQUE_RATIONAL_PROGRAM" and kind["class"]=="INSIDE_EXACT_P4_Q2":
            totals["inside_original_with_candidate"]+=1
            assert actual=="FULL_ORIGINAL_SYMBOLICALLY_EQUIVALENT",("UNEXPECTED_THEOREM_OR_IMPLEMENTATION_BUG",oid,actual,kind)
        out.append({"id":oid,"collection":orig["collection"],"task_ID":orig["task_ID"],
            "formula_sha256":orig["original_formula_sha256"],
            "original_symbolic_grammar_class":kind,
            "sealed_pregrade_status":p["status"],
            "unchanged_original_author_grade":actual})
    assert totals["all"]==32 and totals["original_exact"]==7 and totals["original_rejected"]==6
    final={"schema":"NEUMANN_Q34_ERBENCH_SEVEN_ORACLE_POSTGRADE_EXPRESSIVITY_AUDIT.v1",
       "HISTORIC_ORIGINAL_FIRST_RECEIPTS_SHA256":SHA,
       "original_author_formulas_opened_only_POSTGRADE":True,
       "all_32_source_truth_statuses_preserved":True,
       "theorem_7_accurate_if_true_grammar_and_7_finite_distinct_rational_values":True,
       "all_first_claims_unchanged":True,
       "categories":dict(totals),
       "cases":out,
       "claim_scope":"This is AFTER-FIRST-GRADE diagnostic and does not count additional independent new benchmark performance",
       "G1_learned_new_operator":"OPEN",
       "Q4_total_cost_10x":"NOT_PROVED"}
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(final,sort_keys=True,indent=2)+"\n")
    print("ERBENCH_EXACT7_CONDITIONAL_THEOREM_FIRST_COHORT_ORIGINAL_AUDIT",json.dumps({
       "counts":dict(totals),"sha256":digest(dest)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("private","pred","grade","out"):p.add_argument("--"+k,required=True)
    main(p.parse_args())
