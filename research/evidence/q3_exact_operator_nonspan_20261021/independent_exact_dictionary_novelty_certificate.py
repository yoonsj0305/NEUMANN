"""NEUMANN Q3 exact operator novelty admission gate.

Reads SHA-pinned OFFICIAL actual gradient-learner PR430 source artifacts,
not invented formulas. For each actually learned candidate polynomial,
computes an exact rational span-membership (or nonmembership) certificate
relative to the FROZEN supplied basis. Infeasible M*c=b is supported
by an explicit nonzero left-kernel witness u: u.T*M=0, u.T*b!=0.
Feasible is supported by an exact rational coefficient vector c.

This certifies relative mathematical nonmembership only, NOT that a
new primitive was autonomously learned. The strongest equal-grammar exact
classical solver is never deleted from the comparison.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import sympy as sp
from research.evidence.q3_raw_transition_nonlinear_20261021.learned_original_source_nonlinear_AST import (
    basis,sources,prove
)
RAW_SHA="07a914d0f391119d0089b25fa59afdea0fce87b2aaad1e30e9ee34b3adc14d97"
def coefficient_vector(P,exprs):
    V=P["variables"]
    polynomials=[sp.Poly(sp.expand(a),*V,domain=sp.QQ) for a in exprs]
    monomials=sorted(set().union(*(p.monoms() for p in polynomials)),
                     key=lambda x:(sum(x),x))
    mat=sp.Matrix([[p.coeff_monomial(m) for p in polynomials] for m in monomials])
    return mat,monomials
def exact_span_certificate(P,target,dictionary):
    V=P["variables"]
    mat,monos=coefficient_vector(P,list(dictionary)+[target])
    basis_matrix=mat[:,:-1];column=mat[:,-1]
    rank=basis_matrix.rank();rank_aug=mat.rank()
    member=rank==rank_aug
    report=dict(
      target_AST=str(target),dictionary_AST=[str(e) for e in dictionary],
      exact_polynomial_monomial_rows=[list(x) for x in monos],
      basis_rank=rank,augmented_rank=rank_aug,
      target_in_exact_rational_feature_span=member,
      source_coefficient_equations_exact=True,
      only_relative_to_declared_operator_dictionary=True)
    if member:
        names=sp.symbols("c:"+str(len(dictionary)))
        solutions=sp.linsolve(list(basis_matrix*sp.Matrix(names)-column),names)
        if not solutions:raise AssertionError("EXACT_SPAN_RANK_SOLVER_DISAGREES")
        chosen=list(next(iter(solutions)))
        free=set().union(*(q.free_symbols for q in chosen))
        chosen=[sp.factor(q.subs({f:0 for f in free})) for q in chosen]
        c=sp.Matrix(chosen)
        if basis_matrix*c!=column:raise AssertionError("EXACT_SPAN_POSITIVE_WITNESS_INVALID")
        if sp.expand(sum(z*t for z,t in zip(chosen,dictionary))-target)!=0:
            raise AssertionError("ORIGINAL_POLYNOMIAL_IDENTITY_CHANGED")
        report["membership_exact_rational_coefficient_vector"]=[str(v) for v in chosen]
        report["positive_exact_polynomial_identity_verified"]=True
        report["negative_exact_left_nullspace_witness"]=None
    else:
        candidates=basis_matrix.T.nullspace()
        witness=next((u for u in candidates if (u.T*column)[0]!=0),None)
        if witness is None:raise AssertionError("MISSING_NONMEMBERSHIP_CERTIFICATE")
        if (witness.T*basis_matrix)!=sp.zeros(1,basis_matrix.cols):
            raise AssertionError("LEFT_NULL_WITNESS_NOT_ORTHOGONAL")
        contradiction=(witness.T*column)[0]
        if contradiction==0:raise AssertionError("LEFT_NULL_WITNESS_NOT_SEPARATING")
        report["membership_exact_rational_coefficient_vector"]=None
        report["negative_exact_left_nullspace_witness"]={
            "monomial_weight_vector":[str(q) for q in witness],
            "orthogonal_to_ALL_baseline_features":True,
            "nonzero_dot_target_coefficient":str(contradiction),
            "mathematical_nonmembership_proved":True}
        report["positive_exact_polynomial_identity_verified"]=False
    return report
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--official",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    payload=Path(args.official).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=RAW_SHA:
        raise RuntimeError("FIRST_ORIGINAL_TRAINED_IMMUTABLE_SHA_DRIFT")
    prior=json.loads(payload)
    if prior["schema"]!="neumann.q3.source_transition_nonlinear_learned_AST_synthetic_v1":
        raise RuntimeError("NOT_ACTUAL_FITTED_LEARNED_SOURCE_RECEIPTS")
    problems={p["name"]:p for p in sources()}
    rows=[]
    for record in prior["all_original_source_trials"]:
        P=problems[record["task"]]
        learned=record["all_degree_trials"][-1]
        if not learned["learned_full_original_PASS"]:
            raise RuntimeError("TRAINING_NOT_ACTUALLY_CERTIFIED")
        names={str(x):x for x in P["variables"]}
        candidate=sp.sympify(learned["learned_composed_AST"],locals=names)
        native=prove(P,candidate)
        if not native["fully_inductive_and_original_Post"]:
            raise RuntimeError("ORIGINAL_SOURCE_IDENTITY_DID_NOT_HOLD")
        # This is a dictionary RELATIVE novelty theorem. Degree-1
        # predecessor was unable to express target, whereas supplied
        # up-to-degree-3 operator family already contained it.
        linear=[sp.Integer(1)]+basis(P["variables"],1,P["anchor"])
        full=[sp.Integer(1)]+basis(P["variables"],3,P["anchor"])
        linear_proof=exact_span_certificate(P,candidate,linear)
        full_proof=exact_span_certificate(P,candidate,full)
        if linear_proof["target_in_exact_rational_feature_span"]:
            raise AssertionError("SUPPOSED_NONLINEAR_CANDIDATE_IS_AFFINE")
        if not full_proof["target_in_exact_rational_feature_span"]:
            raise AssertionError("SUPPLIED_FULL_OPERATOR_VOCAB_DID_NOT_INCLUDE_LEARNED")
        rows.append(dict(
          source=record["task"],seed=record["seed"],
          previously_actual_fitted_expression_AST=str(candidate),
          independent_source_pre_trans_post_proof=native,
          relative_to_OLD_LINEAR_grammar=linear_proof,
          relative_to_FULL_SUPPLIED_grammar=full_proof,
          unique_new_primitive_outside_existing_full_dictionary=False))
        print("Q3_FORMAL_DICTIONARY_NOVELTY",record["task"],record["seed"],
              "NOT_IN_LINEAR",True,"IN_FULL_SUPPLIED",True,flush=True)
    report=dict(
      schema="neumann.q3.exact_nonspan_certificate_trained24_original_operators_v1",
      previously_actual_fitted_source_receipt_SHA256=RAW_SHA,
      actual_trained_AST_count=len(rows),
      polynomial_targets_outside_degree1_linear_dictionary=sum(
           not x["relative_to_OLD_LINEAR_grammar"]["target_in_exact_rational_feature_span"]
           for x in rows),
      exact_left_kernel_NONSPAN_certificates=sum(
           bool(x["relative_to_OLD_LINEAR_grammar"]["negative_exact_left_nullspace_witness"])
           for x in rows),
      polynomial_targets_already_inside_full_supplied_dictionary=sum(
           x["relative_to_FULL_SUPPLIED_grammar"]["target_in_exact_rational_feature_span"]
           for x in rows),
      autonomously_discovered_operator_primitive_not_in_supplied_full_dictionary=0,
      proof_gate_admission="REJECT_UNIQUE_NEW_OPERATOR_Q3_FOR_ALL_24",
      negative_certificate_is_exact_rational_linear_algebra_not_neural_score=True,
      real_unseen_external_source_not_tested_in_this_reaudit=True,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
      all_evidence=rows)
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("actual_trained_AST_count",
              "exact_left_kernel_NONSPAN_certificates",
              "polynomial_targets_already_inside_full_supplied_dictionary",
              "autonomously_discovered_operator_primitive_not_in_supplied_full_dictionary"):
        print("Q3_FORMAL_NOVELTY_GATE",k,report[k],flush=True)
    print("Q3_FULL_Q3_OPEN_NO_FAKE_PRIMITIVE_INVENTION")
if __name__=="__main__":main()
