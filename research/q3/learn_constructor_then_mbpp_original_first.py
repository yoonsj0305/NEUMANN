"""Q3 external FIRST: source-learned constructor -> independently authored MBPP.

Phase A (MUST precede downloading MBPP):
  recover *already verified* machine-generated CodeARC source programs
  #834 and #841, inspect only first seven source TRAIN I/O, synthesize
  program-generating constructor AST and freeze its SHA256 on disk.

Phase B (after freezing):
  evaluate on ALL applicable hand-verified external Google MBPP problems,
  using first N-1 published assertions as TRAIN and last assertion as
  independently author-created heldout. Reference code and prompt are NEVER
  passed to the inventor or used for predicting.

Result is PUBLIC DEVELOPMENT transfer, not a sealed blind test.
Human provided generic fold, AST antiunifier, binder meta grammar and one
historic filter-to-fold adapter. DO NOT claim global Q3 creative AGI.
"""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

from research.q3.codearc_universal_meta_external_first import parse_case
from research.q3.reflexive_constructor_from_experience import (
    compile_verified_source_filter,execute_safe,fit_sources,construct,
    ident,canonical,meta_eval
)
from research.q3.typed_semantic_delta_inventor import (
    synth_filter,execute as old_execute,same
)

CODEARC_SHA256="3f08820594d4825c78bbdcc3b8eb2e6c8c0285fb3de966e900463b53f1723962"
SOURCE_TASKS=(834,841)
SOURCE_AST={
    834:{"kind":"DerivedSequenceFilter","source_arg":0,"removed":["!"]},
    841:{"kind":"DerivedSequenceFilter","source_arg":0,"removed":[" "]},
}

SCHEMA="neumann.q3.self-generated-constructor-external-mbpp.v1"


def read_codearc_source(path:Path):
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if sha!=CODEARC_SHA256:raise RuntimeError("CODEARC_SOURCE_SHA_MISMATCH")
    history=defaultdict(dict)
    for line in path.open(encoding="utf8"):
        row=json.loads(line)
        try:
            pid=int(row["problem_id"]);j=int(row["index"])
            if pid in SOURCE_TASKS and j<7 and row.get("type")=="annotated":
                history[pid][j]=row
        except (KeyError,TypeError,ValueError):continue
    experiences=[]
    for pid in SOURCE_TASKS:
        if not all(j in history[pid] for j in range(7)):
            raise ValueError("HISTORIC_VERIFIED_SOURCE_TRAIN_MISSING")
        train=[parse_case(history[pid][j]) for j in range(7)]
        body=compile_verified_source_filter(SOURCE_AST[pid])
        if not all(execute_safe(body,args)==(True,y) for args,y in train):
            raise RuntimeError("OLD_PROGRAM_WAS_NOT_VERIFIED_ON_SOURCE")
        experiences.append({"id":pid,"verified_program":SOURCE_AST[pid],
                            "train_io":train})
    return experiences


def freeze_constructor(codearc:Path,out:Path):
    if out.exists():raise ValueError("CANNOT_OVERWRITE_ORIGINAL_FREEZE")
    out.mkdir(parents=True)
    experiences=read_codearc_source(codearc)
    start=time.perf_counter_ns()
    learned,audits=fit_sources(experiences)
    fingerprint=hashlib.sha256(canonical(learned).encode()).hexdigest()
    result={
        "schema":SCHEMA,
        "source_originals":list(SOURCE_TASKS),
        "source_codearc_dataset_sha256":CODEARC_SHA256,
        "historic_executable_programs_previously_verified_in_PR_712":True,
        "source_test_gold_NOT_READ_now":True,
        "source_programs_compiled_into_generic_fold_IR":True,
        "compiler_adapter_human_authored":True,
        "meta_kernel_human_authored":True,
        "learned_constructor_symbol":learned["symbol"],
        "frozen_generated_constructor_sha256":fingerprint,
        "learned_program_generator":learned,
        "candidate_binder_audit":audits,
        "source_learning_ms":round((time.perf_counter_ns()-start)/1e6,4),
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"
    }
    (out/"FROZEN_CONSTRUCTOR.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3_FROZEN_BEFORE_MBPP",json.dumps({
        "source_originals":list(SOURCE_TASKS),
        "new_constructor":learned["symbol"],
        "binder_AST":learned["constructor_program"]["parameter_binder"],
        "freeze_sha256":fingerprint,
        "source_learning_ms":result["source_learning_ms"]},
        sort_keys=True),flush=True)
    return result


def parse_one_assertion(stmt):
    tree=ast.parse(stmt,mode="exec")
    if len(tree.body)!=1 or type(tree.body[0]) is not ast.Assert:
        raise ValueError("UNSUPPORTED_ASSERTION")
    expr=tree.body[0].test
    if not isinstance(expr,ast.Compare) or len(expr.ops)!=1 \
       or type(expr.ops[0]) is not ast.Eq:
        raise ValueError("ONLY_DIRECT_EQ_ASSERTION")
    if len(expr.comparators)!=1:raise ValueError("NON_SINGLE_EQ")
    func=expr.left
    if not isinstance(func,ast.Call) or \
       not isinstance(func.func,ast.Name) or func.keywords:
        raise ValueError("NON_DIRECT_CALL")
    if len(func.args)!=1:raise ValueError("ONLY_SINGLE_ARGUMENT")
    value=ast.literal_eval(func.args[0])
    expected=ast.literal_eval(expr.comparators[0])
    if type(value) not in (str,list,tuple) or \
       type(expected) is not type(value):
        raise ValueError("NOT_SEQUENCE_TO_SAME_CONTAINER")
    if len(value)>1024 or len(expected)>1024:
        raise ValueError("BOUND_EXCEEDED")
    if any(type(x) not in (str,int,float,bool) for x in
           (value if type(value) is not str else list(value))):
        raise ValueError("UNSUPPORTED_ELEMENT_TYPE")
    if any(type(x) not in (str,int,float,bool) for x in
           (expected if type(expected) is not str else list(expected))):
        raise ValueError("UNSUPPORTED_OUTPUT_ELEMENTS")
    return func.func.id,([value],expected)


def program_nontrivial(program,examples):
    if program is None:return False
    # Never claim identity/constant transformations as new operator.
    return any(args[0]!=y for args,y in examples)


def run_mbpp(mbpp:Path,frozen:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_MBPP_FIRST")
    out.mkdir(parents=True)
    source=json.loads(frozen.read_text())
    if source.get("schema")!=SCHEMA:raise ValueError("BAD_FREEZE_SCHEMA")
    learned=source["learned_program_generator"]
    expected_sha=hashlib.sha256(canonical(learned).encode()).hexdigest()
    if source["frozen_generated_constructor_sha256"]!=expected_sha:
        raise ValueError("TAMPERED_CONSTRUCTOR")
    rows=json.loads(mbpp.read_text(encoding="utf8"))
    if type(rows) is not list or len(rows)<400:
        raise ValueError("SOURCE_DATASET_UNEXPECTED_COUNT")
    data_sha=hashlib.sha256(mbpp.read_bytes()).hexdigest()
    report_rows=[]
    total_source=0
    task_t0=time.perf_counter_ns()
    for row in sorted(rows,key=lambda r:r.get("task_id",0)):
        task_id=row.get("task_id")
        # Official MBPP reserved 11..510 test cohort.
        if type(task_id) is not int or not 11<=task_id<=510:
            continue
        total_source+=1
        record={"id":task_id,"status":"UNSET","function_name_not_given_to_inventor":True}
        try:
            # Never inspect row["code"] or row["prompt"].
            statements=row["test_list"]
            if len(statements)<3:raise ValueError("TOO_FEW_ORIGINAL_TESTS")
            parsed=[parse_one_assertion(q) for q in statements]
            names={name for name,pair in parsed}
            if len(names)!=1:raise ValueError("INCONSISTENT_FUNCTION_NAME")
            train=[pair for name,pair in parsed[:-1]]
            if not all(type(args[0]) is type(train[0][0][0]) and
                       type(y) is type(train[0][1]) for args,y in train):
                raise ValueError("MIXED_TRAINING_TYPES")
            t0=time.perf_counter_ns()
            program=construct(learned,train)
            novel_ms=(time.perf_counter_ns()-t0)/1e6
            # Strong PRIOR manually-coded filter benchmark, frozen at #712.
            old,old_count=synth_filter(train)
            record.update({
                "status":"ABSTAIN" if program is None else "TRAIN_SAT",
                "train_count":len(train),
                "candidate_program_ast":program,
                "constructor_program_source_sha256":expected_sha,
                "is_nontrivial_on_train":program_nontrivial(program,train),
                "source_program_is_newly_generated":program is not None,
                "candidate_generation_ms":round(novel_ms,5),
                "strong_old_filter_baseline_ast":old,
                "strong_old_filter_attempts":old_count})
            # Gold heldout is parsed above to check type, but not given to
            # construct, synth_filter or any source-inference module.
            args,y=parsed[-1][1]
            correct=program is not None and execute_safe(program,args)==(True,y)
            old_correct=old is not None and same(old_execute(old,args),y)
            record.update({
                "heldout_count":1,
                "heldout_exact":bool(correct),
                "old_filter_heldout_exact":bool(old_correct),
                "learned_constructor_novel_exact":bool(correct and
                    record["is_nontrivial_on_train"])})
            if correct:
                print("Q3_MBPP_EXTERNAL_EXACT",task_id,
                      "new_IR",program,
                      "old_strong_filter",old_correct,flush=True)
        except (TypeError,ValueError,KeyError,IndexError,
                SyntaxError,MemoryError,OverflowError,RecursionError) as e:
            record.update({"status":"INELIGIBLE",
                           "reason":(type(e).__name__+":"+str(e))[:180],
                           "heldout_count":0,"heldout_exact":False,
                           "learned_constructor_novel_exact":False})
        report_rows.append(record)
    eligible=[r for r in report_rows if r.get("heldout_count")==1]
    summary={
        "original_source_tasks_in_official_test_split":total_source,
        "eligible_typed_literal_equality_originals":len(eligible),
        "unsupported_originals":total_source-len(eligible),
        "new_constructor_train_satisfied":sum(
            r["candidate_program_ast"] is not None for r in eligible),
        "new_constructor_heldout_exact":sum(
            r["heldout_exact"] for r in eligible),
        "nontrivial_learned_constructor_heldout_exact":sum(
            r["learned_constructor_novel_exact"] for r in eligible),
        "STRONG_PRIOR_HUMAN_FILTER_baseline_heldout_exact":sum(
            r["old_filter_heldout_exact"] for r in eligible),
        "new_constructor_exact_and_strong_filter_failed":sum(
            r["heldout_exact"] and not r["old_filter_heldout_exact"]
            for r in eligible),
        "search_after_source_frozen":True,
        "learned_meta_program_sha256":expected_sha,
        "external_data_sha256":data_sha,
        "external_evaluation_ms":round(
            (time.perf_counter_ns()-task_t0)/1e6,3),
    }
    report={
        "schema":SCHEMA,"source_original_dataset":"CodeARC",
        "external_independent_benchmark":"Google Research sanitized MBPP",
        "external_data_public":True,"mbpp_author_code_not_used":True,
        "function_prompt_not_read":True,
        "original_training_test_split":"all-but-last vs last public assertion",
        "one_heldout_assertion_PER_TASK_limit":True,
        "source_experience_was_development_exposed":True,
        "human_seed_meta_kernel_and_source_adapter":True,
        "new_constructor_ast_generated_before_mbpp_download":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"rows":report_rows,
    }
    (out/"FIRST.json").write_text(json.dumps(
        report,sort_keys=True,indent=2)+"\n")
    print("Q3_MBPP_INDEPENDENT_EXTERNAL_FIRST",json.dumps(
        summary,sort_keys=True),flush=True)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("source","mbpp"))
    p.add_argument("--codearc",type=Path)
    p.add_argument("--mbpp",type=Path)
    p.add_argument("--frozen",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.mode=="source":
        if args.codearc is None:raise ValueError("--codearc missing")
        freeze_constructor(args.codearc,args.out)
    else:
        if args.mbpp is None or args.frozen is None:
            raise ValueError("--mbpp and --frozen required")
        run_mbpp(args.mbpp,args.frozen,args.out)
