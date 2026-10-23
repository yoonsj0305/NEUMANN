"""Train and persist a tiny neural STRUCTURAL ACTION chooser BEFORE Keijzer.

The 240 developmental numeric-only tasks are generic SELF-REWARDED
recurrences and nonrecursive function measurements from DIFFERENT
parameter families, not any of the Keijzer-6..9 exact author formulas:
- positive recurrence increments proportional to 1/(n+b), b=2..9 only
  (withheld original Keijzer6 harmonic corresponds to b=1);
- nonrecursive source traces from SIN/COS/x²/x³/log(n+1)/sqrt(n+1)
  (no n-log, n-sqrt or asinh exact tested originals).
The network never sees a target true author expression or successful
recurrence answer as a supervised gold AST; rewards come from executing
both candidate program generators against source values and choosing
which actually yields source-verified program. Synthetic task templates
are HUMAN-produced, so transfer evidence is restricted and explicit.

Unlike prior fragile across-CI retraining SHA replay, trained sklearn
model is serialised to JOBLIB in separate job; inference JOB loads
THOSE EXACT bytes and compares sha256 to the TRAIN metadata.
"""
import argparse,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPClassifier
import joblib
from recursive_operator_source_inventor import (
  action_result,shape,save,sha,N,
)

ACTIONS=("DEFINE_RECURRENCE","OLD_CLOSED_FORM")
SEED=20261023
def synthetic_train_sources():
    rng=np.random.default_rng(SEED)
    nvals=list(range(1,49))
    rows=[]
    # Do not include the author target's b=1 harmonic increment.
    for i in range(120):
        b=2+i%8
        amp=sp.Rational(int(rng.integers(1,6)),int(rng.integers(1,5)))
        start=sp.Rational(int(rng.integers(-3,4)),int(rng.integers(1,6)))
        x=[sp.Integer(k) for k in nvals]
        y=[start]
        for j in range(47): y.append(y[-1]+amp/(x[j]+b))
        rows.append({"id":f"TRAIN_R_B{b}_{i}",
            "x":nvals,"y":[float(z) for z in y],
            "y_exact":[str(z) for z in y]})
    # Exclude exact test author Keijzer7 log(n), Keijzer8 sqrt(n),
    # Keijzer9 asinh(n); train adjacent but not equal families.
    for i in range(120):
        kind=("SIN","COS","SQUARE","CUBE","LOG_SHIFT1","SQRT_SHIFT1")[i%6]
        q1=sp.Rational(int(rng.integers(1,5)),int(rng.integers(1,4)))
        q0=sp.Rational(int(rng.integers(-3,4)),int(rng.integers(1,5)))
        values=[]
        for k in nvals:
            x=sp.Integer(k)
            f={"SIN":sp.sin(x),"COS":sp.cos(x),"SQUARE":x*x,
               "CUBE":x**3,"LOG_SHIFT1":sp.log(x+1),"SQRT_SHIFT1":sp.sqrt(x+1)}[kind]
            val=float(sp.N(q1*f+q0,16))
            values.append(val)
        rows.append({"id":f"TRAIN_A_{kind}_{i}",
            "x":nvals,"y":values,
            "y_exact":[str(sp.Rational(float(z))) for z in values]})
    assert len(rows)==240
    return rows
def train(modelpath,metapath):
    rows=synthetic_train_sources()
    began=time.process_time();train=[];cost=0;counts={}
    for source in rows:
        features=shape(source)
        assert features is not None
        candidate={}
        for action in ACTIONS:
            proposed,calls=action_result(source,action)
            cost+=calls
            candidate[action]=proposed
            counts[action]=counts.get(action,0)+int(proposed is not None)
        positives=[k for k,v in candidate.items() if v is not None]
        # No ground-truth program is supplied as the target.
        # Actual SOURCE program-verifier outcome generates the label.
        if len(positives)==1:
            train.append((features,positives[0]))
    assert len(train)>=140,("INSUFFICIENT_SELF_VERIFIED_TRAIN",len(train),counts)
    X=np.asarray([z[0] for z in train],float)
    y=np.asarray([z[1] for z in train])
    assert len(set(y))==2
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model=MLPClassifier(hidden_layer_sizes=(32,16),random_state=SEED,
                learning_rate_init=.003,max_iter=400,alpha=.02)
        t=time.process_time();model.fit(X,y)
        modelcpu=time.process_time()-t
    training_cpu=time.process_time()-began
    pathlib.Path(modelpath).parent.mkdir(parents=True,exist_ok=True)
    artifact={"kind":"NEUMANN_SOURCE_REWARD_LEARNED_RECURSIVE_STRUCTURE_SELECTOR.v1",
              "model":model,"classes":ACTIONS,
              "trained_on_test_author_equations":False}
    joblib.dump(artifact,modelpath,compress=0)
    metadata={
      "schema":"NEUMANN_Q3_RECURSIVE_P2_SOURCE_REWARD_TRAINED_MODEL_BEFORE_ORIGINALS.v1",
      "compiled_model_file_sha256":sha(pathlib.Path(modelpath).read_bytes()),
      "synthetic_source_trace_SHA256":sha(json.dumps(rows,sort_keys=True)),
      "training_examples_all":len(rows),
      "model_selection_labels_from_source_only_VERIFIER_NOT_AUTHOR_FORMULA":len(train),
      "only_positive_source_reward_counts":counts,
      "source_action_oracle_calls":cost,
      "model_training_CPU_s":modelcpu,
      "full_source_oracle_train_and_classifier_CPU_s":training_cpu,
      "train_development_source_has_NO_keijzer_target_functions":True,
      "train_generic_rational_recurrence_offsets_exclude_test_b1":True,
      "train_nonrecursive_funcs_exclude_test_log_n_sqrt_n_asinh_n":True,
      "not_a_blind_discovery_of_the_human_provided_RECURSION_SCHEMA":True,
      "model_predicts":"one executable graph action: DEFINE_RECURRENCE vs OLD_CLOSED_FORM",
      "human_supplies":"generic recurrence schema, rational first-difference interpolator and unary atom grammar",
      "MLP_weights_sha256":sha(json.dumps([a.tolist() for a in model.coefs_],sort_keys=True)),
      "source_first_program_validator":"47 exact rational differences or 48 noiseless numeric original source points"}
    s=save(metapath,metadata)
    print("Q3_TRAIN_BEFORE_EXTERNAL_AUTHOR_RECURSIVE_OPERATOR_MODEL_FROZEN",
          json.dumps({"meta_sha256":s,"artifact_sha256":metadata["compiled_model_file_sha256"],
            "self_reward_examples":len(train),
            "source_counts":counts,
            "training_CPU_s":training_cpu,
            "oracle_calls":cost},sort_keys=True),flush=True)
def infer(modelpath,metapath,sourcepath,out):
    metadata=json.loads(pathlib.Path(metapath).read_text())
    assert sha(pathlib.Path(modelpath).read_bytes())==metadata["compiled_model_file_sha256"],"MODEL_ARTIFACT_NOT_BYTE_IDENTICAL"
    stored=joblib.load(modelpath)
    model=stored["model"]
    assert stored["kind"]=="NEUMANN_SOURCE_REWARD_LEARNED_RECURSIVE_STRUCTURE_SELECTOR.v1"
    assert sha(json.dumps([a.tolist() for a in model.coefs_],sort_keys=True))==metadata["MLP_weights_sha256"]
    source=json.loads(pathlib.Path(sourcepath).read_text())
    assert len(source["source_numeric_without_equations"])==4
    assert all("original_expression" not in z for z in source["source_numeric_without_equations"])
    methods=("D_LEARNED_DEFINE_ONE_ACTION","C_FIXED_ONLY_CLOSED","C_FIXED_ONLY_RECURSE",
             "C_RANDOM_ONE_ACTION","A_BOTH_ACTIONS_IDENTICAL_RIGHTS")
    rng=np.random.default_rng(SEED+2)
    receipts={}
    for method in methods:
        started=time.process_time();cases=[];calls_total=0
        for row in source["source_numeric_without_equations"]:
            features=shape(row)
            if features is None:
                cases.append({"id":row["id"],"status":"UNKNOWN_BAD_SOURCE","actions":[],"new_programs":[],"calls":0})
                continue
            if method=="D_LEARNED_DEFINE_ONE_ACTION":
                choices=[str(model.predict([features])[0])]
                probabilities=dict(zip(model.classes_,[float(v) for v in model.predict_proba([features])[0]]))
            elif method=="C_FIXED_ONLY_CLOSED":choices=["OLD_CLOSED_FORM"];probabilities={}
            elif method=="C_FIXED_ONLY_RECURSE":choices=["DEFINE_RECURRENCE"];probabilities={}
            elif method=="C_RANDOM_ONE_ACTION":choices=[str(rng.choice(ACTIONS))];probabilities={}
            else:choices=list(ACTIONS);probabilities={}
            programs=[];calls=0
            for action in choices:
                proposal,steps=action_result(row,action)
                calls+=steps
                if proposal is not None:programs.append(proposal)
            cases.append({"id":row["id"],"status":"EXECUTABLE_NEW_MACRO_FROM_SOURCE" if programs else "UNKNOWN",
                "actions":choices,"source_only_action_probabilities":probabilities,
                "new_programs":programs,"calls":calls})
            calls_total+=calls
        receipts[method]={"cases":cases,"source_verifier_calls":calls_total,
                         "CPU_s":time.process_time()-started}
    report={
       "schema":"NEUMANN_Q3_EXTERNAL_KEIJZER_PUBLISHED_AUTHOR_RECURSIVE_NEW_SYMBOL_FIRST_SOURCE.v1",
       "frozen_exact_model_file_sha256":metadata["compiled_model_file_sha256"],
       "frozen_model_weights_sha256":metadata["MLP_weights_sha256"],
       "originals_source_only_sha256":sha(pathlib.Path(sourcepath).read_bytes()),
       "model_loaded_NOT_retrained_in_inference":True,
       "recurrence_programs_may_only_be_certified_across_ALL_DOMAIN_by_SEPARATE_author_grader":True,
       "methods":receipts,
       "G1":"HOLD","Q3_GLOBAL":"OPEN"}
    s=save(out,report)
    print("Q3_KEIJZER_FIRST_FROZEN_LEARNED_RECURSIVE_OPERATOR_SOURCE_PROPOSALS",json.dumps({
        "sha256":s,"models":{k:{"calls":v["source_verifier_calls"],"CPU":v["CPU_s"],
             "new_recursive_symbols":sum(p["kind"]=="NEW_EXECUTABLE_RECURSIVE_SYMBOL" for c in v["cases"] for p in c["new_programs"])}
             for k,v in receipts.items()}},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("train","infer"),required=True)
    for k in ("model","meta","source","out"):p.add_argument("--"+k)
    a=p.parse_args()
    if a.mode=="train":train(a.model,a.meta)
    else:infer(a.model,a.meta,a.source,a.out)
