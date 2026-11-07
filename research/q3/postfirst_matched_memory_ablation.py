"""POSTFIRST compute-matched Q3 memory-ablation on immutable original MBPP data.

Tests the critical missing causal claim: did the prior source-learned fold
constructor MEMORY, rather than the NEW human-installed typed predicate
grammar, actually cause any extra correct original tasks?

The cold baseline has the EXACT SAME typed predicate grammar, same
keep/drop observation labels, same candidate ranking and a generic fold
already in the universal VM. Remove only the remembered/generated
constructor AST. No target-specific functions, no refitting after test gold.

NOT a new independent evaluation: MBPP target outcomes were exposed by
first run #42354198810. This is a postfirst memory-causality audit.
"""
from __future__ import annotations
import argparse,json,hashlib,time
from pathlib import Path
from research.q3.feature_predicate_from_counterexample import (
    infer_predicate,pred_value
)
from research.q3.learn_constructor_then_mbpp_original_first import (
    parse_one_assertion
)
from research.q3.typed_semantic_delta_inventor import same

ORIGINAL_RUN=42354198810
MBPP_BLOB="a999d25df7e489e4c183cadfa5c0ecf557a702b6"

def cold_fold_with_full_same_feature_vocabulary(args,pred):
    try:
        if len(args)!=1:return None
        source=args[0]
        if type(source) not in (str,list,tuple) or len(source)>1024:return None
        acc=type(source)()
        for item in source:
            if not pred_value(pred,item):
                if type(source) is str:acc=acc+item
                elif type(source) is tuple:acc=acc+(item,)
                else:acc=acc+[item]
            if len(acc)>1024:return None
        return acc
    except (TypeError,ValueError,KeyError,IndexError):
        return None

def audit(dataset:Path,original_first:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_CAUSAL_AUDIT")
    out.mkdir(parents=True)
    data=json.loads(dataset.read_text())
    original=json.loads(original_first.read_text())
    assert original["summary"]["source_learned_constructor_frozen_sha256"]==\
        "2cd85f1712ef91dbcab4a3bc85c583dfd235dd9ef451ae13282c25aef1cfa332"
    prior={r["id"]:r for r in original["rows"]}
    rows=[];t0=time.perf_counter_ns()
    for source in sorted(data,key=lambda x:x.get("task_id",0)):
        i=source.get("task_id")
        if type(i) is not int or not 511<=i<=974:continue
        first=prior.get(i)
        if first is None:raise ValueError("MISSING_ORIGINAL_FIRST_TASK")
        case={"id":i,"first_original_eligible":first.get("original_test_total")==1}
        if first.get("original_test_total")!=1:
            case["status"]="ORIGINAL_UNSUPPORTED"
            rows.append(case);continue
        try:
            calls=[parse_one_assertion(test) for test in source["test_list"]]
            train=[pair for name,pair in calls[:-1]]
            t=time.perf_counter_ns()
            pred,attempts,_=infer_predicate(train)
            cold_ms=(time.perf_counter_ns()-t)/1e6
            args,y=calls[-1][1]
            prediction=cold_fold_with_full_same_feature_vocabulary(args,pred)
                        if pred is not None else None
            exact=pred is not None and same(prediction,y)
            case.update({"status":"SCORED",
                         "cold_predicate_ast":pred,
                         "cold_predictor_attempts":attempts,
                         "cold_ms":round(cold_ms,6),
                         "cold_exact":bool(exact),
                         "source_memory_original_exact":first["new_generated_exact"],
                         "source_memory_original_predicate":first["source_generated_predicate"],
                         "same_generated_predicate_without_memory":pred==first[
                             "source_generated_predicate"]})
        except (ValueError,TypeError,IndexError,KeyError,RecursionError) as e:
            case.update({"status":"COLD_ERROR",
                         "reason":str(e)[:150],"cold_exact":False,
                         "source_memory_original_exact":first["new_generated_exact"]})
        rows.append(case)
    eligible=[r for r in rows if r["first_original_eligible"]]
    scored=[r for r in eligible if r["status"]=="SCORED"]
    summary={
        "same_previous_MBBP_original_task_IDs":len(rows),
        "eligible_originals":len(eligible),
        "cold_scored":len(scored),
        "with_source_learned_constructor_exact":sum(
            r["source_memory_original_exact"] for r in eligible),
        "without_source_learned_constructor_FULL_SAME_FEATURE_GRAMMAR_exact":sum(
            r["cold_exact"] for r in eligible),
        "source_memory_accuracy_lift":sum(
            r["source_memory_original_exact"] for r in eligible)-
            sum(r["cold_exact"] for r in eligible),
        "identical_generated_predicates":sum(
            r.get("same_generated_predicate_without_memory",False) for r in scored),
        "cold_total_feature_candidate_attempts":sum(
            r.get("cold_predictor_attempts",0) for r in eligible),
        "cold_full_wall_ms":round((time.perf_counter_ns()-t0)/1e6,5),
    }
    result={
       "schema":"neumann.q3.postfirst-matched-cold-meta-ablation.v1",
       "original_first_run":ORIGINAL_RUN,
       "original_first_immutable_not_overwritten":True,
       "not_new_blind_independent_originals":True,
       "same_typed_feature_grammar_as_memory_arm":True,
       "only_learned_constructor_AST_removed":True,
       "comparison_uses_predefined_GENERIC_fold_core":True,
       "new_function_not_handcoded_by_task_ID":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
       "summary":summary,"rows":rows}
    (out/"POSTFIRST_MATCHED_MEMORY_ABLATION.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3_POSTFIRST_MEMORY_CAUSAL_ABLATION",
        json.dumps(summary,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--mbpp",type=Path,required=True)
    ap.add_argument("--first",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    audit(a.mbpp,a.first,a.out)
