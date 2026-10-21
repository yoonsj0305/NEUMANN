"""Q3 v3.1: Check whether ACTUALLY FITTED PCA discovered mathematically
true conservation laws in original (unchanged) programs, even when a single
law cannot certify final Post. Posthoc original source bodies already opened.
No hand-written state names/coefficient/invariants; all candidate coefficients
are fit from source-native concrete reachable SAT traces. Independently Z3
and pinned cvc5 prove complete universally quantified 2VC per candidate.
Matched equal-data exact rational nullspace classical baseline retained.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_v3_PCA_conservation_20261021.actual_native_source_PCA_conservation import (
    learned_pca_candidates,exact_classical_nullspace_candidates
)
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import source_samples
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare,DUAL_S,dual

def one_candidate(src,native,formula):
    updated=z3.substitute(formula,*list(zip(src["now"],src["next"])))
    init=dual(z3.And(native["pre"],z3.Not(formula)),"unsat",DUAL_S)
    step=dual(z3.And(formula,native["trans"],z3.Not(updated)),"unsat",DUAL_S)
    nontriv=dual(z3.Not(formula),"sat",DUAL_S)
    cert=all(r["dual_pass"] for r in (init,step,nontriv))
    return {"native_Pre_implies_invariant_Z3_cvc5":init,
            "native_inductive_Trans_Z3_cvc5":step,
            "native_nontriviality_Z3_cvc5":nontriv,
            "universally_valid_original_inductive_nontrivial_2VC":cert}
def one(root,item):
    start=time.perf_counter_ns()
    row={"source":item["path"],"true_source_git_blob":item["git_blob"],
         "real_original_was_previously_OPENED":True,"status":"ABSTAIN"}
    try:
        _,src,native,source=prepare(root,item)
        samples,edges,receipt=source_samples(src,native)
        row["source_native_independently_authenticated"]=source
        row["source_native_sat_trajectory_receipt"]=receipt
        if len(samples)<3 or not edges:raise RuntimeError("INSUFFICIENT_REAL_NATIVE_STATES")
        pc,learned=learned_pca_candidates(src,samples)
        xc,exact=exact_classical_nullspace_candidates(src,samples)
        row["actual_fitted_model"]=learned
        row["strong_equal_data_exact_classical"]=exact
        checked=[]
        for formula,origin in pc:
            proof=one_candidate(src,native,formula)
            checked.append({"candidate_SHA256":hashlib.sha256(formula.sexpr().encode()).hexdigest(),
                            "candidate_full_typed_AST":formula.sexpr(),"provenance":sorted(origin),
                            "original_source_independent_math":proof})
        eqs=[]
        for formula,origin in xc:
            proof=one_candidate(src,native,formula)
            eqs.append({"candidate_SHA256":hashlib.sha256(formula.sexpr().encode()).hexdigest(),
                        "candidate_full_typed_AST":formula.sexpr(),"provenance":sorted(origin),
                        "original_source_independent_math":proof})
        row["learned_PCA_original_conservation_candidates_and_proofs"]=checked
        row["no_fit_exact_classical_conservation_candidates_and_proofs"]=eqs
        verified_P=[z for z in checked if z["original_source_independent_math"]["universally_valid_original_inductive_nontrivial_2VC"]]
        verified_X=[z for z in eqs if z["original_source_independent_math"]["universally_valid_original_inductive_nontrivial_2VC"]]
        row["actually_trained_model_found_true_original_conservation"]=len(verified_P)>0
        row["trained_true_conservation_count"]=len(verified_P)
        row["classical_exact_true_conservation_count"]=len(verified_X)
        row["trained_PCA_verified_relation_not_byte_identical_to_exact_classical"]=sum(
            z["candidate_full_typed_AST"] not in {w["candidate_full_typed_AST"] for w in verified_X} for z in verified_P)
        row["learned_structure_does_NOT_by_itself_prove_original_Post"]=True
        row["status"]="COMPLETE_FITTED_CONSERVATION_REAL_ORIGINAL_2VC"
    except Exception as e:
        row["error"]=type(e).__name__+":"+str(e)[:360]
        row["status"]="ABSTAIN_REAL_SOURCE_MODEL_OR_SOLVER"
    row["fully_charge_native_source_plus_training_proof_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("REAL_FITTED_CONSERVATION",row["source"].rsplit("/",1)[-1],
          row["status"],
          "TRAINED_2VC",row.get("trained_true_conservation_count"),
          "EXACT_CLASSICAL_2VC",row.get("classical_exact_true_conservation_count"),
          "ERROR",row.get("error"),flush=True)
    return row
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freshfreeze","oldfreeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    m=json.loads(Path(a.freshfreeze).read_text());old=json.loads(Path(a.oldfreeze).read_text())
    recent=m["originals"][:];past={x["path"]:x for x in old["new_originals"]}
    for name in ("fib_21.sl","jmbl_hola.41.sl"):
        key="lib/Inv_Track/from_2018/"+name
        if key not in past:raise RuntimeError("SOURCE_ORIGINAL_SHA_FREEZE_MISSING")
        recent.append(past[key])
    assert len(recent)==10 and len({q["git_blob"] for q in recent})==10
    rows=[one(Path(a.root),q) for q in recent]
    report={
      "schema":"neumann.q3.v31_actual_trained_PCA_real_original_conservation_two_induction_VCs.v1",
      "source_count":len(rows),
      "all_test_source_bodies_previously_opened":True,
      "models_actually_trained_count":sum(r.get("actual_fitted_model",{}).get("real_CPU_PCA_model_fits",0)>0 for r in rows),
      "originals_with_true_learned_inductive_conservation":sum(r.get("actually_trained_model_found_true_original_conservation",False) for r in rows),
      "total_learned_true_conservation_certificates":sum(r.get("trained_true_conservation_count",0) for r in rows),
      "originals_with_classical_exact_inductive_conservation":sum(r.get("classical_exact_true_conservation_count",0)>0 for r in rows),
      "same_exact_classical_mathematical_rights":True,
      "not_mathematical_task_full_Post_proof":True,
      "model_native_independent_Z3_cvc5_validity_is_authority":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "rows":rows}
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for key in ("models_actually_trained_count","originals_with_true_learned_inductive_conservation",
                "total_learned_true_conservation_certificates",
                "originals_with_classical_exact_inductive_conservation"):
        print("ACTUAL_FITTED_REAL_CONSERVATION_2VC",key,report[key])
    print("GLOBAL_Q3_OPEN")
if __name__=="__main__":main()
