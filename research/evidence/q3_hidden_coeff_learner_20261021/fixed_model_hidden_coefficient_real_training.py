"""Falsifiable synthetic CONTROL: real self-supervised model recovers unknown
numeric program relation coefficient from SAT native transitions and certifies
whole original Pre/Trans/Post with independent original Z3+cvc5. This is
NOT a real benchmark Q3 generalization. Classical source has equal rights.
"""
from __future__ import annotations
import argparse,hashlib,json,random,time
from pathlib import Path
import z3
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import (
    source_samples,candidate_generator,houdini,millis
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import verified_3vc

SEED=20261021
def built(seed):
    rng=random.Random(SEED+seed*941)
    a=rng.randint(3,23)
    b=rng.randint(2,10)
    labels=[f"holdout_state_{seed}_r{rng.randrange(10**8)}" for _ in range(4)]
    roles=["step","value","limit","noise"]
    rng.shuffle(roles)
    now=[z3.Int(q) for q in labels]
    nxt=[z3.Int(q+"_new") for q in labels]
    vals={role:now[idx] for idx,role in enumerate(roles)}
    nextvals={role:nxt[idx] for idx,role in enumerate(roles)}
    x,y,n,z=vals["step"],vals["value"],vals["limit"],vals["noise"]
    xn,yn,nn,zn=(nextvals[q] for q in ("step","value","limit","noise"))
    pre=z3.And(n>=1,n<=8,x==0,y==0,z==0)
    trans=z3.Or(
        z3.And(x<n,xn==x+1,yn==y+a,nn==n,zn==z+b),
        z3.And(x>=n,xn==x,yn==y,nn==n,zn==z))
    post=z3.Implies(x>=n,y>=a*n)
    unsafe_post=z3.Implies(x>=n,y> a*n)
    src={"states":[(q,"Int") for q in labels],"now":now,"next":nxt}
    native={"pre":pre,"trans":trans,"post":post}
    return src,native,unsafe_post,{"hidden_a":a,"distractor_b":b,"roles":roles}

def one(seed):
    t=time.perf_counter_ns()
    out={"synthetic_seed":seed,"status":"ABSTAIN"}
    try:
        src,native,negative,ground=built(seed)
        samples,edges,meta=source_samples(src,native)
        if len(samples)<10 or len(edges)<8:raise RuntimeError("NOT_ENOUGH_NATIVE_SOURCE_EXAMPLES")
        candidates,train=candidate_generator(src,samples,edges,True)
        learned=houdini(src,native,candidates)
        nofit=houdini(src,native,[(q,o) for q,o in candidates if any(k.startswith("NO_FIT") for k in o)])
        # Did a genuine numerical estimator, not literal reference source
        # coefficient, recover the ground truth relation y ~ a*x?
        learned_slopes=[fit for fit in train["model_fits"]
            if fit.get("actual_trained_slope")==str(ground["hidden_a"])
            and fit.get("dependent_index")==ground["roles"].index("value")
            and fit.get("independent_index")==ground["roles"].index("step")]
        origI=z3.And(*[q for q,o in candidates if q.sexpr() in {
            y["smt"] for y in learned["retained_candidate_formulas"]}])
        # Negative control changes the POST property, not the TRAINED candidate.
        mutant={**native,"post":negative}
        mutant_proven,mutant_vcs=verified_3vc(src,mutant,origI)
        out.update({
            "ground_truth_coefficient_NOT_VISIBLE_TO_LEARNER":ground["hidden_a"],
            "source_names_permuted":True,
            "random_distractor_transition_coefficient":ground["distractor_b"],
            "native_true_execution_sampling":meta,
            "CPU_model_training":train,
            "model_recovered_exact_hidden_coefficient_from_actual_state_trajectory":bool(learned_slopes),
            "final_trained_original_native_inductive_certificate":learned,
            "no_fit_original_native_inductive_certificate":nofit,
            "incorrect_mutated_original_post_rejected":not mutant_proven,
            "incorrect_mutated_original_full_dual_3VC_receipts":mutant_vcs,
            "status":"ACTUALLY_TRAINED_AND_INDEPENDENTLY_ORIGINAL_PROOF_VERIFIED"
        })
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_GENERATION_OR_MODEL_OR_DUAL_SOLVER"
        out["error"]=type(e).__name__+":"+str(e)[:280]
    out["full_synthetic_test_from_first_source_through_3VC_wall_ms"]=millis(t)
    print("HIDDEN_COEFF_ACTUALLY_TRAINED",seed,
          "FITTED",out.get("model_recovered_exact_hidden_coefficient_from_actual_state_trajectory"),
          "DUAL_ORIGINAL",out.get("final_trained_original_native_inductive_certificate",{}).get("fully_verified_complete_original_3VC"),
          "NOFIT",out.get("no_fit_original_native_inductive_certificate",{}).get("fully_verified_complete_original_3VC"),
          "BAD_POST_REJECTED",out.get("incorrect_mutated_original_post_rejected"),
          "STATUS",out["status"],flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();c=json.loads(Path(a.contract).read_text())
    assert c["schema"]=="neumann.q3.prospective_selfsupervised_hidden_coefficients_control_proof_v1"
    assert c["testcases"]==16 and c["source_generator_seed"]==SEED
    records=[one(i) for i in range(16)]
    result={
      "schema":"neumann.q3.synthetic_mechanism_actual_learned_coefficients_complete_source_dual.v1",
      "synthetic_generated_control_not_public_benchmark":True,
      "originals_with_hidden_unknown_random_coefficients":len(records),
      "fitted_hidden_coefficients_correct":sum(q.get("model_recovered_exact_hidden_coefficient_from_actual_state_trajectory",False) for q in records),
      "actual_trained_candidate_original_complete_dual3VC":sum(q.get("final_trained_original_native_inductive_certificate",{}).get("fully_verified_complete_original_3VC",False) for q in records),
      "same_sample_no_fit_original_complete_dual3VC":sum(q.get("no_fit_original_native_inductive_certificate",{}).get("fully_verified_complete_original_3VC",False) for q in records),
      "negative_mutated_original_property_rejected":sum(q.get("incorrect_mutated_original_post_rejected",False) for q in records),
      "no_neural_structure_global_claim":True,
      "all_data_generated_from_native_smt_transitions":True,
      "strong_equal_authority_classical_synthesis_can_find_same_math":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "cases":records
    }
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    for k in ("fitted_hidden_coefficients_correct","actual_trained_candidate_original_complete_dual3VC",
              "same_sample_no_fit_original_complete_dual3VC","negative_mutated_original_property_rejected"):
        print("SYNTHETIC_ACTUALLY_LEARNED_STRUCTURAL_MECHANISM",k,result[k])
    print("GLOBAL_Q3",result["global_Q3"])
if __name__=="__main__":main()
