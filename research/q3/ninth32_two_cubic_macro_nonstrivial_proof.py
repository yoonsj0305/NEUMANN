"""Independent postgrade original-source degree-3 two-branch necessity proof.

From original FIRST true author expression and FIRST source-only proposed
neural macro, prove exact equality. Then prove IMPOSSIBILITY of reproducing
the same polynomial by a single arbitrary shifted-scaled cubic
A*(B*x+C)^3+D, even with any REAL coefficients A,B,C,D.

For cubic a3*x³+a2*x²+a1*x+a0, any single shifted cube implies
a2²=3*a3*a1. Genuine OEIS source fails. Basic historical classical math,
not a new theorem, and original program was ALSO found by classical control.
"""
import argparse,hashlib,json,pathlib
import sympy as sp
from erbench_original_ninth import allowed_formula,calc,SYM
X=sp.Symbol("x")
TRUTH_SHA="70177035c01d16a7c0ed0da003ee3049bc3d605ea282a16bf927ba22a80206e1"
FIRST_PRED_SHA="d00edb5e3ecb019286f8c18dc2f660613e20315854e966f7f1bc222251b147de"
FIRST_GRADE_SHA="9f4235b00a706db6edeb4232bc51c03290f6d2439b75f54c1f7a2125d02accc7"
def checksum(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def certificate(truth,pred,grade,out):
    assert checksum(truth)==TRUTH_SHA,"ORIGINAL_AUTHOR_FIRST_TRUE_SHA_MISMATCH"
    assert checksum(pred)==FIRST_PRED_SHA,"FROZEN_SOURCE_FIRST_GENERATED_MACRO_SHA_MISMATCH"
    assert checksum(grade)==FIRST_GRADE_SHA,"ORIGINAL_AUTHOR_FIRST_INDEPENDENT_GRADE_SHA_MISMATCH"
    targets=json.loads(pathlib.Path(truth).read_text())["private_true_equations"]
    programs=json.loads(pathlib.Path(pred).read_text())["Arms"]
    grader=json.loads(pathlib.Path(grade).read_text())
    t=[r for r in targets if r["collection"]=="OEIS" and r["task_ID"]=="oeis_1468"]
    assert len(t)==1
    target=t[0]
    tree,var=allowed_formula(target["original_expression"])
    original=sp.cancel(calc(tree,{var:X},SYM))
    assert original.is_polynomial(X)
    poly=sp.Poly(original,X,domain=sp.QQ)
    assert poly.degree()==3
    c3,c2,c1,c0=(sp.Rational(v) for v in poly.all_coeffs())
    # Formula for a single shifted-scaled cube with any real A,B,C,D:
    # A(Bx+C)^3+D => c3=AB^3, c2=3AB²C, c1=3ABC².
    # Thus c2²=3*c3*c1 necessarily. Our author polynomial violates.
    invariant=sp.cancel(c2*c2-3*c3*c1)
    assert invariant!=0, "ONE_SHIFTED_CUBIC_HAS_NOT_BEEN_EXCLUDED"
    learned={x["id"]:x for x in programs["D_learned_macro_top80"]["predictions"]}
    row=learned[target["id"]]
    exact=[]
    for item in row["exact_numeric_macro_candidates"]:
        try:
            candidate=sp.sympify(item["named_lambda"].replace("lambda x: ",""),
                locals={"x":X})
            if sp.cancel(original-candidate)==0:exact.append(item)
        except Exception:continue
    assert exact and any(len(q["macro_nodes"])==2 for q in exact)
    # Choose concrete two-cubic source-generated candidate,
    # not hand-created once the grader's author formula is known.
    cubes=[]
    for q in exact:
        nodes=[sp.sympify(s,locals={"x":X}) for s in q["macro_nodes"]]
        if len(nodes)==2 and all(sp.Poly(sp.expand(p),X).degree()==3 for p in nodes):
            cubes.append(q)
    assert cubes,"REAL_SOURCE_LEARNER_DID_NOT_ACTUALLY_CREATE_TWO_CUBE_EXPR"
    original_grade={x["id"]:x for x in grader["cases"]["D_learned_macro_top80"]}
    assert original_grade[target["id"]]["status"]=="FULL_AUTHOR_ORIGINAL_EXACT"
    equal_classical={k: any(x["id"]==target["id"] and x["status"]=="FULL_AUTHOR_ORIGINAL_EXACT"
                        for x in v) for k,v in grader["cases"].items()
                     if k!="D_learned_macro_top80"}
    proof={"schema":"NEUMANN_Q3_FIRST_AUTHORED_ORIGINAL_CUBIC_TWO_BRANCH_STRICT_NECESSITY.v1",
         "immutable_sha_source_author_and_grader":{"truth":TRUTH_SHA,"pred":FIRST_PRED_SHA,"grade":FIRST_GRADE_SHA},
         "external_original_author":"OEIS:oeis_1468",
         "frozen_original_id":target["id"],
         "true_full_original_polynomial":str(original),
         "original_coefficients_descending":[str(v) for v in (c3,c2,c1,c0)],
         "shifted_single_cube_necessary_coefficient_identity":"c2² == 3*c3*c1",
         "observed_c2_squared":str(c2*c2),
         "observed_3c3c1":str(3*c3*c1),
         "nonzero_impossibility_witness":str(invariant),
         "no_one_shifted_cubic_even_with_arbitrary_real_scale_shift_gain_offset":True,
         "frozen_source_generated_genuinely_two_cubic_macros":[q["named_lambda"] for q in cubes],
         "whole_original_function_exactly_proved_by_sympy":True,
         "source_native_mathematical_certificate":"explicit polynomial identity + exact coefficient impossibility for one shifted cube",
         "same_original_exact_also_found_by_classical_controls":equal_classical,
         "mathematical_priority_claim":"NONE_ELEMENTARY_KNOWN_CUBIC_COEFFICIENT_RELATION",
         "learned_graph_policy_exclusive_vs_classical":"NO",
         "new_fundamental_operator_semantics":"NOT_PROVED",
         "cross_author_model_weights_transfer":"NOT_PROVED",
         "G1":"HOLD","Q3_global":"OPEN","full_frontier_10x":"NOT_PROVED"}
    path=pathlib.Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(proof,sort_keys=True,indent=2)+"\n")
    print("Q3_NINTH_ORIGINAL_TWO_CUBIC_NONREDUCIBLE_LEARNED_GENERATED_PROOF",
          json.dumps({"orig":proof["true_full_original_polynomial"],
          "invariant":str(invariant),
          "source_learned_proposed_two_cubes":proof["frozen_source_generated_genuinely_two_cubic_macros"],
          "classical_also_exact":equal_classical,
          "sha256":checksum(path)},sort_keys=True),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser()
    for k in ("truth","pred","grade","out"):a.add_argument("--"+k,required=True)
    q=a.parse_args();certificate(q.truth,q.pred,q.grade,q.out)
