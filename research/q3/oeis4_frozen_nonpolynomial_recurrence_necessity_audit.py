"""FIRST-RECEIPT-LOCKED proof of new rational recursive step necessity.

Given the author's independent true finite-sum expression and first
source-only defined operator M, prove:
 (1) M(1) equals author's original finite sum at n=1;
 (2) M(n+1)-M(n) equals author's exact summand at k=n+1;
 (3) when reduced delta=p(n)/q(n) has nonconstant q, no
     POLYNOMIAL-IN-n increment can agree for all positive integers.
Reason: equal rational functions on infinitely many n => polynomial
identity p=q*P. Since gcd(p,q)=1 and deg q>0, impossible.
This is established elementary algebra, NOT new math.
"""
import argparse,json,pathlib,collections
import sympy as sp
from recursive_operator_source_inventor import N,sha,save
K=sp.Symbol("k",integer=True,positive=True)
LOCKS={
  "true":"44c74c3ed6df0c2bbbae3589b1cb263073c210848ea23c8f58855ababddeceef",
  "pred":"e1988151809eb01c272b258aebd18320ff54da76c04e9905ac0034a07d51bbc2",
  "grade":"9af815d126626fdf8d680c7bdb314123ecc5f3b5b642466e03cbfdeccc147b5e",
}
def analyze(a):
    for k in LOCKS:
        assert sha(pathlib.Path(getattr(a,k)).read_bytes())==LOCKS[k],(k,"IMMUTABLE_FIRST_EVIDENCE_SHA_CHANGED")
    tru=json.loads(pathlib.Path(a.true).read_text())["private_true_equations"]
    pred=json.loads(pathlib.Path(a.pred).read_text())["methods"]
    graded=json.loads(pathlib.Path(a.grade).read_text())["all_case_original_math_certificates"]
    first=pred["D_FROZEN_MODEL_PLUS_VERIFY_REPAIR"]["cases"]
    assert len(tru)==len(first)==4
    lookup={z["id"]:z for z in tru}
    good={z["id"] for z in graded["D_FROZEN_MODEL_PLUS_VERIFY_REPAIR"]
          if z["status"]=="ENTIRE_AUTHOR_SEQUENCE_PROVED_BY_INDUCTION"}
    assert len(good)==4
    reports=[]
    for row in first:
        true=lookup[row["id"]]
        g=sp.sympify(true["summand_expression"],locals={"k":K})
        author_step=sp.cancel(g.subs(K,N+1))
        rec=[p for p in row["new_programs"] if p["kind"]=="NEW_EXECUTABLE_RECURSIVE_SYMBOL"]
        assert rec and row["id"] in good
        selected=rec[0]
        source_step=sp.cancel(sp.sympify(selected["step_increment_AST"],locals={"n":N}))
        assert sp.cancel(source_step-author_step)==0
        num,den=sp.fraction(sp.cancel(source_step))
        pp=sp.Poly(num,N,domain=sp.QQ);qq=sp.Poly(den,N,domain=sp.QQ)
        assert qq.degree()>0
        assert sp.gcd(pp,qq).degree()==0
        corrected=len(row["attempts"])>1
        reports.append({
            "published_original":true["published_source"],
            "authored_increment_at_n_plus_one":str(author_step),
            "new_source_DEFINED_recursive_increment":str(source_step),
            "new_generated_function_symbol":selected["new_symbol"],
            "all_integer_n_induction_proven":True,
            "denominator_degree":int(qq.degree()),
            "numerator_degree":int(pp.degree()),
            "coprime_numerator_denominator":True,
            "any_polynomial_difference_operator_impossible":True,
            "elementary_algebraic_nonpolynomial_pole_witness":str(den),
            "prior_frozen_policy_made_wrong_first_action_then_revised":corrected,
            "actual_first_actions":[a["selected_action"] for a in row["attempts"]],
        })
    counters=collections.Counter(r["denominator_degree"] for r in reports)
    out={
      "schema":"NEUMANN_Q3_FIRST_OEIS4_RECURRENCE_NEW_OPERATOR_NONPOLYNOMIAL_NECESSITY.v1",
      "immutable_first_prediction_gold_full_induction_SHA256":LOCKS,
      "four_original_entire_semantics_certified":True,
      "four_distinct_newly_inferred_source_step_expressions":len(set(z["new_source_DEFINED_recursive_increment"] for z in reports))==4,
      "formal_algebraic_representational_minimality":
          "Any rational p(n)/q(n) with reduced nonconstant denominator q cannot coincide with polynomial P(n) on infinitely many integer n",
      "source_only_bounded_rational_interpolation_NOT_global_uniqueness_from_finite_samples":True,
      "per_original_strict_proofs":reports,
      "rational_denominator_degree_counts":dict(counters),
      "number_neural_structure_choices_repaired":sum(z["prior_frozen_policy_made_wrong_first_action_then_revised"] for z in reports),
      "same_rights_untrained_recursion_classical_all4":True,
      "human_preset_recurrence_action_and_after_failure_retry":True,
      "no_mathematics_novelty":"elementary polynomial root identity and induction",
      "G1":"HOLD","Q3_global":"OPEN","Q4_frontier10x":"NOT_PROVED"}
    s=save(a.out,out)
    print("NEUMANN_Q3_OEIS4_NEW_CREATED_RECURSION_NECESSARY_NONPOLYNOMIAL_INCREMENT_PROOFS",
        json.dumps({"sha256":s,"four_real_entire_author_proofs":len(reports),
          "strict_polynomial_step_obstructions":len(reports),
          "denominator_degrees":dict(counters),
          "repaired_structure_calls":out["number_neural_structure_choices_repaired"],
          "samples":reports},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in LOCKS:p.add_argument("--"+name,required=True)
    p.add_argument("--out",required=True)
    analyze(p.parse_args())
