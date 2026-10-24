"""Actual deployable SOURCE-ONLY frozen neural controller checkpoint.

Do NOT re-train whenever we visit a new benchmark: train ONCE on prior
independent ERBench128 48x-y source numeric-only, record all exact model
weights, and serialize that exact model from a fully-trusted local object.

Reimport in same CI job, assert bit-exact coefficients, intercepts,
predictions for deterministic independent numerically created feature
vectors, and prediction order of all structural graph edit ACTIONS.
Commit/train provenance immutable and checkpoint blob SHA published.
"""
import argparse,hashlib,json,pathlib
import joblib
import numpy as np
from learned_derived_power_eleventh32 import train,ACTIONS,feature
from erbench_original_eleventh import sha,save

def checkpoint(train_file,model_out,receipt_out):
    model,metadata=train(train_file)
    assert len(ACTIONS)==3
    result={
       "schema":"NEUMANN_Q6_REAL_SERIALIZED_SOURCE_REWARD_STRUCTURAL_ACTION_POLICY.v1",
       "original_training_numeric_source_SHA256":sha(pathlib.Path(train_file).read_bytes()),
       "learned_policy_weights_sha256":metadata["trained_weights_SHA256"],
       "learned_numerical_reward_trace_sha256":metadata["training_rewards_SHA256"],
       "newly_defined_source_valid_macro_memory_sha256":metadata["memory_SHA256"],
       "no_target_original_truth_training":True,
       "train_once_then_load_weights_without_retraining":True,
       "not_guaranteed_bit_equal_to_the_historical_prior_first_MLP":"TRUE_ALREADY_PROVED_WEIGHTS_VARY_BETWEEN_RETRAINS",
       "versioned_primitive_structural_actions":list(ACTIONS)
    }
    sample=np.random.default_rng(151).normal(0,2,size=(20,24))
    x=np.array([feature(row,a) for row in sample for a in ACTIONS])
    before=model.predict(x)
    path=pathlib.Path(model_out);path.parent.mkdir(parents=True,exist_ok=True)
    # trusted output, never load untrusted remote pickle from unknown source
    joblib.dump({"model":model,"training_receipt":metadata,"schema":result["schema"]},path,compress=3)
    reread=joblib.load(path)
    after=reread["model"].predict(x)
    assert np.array_equal(before,after),"SAVED_RELOADED_MODEL_PREDICTION_MISMATCH"
    assert reread["training_receipt"]["trained_weights_SHA256"]==metadata["trained_weights_SHA256"]
    for first,second in zip(model.coefs_,reread["model"].coefs_):
        assert np.array_equal(first,second),"WEIGHTS_CHANGED_ON_SERIALIZATION"
    for first,second in zip(model.intercepts_,reread["model"].intercepts_):
        assert np.array_equal(first,second),"INTERCEPTS_CHANGED_ON_SERIALIZATION"
    results_before=np.asarray([[model.predict([feature(row,a)])[0] for a in ACTIONS] for row in sample])
    results_after=np.asarray([[reread["model"].predict([feature(row,a)])[0] for a in ACTIONS] for row in sample])
    assert np.array_equal(results_before,results_after)
    result["real_frozen_model_blob_SHA256"]=sha(path.read_bytes())
    result["exact_source_model_reload_predictions_tested"]=len(x)
    result["bit_exact_coefficients_and_intercepts_RELOADED"]="PASS"
    result["inference_action_rank_RELOADED"]="PASS"
    result["real_trained_model_blob_bytes"]=path.stat().st_size
    signature=save(receipt_out,result)
    print("Q6_ACTUAL_SERIALIZED_TRAINED_STRUCTURAL_POLICY_RELOAD_NO_MORE_STOCHASTIC_REFIT",
       json.dumps({"receipt_SHA256":signature,"checkpoint_SHA256":result["real_frozen_model_blob_SHA256"],
          "MLP_actual_sha256":metadata["trained_weights_SHA256"],
          "bit_identical_reloaded_predictions":len(x),
          "bytes":path.stat().st_size},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--train",required=True);p.add_argument("--model",required=True);p.add_argument("--receipt",required=True)
    a=p.parse_args();checkpoint(a.train,a.model,a.receipt)
