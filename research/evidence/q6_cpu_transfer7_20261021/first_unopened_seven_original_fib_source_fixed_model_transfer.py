"""First true source-body blind seven-program transfer of fixed PR376 model.

NEVER fit the tree on target source. Train only on fib32 native original
reachable k1..5 source-transition data, then hold the FOUR CASE OUTPUTS
fixed for seven precommitted unseen source BODY files.

Conservative typed grammar requires an exact (k,b,i,j,n) native program
signature. Interface mismatch is a distinct ABSTAIN, not source UNSAFE or
a learned invariant wrong. For compatible original source, require actual
independently native full Z3/cvc5 three verification conditions PASS.

Given no generic AST role adapter, do not claim Q6 independent author or
strong generalization if the model cannot apply to a new source.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import z3
from research.evidence.q3_cpu_phase_20261021.real_original_fib32_cpu_trained_phase_source_3vc import (
    ORIGINAL_PATH,ORIGINAL_BLOB,ORIGINAL_SIZE,
    INITIAL_TRAIN_K,execute_splits,actual_cpu_train,extract_case_offsets,
    independently_validate_candidate,millis
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,original_syguS,native_pdr
)
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
FROZEN_BEFORE_ANY_NEW_TEST_BODY_COMMIT="aed388ba7e00a31049d2f0612dfc4d7af22e7d71"
TYPED_INTERFACE=["k","b","i","j","n"]

def sha1blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def test_actual_new_program(root,item,mapping,nonlearned_map):
    start=time.perf_counter_ns()
    record={"actual_original_source":item["path"],
            "original_git_sha_expected":item["git_blob"],
            "original_source_SHA_authenticated":False,
            "no_retraining_on_target":True,
            "actual_original_learned_3VC":False,
            "original_source_original_gold_labels_consumed":False,
            "status":"ABSTAIN_SOURCE_NOT_OPENED"}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or sha1blob(raw)!=item["git_blob"]:
            raise RuntimeError("ORIGINAL_PRESOURCE_GIT_BLOB_OR_LENGTH_MISMATCH")
        record["original_source_SHA_authenticated"]=True
        record["original_source_SHA256"]=hashlib.sha256(raw).hexdigest()
        source_text=raw.decode("utf-8")
        _,source,native,ids=prepare(root,item)
        record["source_native_original_independently_parsed_and_verified"]=ids
        actual_signature=[x[0] for x in source["states"]]
        record["true_original_source_state_signature"]=actual_signature
        record["native_model_frozen_interface_compatible"]=actual_signature==TYPED_INTERFACE
        if actual_signature!=TYPED_INTERFACE:
            record["status"]="ABSTAIN_FIXED_HUMAN_CHOSEN_SOURCE_INTERFACE_MISMATCH"
        else:
            learned=independently_validate_candidate(
                source,native,mapping,"frozen_CPU_model_from_different_original_fib32")
            nolearn=independently_validate_candidate(
                source,native,nonlearned_map,"frozen_zero_train_four_case_table_from_fib32")
            record["learned_fixed_other_source_actual_native_3VC"]=learned
            record["same_authority_zero_train_lookup_actual_native_3VC"]=nolearn
            record["actual_original_learned_3VC"]=learned["actual_original_3VC_dual_success"]
            record["status"]="TRUE_NEW_UNSEEN_PROGRAM_LEARNED_TRANSFER_DUAL_CERTIFIED" if record[
                "actual_original_learned_3VC"] else "FAIL_TO_PROVE_NEW_TRUE_ORIGINAL_3VC"
        # Every source gets available strong ORIGINAL classical baseline.
        # Error/unextractable invariants do not mean source is actually unsafe.
        record["original_full_cvc5_SyGuS_strong_2s"]=original_syguS(raw,source,native,2.0)
        record["original_full_Z3_SPACER_strong"]=native_pdr(source,native)
        record["classical_full_source_original_independently_SAFE_certified"]=(
            record["original_full_cvc5_SyGuS_strong_2s"].get("certified",False) or
            record["original_full_Z3_SPACER_strong"].get("certified",False))
    except Exception as e:
        record["status"]="ABSTAIN_UNSUPPORTED_OR_SOURCE_PROOF_EXCEPTION"
        record["error"]=type(e).__name__+":"+str(e)[:330]
    record["all_attempted_original_source_validation_full_wall_ms"]=millis(start)
    print("Q6_FROZEN_LEARNED_MODEL_NEW_ORIGINAL_SOURCE",item["path"].split("/")[-1],
          "AUTHENTIC",record["original_source_SHA_authenticated"],
          "INTERFACE",record.get("native_model_frozen_interface_compatible"),
          "LEARNED_ORIGINAL_3VC",record["actual_original_learned_3VC"],
          "CLASSICAL_ORIGINAL_SAFE",record.get("classical_full_source_original_independently_SAFE_certified"),
          "STATUS",record["status"],"ERROR",record.get("error"),flush=True)
    return record

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--source24",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    o=ap.parse_args()
    reg=json.loads(o.freeze.read_text());source24=json.loads(o.source24.read_text())
    if reg["schema"]!="neumann.q6.seven_presource_hypothesis_fib32_fixed_CPU_model_no_target_fit.v1":
        raise RuntimeError("PRESOURCE_Q6_FROZEN_MODEL_PROTOCOL_CHANGED")
    if len(reg["test_case_git_blobs"])!=7 or len(set(x["git_blob"] for x in reg["test_case_git_blobs"]))!=7:
        raise RuntimeError("PRESOURCE_SEVEN_ORIGINAL_GIT_IDENTITIES_CHANGED")
    training_original=next(q for q in source24["cases"] if q["path"]==ORIGINAL_PATH)
    if training_original["git_blob"]!=ORIGINAL_BLOB or training_original["bytes"]!=ORIGINAL_SIZE:
        raise RuntimeError("PREVIOUS_PR376_REAL_TRAINING_ORIGINAL_CHANGED")
    beginning=time.perf_counter_ns()
    outcome={"schema":"neumann.q6.first7_new_source_original_frozen_phase_CPU_model_transfer.v1",
             "source_body_unopened_at_seven_git_blob_freeze_commit":FROZEN_BEFORE_ANY_NEW_TEST_BODY_COMMIT,
             "all_7_source_file_rows_preserved":True,
             "actual_new_original_source_sha_authenticated_count":0,
             "training_source_is_ALREADY_OPENED_fib32":True,
             "training_labels_derived_only_from_prior_fib32_source_native_trans":True,
             "target_original_model_training_updates":0,
             "same_source_author_family_not_independent_authors":True,
             "fixed_training_features_are_human_selected_not_new_AST_roles":True,
             "q6_true_sealed_source_body_program_transfer_dual_count":0,
             "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN"}
    try:
        raw,src,native,ids=prepare(o.root,training_original)
        actual_train_rows,actual_train_costs=execute_splits(src,native,INITIAL_TRAIN_K)
        X=[row["features"] for row in actual_train_rows]
        y=[row["observed_offset_i_minus_j"] for row in actual_train_rows]
        model,model_fit_ms,tree=actual_cpu_train(X,y)
        weights,error=extract_case_offsets(model,(0,1))
        if weights is None:raise RuntimeError("FROZEN_LEARNED_SOURCE_MODEL_NOT_TYPED:"+str(error))
        deterministic={}
        for datum in actual_train_rows:
            pair=tuple(datum["features"]);observed=int(datum["observed_offset_i_minus_j"])
            if pair in deterministic and deterministic[pair]!=observed:
                raise RuntimeError("ZERO_LEARN_COMPARATOR_TRAINING_SOURCE_CONTRADICTORY")
            deterministic[pair]=observed
        if len(deterministic)!=4 or weights!=deterministic:
            raise RuntimeError("PR376_FROZEN_CPU_TRAINING_REPRODUCIBILITY_OR_MODEL_PARITY_FAIL")
        outcome["true_training_original_source_SHA_authenticated"]=True
        outcome["real_source_CPU_model_trained_once_ms"]=model_fit_ms
        outcome["trained_CPU_tree_native_structure"]=tree
        outcome["frozen_CPU_model_actual_integer_case_predictions"]={
            f"parity{p}b{b}":int(v) for (p,b),v in sorted(weights.items())}
        outcome["frozen_trained_model_equals_0train_trace_lookup"]=True
        rows=[test_actual_new_program(o.root,item,weights,deterministic)
              for item in reg["test_case_git_blobs"]]
        outcome["new_originals"]=rows
        outcome["actual_new_original_source_sha_authenticated_count"]=sum(
            r["original_source_SHA_authenticated"] for r in rows)
        outcome["original_new_source_programs_with_fixed_supported_interface"]=sum(
            r.get("native_model_frozen_interface_compatible",False) for r in rows)
        outcome["q6_true_sealed_source_body_program_transfer_dual_count"]=sum(
            r["actual_original_learned_3VC"] for r in rows)
        outcome["new_original_source_matched_classical_original_safety_proofs"]=sum(
            r.get("classical_full_source_original_independently_SAFE_certified",False) for r in rows)
        outcome["not_true_source_author_independent_model_generalization"]=True
    except Exception as e:
        outcome["error"]=type(e).__name__+":"+str(e)[:390]
        outcome["not_true_source_author_independent_model_generalization"]=True
    outcome["source_training_and_all_test_original_solver_wall_ms"]=millis(beginning)
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(outcome,sort_keys=True,indent=2)+"\n")
    print("Q6_TRUE_NEW_GIT_SHA_AUTHENTIC_SEVEN",
          outcome["actual_new_original_source_sha_authenticated_count"],"/7")
    print("Q6_TRUE_NEW_FIXED_MODEL_TYPED_SOURCE_INTERFACES",
          outcome.get("original_new_source_programs_with_fixed_supported_interface"),"/7")
    print("Q6_TRUE_NEW_MODEL_NATIVE_ORIGINAL_INDUCTIVE_3VC",
          outcome["q6_true_sealed_source_body_program_transfer_dual_count"],"/7")
    print("Q6_TRUE_NEW_STRONG_CLASSICAL_ORIGINAL_SAFE",
          outcome.get("new_original_source_matched_classical_original_safety_proofs"))
    print("Q6_TRUE_NEW_MODEL_GLOBAL_Q6_OPEN",outcome["global_Q6"])
    print("Q6_SEVEN_NEW_PROSPECTIVE_TRANSFER_ERROR",outcome.get("error"))
if __name__=="__main__":
    main()
