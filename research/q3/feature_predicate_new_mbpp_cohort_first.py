"""Q3 post-first predicate abstraction audit and new MBPP validation/train cohort.

Same benchmark author, but task IDs 511..974 have NEVER been scored in the
previous #713 run (which selected 11..510 only). Source library is FROZEN
before data retrieval by workflow, and no reference code or natural-language
prompt is supplied to the source program invention kernel.

Training: all but last official test assertions; heldout: last official
assertion. Small sample count and public tests prevent global Q3 PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

from research.q3.learn_constructor_then_mbpp_original_first import (
    parse_one_assertion,SCHEMA as SOURCE_SCHEMA
)
from research.q3.reflexive_constructor_from_experience import (
    canonical,construct,execute_safe
)
from research.q3.feature_predicate_from_counterexample import (
    generate_fold_from_learned_constructor,run_generated
)
from research.q3.typed_semantic_delta_inventor import (
    synth_filter,execute as old_execute,same
)

SCHEMA="neumann.q3.source-frozen-feature-predicate-new-mbpp-cohort.v1"

def evaluate(path:Path,source_freeze:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_ORIGINAL_COHORT")
    out.mkdir(parents=True)
    data=json.loads(source_freeze.read_text())
    if data.get("schema")!=SOURCE_SCHEMA:
        raise RuntimeError("BAD_SOURCE_CONSTRUCTOR_SCHEMA")
    source=data["learned_program_generator"]
    fingerprint=hashlib.sha256(canonical(source).encode()).hexdigest()
    if fingerprint!="2cd85f1712ef91dbcab4a3bc85c583dfd235dd9ef451ae13282c25aef1cfa332":
        raise RuntimeError("SOURCE_GENERATED_CONSTRUCTOR_CHANGED")
    corpus=json.loads(path.read_text())
    if len(corpus)<400:raise ValueError("NOT_OFFICIAL_SANITIZED_MBPP")
    start=time.perf_counter_ns()
    records=[]
    for task in sorted(corpus,key=lambda x:x.get("task_id",0)):
        ident=task.get("task_id")
        if type(ident) is not int or not 511<=ident<=974:continue
        rec={"id":ident,"source_status":"UNKNOWN",
             "train_test_original_assertions":"all-but-last vs last",
             "no_reference_function_code_or_prompt_used":True}
        try:
            tests=task["test_list"]
            if len(tests)<3:raise ValueError("LESS_THAN_THREE_TESTS")
            cases=[parse_one_assertion(test) for test in tests]
            if len({a for a,b in cases})!=1:
                raise ValueError("MULTIPLE_NAMES")
            source_only=[pair for name,pair in cases[:-1]]
            if len({type(args[0]) for args,y in source_only})!=1 or \
               len({type(y) for args,y in source_only})!=1:
                raise ValueError("HETEROGENEOUS_SOURCE")
            t0=time.perf_counter_ns()
            generated,attempts,trace=generate_fold_from_learned_constructor(
                source,source_only)
            new_ms=round((time.perf_counter_ns()-t0)/1e6,6)
            literal=construct(source,source_only)
            old,count=synth_filter(source_only)
            rec.update({
                "source_status":"TRAIN_SAT" if generated else "ABSTAIN",
                "source_generated_ast":generated,
                "source_generated_predicate":generated["predicate"] if generated else None,
                "source_predicate_candidate_attempts":attempts,
                "source_candidate_trace":trace,
                "source_new_construction_ms":new_ms,
                "source_old_literal_constructor_ast":literal,
                "source_prior_strong_filter_ast":old,
                "source_prior_strong_filter_candidates":count})
            # All learners have returned/frozen a program BEFORE using
            # last published assertion for score.
            args,actual=cases[-1][1]
            a=(generated is not None and
               same(run_generated(generated,args),actual))
            b=(literal is not None and execute_safe(literal,args)==(True,actual))
            c=(old is not None and same(old_execute(old,args),actual))
            nonliteral=(
                generated is not None and
                generated["predicate"][0]!="member")
            rec.update({
                "status":"EXACT" if a else "WRONG_OR_ABSTAIN",
                "original_test_total":1,
                "new_generated_exact":bool(a),
                "old_learned_literal_exact":bool(b),
                "old_strong_filter_exact":bool(c),
                "new_predicate_kind":generated["predicate"][0] if generated else None,
                "nonliteral_executable_AST":bool(nonliteral),
                "nonliteral_exact_beats_strong_baseline":bool(a and nonliteral and not c),
            })
            if a:
                print("Q3_PREDICATE_EXTERNAL_EXACT",ident,
                      "predicate",generated["predicate"],
                      "old_strong",c,flush=True)
        except (TypeError,ValueError,KeyError,IndexError,
                SyntaxError,MemoryError,RecursionError,OverflowError) as e:
            rec.update({"status":"INELIGIBLE",
                        "reason":(type(e).__name__+":"+str(e))[:170],
                        "original_test_total":0,
                        "new_generated_exact":False,
                        "nonliteral_exact_beats_strong_baseline":False})
        records.append(rec)
    eligible=[r for r in records if r.get("original_test_total")==1]
    summary={
        "official_validation_and_train_IDs":len(records),
        "new_originals_eligible":len(eligible),
        "new_originals_ineligible":len(records)-len(eligible),
        "self_generated_predicate_train_satisfied":sum(
            x["source_generated_ast"] is not None for x in eligible),
        "original_heldout_exact_new_predicate":sum(
            x["new_generated_exact"] for x in eligible),
        "original_heldout_exact_strong_old_filter":sum(
            x["old_strong_filter_exact"] for x in eligible),
        "original_heldout_exact_old_literal_constructor":sum(
            x["old_learned_literal_exact"] for x in eligible),
        "novel_nonliteral_predicate_exact_beating_strong":sum(
            x["nonliteral_exact_beats_strong_baseline"] for x in eligible),
        "total_new_predicate_candidate_checks":sum(
            x["source_predicate_candidate_attempts"] for x in eligible),
        "source_learned_constructor_frozen_sha256":fingerprint,
        "original_public_heldout_one_assertion_per_task":True,
        "same_benchmark_author_other_task_IDs":True,
        "score_ms":round((time.perf_counter_ns()-start)/1e6,4),
    }
    result={
        "schema":SCHEMA,"source_dataset":"Official Google Research MBPP sanitized",
        "source_data_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_LEARNED_meta_constructor_before_target":True,
        "source_new_generic_feature_primitives_HUMAN_CODED":True,
        "source_MBPP_first_test_IDs_11_510_EXCLUDED":True,
        "old_mbpp_exposed_tasks_postfirst_audit_only":[412,426,451],
        "input_output_inductive_program_synthesis":True,
        "output_functions_unknown":True,"global_Q3":"OPEN",
        "global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"rows":records,
    }
    (out/"FIRST.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3_FEATURE_PREDICATE_UNSCORED_MBPP_NEW_COHORT",
          json.dumps(summary,sort_keys=True),flush=True)
    return result

def exposed_development_audit(source_freeze:Path):
    """Never score these as new external originals. They are EXPOSED tasks."""
    frozen=json.loads(source_freeze.read_text())["learned_program_generator"]
    examples={
      412:([([1,2,3],[2]),([2,4,6],[2,4,6])],[[9,10]],[10]),
      426:([([1,2,3,4,5,6,7,8,9,10],[1,3,5,7,9]),
            ([10,20,45,67,84,93],[45,67,93])],[[11,12,13,14]],[11,13]),
      451:([([" Google    Flutter "],"GoogleFlutter"),
            ([" Google    Dart "],"GoogleDart")],
            ["x\ty\nz"],"xyz"),
    }
    result=[]
    for ident,(train,inputs,y) in examples.items():
        generated,attempts,_=generate_fold_from_learned_constructor(frozen,train)
        passed=generated is not None and run_generated(generated,inputs)==y
        literal=construct(frozen,train)
        old_ok=literal is not None and execute_safe(literal,inputs)==(True,y)
        result.append({"id":ident,"target_exposed_postfirst":True,
                       "new_generated_predicate":generated["predicate"]
                            if generated else None,
                       "separate_probing_input":inputs,
                       "separate_probe_expected":y,
                       "actual":run_generated(generated,inputs)
                            if generated else None,
                       "passes":bool(passed),"old_literal_passes":bool(old_ok),
                       "candidate_attempts":attempts})
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mbpp",required=True,type=Path)
    p.add_argument("--source-frozen",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    source=a.source_frozen
    check=exposed_development_audit(source)
    print("Q3_DEVELOPMENT_EXPOSED_POSTFIRST_COUNTEREXAMPLE_REPAIR",
          json.dumps(check,sort_keys=True),flush=True)
    target=evaluate(a.mbpp,source,a.out)
    (a.out/"EXPOSED_DEVELOPMENT_AUDIT.json").write_text(
        json.dumps(check,sort_keys=True,indent=2)+"\n")
