"""Independent *FIRST-SOURCE-LOCKED* minimal exponential macro rank proof.

Author OEIS:oeis_428 first original f(x)=4**x+8**x is EXACTLY a
two-term source-generated exp(log(b)*k*x) program. Prove no arbitrary
one positive-base real exponential with real affine gain/offset can
equal it by analytic differential invariant:

For g(x)=A*exp(lambda*x)+C, g'(0)*g'''(0)-(g''(0))**2 = 0.
For f(x)=exp(log(4)*x)+exp(log(8)*x), invariant =
log(4)*log(8)*(log(8)-log(4))**2=6*log(2)**4>0.

Thus first original analytic function needs at least two exponential
atoms even when all REAL positive bases, gains, and slopes are allowed;
first source program gives exactly two: rank=2 for the exponential
basis of positive real exponentials plus affine offset.

This proof is elementary known algebra/analysis, NOT novel math, and
the source program was also found by same-rights classical A.
"""
import argparse,hashlib,json,pathlib
import sympy as sp
from erbench_original_eleventh import allowed_formula,calc,SYM

X=sp.Symbol("x",real=True)
LOCKS={
 "truth":"a6becf118284cfb10a84f520ccd0b055ce34af167dfb330b2a117557275b841e",
 "pred":"428c8a0f245d22577970bd26995f431088ccba6a4e9ef5b7065fbc89a3bf94fc",
 "grade":"0c05dce89897cf0046693f556f22b5b0bf1e74b27283c6daf9783df9dbe1be8c",
}
def checksum(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def certificate(a):
    for role,expected in LOCKS.items():
        found=checksum(getattr(a,role))
        assert found==expected,(role,"UNSEALED_OR_MUTATED_FIRST_RESULTS",found,expected)
    t=json.loads(pathlib.Path(a.truth).read_text())["private_true_equations"]
    pred=json.loads(pathlib.Path(a.pred).read_text())["methods"]
    graded=json.loads(pathlib.Path(a.grade).read_text())["cases"]
    assert len(t)==32
    rows=[r for r in t if r["collection"]=="OEIS" and r["task_ID"]=="oeis_428"]
    assert len(rows)==1
    author=rows[0];ident=author["id"]
    tree,var=allowed_formula(author["original_expression"])
    fn=sp.simplify(calc(tree,{var:X},SYM))
    expected=4**X+8**X
    assert sp.simplify(fn-expected)==0

    # General arbitrary REAL one-branch exponential with optional offset.
    amp,rate,offset=sp.symbols("A rate offset",real=True)
    one=amp*sp.exp(rate*X)+offset
    witness=lambda f:sp.simplify(sp.diff(f,X).subs(X,0)*sp.diff(f,X,3).subs(X,0)-
                            sp.diff(f,X,2).subs(X,0)**2)
    universal_one=witness(one)
    assert universal_one==0
    observed=sp.simplify(witness(fn))
    assert sp.simplify(observed-6*sp.log(2)**4)==0
    assert sp.log(2).is_positive
    assert observed!=0

    # Assert this source-only learned program (not post-grade engineered)
    # exists among pregrade sealed candidates and was independently graded.
    learned={r["id"]:r for r in pred["D_learned_derived_power_top2"]["cases"]}[ident]
    goldgraded={r["id"]:r for r in graded["D_learned_derived_power_top2"]}[ident]
    assert goldgraded["status"]=="WHOLE_ORIGINAL_AUTHOR_PROVED"
    obtained=[]
    for proposal in learned["source_proposals"]:
        if not proposal.get("derived_EXPLOG_macros"):continue
        sy=sp.sympify(proposal["defined_operator_AST"],locals={"x":X})
        if sp.simplify(sy-fn)!=0:continue
        certs=proposal["derived_EXPLOG_macros"]
        if len(certs)!=2:continue
        for c in certs:
            b,k=c["base"],c["slope"]
            assert b>1 and k!=0
            lowered=sp.exp(sp.Integer(k)*X*sp.log(sp.Integer(b)))
            assert sp.powdenest(lowered,force=True)==sp.Pow(sp.Integer(b),sp.Integer(k)*X)
        obtained.append({"first_source_generated_lambda":proposal["named_lambda"],
               "components_from_numeric_x_y_only":certs})
    assert obtained,"NO_FIRST_SOURCE_PROGRAM_WITH_EXACT_TWO_EXPONENTS"
    classical={r["id"]:r for r in graded["A_full_same_actions"]}[ident]
    safe={r["id"]:r for r in graded["C_safe_add_rational"]}[ident]
    assert classical["status"]=="WHOLE_ORIGINAL_AUTHOR_PROVED"
    assert safe["status"]=="UNKNOWN"

    out={
      "schema":"NEUMANN_Q3_FIRST_ELEVENTH32_REAL_AUTHOR_TWO_EXPONENTIAL_COMPONENTS_NECESSARY_AND_SUFFICIENT.v1",
      "exact_first_author_truth_pred_grade_SHA256":LOCKS,
      "author_original":"OEIS:oeis_428",
      "author_source_original_expression":author["original_expression"],
      "canonical_entire_original":str(expected),
      "all_real_single_exponential_family":"A*exp(rate*x)+offset with arbitrary real A,rate,offset",
      "all_single_exponentials_satisfy":"g'(0)*g'''(0)-g''(0)^2=0",
      "universal_single_exp_differential_invariant":str(universal_one),
      "real_original_invariant":str(observed),
      "strict_positive_exact_witness":"6*log(2)**4 > 0",
      "single_exponential_even_unrestricted_real_parameters_impossible":True,
      "exact_required_exponential_basis_rank":2,
      "first_source_generated_exact_two_exponential_macros":obtained,
      "author_entire_real_analytic_expression_exact":True,
      "prior_old_SAFE_classical_cannot_recover_same_original":True,
      "identical_rights_full_new_CLASSICAL_also_recovers_original":True,
      "novel_mathematics_theorem":"NO_CLASSICAL_ELEMENTARY_ANALYSIS",
      "learner_only_v_full_classical":"NO",
      "G1":"HOLD","Q3_global":"OPEN","Q4_allin_10x":"NOT_PROVED"
    }
    path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("Q3_ELEVENTH_FIRST_ORIGINAL_TWO_EXPONENTIAL_BASIS_MINIMALITY_STRICT_PROOF",
       json.dumps({"original":str(fn),"differential_witness":str(observed),
        "source_generated":obtained,
        "SHA256":checksum(path)},sort_keys=True),flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for k in LOCKS:parser.add_argument("--"+k,required=True)
    parser.add_argument("--out",required=True)
    certificate(parser.parse_args())
