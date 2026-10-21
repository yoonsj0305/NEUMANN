"""Source-first-blind 12 REAL ORIGINAL programs: actually trained CPU verifier router.

The model predicts only WHICH EXISTING CLASSICAL PROVER TO INVOKE.
Not novel invariants, not learned Q3 global, not frontier compute proof.
All 12 heldout Git blobs selected and locked BEFORE opening source bodies.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, time
from pathlib import Path
import z3
import numpy as np
from sklearn.tree import DecisionTreeClassifier
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as base
from research.evidence.q4_source12_budget_20261021.real_12_native_full_cost_portfolio import (
    post_only, ms
)
REV="13c8deb68a873635879c9a69bc78caebd340f646"
TRAIN_RECEIPT_SHA="fa0fc6f7218761082aef77d02efdbe91da541477800eea8d32c956dd0e9e6839"
FRESH_FREEZE_COMMIT="4cd7ab0016e891af94deb702fdc4f7eb363cbf9b"
KINDS=(
    z3.Z3_OP_AND,z3.Z3_OP_OR,z3.Z3_OP_NOT,
    z3.Z3_OP_EQ,z3.Z3_OP_LT,z3.Z3_OP_LE,z3.Z3_OP_GT,z3.Z3_OP_GE,
    z3.Z3_OP_ADD,z3.Z3_OP_SUB,z3.Z3_OP_MUL,z3.Z3_OP_ITE,
    z3.Z3_OP_MOD,z3.Z3_OP_IDIV,z3.Z3_OP_IMPLIES
)
def sha_git(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def walk(expr):
    n=0;freq=collections.Counter()
    # Traversal counts full syntax-tree occurrences, not variable names or gold.
    stack=[expr]
    while stack:
        q=stack.pop();n+=1
        if z3.is_app(q):
            freq[q.decl().kind()]+=1
            stack.extend(q.children())
    return n,freq
def features(raw,src,native):
    v=[len(src["now"]),len(raw)]
    freq=collections.Counter()
    for k in ("pre","trans","post"):
        n,counts=walk(native[k])
        v.append(n);freq.update(counts)
    v.extend(freq[k] for k in KINDS)
    return v

def oracle_training_label(entry):
    assert entry["status"]=="COMPLETE_THREE_ACTUAL_ORIGINAL_ROUTES"
    op=entry["fixed_post_first_cheapest_safe"]["original_Post_dual3VC"]
    sg=entry["standalone_cvc5_SyGuS"]
    pd=entry["standalone_Z3_SPACER"]
    options=[]
    if op["certified"]:options.append((op["wall_ms"],"P"))
    if sg["certified"]:options.append((sg["total_route_wall_ms"],"S"))
    if pd["certified"]:options.append((pd["total_route_wall_ms"],"D"))
    if not options:return None
    return min(options)[1]

def train(root,old_freeze,raw_train):
    start=time.perf_counter_ns()
    if hashlib.sha256(raw_train).hexdigest()!=TRAIN_RECEIPT_SHA:
        raise RuntimeError("NEUMANN_ORIGINAL_Q4_TRAIN_RESULT_IMMUTABLE_SHA_MISMATCH")
    prior=json.loads(raw_train)
    assert prior["schema"]=="neumann.q4.genuine_prior_opened_original12_CPU_proof_matched_cost_v1"
    assert prior["actually_executed_full_three_route_cases"]==12
    old=old_freeze["cases"]
    assert len(old)==12 and len(prior["originals"])==12
    X=[];Y=[];rows=[]
    for orig,record in zip(old,prior["originals"]):
        assert orig["path"]==record["source"] and orig["git_blob"]==record["git_blob"]
        assert record["source_valid"] and record["source_SHA_authenticated"]
        label=oracle_training_label(record)
        if label is None:continue
        raw,src,native,receipt=base.prepare(root,orig)
        X.append(features(raw,src,native));Y.append(label)
        rows.append({"original_blob":orig["git_blob"],"training_label":label,
                     "original_full_source_pre_trans_post_identity":receipt,
                     "source_independent_feature_values":X[-1]})
    assert len(X)==12 and len({r["original_blob"] for r in rows})==12
    t=time.perf_counter_ns()
    mdl=DecisionTreeClassifier(max_depth=2,min_samples_leaf=2,random_state=20261021)
    mdl.fit(np.asarray(X,dtype=np.int64),np.asarray(Y))
    fit=ms(t)
    majority=collections.Counter(Y).most_common(1)[0][0]
    return mdl,{
        "source_train_genuine_originals":len(X),"human_gold_smt_invariant_labels_used":False,
        "training_true_historical_posthoc_task_cost_labels":list(Y),
        "training_prior_input_json_sha256":TRAIN_RECEIPT_SHA,
        "feature_dimension":len(X[0]),
        "training_data_excludes_every_new_original":True,
        "training_label_histogram":dict(collections.Counter(Y)),
        "fitted_model_depth":int(mdl.get_depth()),
        "fitted_model_leaves":int(mdl.get_n_leaves()),
        "actual_model_fit_wall_ms":fit,
        "full_training_load_source_parsing_Z3_cvc5_features_and_fit_wall_ms":ms(start),
        "zero_learn_majority_label":majority,
        "trained_original_source_evidence":rows
    }

def invoke(route,raw,src,native):
    start=time.perf_counter_ns();calls=[]
    if route=="P": schedule=("P","f","D")
    elif route=="S":schedule=("S","D")
    elif route=="D":schedule=("D","S")
    else:raise ValueError("OUT_OF_FROZEN_TRINARY_ROUTE")
    certified=False
    for name in schedule:
        if name=="P":
            q=post_only(src,native);success=q["certified"]
        elif name=="f":
            q=base.original_syguS(raw,src,native,.55);success=q["certified"]
        elif name=="S":
            q=base.original_syguS(raw,src,native,3.0);success=q["certified"]
        else:
            q=base.native_pdr(src,native);success=q["certified"]
        calls.append({"route":name,"receipt":q,"fully_native_independent_3VC_certified":bool(success)})
        if success:certified=True;break
    return {"chosen_primary_route":route,"calls":calls,"original_full_dual_certified":certified,
            "full_actual_route_wall_ms":ms(start),
            "failed_solver_calls_retained":sum(not t["fully_native_independent_3VC_certified"] for t in calls)}

def per_new(root,item,i,model,train):
    initial=time.perf_counter_ns()
    entry={"source":item["path"],"git_blob":item["git_blob"],"status":"ABSTAIN","original_file_exact_SHA_authenticated":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if sha_git(raw)!=item["git_blob"] or len(raw)!=item["bytes"]:
            raise RuntimeError("NEW_ORIGINAL_SOURCE_SHA_OR_SIZE_NOT_FROZEN")
        entry["original_file_exact_SHA_authenticated"]=True
        t=time.perf_counter_ns()
        raw,src,native,proof=base.prepare(root,item)
        entry["same_original_full_Pre_Trans_Post_independent_source_parity"]=proof
        entry["common_authentication_native_compile_proof_ms"]=ms(t)
        if i==0:
            false_ok,tests=base.verified_3vc(src,native,z3.BoolVal(False))
            entry["source_negative_mutant_Post_false_rejected"]=not false_ok
            entry["negative_control_actual_Z3_cvc5_receipts"]=tests
            if false_ok:raise RuntimeError("FALSE_SOURCE_MUTATION_PROVED_SAFE")
        t=time.perf_counter_ns()
        xs=features(raw,src,native)
        predict=str(model.predict([xs])[0])
        entry["actual_source_feature_and_CPU_inference_wall_ms"]=ms(t)
        entry["neural_forwards"]=0
        entry["model_prediction_without_heldout_solver_gold"]=predict
        entry["actual_source_features_not_names"]=xs
        # Bounded actual comparisons. Repeat each full complete-task route on
        # EXACT same original, with fallback; never use outcome oracle at inference.
        orders=("P","S","D") if i%2==0 else ("D","S","P")
        comps={}
        for cls in orders:
            comps[cls]=invoke(cls,raw,src,native)
        entry["static_P_POST_FastSyGuS_PDR"]=comps["P"]
        entry["static_S_SyGuS_PDR"]=comps["S"]
        entry["static_D_PDR_SyGuS"]=comps["D"]
        entry["trained_routing_full_original"]=invoke(predict,raw,src,native)
        successes={k:v["original_full_dual_certified"] for k,v in comps.items()}
        entry["all_comparators_original_proof_success"]=successes
        entry["matched_baseline_success_count"]=sum(successes.values())
        entry["matched_trained_success"]=entry["trained_routing_full_original"]["original_full_dual_certified"]
        # Only posthoc accuracy diagnostic. Never use these labels in selection.
        post_diag=comps["P"]["calls"][0]
        known=[(post_diag["receipt"]["wall_ms"],"P")] if post_diag["fully_native_independent_3VC_certified"] else []
        # Static S and D have fallback. Their first attempts are fair oracle
        # candidate costs only when successful on first call.
        for label in ("S","D"):
            first=comps[label]["calls"][0]
            if first["fully_native_independent_3VC_certified"]:
                known.append((first["receipt"]["total_route_wall_ms"],label))
        true_cheapest=min(known)[1] if known else None
        entry["posthoc_primary_fastest_label_NOT_model_input"]=true_cheapest
        entry["trained_correct_primary_label"]=predict==true_cheapest
        entry["zero_learning_train_majority_correct_label"]=(train["zero_learn_majority_label"]==true_cheapest)
        common=entry["common_authentication_native_compile_proof_ms"]
        entry["model_full_deployment_wall_with_amortized_training_ms"]=(
            common+entry["actual_source_feature_and_CPU_inference_wall_ms"]+
            entry["trained_routing_full_original"]["full_actual_route_wall_ms"]+
            train["full_training_load_source_parsing_Z3_cvc5_features_and_fit_wall_ms"]/12)
        entry["static_deployment_wall_including_same_source_prep_ms"]={
            cls:common+comps[cls]["full_actual_route_wall_ms"] for cls in ("P","S","D")}
        entry["status"]="COMPLETE_SAME_NATIVE_ORIGINAL_CPU_ROUTE_COMPARISON"
    except Exception as e:
        entry["status"]="ABSTAIN_NATIVE_SOURCE_UNSUPPORTED_OR_RUNTIME"
        entry["exception"]=type(e).__name__+":"+str(e)[:450]
    entry["full_repeated_study_wall_ms"]=ms(initial)
    print("Q4Q6_FRESH_ORIGINAL",i+1,entry["source"],entry["status"],
          "PRED",entry.get("model_prediction_without_heldout_solver_gold"),
          "SUCCESS",entry.get("matched_trained_success"),
          "P/S/D",entry.get("all_comparators_original_proof_success"),
          "ACC",entry.get("trained_correct_primary_label"),flush=True)
    return entry

def run(root,freeze,oldfreeze,contract,trainbytes):
    assert contract["schema"]=="neumann.q4q6.first_fresh_12_CPU_trained_verifier_dispatch_complete_system.v1"
    assert contract["locked_heldout_metadata_commit"]==FRESH_FREEZE_COMMIT
    assert freeze["schema"]=="neumann.q4q6_first12_heldout_original_source_metadata_LOCK_v1"
    assert freeze["upstream"].split("@")[-1]==REV and len(freeze["new_originals"])==12
    assert len({z["git_blob"] for z in freeze["new_originals"]})==12
    assert len([z for z in freeze["new_originals"] if z["family"]=="fib"])==6
    assert len([z for z in freeze["new_originals"] if z["family"]=="nonfib"])==6
    assert not {x["git_blob"] for x in freeze["new_originals"]}&{
        x["git_blob"] for x in oldfreeze["cases"]}
    base.PDR_MS=5000
    t=time.perf_counter_ns()
    model,train=train_model(root,oldfreeze,trainbytes)
    duration=ms(t)
    assert train["source_train_genuine_originals"]==12
    new=[per_new(root,z,i,model,train) for i,z in enumerate(freeze["new_originals"])]
    valid=[r for r in new if r["status"]=="COMPLETE_SAME_NATIVE_ORIGINAL_CPU_ROUTE_COMPARISON"]
    matched=[r for r in valid if r["matched_trained_success"] and all(
        r["all_comparators_original_proof_success"].values())]
    matched_same=[r for r in valid if r["matched_trained_success"] and any(
        r["all_comparators_original_proof_success"].values())]
    full={k:sum(r["static_deployment_wall_including_same_source_prep_ms"][k] for r in matched) for k in ("P","S","D")}
    traincost=sum(r["model_full_deployment_wall_with_amortized_training_ms"] for r in matched)
    strong=min(full.values()) if full else None
    # This is a source-collection BEST static comparator chosen POSTHOC,
    # explicitly an optimistic lower bound, NOT available at deployment.
    report={
      "schema":"neumann.q4q6.source_disjoint_real_CPU_router_first_new_originals_v1",
      "training_original_count":train["source_train_genuine_originals"],
      "new_original_count":len(new),"fully_executed_new_originals":len(valid),
      "new_original_SHA_authenticated":sum(x["original_file_exact_SHA_authenticated"] for x in new),
      "trained_new_original_full_native_3VC_success":sum(x["matched_trained_success"] for x in valid),
      "static_P_success":sum(x["all_comparators_original_proof_success"]["P"] for x in valid),
      "static_S_success":sum(x["all_comparators_original_proof_success"]["S"] for x in valid),
      "static_D_success":sum(x["all_comparators_original_proof_success"]["D"] for x in valid),
      "matched_every_full_method_certified_same_sources":len(matched),
      "matched_trained_and_any_baseline_certified":len(matched_same),
      "matched_best_static_cohort_posthoc_lowerbound_wall_ms":strong,
      "matched_trained_full_cost_amortized_wall_ms":traincost,
      "matched_best_static_posthoc_over_trained_wall_ratio":(
          strong/traincost if traincost>0 and strong is not None else None),
      "matched_static_full_costs_ms":full,
      "learned_primary_route_exact_hindsight_accuracy":sum(r["trained_correct_primary_label"] for r in valid),
      "majority_no_train_exact_hindsight_accuracy":sum(r["zero_learning_train_majority_correct_label"] for r in valid),
      "all_source_data_heldout_until_official_run":True,
      "training_was_on_separate_previously_OPENED_originals":True,
      "no_new_inductive_invariant_learning_or_Q3_discovery":True,
      "all_classical_verifiers_have_equal_authority":True,
      "model_training_update_once":1,"model_inference_calls":len(valid),
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "training":train,"original_new_programs":new
    }
    return report

# Explicit alias prevents accidental recursion if replacing training code.
train_model=train

def main():
    p=argparse.ArgumentParser()
    for name in ("root","freeze","oldfreeze","contract","prior-result","out"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    x=run(Path(a.root),json.loads(Path(a.freeze).read_text()),
          json.loads(Path(a.oldfreeze).read_text()),
          json.loads(Path(a.contract).read_text()),Path(getattr(a,"prior_result").replace("-","_") if False else a.prior_result).read_bytes())
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    for key in ("training_original_count","new_original_count","fully_executed_new_originals",
                "trained_new_original_full_native_3VC_success","static_P_success","static_S_success","static_D_success",
                "matched_every_full_method_certified_same_sources","matched_best_static_posthoc_over_trained_wall_ratio",
                "learned_primary_route_exact_hindsight_accuracy","majority_no_train_exact_hindsight_accuracy"):
        print("Q4Q6_FRESH_REAL_ORIGINAL",key,x[key])
    print("Q3_Q4_Q6_GLOBAL","OPEN")
if __name__=="__main__":main()
