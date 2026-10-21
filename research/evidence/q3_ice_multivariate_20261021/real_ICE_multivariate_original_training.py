"""ACTUAL fitted counterexample-guided invariant learner, posthoc opened originals.

First prior self-supervised pairwise learner passed two development source originals,
but FIXED v1 had 0/8 fresh source proofs. This V2 changes learning architecture
AFTER those 8 source bodies were opened. Never retroactively label V2 blind.
Model learns multivariate integer affine candidate separators from true native
Pre/Trans reachable state traces vs native actual NotPost and verifier ICE
counterexample states; Houdini + independent full Z3,cvc5 3VC are authority.
No hard-coded program variable names, invariant coefficients or published answer.
"""
from __future__ import annotations
import argparse,hashlib,json,time,collections
from pathlib import Path
import numpy as np
import z3
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import (
    source_samples,candidate_generator,houdini,millis
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare
ORIGINAL_REV="13c8deb68a873635879c9a69bc78caebd340f646"
RNG=20261021

def actual_native_bad_witnesses(src,native,I,positives,max_negative=18):
    """Sample actual native symbolic I AND NotPost, not synthetic hidden gold."""
    variables=list(src["now"])
    unique=set(positives);out=[];tries=0
    base=z3.Solver();base.set(timeout=2200)
    base.add(I,z3.Not(native["post"]))
    constraints=[]
    for i in range(len(variables)):
        values=[int(row[i]) for row in positives]
        center=(min(values)+max(values))//2
        constraints.append((i,center))
    for typ,ind,v in [("none",-1,0)]+[("single",i,mid) for i,mid in constraints]:
        if len(out)>=max_negative:break
        s=z3.Solver();s.set(timeout=2200)
        s.add(base.assertions())
        if typ=="single":
            # Probe near empirical state ranges without changing true source.
            s.add(variables[ind]==v)
        for _ in range(4):
            tries+=1
            if s.check()!=z3.sat:break
            m=s.model()
            item=tuple(m.eval(q,model_completion=True).as_long() for q in variables)
            if item not in unique:
                unique.add(item);out.append(item)
            s.add(z3.Or(*[x!=q for x,q in zip(variables,item)]))
            if len(out)>=max_negative:break
    return out,tries
def svm_source_candidates(src,pos,neg):
    """Fit ACTUAL learned linear separators, candidate arithmetic from learned w."""
    start=time.perf_counter_ns()
    if len(set(pos))<3 or len(set(neg))<2:return [],{"trained":False,"reason":"DATA_INSUFFICIENT"}
    X=np.asarray(pos+neg,dtype=np.float64)
    Y=np.asarray([1]*len(pos)+[-1]*len(neg),dtype=np.int64)
    scaler=StandardScaler().fit(X)
    Z=scaler.transform(X)
    named={}
    fitted=[]
    for C in (.03,1.0,30.0):
        model=LinearSVC(C=C,dual=False,random_state=RNG,max_iter=3000)
        model.fit(Z,Y)
        real_w=model.coef_[0]/scaler.scale_
        if not np.any(np.abs(real_w)>1e-9):continue
        for scale in (8,64,512,4096):
            coefficients=[int(round(w/max(abs(real_w))*scale)) for w in real_w]
            if not any(coefficients):continue
            values_pos=[sum(a*int(v) for a,v in zip(coefficients,row)) for row in pos]
            values_neg=[sum(a*int(v) for a,v in zip(coefficients,row)) for row in neg]
            lower=min(values_pos)
            if not any(v<lower for v in values_neg):continue
            expr=sum((int(a)*x for a,x in zip(coefficients,src["now"])),z3.IntVal(0))>=lower
            if expr.sexpr() not in named:named[expr.sexpr()]=(expr,{"TRAINED_ICE_LINEAR_SVM"})
            fitted.append({"C":C,"quantization_scale":scale,
                           "source_state_coefficients":coefficients,
                           "candidate_lower_bound":lower,
                           "actual_post_violation_samples_excluded":sum(v<lower for v in values_neg)})
    return list(named.values()),{"trained":True,"actual_CPU_SVM_models":3,
                "actual_counterexample_labeled_positive_observations":len(pos),
                "actual_counterexample_labeled_negative_observations":len(neg),
                "actual_SVM_classification_separators_kept":len(named),
                "learned_multivariate_invariant_separators":fitted,
                "training_and_candidate_generation_wall_ms":millis(start)}
def retained_ast(report,original_candidates):
    keys={x["smt"] for x in report["retained_candidate_formulas"]}
    return z3.And(*[expr for expr,_ in original_candidates if expr.sexpr() in keys])
def one(root,item):
    start=time.perf_counter_ns()
    record={"source":item["path"],"git_blob":item["git_blob"],
            "status":"ABSTAIN","source_bodies_open_before_this_V2":True}
    try:
        raw,src,native,proof=prepare(root,item)
        record["native_PreTransPost_source_identity"]=proof
        states,edges,data=source_samples(src,native)
        if len(states)<3 or len(edges)<2:raise RuntimeError("TOO_FEW_ACTUAL_SOURCE_STATES_TO_TRAIN")
        record["actual_native_source_state_sample"]=data
        # Same source and training data, same baseline and prior frozen v1.
        original,quantile=candidate_generator(src,states,edges,True)
        nofit=[z for z in original if any(k.startswith("NO_FIT") for k in z[1])]
        bare=houdini(src,native,nofit)
        v1=houdini(src,native,original)
        record["ZERO_TRAIN_NO_FIT_BOUNDED_CLASSICAL"]=bare
        record["PRIOR_FROZEN_V1_QUANTILE_MODEL"]=v1
        record["prior_quantile_learning"]=quantile
        current=original[:]
        rounds=[]
        repeated_names=set(z[0].sexpr() for z in current)
        for idx in range(4):
            prior=houdini(src,native,current)
            if prior["fully_verified_complete_original_3VC"]:
                rounds.append({"round":idx,"pass_before_any_more_learning":True,
                               "already_independent_original_dual_proved":True})
                break
            I=retained_ast(prior,current)
            negatives,ntries=actual_native_bad_witnesses(src,native,I,states)
            generated,fit=svm_source_candidates(src,states,negatives)
            new=[t for t in generated if t[0].sexpr() not in repeated_names]
            current.extend(new)
            repeated_names.update(x.sexpr() for x,o in new)
            rounds.append({"round":idx,"native_actual_source_bad_model_calls":ntries,
                           "counterexample_linear_model":fit,
                           "genuinely_new_learned_candidate_count":len(new),
                           "pre_round_original_inductive_proof":False})
            if not new:break
        final=houdini(src,native,current)
        record["learner_ICE_SVM_candidate_rounds"]=rounds
        record["actual_trained_original_full_native_Z3_cvc5_3VC"]=final
        record["model_trained_new_ICE_candidate_count"]=sum(x.get("genuinely_new_learned_candidate_count",0) for x in rounds)
        record["bounded_SVM_contribution_vs_prior_v1"]=bool(
            final["fully_verified_complete_original_3VC"] and not v1["fully_verified_complete_original_3VC"] and
            final["retained_train_only_candidates"]>0)
        record["status"]="COMPLETE_POSTHOC_ICE_TRAINED_NATIVE_VERIFIED"
    except Exception as e:
        record["status"]="ABSTAIN_REAL_SOURCE_OR_MODEL_OR_PROOF"
        record["failure"]=type(e).__name__+":"+str(e)[:480]
    record["whole_original_data_learning_houdini_proof_wall_ms"]=millis(start)
    print("Q3_ICE_ACTUAL_TRAINED",item["path"],
          "SOURCE",record["status"],
          "PRIOR_V1",record.get("PRIOR_FROZEN_V1_QUANTILE_MODEL",{}).get("fully_verified_complete_original_3VC"),
          "V2",record.get("actual_trained_original_full_native_Z3_cvc5_3VC",{}).get("fully_verified_complete_original_3VC"),
          "ICE_NEW",record.get("model_trained_new_ICE_candidate_count"),
          "CAUSE",record.get("bounded_SVM_contribution_vs_prior_v1"),
          "ERROR",record.get("failure"),flush=True)
    return record
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args();m=json.loads(Path(a.freeze).read_text())
    assert m["schema"]=="neumann.q3.first_unseen_eight_actual_CPU_invariant_training_benchmark_sha_lock_v1"
    assert len(m["originals"])==8
    result=[one(Path(a.root),q) for q in m["originals"]]
    summary={
        "schema":"neumann.q3.posthoc_ice_actual_trained_multivariate_counterexample_invariants.v1",
        "original_programs_previously_opened_by_PR395":True,
        "source_native_PreTransPost_SHAs_original":True,
        "original_case_count":len(result),
        "prior_v1_certified":sum(q.get("PRIOR_FROZEN_V1_QUANTILE_MODEL",{}).get("fully_verified_complete_original_3VC",False) for q in result),
        "trained_v2_ice_full_original_dual_certified":sum(q.get("actual_trained_original_full_native_Z3_cvc5_3VC",{}).get("fully_verified_complete_original_3VC",False) for q in result),
        "model_ICE_bounded_new_contribution_vs_prior_v1":sum(q.get("bounded_SVM_contribution_vs_prior_v1",False) for q in result),
        "model_ICE_learned_novel_candidate_total":sum(q.get("model_trained_new_ICE_candidate_count",0) for q in result),
        "real_programs":result,
        "strongest_equal_authority_classical_structure_not_exhaustively_compared":True,
        "new_first_unseen_source_claim":False,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"
    }
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    for k in ("prior_v1_certified","trained_v2_ice_full_original_dual_certified",
              "model_ICE_bounded_new_contribution_vs_prior_v1","model_ICE_learned_novel_candidate_total"):
        print("Q3_ICE_POSTHOC_REAL_MODEL",k,summary[k])
    print("GLOBAL_Q3","OPEN")
if __name__=="__main__":main()
