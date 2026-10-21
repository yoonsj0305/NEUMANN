"""Actually trained CPU tree proposes original native fib32 phase invariant.

Unlike historical PR373 the phase offsets i-j are NOT encoded. They are
learned from source-executed Z3 SAT trajectories (k=1..5 only); the model
then proposes original symbolic case clauses, independently Z3+cvc5 checked
on unrestricted source k>0, not just sampled rollouts. Heldout k=6..12.

IMPORTANT epistemic boundary: source names, phase features n%2/b, safety
envelope k>0, 0<=n<=2*k are HUMAN-PRESELECTED on this already opened
program. Classic lookup constructed from IDENTICAL trace data can recover
the same candidate. No learned UNIQUE Q3, no unseen-source claim.
"""
from __future__ import annotations
import argparse, hashlib, json, os, resource, time
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeRegressor
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare, verified_3vc, original_syguS, native_pdr
)

ORIGINAL_PATH="lib/Inv_Track/from_2018/fib_32.sl"
ORIGINAL_BLOB="4fb129488bee3e1e0cdae899b318d6503ae23c12"
ORIGINAL_SIZE=824
SOURCE_FREEZE="6a5792e196b2234358dca31ec9dd733f3ffed42d"
PRE_REGISTERED_COMMIT="d818e153b46a513c2f5a599425e8b8c8ed2ce6b8"
INVARIANT_PROPOSER_HUMAN_FEATURE_GRAMMAR=("n_parity","b")
INITIAL_TRAIN_K=tuple(range(1,6))
OUT_OF_TRAIN_K=tuple(range(6,13))
TREE_RANDOM_STATE=20261021

def millis(start_ns):
    return (time.perf_counter_ns()-start_ns)/1_000_000

def check_original_state(s,native,variables,state):
    solver=z3.Solver();solver.set(timeout=3000)
    solver.add(native["pre"])
    solver.add(*[v==state[idx] for idx,v in enumerate(variables)])
    verdict=solver.check()
    if verdict!=z3.sat:
        raise RuntimeError("SOURCE_CONCRETE_INITIAL_STATE_NOT_NATIVE_PRE_SAT:"+str(verdict))

def source_native_rollout(src,native,number_k,initial_b):
    """Every next state is fetched from the actual ORIGINAL TransF SAT model;
    no manual update logic or reference invariant is ever used."""
    names=[name for name,sort in src["states"]]
    if names!=["k","b","i","j","n"]:
        raise RuntimeError("SOURCE_NATIVE_TRUE_FIB32_SIGNATURE_CHANGED")
    now=src["now"];nxt=src["next"]
    state=[int(number_k),int(initial_b),0,0,0]
    check_original_state(z3.Solver(),native,now,state)
    rows=[]
    clock=time.perf_counter_ns()
    for step in range(2*number_k+1):
        k,b,i,j,n=state
        if k!=number_k or n!=step:
            raise RuntimeError("SOURCE_TRANSITION_TRAJECTORY_K_OR_N_INVARIANT_INVALID")
        rows.append({"features":[int(n%2),int(b)],"observed_offset_i_minus_j":int(i-j),
                     "actual_state":[int(z) for z in state],"k_training_or_test":int(number_k)})
        if step==2*number_k:break
        solver=z3.Solver();solver.set(timeout=3000)
        solver.add(native["trans"])
        solver.add(*[var==v for var,v in zip(now,state)])
        result=solver.check()
        if result!=z3.sat:
            raise RuntimeError("TRUE_ORIGINAL_SOURCE_TRANS_WITNESS_NOT_SAT:"+str(result))
        m=solver.model()
        state=[int(m.eval(q,model_completion=True).as_long()) for q in nxt]
    return rows,{"k":number_k,"initial_b":initial_b,"actual_source_native_transition_SAT_calls":2*number_k,
                 "rollout_and_solver_cost_ms":millis(clock)}

def execute_splits(src,native,ks):
    all_rows=[];receipts=[]
    for k in ks:
        for start_b in (0,1):
            rows,rec=source_native_rollout(src,native,k,start_b)
            all_rows.extend(rows);receipts.append(rec)
    return all_rows,receipts

def actual_cpu_train(X,Y,feature_indices=None,permuted=False):
    if feature_indices is None:feature_indices=(0,1)
    x=np.array(X,dtype=np.float64)[:,list(feature_indices)]
    y=np.array(Y,dtype=np.float64)
    if permuted:
        perm=np.random.default_rng(20261021).permutation(len(y))
        y=y[perm]
    t=time.perf_counter_ns()
    model=DecisionTreeRegressor(max_depth=3,random_state=TREE_RANDOM_STATE)
    model.fit(x,y)
    elapsed=millis(t)
    return model,elapsed,{"nodes":int(model.tree_.node_count),
                          "leaves":int(model.get_n_leaves()),
                          "learned_tree_feature":model.tree_.feature.tolist(),
                          "learned_tree_split_threshold":model.tree_.threshold.tolist(),
                          "learned_leaf_offsets":model.tree_.value.reshape(-1).tolist(),
                          "actual_fit_samples":len(y),
                          "actual_train_labels_permuted":bool(permuted),
                          "feature_indices":list(feature_indices)}

def extract_case_offsets(model,indices):
    mapping={}
    for p in (0,1):
        for b in (0,1):
            v=np.asarray([[p,b]],dtype=np.float64)[:,list(indices)]
            prediction=float(model.predict(v)[0])
            if not np.isfinite(prediction) or abs(prediction-round(prediction))>1e-9:
                return None,{"bad_feature_case":[p,b],"nonintegral_prediction":prediction}
            mapping[(p,b)]=int(round(prediction))
    return mapping,None

def source_grammar_to_inductive_candidate(src,mapping):
    if mapping is None or set(mapping)!={(p,b) for p in (0,1) for b in (0,1)}:
        raise ValueError("TRAINED_MODEL_DID_NOT_CREATE_COMPLETE_TYPED_ORIGINAL_MAP")
    k,b,i,j,n=src["now"]
    envelope=z3.And(k>0,n>=0,n<=2*k,z3.Or(b==0,b==1))
    learned_terms=[
        z3.And(n%2==p,b==bit,i-j==mapping[(p,bit)])
        for p in (0,1) for bit in (0,1)]
    return z3.And(envelope,z3.Or(*learned_terms))

def independently_validate_candidate(src,native,mapping,label):
    if mapping is None:
        return {"label":label,"actual_original_3VC_dual_success":False,
                "status":"ABSTAIN_NONINTEGER_LEARNED_OUTPUT"}
    candidate=source_grammar_to_inductive_candidate(src,mapping)
    start=time.perf_counter_ns()
    okay,checks=verified_3vc(src,native,candidate)
    return {"label":label,"actual_original_3VC_dual_success":bool(okay),
            "full_original_Z3_cvc5_3VC_receipts":checks,
            "original_true_source_AST_candidate_sha256":hashlib.sha256(candidate.sexpr().encode()).hexdigest(),
            "original_true_source_actual_symbolic_invariant":candidate.sexpr(),
            "prediction_by_human_selected_phase_features":{
                f"parity{p}_branch{b}":mapping[(p,b)] for p in (0,1) for b in (0,1)},
            "full_original_3VC_wall_ms":millis(start)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    contract=json.loads(a.contract.read_text())
    if contract["schema"]!="neumann.q3.20261021.posthoc_original_fib32_actually_trained_phase_proposer.v1":
        raise RuntimeError("FROZEN_REAL_CPU_LEARNER_PROTOCOL_CHANGED")
    freeze=json.loads(a.freeze.read_text())
    item=next(q for q in freeze["cases"] if q["path"]==ORIGINAL_PATH)
    if item["git_blob"]!=ORIGINAL_BLOB or item["bytes"]!=ORIGINAL_SIZE:
        raise RuntimeError("HISTORIC_AUTHENTIC_SOURCE_FIB32_CHANGED")
    full_start=time.perf_counter_ns()
    report={"schema":"neumann.q3.real_cpu_trained_fib32_posthoc_source_phase_proposer_dual_3vc.v1",
            "preregistered_before_training_SHA":PRE_REGISTERED_COMMIT,
            "original_source_frozen_before_training_SHA":SOURCE_FREEZE,
            "posthoc_source_and_human_feature_grammar_leaked":True,
            "actual_model_training_updates":0,
            "actual_original_full_native_3VC_learned_proposer_pass":False,
            "not_a_unique_learned_Q3_result":True,
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN",
            "status":"INCOMPLETE"}
    try:
        raw,src,native,identity=prepare(a.root,item)
        report["authenticated_original_native_source"]=identity
        train,train_receipts=execute_splits(src,native,INITIAL_TRAIN_K)
        test,test_receipts=execute_splits(src,native,OUT_OF_TRAIN_K)
        report["training_actual_original_Z3_executed_rows"]=len(train)
        report["heldout_k6_to_12_original_Z3_executed_rows"]=len(test)
        report["original_true_source_trace_proof_costs_training"]=train_receipts
        report["original_true_source_trace_proof_costs_holdout"]=test_receipts
        x=[r["features"] for r in train]
        y=[r["observed_offset_i_minus_j"] for r in train]
        learned,fit_ms,tree=actual_cpu_train(x,y)
        mapping,err=extract_case_offsets(learned,(0,1))
        if err is not None:raise RuntimeError("TRAINED_TYPED_MODEL_ABSTAIN:"+str(err))
        report["actual_model_training_updates"]=1
        report["CPU_decision_tree_training_wall_ms"]=fit_ms
        report["actual_trained_tree_learned_structure"]=tree
        learned_result=independently_validate_candidate(src,native,mapping,"actual_fitted_CPU_tree")
        report["actual_original_trained_model_proposed_source_native_3VC"]=learned_result
        report["actual_original_full_native_3VC_learned_proposer_pass"]=learned_result["actual_original_3VC_dual_success"]
        # Test is unseen parametric values, NOT an unseen source program.
        y_hat=[int(round(v)) for v in learned.predict(np.array([r["features"] for r in test],dtype=float))]
        y_test=[r["observed_offset_i_minus_j"] for r in test]
        report["heldout_original_transition_state_predictions_correct"]=sum(a==b for a,b in zip(y_hat,y_test))
        report["heldout_original_transition_state_predictions_total"]=len(y_test)
        report["heldout_k_outside_training_support"]=all(r["k_training_or_test"]>5 for r in test)
        # Model absent entirely: same original trace data, source-feature grammar
        # supplied, deterministic finite bucket lookup with zero training.
        table_begin=time.perf_counter_ns()
        buckets=defaultdict(set)
        for row in train:
            buckets[tuple(row["features"])].add(row["observed_offset_i_minus_j"])
        deterministic_mapping=( {key:next(iter(vals)) for key,vals in buckets.items()}
                               if len(buckets)==4 and all(len(v)==1 for v in buckets.values()) else None )
        report["nonlearner_exact_finite_trace_lookup_build_ms"]=millis(table_begin)
        report["nonlearner_same_source_trace_lookup"]=independently_validate_candidate(
            src,native,deterministic_mapping,"zero_train_deterministic_original_trace_table")
        report["learned_vs_zero_train_actual_typed_invariant_identical_SHA256"]=(
            learned_result["original_true_source_AST_candidate_sha256"]==
            report["nonlearner_same_source_trace_lookup"]["original_true_source_AST_candidate_sha256"])
        report["finite_feature_domain_count"]=4
        report["finite_source_feature_table_complete_and_unique"]=(
            deterministic_mapping is not None and
            all(len(values)==1 for values in buckets.values()))
        # This *concrete bounded question* is now adjudicated:
        # both mechanisms propose the IDENTICAL native original formula.
        # A statistical fit cannot be a UNIQUE original-solving capability
        # over a zero-learn direct exact four-key table on this program.
        report["bounded_original_learned_unique_advantage_absent_on_this_domain"]=(
            report["learned_vs_zero_train_actual_typed_invariant_identical_SHA256"] and
            report["finite_source_feature_table_complete_and_unique"] and
            learned_result["actual_original_3VC_dual_success"] and
            report["nonlearner_same_source_trace_lookup"]["actual_original_3VC_dual_success"])
        report["no_train_hypothesis_constant_zero"]=independently_validate_candidate(
            src,native,{(p,b):0 for p in (0,1) for b in (0,1)},"nonlearner_constant_i_eq_j")
        parity_tree,parity_cost,parity_desc=actual_cpu_train(x,y,feature_indices=(0,))
        parity_map,parity_error=extract_case_offsets(parity_tree,(0,))
        report["ablated_parity_only_CPU_train_wall_ms"]=parity_cost
        report["ablated_parity_only_tree_structure"]=parity_desc
        report["ablated_parity_only_output_grammar_error"]=parity_error
        report["ablated_parity_only_full_original_verification"]=independently_validate_candidate(
            src,native,parity_map,"trained_parity_only_without_original_branch_feature")
        shuffled,shuffled_cost,shuffle_desc=actual_cpu_train(x,y,permuted=True)
        shuffle_map,shuffle_error=extract_case_offsets(shuffled,(0,1))
        report["ablated_permuted_label_train_wall_ms"]=shuffled_cost
        report["ablated_permuted_tree_structure"]=shuffle_desc
        report["ablated_permuted_output_grammar_error"]=shuffle_error
        report["ablated_permuted_label_original_3VC"]=independently_validate_candidate(
            src,native,shuffle_map,"randomly_permuted_original_trace_offset_labels")
        # Actual equally authorized generic strongest Direct, not simulated
        # static historical citations. These can legitimately stay UNKNOWN.
        report["same_CPU_original_raw_strong_cvc5_SyGuS_3s"]=original_syguS(raw,src,native,3.0)
        report["same_CPU_original_raw_strong_Z3_Spacer"]=native_pdr(src,native)
        report["process_max_RSS_kilobytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report["status"]="COMPLETE_TRAINED_TRUE_ORIGINAL_PROOFCARRYING_STRUCTURE_EXPERIMENT"
    except Exception as e:
        report["status"]="FAIL_CLOSED_SOURCE_TRAINING_OR_INDEPENDENT_PROOF_EXCEPTION"
        report["error"]=type(e).__name__+":"+str(e)[:500]
    report["all_tracing_training_learning_independent_verification_and_ablations_wall_ms"]=millis(full_start)
    report["global_Q3"]="OPEN"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_REAL_CPU_TRAINED_SOURCE_FIB32_PHASE_3VC_DUAL",
          report["actual_original_full_native_3VC_learned_proposer_pass"])
    print("Q3_REAL_CPU_TRAINED_SOURCE_FIB32_HELDOUT_TRACES",
          report.get("heldout_original_transition_state_predictions_correct"),
          "/",report.get("heldout_original_transition_state_predictions_total"))
    print("Q3_REAL_CPU_TRAINED_NONLEARNER_SAME_SOURCE_TABLE_ORIGINAL_3VC",
          report.get("nonlearner_same_source_trace_lookup",{}).get("actual_original_3VC_dual_success"))
    print("Q3_REAL_CPU_TRAINED_AND_NONLEARNED_PROPOSALS_EXACT_AST_HASH_EQUAL",
          report.get("learned_vs_zero_train_actual_typed_invariant_identical_SHA256"))
    print("Q3_REAL_CPU_TRAINED_ONLY_FOUR_FEATURE_CASES_CLASSICAL_LOOKUP_DOMINATES",
          report.get("bounded_original_learned_unique_advantage_absent_on_this_domain"),
          "MODEL_FIT_MS",report.get("CPU_decision_tree_training_wall_ms"),
          "CLASSICAL_TABLE_BUILD_MS",report.get("nonlearner_exact_finite_trace_lookup_build_ms"))
    print("Q3_REAL_CPU_TRAINED_PARITY_ONLY_NEGATIVE",
          report.get("ablated_parity_only_full_original_verification",{}).get("actual_original_3VC_dual_success"))
    print("Q3_REAL_CPU_TRAINED_SHUFFLED_LABEL_NEGATIVE",
          report.get("ablated_permuted_label_original_3VC",{}).get("actual_original_3VC_dual_success"))
    print("Q3_REAL_CPU_TRAINED_SOURCE_FIB32_STATUS",report["status"],report.get("error"))
    print("Q3_REAL_CPU_TRAINED_GLOBAL_Q3_OPEN",report["global_Q3"])
if __name__=="__main__":
    main()
