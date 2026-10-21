"""Mathematical expressivity audit on 24 actual original SyGuS source programs.

Exact subspace theorem: for observed integer states x0,...,xm, every rational
affine candidate a·x=b fitting ALL observations has a in ker_Q(D) where
D rows are xi-x0. Exact rational nullspace contains every PCA-rationalized
candidate. This is about candidate *representation*, NOT proof-search cost,
Houdini choice, actual full Post success, or generalization beyond samples.

Read original program bytes only in previously opened PR403/404 cohorts;
same fixed PR400 learner + exact rational comparator on each source.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from sympy import Matrix
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import source_samples
from research.evidence.q3_v3_PCA_conservation_20261021.actual_native_source_PCA_conservation import learned_pca_candidates
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare

def check(item,root):
    row={"source":item["path"],"source_git_sha":item["git_blob"],"status":"ABSTAIN"}
    try:
        _,src,native,identity=prepare(root,item)
        states,edges,observation=source_samples(src,native)
        if len(states)<3 or not edges:raise RuntimeError("INSUFFICIENT_ORIGINAL_PRE_TRANS_DATA")
        proposals,fit=learned_pca_candidates(src,states)
        seen=set();examples=[]
        for component in fit["learned_components"]:
            if "fitted_integer_coefficients" not in component:continue
            idx=component["variable_indices"]
            nums=component["fitted_integer_coefficients"]
            k=component["fitted_integer_constant"]
            if len(idx)!=len(nums) or not any(nums):
                raise AssertionError("NOT_A_TYPED_INTEGER_AFFINE_CANDIDATE")
            data=[[int(s[j]) for j in idx] for s in states]
            if any(sum(int(c)*x for c,x in zip(nums,z))!=k for z in data):
                raise AssertionError("LEARNED_RELATION_DOES_NOT_FIT_SOURCE_OBSERVATIONS")
            D=Matrix([[v-v0 for v,v0 in zip(x,data[0])] for x in data[1:]])
            coeff=Matrix(nums)
            if D*coeff!=Matrix.zeros(len(data)-1,1):
                raise AssertionError("LEARNED_RELATION_OUTSIDE_EXACT_RATIONAL_NULLSPACE")
            basis=D.nullspace()
            if len(basis)==0:
                raise AssertionError("NONZERO_LEARNED_RELATION_BUT_EXACT_NULLSPACE_EMPTY")
            B=Matrix.hstack(*basis)
            try:
                B.gauss_jordan_solve(coeff)
            except ValueError:
                raise AssertionError("LEARNED_CANDIDATE_NOT_SPANNED_BY_EXACT_CLASSICAL_BASIS")
            signature=(tuple(idx),tuple(nums),k)
            if signature not in seen:
                seen.add(signature)
                examples.append({"original_variable_indices":list(idx),
                                 "actual_fitted_integer_coefficients":list(nums),
                                 "integer_constant":k,"exact_Q_kernel_span_verified":True})
        row.update({
            "status":"COMPLETE_EXACT_REPRESENTATIONAL_SPAN_VERIFIED",
            "actual_CPU_PCA_fit_count":fit["real_CPU_PCA_model_fits"],
            "actual_learned_affine_candidate_count":len(proposals),
            "individual_fitted_numerical_candidates_exactly_in_Q_nullspace":len(examples),
            "native_original_transition_states":observation["distinct_source_state_observations"],
            "original_native_source_parity":identity,
            "source_affine_span_examples":examples[:6]
        })
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_NOT_SUPPORTED_OR_THEOREM_VIOLATED"
        row["error"]=type(e).__name__+":"+str(e)[:500]
        # If a claim of fitted candidate actually violates theorem, refuse to
        # hide it as harmless source data preflight abstention.
        if isinstance(e,AssertionError):raise
    print("Q3_REAL_ORIGINAL_AFFINE_SUBSPACE",row["source"].rsplit("/",1)[-1],
          row["status"],row.get("actual_CPU_PCA_fit_count"),
          row.get("individual_fitted_numerical_candidates_exactly_in_Q_nullspace"),
          "ERROR",row.get("error"),flush=True)
    return row
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze1","freeze2","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    one=json.loads(Path(a.freeze1).read_text());two=json.loads(Path(a.freeze2).read_text())
    inputs=one["cases"]+two["cases"]
    if len(inputs)!=24 or len({v["git_blob"] for v in inputs})!=24:
        raise RuntimeError("NOT_TWO_DISJOINT_FIRST_SOURCE_ORIGINAL_COHORTS")
    rows=[check(v,Path(a.root)) for v in inputs]
    success=[x for x in rows if x["status"]=="COMPLETE_EXACT_REPRESENTATIONAL_SPAN_VERIFIED"]
    report={
        "schema":"neumann.q3.actual_original24_exact_Q_kernel_contains_learned_PCA_affine_candidates.v1",
        "original_programs":24,
        "original_programs_with_concrete_PreTrans_samples":len(success),
        "actual_fit_programs":sum(z["actual_CPU_PCA_fit_count"]>0 for z in success),
        "sample_consistent_trained_affine_candidates_checked":sum(z["individual_fitted_numerical_candidates_exactly_in_Q_nullspace"] for z in success),
        "counterexamples_to_exact_affine_subspace_theorem":0,
        "verified_quantifier":"FOR_EVERY_GENERATED_AFFINE_CANDIDATE_ON_EVERY_OBSERVED_NATIVE_STATE",
        "theorem_affine_representation_only_NOT_identical_bounded_Houdini_runtime":True,
        "does_not_prove_candidate_globally_inductive_only_sampled_affine_span":True,
        "strong_exact_classical_has_all_same_source_data_and_candidate_space":True,
        "important_architecture_requirement":"Search learnable structures BEYOND cheaply enumerated affine nullspaces or prove computation-efficiency gains; do not claim mathematical uniqueness of PCA",
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "rows":rows
    }
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for k in ("original_programs_with_concrete_PreTrans_samples","actual_fit_programs",
              "sample_consistent_trained_affine_candidates_checked",
              "counterexamples_to_exact_affine_subspace_theorem"):
        print("EXACT_CLASSICAL_SUBSPACE_INCLUDES_ACTUAL_LEARNED",k,report[k])
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
