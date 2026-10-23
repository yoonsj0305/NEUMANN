"""Feedback-controlled learned structural decision with independent verifier repair.

Load EXACT pre-Keijzer model bytes from run39957688283, no retraining and
NO original OEIS formulas. Execute the neural-first action, test whether
it produces exact validated SOURCE program, if it fails: construct a
counterexample/source failure signal and try the alternate action.
This is a human-coded feedback policy around genuine prior neural choice,
NOT autonomous discovery of the VERIFY_THEN_REVISE action schema.

Compare first neural action, learned+repair, fixed-rec, fixed-closed,
full both classical. Every code path uses same numerical oracle rights.
"""
import argparse,collections,json,pathlib,time
import numpy as np
import joblib
from recursive_operator_source_inventor import action_result,shape,sha,save
from learned_recursive_symbol_policy import ACTIONS

PRIOR_FROZEN_SHA="de625e81f68418d2613983c20011901f887415e76a7b82ef4ef9fe2bb26874e5"

def evaluate(modelpath,metapath,sourcepath,out):
    meta=json.loads(pathlib.Path(metapath).read_text())
    digest=sha(pathlib.Path(modelpath).read_bytes())
    assert digest==PRIOR_FROZEN_SHA==meta["compiled_model_file_sha256"], (
       "FROZEN_MODEL_CHANGED_FROM_FIRST_PRIOR_AUTHOR_TEST",digest)
    package=joblib.load(modelpath)
    model=package["model"]
    assert sha(json.dumps([x.tolist() for x in model.coefs_],sort_keys=True))==meta["MLP_weights_sha256"]
    data=json.loads(pathlib.Path(sourcepath).read_text())
    rows=data["source_numeric_without_equations"]
    assert len(rows)==4
    assert all("summand_expression" not in r for r in rows)
    methods=("D_PRIOR_FROZEN_MODEL_ONLY","D_FROZEN_MODEL_PLUS_VERIFY_REPAIR",
             "C_STATIC_ONLY_CLOSED","C_STATIC_ONLY_RECURSIVE",
             "A_ALL_BOTH_ACTIONS")
    receipt={}
    for method in methods:
        start=time.process_time();case=[];totals=collections.Counter()
        for row in rows:
            features=shape(row)
            if features is None:
                case.append({"id":row["id"],"source_status":"UNKNOWN_NO_VALID_SOURCE",
                   "attempts":[],"new_programs":[],"source_math_calls":0})
                continue
            neural=str(model.predict([features])[0])
            if method.startswith("D_"):
                proposed=[neural]
            elif method=="C_STATIC_ONLY_CLOSED":proposed=["OLD_CLOSED_FORM"]
            elif method=="C_STATIC_ONLY_RECURSIVE":proposed=["DEFINE_RECURRENCE"]
            else:proposed=list(ACTIONS)
            attempt=[];winners=[];calls=0
            def execute(act):
                nonlocal calls
                prog,n=action_result(row,act)
                calls+=n
                attempt.append({"selected_action":act,"real_source_program_found":prog is not None,
                    "source_verifier_calls":n})
                if prog is not None:winners.append(prog)
            for chosen in proposed:execute(chosen)
            if method=="D_FROZEN_MODEL_PLUS_VERIFY_REPAIR" and not winners:
                remaining=[a for a in ACTIONS if a not in proposed]
                assert len(remaining)==1
                totals["previous_neural_structure_decision_rejected_by_source_VERIFIER"]+=1
                execute(remaining[0])
                totals["verified_structural_revision_calls"]+=1
                if winners:totals["counterexample_triggered_successful_new_operator"]+=1
            case.append({"id":row["id"],
               "source_status":"EXACT_SOURCE_PROGRAM_DEFINED" if winners else "UNKNOWN",
               "first_frozen_learned_graph_choice":neural,
               "attempts":attempt,"new_programs":winners,"source_math_calls":calls})
            totals["tasks_with_numeric_source_program"]+=int(bool(winners))
            totals["source_oracle_calls"]+=calls
            totals["new_recursive_symbols"]+=sum(p.get("kind")=="NEW_EXECUTABLE_RECURSIVE_SYMBOL" for p in winners)
        receipt[method]={"cases":case,"counts":dict(totals),"CPU_s":time.process_time()-start}
    outdata={"schema":"NEUMANN_P2_FROZEN_PRIOR_NEURAL_STRUCTURE_PLUS_COUNTEREXAMPLE_REPAIR_NEW_OEIS4.v1",
       "original_model_artifact_SHA256_FROM_PREVIOUS_KEIJZER_RUN":PRIOR_FROZEN_SHA,
       "same_prior_model_MLP_weight_SHA256":meta["MLP_weights_sha256"],
       "no_retraining_and_no_target_original_author_equations":True,
       "new_OEIS4_source_numeric_SHA256":sha(pathlib.Path(sourcepath).read_bytes()),
       "human_coded_fallback_from_verifier_failure":True,
       "neural_first_action_is_genuine_frozen_trained_model":True,
       "all_rights_and_atomic_recursion_operations_the_same_across_all_methods":True,
       "methods":receipt,
       "global_Q3":"OPEN","G1":"HOLD","frontier_10x":"NOT_PROVED"}
    signature=save(out,outdata)
    print("NEUMANN_P2_OEIS4_FIRST_SOURCE_PRIOR_NEURAL_AND_VERIFIER_REPAIR_FROZEN",
       json.dumps({"sha256":signature,"methods":{k:{"calls":v["counts"].get("source_oracle_calls",0),
           "new_recursions":v["counts"].get("new_recursive_symbols",0),
           "repaired":v["counts"].get("counterexample_triggered_successful_new_operator",0),
           "CPU_s":v["CPU_s"]} for k,v in receipt.items()}},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("model","meta","source","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args();evaluate(a.model,a.meta,a.source,a.out)
