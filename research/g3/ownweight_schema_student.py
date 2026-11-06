"""G3 own-weight structural *teacher distillation* with original-source proof.

This does NOT claim autonomous discovery of the human-designed quantified
prefix/suffix/whole grammar, nor frontier generalization. It is a minimal
actual learned-weight -> factorized predicate AST -> original Horn proof bridge.
TEST source files MUST NOT be opened by this train-only module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np

from research.g3.array_fill_parametric_invariant import (
    KNOWN_SOURCE, source, source_role_info, prove_each
)

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/experiments/G3_OWNWEIGHT_QUANTIFIED_SCHEMA_FIRST_PREREG_2026_11_06.json"
RANGES=("OFF","PREFIX","SUFFIX","WHOLE")
VALUES=("OFF","NEW","PREVIOUS","NEGATIVE_CONTROL")
FEATURE_COUNT=6
HEADS=4
CATEGORIES=4


def vector(stage:int, n:int)->np.ndarray:
    if type(stage) is not int or type(n) is not int or n<2 or not 0<=stage<=n:
        raise ValueError("INVALID_STAGE_METADATA")
    return np.array([1.0,float(stage==0),float(0<stage<n),
                     float(stage==n),stage/n,n/12.0],dtype=np.float64)


def certified_teacher_targets(stage:int,n:int)->tuple[int,int,int,int]:
    """Human proven rule labels, TRAIN ONLY. Not original neural invention."""
    if stage==0:return (1,1,0,0)  # prefix/new
    if stage==n:return (3,2,0,0)  # whole/previous
    return (1,1,2,2)  # prefix/new + suffix/previous


def policy(weights:np.ndarray,stage:int,n:int)->tuple[int,int,int,int]:
    if weights.shape!=(HEADS,FEATURE_COUNT,CATEGORIES) or not np.isfinite(weights).all():
        raise ValueError("INVALID_STUDENT_TENSOR")
    feature=vector(stage,n)
    return tuple(int(x) for x in np.einsum("f,hfc->hc",feature,weights).argmax(axis=1))


def q_interval(span:int, value:int, stage:int, values:list[int])->str:
    if span==0 and value==0:return ""
    if span==0 or value==0:
        raise ValueError("UNPAIRED_INTERVAL_VALUE_PREDICTION")
    bounds={1:("0","i"),2:("i","limit"),3:("0","limit")}
    if span not in bounds or value not in (1,2,3):
        raise ValueError("OUT_OF_TYPED_AST_LANGUAGE")
    if value==1:
        if stage>=len(values):raise ValueError("FINAL_STAGE_NEW_VALUE_NOT_DEFINED")
        cell=values[stage]
    elif value==2:
        if stage==0:raise ValueError("FIRST_STAGE_NO_OLD_VALUE")
        cell=values[stage-1]
    else:
        cell=-987654321 # fixed negative control, not a plausible learned source value
    lo,hi=bounds[span]
    return ("(forall ((j Int)) (=> (and (<= "+lo+" j) (< j "+hi+"))"
            " (= (select arr (+ n j)) "+str(cell)+")))")


def compiled_predicate(stage:int,nstages:int,values:list[int],predicate:str,
                       arrslot:int,predicted:tuple[int,int,int,int])->str:
    if arrslot not in (1,2):raise ValueError("UNKNOWN_TYPED_ARRAY_POSITION")
    par=[("n","Int"),("i","Int"),("arr","(Array Int Int)"),("limit","Int")]
    if arrslot==1:
        par=[par[0],par[2],par[1],par[3]]
    items=["(> n 0)","(> limit 0)","(<= 0 i)","(<= i limit)"]
    for k in (0,2):
        v=q_interval(predicted[k],predicted[k+1],stage,values)
        if v:items.append(v)
    if len(items)==4:raise ValueError("STUDENT_GUESSED_TRIVIAL_NO_INVARIANT")
    return ("(define-fun |"+predicate+"| ("+
        " ".join("("+x+" "+typ+")" for x,typ in par)+
        ") Bool (and "+" ".join(items)+"))")


def compile_from_weights(source_text:str,weights:np.ndarray)->dict:
    """Human source parser and concrete SMT compiler; STUDENT decides 4 AST tokens."""
    info=source_role_info(source_text)
    values=list(info["values"])
    n=len(values)
    forms=info["source_forms"]
    interpreted={}
    emitted=[]
    for stage,(idx,decl,sorts) in enumerate(info["predicates"]):
        pred="main@bb"+str(idx)+".i"
        decision=policy(weights,stage,n)
        emitted.append({"stage":stage,"four_token_AST":list(decision),
                        "role_labels_not_supplied_at_eval":True})
        interpreted[decl]=compiled_predicate(stage,n,values,pred,
                                              sorts.index("(Array Int Int)"),decision)
    entry_count=0
    for form in forms:
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@verifier\.error\.split\|\s+\(\s*\)\s+Bool\s*\)",form):
            interpreted[form]="(define-fun |main@verifier.error.split| () Bool false)"
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@entry\|\s+\(\s*Int\s*\)\s+Bool\s*\)",form):
            interpreted[form]="(define-fun |main@entry| ((n Int)) Bool true)"
            entry_count+=1
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@entry\|\s+\(\s*\)\s+Bool\s*\)",form):
            interpreted[form]="(define-fun |main@entry| () Bool true)"
            entry_count+=1
    if entry_count!=1 or len(interpreted)!=len(info["predicates"])+2:
        raise ValueError("UNSUPPORTED_EXPLICIT_ENTRY_ERROR_INTERFACE")
    for form in forms:
        if form.startswith("(declare-fun") and form not in interpreted:
            raise ValueError("UNSUPPORTED_OTHER_UNINTERPRETED_RELATION")
    assertions=[form for form in forms if re.match(r"^\(\s*assert\s+",form)]
    if len(assertions)!=info["n_source_assertions"]:
        raise ValueError("ORIGINAL_ASSERTION_COUNT_DRIFT")
    return {
        "prefix":"(set-logic ALL)\n"+"\n".join(interpreted[f] for f in forms if f in interpreted)+"\n",
        "source_assertions":assertions,"original_clause_count":len(assertions),
        "num_stages":n,"predicted_AST_tokens":emitted,
        "model_generates_quantifier_AST_tokens":True,
        "explicit_human_defined_quantifier_syntax":True,
    }


def train(checkpoint:Path,report_path:Path)->dict:
    contract=json.loads(CONTRACT.read_text())
    trained=contract["training"]
    if trained["gradient_steps"]!=320 or trained["feature_count"]!=6 or trained["model_heads"]!=4:
        raise ValueError("FROZEN_TRAIN_PARAMETER_CHANGED")
    trainX=[]; trainY=[]; source_receipts=[]
    started=time.perf_counter_ns()
    for row in trained["already_opened_originals"]:
        name=row["file"]
        if name not in KNOWN_SOURCE or KNOWN_SOURCE[name]!=row["git_blob"]:
            raise ValueError("NOT_ALREADY_OPENED_SOURCE_G3")
        raw=source(name,row["git_blob"])
        info=source_role_info(raw.decode("utf8"))
        stages=len(info["values"])
        for k in range(stages+1):
            trainX.append(vector(k,stages))
            trainY.append(certified_teacher_targets(k,stages))
        source_receipts.append({"file":name,"blob":row["git_blob"],
                 "stages":stages,"source_sha256":hashlib.sha256(raw).hexdigest()})
    X=np.asarray(trainX);Y=np.asarray(trainY,dtype=np.int64)
    rng=np.random.default_rng(trained["training_seed"])
    W=rng.normal(0,0.006,size=(HEADS,FEATURE_COUNT,CATEGORIES))
    W_initial=W.copy()
    m=np.zeros_like(W);v=np.zeros_like(W); lr=0.24
    nrow=len(X)
    for step in range(1,trained["gradient_steps"]+1):
        logits=np.einsum("nf,hfc->nhc",X,W)
        logits-=np.max(logits,axis=2,keepdims=True)
        p=np.exp(logits);p/=np.sum(p,axis=2,keepdims=True)
        grad=p.copy()
        for head in range(HEADS):
            grad[np.arange(nrow),head,Y[:,head]]-=1
        grad/=nrow
        dw=np.einsum("nf,nhc->hfc",X,grad)+0.00003*W
        m=0.9*m+0.1*dw;v=0.999*v+0.001*dw*dw
        W-=lr*(m/(1-0.9**step))/(np.sqrt(v/(1-0.999**step))+1e-8)
    measured_training_wall_s=(time.perf_counter_ns()-started)/1e9
    exact=sum(policy(W,k,n)==certified_teacher_targets(k,n)
              for row in source_receipts for n in [row["stages"]] for k in range(n+1))
    full=sum(r["stages"]+1 for r in source_receipts)
    if exact!=full:
        raise ValueError("TRAIN_MODEL_COULD_NOT_REPRODUCE_CERTIFIED_DEVELOPMENT_SEMANTICS")
    # Freeze actual 4-head own weights BEFORE any candidate external original access.
    data={
        "schema":"neumann.g3.ownweight-factorized-quantifier-AST-weights.v1",
        "scientific_scope":"SUPERVISED_HUMAN_TEACHER_DISTILLATION",
        "seed":trained["training_seed"],"steps":trained["gradient_steps"],
        "feature_count":FEATURE_COUNT,"heads":HEADS,"categories":CATEGORIES,
        "array_interval_grammar":list(RANGES),"array_value_grammar":list(VALUES),
        "student_weight_shape":list(W.shape),"student_weight":W.round(10).tolist(),
        "training_originals":source_receipts,
        "training_token_labels_written_by_HUMAN_PROVEN_G3_RULE":True,
        "original_external_test_sources_opened":0,
        "original_external_test_task_results":None
    }
    raw=(json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
    checkpoint.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest()
    # Prove real unchanged opened source clauses, not just token accuracy.
    opened_proofs=[]
    model=load(checkpoint,expected_sha=digest)
    for row in source_receipts:
        orig=source(row["file"],row["blob"]).decode("utf8")
        compiled=compile_from_weights(orig,model)
        checked=prove_each(compiled,budget_per_clause_s=7)
        opened_proofs.append({"source":row["file"],"stages":compiled["num_stages"],
          "original_clauses":checked["total_original_clauses"],
          "proved":checked["original_clauses_independently_proven"],
          "all_verified":checked["all_original_clauses_proven"],
          "emitted_student_decisions":compiled["predicted_AST_tokens"],
          "first_nonproof":checked["first_nonproof"]})
    scope="OPENED_TRAIN_ONLY"
    report={
        "schema":"neumann.g3.ownweight-teacher-distilled-training-first.v1",
        "scope":scope,"checkpoint_SHA256":digest,
        "actual_weights_updated":bool(np.max(np.abs(W-W_initial))>0.01),
        "num_train_originals":len(source_receipts),"num_train_role_examples":len(Y),
        "training_exact_four_head_symbols":exact,"training_total_stages":full,
        "trained_vs_untrained_train_delta_Linf":float(np.max(np.abs(W-W_initial))),
        "training_wall_seconds_including_source_fetch":round(measured_training_wall_s,5),
        "opened_originals_all_independently_verified":all(x["all_verified"] for x in opened_proofs),
        "opened_original_total_clauses":sum(x["original_clauses"] for x in opened_proofs),
        "opened_original_proved":sum(x["proved"] for x in opened_proofs),
        "original_test_sources_fetched":0,
        "test_bodies_unopened_before_weights_freeze":True,
        "trained_own_weight_but_not_invented_base_operator":True,
        "human_template_direct_baseline_known_fast":True,
        "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
        "opened_proofs":opened_proofs
    }
    report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if not report["opened_originals_all_independently_verified"]:
        raise RuntimeError("STUDENT_OPENED_DEVELOPMENT_CHC_PROOFS_FAIL")
    return report


def load(checkpoint:Path,expected_sha:str)->np.ndarray:
    raw=checkpoint.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError("STUDENT_WEIGHT_CHECKPOINT_DRIFT")
    data=json.loads(raw)
    if data.get("schema")!="neumann.g3.ownweight-factorized-quantifier-AST-weights.v1" or data.get("original_external_test_sources_opened")!=0:
        raise ValueError("NOT_ORIGINAL_FROZEN_STUDENT")
    arr=np.asarray(data["student_weight"],dtype=np.float64)
    if arr.shape!=(HEADS,FEATURE_COUNT,CATEGORIES) or not np.isfinite(arr).all():
        raise ValueError("INVALID_CHECKPOINT_CONTENTS")
    return arr


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    result=train(args.checkpoint,args.report)
    print(json.dumps({k:v for k,v in result.items() if k!="opened_proofs"},indent=2,sort_keys=True))


if __name__=="__main__":
    main()
