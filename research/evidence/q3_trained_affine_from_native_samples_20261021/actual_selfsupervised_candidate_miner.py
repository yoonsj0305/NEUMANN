"""Actually trained CPU structural-invariant miner on untouched native program execution samples.

Development/posthoc originals whose source bodies have ALREADY BEEN OPENED.
Crucially NO manually supplied invariant, gold invariant, source variable names,
or source-specific coefficients enter the learner. sk-learn QuantileRegressor
fits lower/upper affine conditional envelopes from genuine source transitions.
Source-native SMT Houdini retains only independently inductive candidates.
Report whether trained candidates are NECESSARY relative to identical-data
zero-fit shallow templates; do not conflate model use with unique invention.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,time,random
from fractions import Fraction
from pathlib import Path
import numpy as np
import z3
from sklearn.linear_model import QuantileRegressor
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc
)
ORIGINAL_REV="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE_CASES=(
    ("lib/Inv_Track/from_2018/fib_21.sl","836f4cbecd25fbd37fddd3a2c3c936a8ac230293",986),
    ("lib/Inv_Track/from_2018/jmbl_hola.41.sl","19e13372aa064e62b539bb6c8fbf13e1d45ccc3c",534)
)
MAX_SAMPLES=270
MAX_DEPTH=6
Z3_MS=2500
def millis(start):return (time.perf_counter_ns()-start)/1e6
def model_vector(model,variables):
    return tuple(model.eval(v,model_completion=True).as_long() for v in variables)
def source_samples(src,native):
    """Native SAT witnesses only, varying a variable by index, never source names."""
    t=time.perf_counter_ns()
    variables=list(src["now"]);nexts=list(src["next"])
    roots=[];seen_roots=set();calls=0
    def sample_pre(idx=None,value=None):
        nonlocal calls
        s=z3.Solver();s.set(timeout=Z3_MS);s.add(native["pre"])
        if idx is not None:s.add(variables[idx]==value)
        calls+=1
        if s.check()==z3.sat:
            x=model_vector(s.model(),variables)
            if x not in seen_roots:
                seen_roots.add(x);roots.append(x)
    sample_pre()
    for val in (0,1,2,3,4,5,-1):
        for idx in range(len(variables)):
            sample_pre(idx,val)
    observed=set();samples=[];edges=[];branch_queries=0
    for root in roots:
        frontier=[(root,0)];visited=set()
        while frontier and len(samples)<MAX_SAMPLES:
            current,depth=frontier.pop(0)
            if (current,depth) in visited:continue
            visited.add((current,depth))
            if current not in observed:
                observed.add(current);samples.append(current)
            if depth>=MAX_DEPTH:continue
            s=z3.Solver();s.set(timeout=Z3_MS)
            s.add(native["trans"])
            s.add(*[v==val for v,val in zip(variables,current)])
            # Explore genuine nondeterministic branches; at most 3 per state.
            for _ in range(3):
                branch_queries+=1
                if s.check()!=z3.sat:break
                after=model_vector(s.model(),nexts)
                edges.append((current,after))
                if after not in observed and len(samples)<MAX_SAMPLES:
                    frontier.append((after,depth+1))
                s.add(z3.Or(*[q!=val for q,val in zip(nexts,after)]))
            if len(samples)>=MAX_SAMPLES:break
    return samples,edges,{"real_native_Pre_solver_calls":calls,
                           "real_native_Trans_solver_calls":branch_queries,
                           "distinct_actual_Pre_roots":len(roots),
                           "distinct_source_state_observations":len(samples),
                           "source_original_transition_edges":len(edges),
                           "data_collection_wall_ms":millis(t)}
def candidate_generator(src,samples,edges,learn):
    start=time.perf_counter_ns()
    n=len(src["now"])
    data=np.asarray(samples,dtype=np.int64)
    candidates={}
    learned_names=set();fits=[]
    def add(expr,origin):
        key=expr.sexpr()
        if key not in candidates:
            candidates[key]=(expr,{origin})
        else:candidates[key][1].add(origin)
        if origin=="TRAINED_QUANTILE":learned_names.add(key)
    # Model-independent, identical-data no-fitting comparator.
    for j in range(n):
        y=src["now"][j]
        add(y>=int(min(data[:,j])),"NO_FIT_INTERVAL")
        add(y<=int(max(data[:,j])),"NO_FIT_INTERVAL")
        for i in range(n):
            if i==j:continue
            x=src["now"][i]
            for slope in (-1,1):
                offsets=[int(row[j])-slope*int(row[i]) for row in samples]
                add(y-slope*x>=min(offsets),"NO_FIT_PAIR_SLOPE1")
                add(y-slope*x<=max(offsets),"NO_FIT_PAIR_SLOPE1")
    if learn:
        # Training targets are ORIGINAL numeric STATE VALUES, never verifier
        # labels, hand-entered invariant identities or solver success outcomes.
        for j in range(n):
            for i in range(n):
                if i==j or len(set(data[:,i].tolist()))<2:continue
                X=data[:,i].reshape(-1,1).astype(float)
                y=data[:,j].astype(float)
                if np.max(np.abs(X))>1e12 or np.max(np.abs(y))>1e12:continue
                for quantile in (0.10,0.90):
                    try:
                        fitted=QuantileRegressor(quantile=quantile,alpha=0.0,solver="highs").fit(X,y)
                        a=Fraction(float(fitted.coef_[0])).limit_denominator(16)
                        if abs(a.numerator)>100000 or a.denominator>16:continue
                        # Derive symbolic offset conservatively from *all*
                        # observed states; exact integer rational arithmetic.
                        residual=[Fraction(int(row[j]))-a*int(row[i]) for row in samples]
                        if not residual:continue
                        lo=min(residual);hi=max(residual)
                        lhs=a.denominator*src["now"][j]-a.numerator*src["now"][i]
                        add(lhs>=int(lo*a.denominator),"TRAINED_QUANTILE")
                        add(lhs<=int(hi*a.denominator),"TRAINED_QUANTILE")
                        fits.append({"dependent_index":j,"independent_index":i,
                                     "quantile":quantile,
                                     "actual_trained_slope":str(a),
                                     "train_observations":len(samples),
                                     "fit_intercept":float(fitted.intercept_)})
                    except Exception as e:
                        fits.append({"dependent_index":j,"independent_index":i,
                                     "quantile":quantile,"abstain":type(e).__name__})
    allc=list(candidates.values())
    return allc,{"training_quantile_fit_calls":len(fits),
                 "trained_valid_quantile_slopes":sum("actual_trained_slope" in z for z in fits),
                 "model_fits":fits,
                 "actual_learned_candidate_signatures":len(learned_names),
                 "all_distinct_candidate_count":len(allc),
                 "candidate_proposal_wall_ms":millis(start)}
def houdini(src,native,candidates):
    t=time.perf_counter_ns()
    true_pre=[];checks=0;unknown=0
    for formula,origins in candidates:
        s=z3.Solver();s.set(timeout=Z3_MS)
        s.add(native["pre"],z3.Not(formula))
        r=s.check();checks+=1
        if r==z3.unsat:true_pre.append((formula,origins))
        elif r==z3.unknown:unknown+=1
    # Houdini is proof-preserving deletion, not an answer oracle for training.
    kept=true_pre;steps=0;deleted=0;status="INCOMPLETE"
    while steps<max(10,len(kept)+1):
        steps+=1
        I=z3.And(*[q for q,_ in kept]) if kept else z3.BoolVal(True)
        nxt=[z3.substitute(q,*list(zip(src["now"],src["next"]))) for q,_ in kept]
        s=z3.Solver();s.set(timeout=Z3_MS)
        s.add(I,native["trans"],z3.Or(*[z3.Not(q) for q in nxt]) if nxt else z3.BoolVal(False))
        result=s.check();checks+=1
        if result==z3.unsat:
            status="FIXPOINT";break
        if result==z3.unknown:
            status="UNKNOWN_CAP";break
        m=s.model()
        violated=[i for i,q in enumerate(nxt)
                  if z3.is_false(m.eval(q,model_completion=True))]
        if not violated:
            status="MODEL_EVALUATION_ERROR";break
        banned=set(violated);deleted+=len(banned)
        kept=[p for i,p in enumerate(kept) if i not in banned]
    I=z3.And(*[q for q,_ in kept]) if kept else z3.BoolVal(True)
    # Final authority DOES NOT come from Houdini's approximate time budget.
    # Independently prove all three full original induction VCs with Z3+cvc5.
    success,proof=verified_3vc(src,native,I)
    learned_in_final=sum("TRAINED_QUANTILE" in owners and
                         not any(x.startswith("NO_FIT") for x in owners) for _,owners in kept)
    return {"status":status,"fully_verified_complete_original_3VC":bool(success),
            "kept_candidate_count":len(kept),
            "retained_train_only_candidates":learned_in_final,
            "retained_source_ast_sha256":hashlib.sha256(I.sexpr().encode()).hexdigest(),
            "retained_candidate_formulas":[{"smt":q.sexpr(),"origins":sorted(o)} for q,o in kept],
            "independent_original_pre_trans_post_dual_proofs":proof,
            "Houdini_iterations":steps,"precondition_checks":len(candidates),
            "candidate_deletions_induction":deleted,"solver_calls":checks,
            "solver_unknown_single_pre_check":unknown,
            "verified_proof_and_houdini_wall_ms":millis(t)}
def one(root,item):
    begin=time.perf_counter_ns()
    result={"source":item["path"],"original_git_blob":item["git_blob"],
            "status":"ABSTAIN","actually_trained_learned_numeric_relation_model":False}
    try:
        raw,src,native,identity=prepare(root,item)
        result["source_identity"]=identity
        samples,edges,sampling=source_samples(src,native)
        if len(samples)<3 or len(edges)<2:raise RuntimeError("INSUFFICIENT_TRUE_SOURCE_TRANSITION_OBSERVATIONS")
        result["source_original_samples"]=sampling
        candidates,trained=candidate_generator(src,samples,edges,True)
        result["actually_trained_learned_numeric_relation_model"]=trained["trained_valid_quantile_slopes"]>0
        result["training"]=trained
        result["TRAINED_model_source_invariant"]=houdini(src,native,candidates)
        baselines=[(q,o) for q,o in candidates if "TRAINED_QUANTILE" not in o or
                   any(x.startswith("NO_FIT") for x in o)]
        result["ZERO_TRAIN_equal_data_shallow_linear_Houdini"]=houdini(src,native,baselines)
        result["training_model_unique_bounded_original_discovery"]=bool(
            result["TRAINED_model_source_invariant"]["fully_verified_complete_original_3VC"] and
            not result["ZERO_TRAIN_equal_data_shallow_linear_Houdini"]["fully_verified_complete_original_3VC"] and
            result["TRAINED_model_source_invariant"]["retained_train_only_candidates"]>0)
        result["status"]="EXECUTED_TRAINED_VS_NO_FIT_NATIVE_SOURCE_3VC"
    except Exception as e:
        result["status"]="ABSTAIN_SOURCE_OR_DATA_OR_SOLVER"
        result["exception"]=type(e).__name__+":"+str(e)[:440]
    result["total_model_training_sampling_proposal_and_original_proof_wall_ms"]=millis(begin)
    print("Q3_ACTUAL_TRAINED_SOURCE",item["path"],"STATUS",result["status"],
          "TRAINED",result.get("actually_trained_learned_numeric_relation_model"),
          "ORIGINAL_PROOF",result.get("TRAINED_model_source_invariant",{}).get("fully_verified_complete_original_3VC"),
          "NO_FIT_PROOF",result.get("ZERO_TRAIN_equal_data_shallow_linear_Houdini",{}).get("fully_verified_complete_original_3VC"),
          "TRAIN_ONLY_PROVED",result.get("TRAINED_model_source_invariant",{}).get("retained_train_only_candidates"),
          "ERROR",result.get("exception"),flush=True)
    return result
def main():
    p=argparse.ArgumentParser()
    for key in ("root","source-freeze","out"):p.add_argument("--"+key,required=True)
    a=p.parse_args()
    m=json.loads(Path(a.source_freeze).read_text())
    cases=m["new_originals"]
    frozen={x["path"]:x for x in cases}
    required=[]
    for path,sha,bytes_ in SOURCE_CASES:
        if path not in frozen or frozen[path]["git_blob"]!=sha or frozen[path]["bytes"]!=bytes_:
            raise RuntimeError("FROZEN_SOURCE_IDENTITY_MISMATCH")
        required.append(frozen[path])
    out=[one(Path(a.root),q) for q in required]
    report={
      "schema":"neumann.q3.development_actual_trained_affine_proposal_from_original_transitions.v1",
      "already_opened_original_source_after_previous_Q4_test":True,
      "neural_weights_or_manual_prior_solution_injected":False,
      "model_family":"sklearn_QuantileRegressor_self_supervised_real_original_trajectory_feature_relationships",
      "genuine_original_source_count":2,
      "real_trained_model_executed_count":sum(r["actually_trained_learned_numeric_relation_model"] for r in out),
      "original_source_native_inductive_3VC_trained_pass":sum(r.get("TRAINED_model_source_invariant",{}).get("fully_verified_complete_original_3VC",False) for r in out),
      "original_source_native_inductive_3VC_no_fit_shallow_pass":sum(r.get("ZERO_TRAIN_equal_data_shallow_linear_Houdini",{}).get("fully_verified_complete_original_3VC",False) for r in out),
      "bounded_train_only_contribution":sum(r.get("training_model_unique_bounded_original_discovery",False) for r in out),
      "originals":out,
      "strong_classical_Houdini_is_allowed_equal_authority":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"}
    Path(a.out).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for key in ("real_trained_model_executed_count","original_source_native_inductive_3VC_trained_pass",
                "original_source_native_inductive_3VC_no_fit_shallow_pass","bounded_train_only_contribution"):
        print("ACTUAL_TRAINED_DISCOVERY_EVIDENCE",key,report[key])
    print("Q3_GLOBAL",report["global_Q3"])
if __name__=="__main__":main()
