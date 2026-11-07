"""Q3 source-frozen original CodeARC execution-only external FIRST.

CodeARC was independently published by COLM 2025 authors (1114 functions).
NEUMANN receives ONLY literal function argument values and seven I/O pairs,
never code, task prompts, source function name, or reserved last-three outputs.
The program is FROZEN before scoring indices 7/8/9.

Preregistered cohort: exclude IDs <= 20 already glimpsed in website;
among remaining IDs select SHA256('NEUMANN-Q3-FIRST/'+id) modulo 17 == 0;
ALL selected, no cherry-pick. The CodeARC authors' examples were previously
published; this is external-source development evidence, not secret blind.
"""
from __future__ import annotations
import argparse
import ast
import copy
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from research.q3.universal_recursive_meta_inventor import (
    InventingLanguage,enumerate_solution,run,digest,typeid,
)

SCHEMA="neumann.q3.universal-recursive-meta-codearc-external-first.v1"
LABEL=re.compile(r"^Result\s+\d+\s*:\s?")

def parse_case(row):
    if row.get("errored") not in (False,0,"false","False"):
        raise ValueError("source_invocation_errored")
    body=row.get("input")
    if type(body) is not str or len(body)>10000:
        raise ValueError("not_python_source")
    code=ast.parse(body,mode="exec")
    if len(code.body)!=1 or not isinstance(code.body[0],ast.Expr):
        raise ValueError("not_single_print")
    call=code.body[0].value
    if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) \
       or call.func.id!="print" or len(call.args)!=1:
        raise ValueError("unsupported_display")
    wrapped=call.args[0]
    if not isinstance(wrapped,ast.BinOp) or not isinstance(wrapped.op,ast.Add):
        raise ValueError("non_standard_display_prefix")
    hidden=wrapped.right
    if isinstance(hidden,ast.Call) and isinstance(hidden.func,ast.Name) \
       and hidden.func.id=="str":
        if len(hidden.args)!=1:raise ValueError("bad_str_wrapper")
        hidden=hidden.args[0]
    if not isinstance(hidden,ast.Call) or hidden.keywords:
        raise ValueError("unsupported_hidden_invocation")
    if len(hidden.args) not in (1,2):
        raise ValueError("unsupported_arity")
    # Crucial: hidden.func identifier is NOT read, stored, or supplied.
    args=[]
    for arg in hidden.args:
        value=ast.literal_eval(arg)
        if type(value) not in (int,float,bool,list,str,tuple):
            raise ValueError("unsupported_input_type")
        args.append(value)
    displayed=row.get("output")
    if type(displayed) is not str:raise ValueError("not_display_output")
    label=LABEL.match(displayed)
    if not label:raise ValueError("unrecognized_label")
    text=displayed[label.end():]
    if len(text)>2000:raise ValueError("large_output")
    try:answer=ast.literal_eval(text)
    except (SyntaxError,ValueError,TypeError,MemoryError):answer=text
    if type(answer) not in (int,float,bool,str,list,tuple):
        raise ValueError("unsupported_output_type")
    return args,answer

def cohort(identifier,mod=17):
    if identifier<=20:return False
    h=sha256(("NEUMANN-Q3-FIRST/"+str(identifier)).encode()).hexdigest()
    return int(h[:8],16)%mod==0

def study(dataset:Path,out:Path,modulus=17,budget=34000):
    if out.exists():raise ValueError("NO_OVERWRITE_EXTERNAL_FIRST")
    out.mkdir(parents=True)
    groups=defaultdict(dict)
    raw_rows=0
    with dataset.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():continue
            raw_rows+=1
            source=json.loads(line)
            try:
                pid=int(source["problem_id"])
                idx=int(source["index"])
                if source.get("type")!="annotated" or not 0<=idx<=9:continue
                if idx not in groups[pid]:groups[pid][idx]=source
            except (KeyError,TypeError,ValueError):continue
    public_ids=sorted(groups)
    selected=[pid for pid in public_ids if cohort(pid,modulus)]
    language=InventingLanguage()
    rows=[]
    for pid in selected:
        original=groups[pid]
        record={
            "id":pid,"external_source":"CodeARC published annotated 10 I/O",
            "source_code_or_function_name_given_to_solver":False,
            "train_indices":list(range(7)),"test_indices":[7,8,9],
            "status":"UNSET"}
        try:
            if any(idx not in original for idx in range(10)):
                raise ValueError("missing_invocation_index")
            # First 7 only. All generated programs are frozen before test parse.
            train=[parse_case(original[idx]) for idx in range(7)]
            contracts={
                (tuple(typeid(v) for v in args),typeid(y))
                for args,y in train}
            if len(contracts)!=1:raise ValueError("heterogeneous_training_schema")
            contract=next(iter(contracts))
            # Cold full recursive search, static first-order baseline, online
            # language (which includes only PRIOR independently verified ASTs).
            static=enumerate_solution(train,min(2000,budget),
                                      allow_recursive=False)
            cold=enumerate_solution(train,budget,allow_recursive=True)
            before=(copy.deepcopy(language.definitions),
                    copy.deepcopy(language.grammar),
                    copy.deepcopy(language.history))
            found=language.solve(train,budget=budget)
            record.update({
                "status":found["status"],
                "contract":contract,
                "generated_executable_AST":found["program"],
                "program_hash":digest(found["program"]) if found["program"] else None,
                "train_search_attempts":found["attempts"],
                "train_wall_ms":found.get("time_ms"),
                "cold_baseline_status":cold["status"],
                "static_baseline_status":static["status"],
                "cold_search_attempts":cold["attempts"],
            })
            # The three actual original heldouts are accessed ONLY here,
            # after ALL three ASTs (cold/static/growing) have been generated.
            test=[parse_case(original[idx]) for idx in (7,8,9)]
            if any((tuple(typeid(a) for a in x),typeid(y))!=contract
                    for x,y in test):
                language.definitions,language.grammar,language.history=before
                raise ValueError("test_type_signature_drift")
            def matches(program):
                return [program is not None and
                    type(run(program,x)) is type(y) and run(program,x)==y
                    for x,y in test]
            warm_marks=matches(found["program"])
            cold_marks=matches(cold["program"])
            static_marks=matches(static["program"])
            record.update({
                "test_total":len(test),"heldout_correct":sum(warm_marks),
                "heldout_exact":all(warm_marks),
                "cold_test_exact":all(cold_marks),
                "static_test_exact":all(static_marks),
                "cold_test_correct":sum(cold_marks),
                "static_test_correct":sum(static_marks),
            })
            if not all(warm_marks):
                # A failed/overfit program is NOT deposited into active memory.
                language.definitions,language.grammar,language.history=before
            record["retained_in_library"]=bool(all(warm_marks)
                and found["program"] is not None
                and found["status"]!="reused")
            record["library_programs_after"]=len(language.definitions)
            record["learned_grammar_productions_after"]=len(language.grammar)
        except (ValueError,TypeError,SyntaxError,KeyError,
                OverflowError,MemoryError,RecursionError) as e:
            record.update({
                "status":"INELIGIBLE_OR_ERROR",
                "reason":(type(e).__name__+":"+str(e))[:180],
                "heldout_exact":False,"heldout_correct":0,"test_total":0})
        rows.append(record)
        if record.get("heldout_exact"):
            print("EXTERNAL_CODEARC_EXACT",pid,record["status"],
                  "attempts",record.get("train_search_attempts"),flush=True)
    eligible=[a for a in rows if a.get("test_total")==3]
    results={
        "original_problem_ids":len(public_ids),
        "raw_invocation_rows":raw_rows,
        "predeclared_modulus":modulus,
        "source_exposed_ids_excluded":list(range(21)),
        "preregistered_cohort_size":len(selected),
        "eligible_full_10_case_problems":len(eligible),
        "program_submissions":sum(x.get("generated_executable_AST") is not None
                                  for x in eligible),
        "cold_recursive_exact_tasks":sum(x["cold_test_exact"] for x in eligible),
        "static_first_order_exact_tasks":sum(x["static_test_exact"] for x in eligible),
        "growing_language_exact_tasks":sum(x["heldout_exact"] for x in eligible),
        "heldout_invocations_exact":sum(x["heldout_correct"] for x in eligible),
        "heldout_invocations_total":3*len(eligible),
        "invented_recursion_exact_tasks":sum(
            x.get("status")=="invented_recursive_operator" and x["heldout_exact"]
            for x in eligible),
        "meta_invented_rule_exact_tasks":sum(
            x.get("status")=="learned_meta_grammar" and x["heldout_exact"]
            for x in eligible),
        "memory_reuse_exact_tasks":sum(
            x.get("status")=="reused" and x["heldout_exact"]
            for x in eligible),
        "active_verified_programs":len(language.definitions),
        "active_new_grammar_rules":len(language.grammar),
        "search_budget_each":budget,
    }
    report={
        "schema":SCHEMA,
        "external_authors":"Anjiang Wei et al., CodeARC COLM 2025",
        "dataset":"anjiangwei/CodeARC-Invocations",
        "dataset_license":"Apache-2.0",
        "dataset_commit_pinned_in_workflow":True,
        "input_output_only_no_gold_function_names":True,
        "human_provided_universal_recursion_base":True,
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
        "all_original_outcomes_retained":True,
        "results":rows,"summary":results,
    }
    (out/"FIRST.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"VERIFIED_GROWN_LANGUAGE.json").write_text(
        json.dumps(language.dump(),indent=2,sort_keys=True)+"\n")
    print("CODEARC_FROZEN_EXTERNAL_FIRST",json.dumps(results,sort_keys=True),
          flush=True)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--modulus",type=int,default=17)
    p.add_argument("--budget",type=int,default=34000)
    a=p.parse_args()
    study(a.dataset,a.out,a.modulus,a.budget)
