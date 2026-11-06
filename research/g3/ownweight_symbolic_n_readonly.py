"""Read-only frozen weights: n=2..128 symbolic stage-role extrapolation.

No model training; no original task body; no Z3 or external solver run.
The teacher expected relation-role tokens were HUMAN designed and mathematically
proven for arbitrary finite N in prior G3 work. This does NOT prove Q3.
Also fixes a *metadata* misclassification in the archived FIRST native logs:
literal "timeout\\n" is a bounded timeout, not a checker error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PREREG=ROOT/"docs/experiments/G3_OWNWEIGHT_ALL_N_2_TO_128_PREREG_2026_11_06.json"


def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def target(stage:int,n:int)->tuple[int,int,int,int]:
    if type(n) is not int or n<2 or type(stage) is not int or not 0<=stage<=n:
        raise ValueError("INVALID_SYMBOLIC_STAGE")
    if stage==0:
        return (1,1,0,0)
    if stage==n:
        return (3,2,0,0)
    return (1,1,2,2)


def independent_score(weights:list,stage:int,n:int)->tuple[tuple[int,...],tuple[float,...]]:
    """Pure Python scorer; does not import train/first/checker implementations."""
    if (type(weights) is not list or len(weights)!=4
            or any(type(h) is not list or len(h)!=6 for h in weights)):
        raise ValueError("WRONG_WEIGHT_DIMENSIONS")
    vec=(1.0,float(stage==0),float(0<stage<n),float(stage==n),
         stage/n,n/12.0)
    tokens=[]
    margins=[]
    for head in weights:
        if any(type(v) is not list or len(v)!=4 for v in head):
            raise ValueError("WRONG_LOGIT_WEIGHT_SHAPE")
        logits=[sum(vec[f]*head[f][k] for f in range(6)) for k in range(4)]
        if not all(math.isfinite(x) for x in logits):
            raise ValueError("NONFINITE_MODEL_LOGIT")
        rank=sorted(range(4),key=lambda k:(-logits[k],k))
        tokens.append(rank[0])
        margins.append(logits[rank[0]]-logits[rank[1]])
    return tuple(tokens),tuple(margins)


def original_native_censored_readonly(original:dict,prereg:dict)->dict:
    frozen=prereg["postfirst_native_metadata_correction"]
    original_raw=json.dumps(original) # only for sanity, NEVER used as claimed exact first SHA
    if original.get("checkpoint_SHA256")!=prereg["frozen_checkpoint"]["checkpoint_sha256"]:
        raise ValueError("FIRST_ORIGINAL_STUDENT_SHA_MISMATCH")
    if original.get("train_source_only_actual_run")!=prereg["frozen_checkpoint"]["first_train_run"]:
        raise ValueError("FIRST_ORIGINAL_TRAIN_RUN_DRIFT")
    if len(original.get("rows",[]))!=2:
        raise ValueError("ORIGINAL_FIRST_ROW_COUNT_CHANGED")
    rows=[]
    expected=frozen["stdout_sha256_for_Z3_literal_timeout_newline"]
    if digest(b"timeout\n")!=expected:
        raise ValueError("LITERAL_TIMEOUT_STDOUT_HASH_MISMATCH")
    for row in original["rows"]:
        native=row.get("original_source_strong_native",{})
        if not (native.get("bounded_native_verdict")=="CHECKER_ERROR" and
                native.get("exit")==0 and native.get("stdout_sha256")==expected and
                native.get("native_time_cap_s")==15):
            raise ValueError("UNEXPECTED_FIRST_NATIVE_LOG_DO_NOT_RECLASSIFY")
        rows.append({
            "original_file":row["name"],
            "first_native_author_label":"CHECKER_ERROR",
            "postfirst_readonly_qualified_label":"TIMEOUT_CENSORED_15_SECONDS",
            "sha256_of_literal_native_stdout_timeout":expected,
            "original_first_wall_ms":native["wall_ms"],
            "first_result_replaced_or_rerun":False
        })
    return {"timeout_censored_corrections":len(rows),"rows":rows,
            "original_first_json_sha256":frozen["original_first_json_sha256"],
            "native_new_solver_runs":0,
            "actual_first_results_modified":False}


def audit(checkpoint:Path,first_file:Path)->dict:
    c=json.loads(PREREG.read_text())
    frozen=c["frozen_checkpoint"]
    checkpoint_raw=checkpoint.read_bytes()
    first_raw=first_file.read_bytes()
    if digest(checkpoint_raw)!=frozen["checkpoint_sha256"]:
        raise ValueError("FROZEN_WEIGHT_BYTES_DO_NOT_MATCH_ORIGINAL_FIRST")
    if digest(first_raw)!=c["postfirst_native_metadata_correction"]["original_first_json_sha256"]:
        raise ValueError("EXACT_FIRST_ORIGINAL_JSON_BYTES_MISMATCH")
    data=json.loads(checkpoint_raw)
    if data.get("schema")!="neumann.g3.ownweight-factorized-quantifier-AST-weights.v1":
        raise ValueError("NOT_ORIGINAL_MODEL_CHECKPOINT")
    if data.get("original_external_test_sources_opened")!=0:
        raise ValueError("ORIGINAL_TRAIN_SOURCE_LEAK")
    rows=[]
    point_count=0
    point_correct=0
    zero_correct=0
    lengths_exact=0
    first_counterexample=None
    min_margin=float("inf")
    start=time.perf_counter_ns()
    for n in range(c["registered_n_range"]["min"],c["registered_n_range"]["max_inclusive"]+1):
        passes=0
        for stage in range(n+1):
            want=target(stage,n)
            got,margins=independent_score(data["student_weight"],stage,n)
            point_count+=1
            if got==want:
                passes+=1
                point_correct+=1
            elif first_counterexample is None:
                first_counterexample={
                  "n":n,"stage":stage,"expected":list(want),
                  "actual_frozen_own_weight":list(got),
                  "per_head_margin":list(margins)
                }
            min_margin=min(min_margin,*margins)
            zero_guess,_=independent_score([[[0.0]*4 for _ in range(6)] for _ in range(4)],stage,n)
            zero_correct+=int(zero_guess==want)
        lengths_exact+=int(passes==n+1)
        rows.append({"stage_length":n,"roles_exact":passes,
                     "roles_total":n+1,"entire_symbolic_n_roles_exact":passes==n+1})
    if point_count!=c["registered_n_range"]["total_token_prediction_points"]:
        raise ValueError("REGISTERED_SYMBOLIC_N_DENOMINATOR_CHANGED")
    native=original_native_censored_readonly(json.loads(first_raw),c)
    claimed=(point_correct==point_count)
    return {
        "schema":"neumann.g3.ownweight-frozen-2-128-sourcefree-extrapolation-first.v1",
        "scientific_status":("PASS_SCOPED_FIXED_HUMAN_AST_LANGUAGE" if claimed
                             else "FAIL_FROZEN_OUT_OF_DISTRIBUTION_SYMBOLIC_N"),
        "original_frozen_weights_SHA256":digest(checkpoint_raw),
        "original_first_external_result_sha256":digest(first_raw),
        "stage_counts_tested":len(rows),
        "total_role_prediction_points":point_count,
        "trained_role_predictions_exact":point_correct,
        "untrained_zero_role_predictions_exact":zero_correct,
        "human_rule_role_predictions_exact":point_count,
        "fully_exact_stage_counts":lengths_exact,
        "first_out_of_distribution_counterexample":first_counterexample,
        "smallest_raw_logit_margin":round(min_margin,8),
        "source_task_bodies_fetched":0,"new_training_runs":0,
        "new_original_solver_runs":0,
        "old_first_original_unchanged":True,
        "first_native_timeout_correction":native,
        "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
        "learned_operator_outside_human_H0":False,
        "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
        "by_stage_count":rows
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--first-original",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.checkpoint,args.first_original)
    args.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="by_stage_count"},sort_keys=True,indent=2))
    if result["scientific_status"]!="PASS_SCOPED_FIXED_HUMAN_AST_LANGUAGE":
        raise SystemExit(1)


if __name__=="__main__":
    main()
