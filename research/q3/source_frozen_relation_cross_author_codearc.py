"""Q3 source-frozen relational-constructor transfer to independently authored
CodeARC originals, with an honest COLD matched comparator.

IMPORTANT: all CodeARC original IDs appeared in previous #712 full original
audit. Therefore the corpus is DEV-EXPOSED, not a pristine Q3 blind set.
The relation constructor source AST is frozen from HumanEval/48 POSTFIRST
#717 before its new CodeARC execution. No human adds a source task operator.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from collections import defaultdict
from pathlib import Path
from research.q3.codearc_universal_meta_external_first import parse_case
from research.q3.discover_index_relation_constructor import (
    discover,run_new_representation,SCHEMA as PROGRAM_SCHEMA
)

CODEARC_SHA="3f08820594d4825c78bbdcc3b8eb2e6c8c0285fb3de966e900463b53f1723962"
PREVIOUS_RELATIONAL_RUN=42363017165

def transfer(dataset:Path,prior:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_CROSS_AUTHOR_FIRST")
    if hashlib.sha256(dataset.read_bytes()).hexdigest()!=CODEARC_SHA:
        raise RuntimeError("CODEARC_SOURCE_SHA_MISMATCH")
    out.mkdir(parents=True)
    original=json.loads(prior.read_text())
    if original["original_first_source_actions_run"]!=42361601013 or \
       original["summary"]["new_symbolically_proven_relation_programs"]!=1:
        raise ValueError("UNVERIFIED_PRIOR_SOURCE_EVIDENCE")
    parent=next(r for r in original["rows"] if r["id"]=="HumanEval/48")
    if not parent["original_heldout_exact"] or \
       parent["affine_relation_coeffs"]!=[-1,1,-1]:
        raise ValueError("SOURCE_PROGRAM_NOT_PROVEN")
    source_program=parent["invented_representation_ast"]
    source_hash=hashlib.sha256(json.dumps(
        source_program,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    taskrows=defaultdict(dict);allids=set()
    for line in dataset.open(encoding="utf8"):
        if not line.strip():continue
        record=json.loads(line)
        try:
            if record.get("type")!="annotated":continue
            ident=int(record["problem_id"]);ix=int(record["index"])
            allids.add(ident)
            if 0<=ix<=9 and ix not in taskrows[ident]:
                taskrows[ident][ix]=record
        except (ValueError,KeyError,TypeError):
            continue
    start=time.perf_counter_ns()
    results=[]
    for identifier in sorted(allids):
        r={"external_original_id":identifier,"status":"NOT_CHECKED",
           "source_code_or_function_name_not_passed":True,
           "train_indices":list(range(7)),
           "original_test_indices":[7,8,9]}
        try:
            src=taskrows[identifier]
            if any(j not in src for j in range(10)):
                raise ValueError("MISSING_ORIGINAL_IO")
            train=[parse_case(src[j]) for j in range(7)]
            if any(len(args)!=1 or type(y) is not bool or
                   type(args[0]) not in (str,list,tuple)
                   for args,y in train):
                raise ValueError("NOT_SEQUENCE_TO_BOOL")
            # BOTH competing programs generated/frozen BEFORE any test IO:
            t=time.perf_counter_ns()
            reuse_pass=all(run_new_representation(source_program,args) is y
                           for args,y in train)
            reuse_ms=round((time.perf_counter_ns()-t)/1e6,5)
            cold=discover(train,budget=1200)
            memory_ast=source_program if reuse_pass else cold["program"]
            memory_attempts=1 if reuse_pass else 1+cold["attempts"]
            # Only now read independently published source original test IO.
            test=[parse_case(src[j]) for j in (7,8,9)]
            if any(len(args)!=1 or type(y) is not bool for args,y in test):
                raise ValueError("HELDOUT_TARGET_TYPE_DRIFT")
            marks=[memory_ast is not None and
                   run_new_representation(memory_ast,args) is y
                   for args,y in test]
            coldmarks=[cold["program"] is not None and
                   run_new_representation(cold["program"],args) is y
                   for args,y in test]
            r.update({
                "status":"EVALUATED",
                "prior_symbolic_relation_used":reuse_pass,
                "source_prior_program_sha256":source_hash,
                "memory_AST":memory_ast,
                "cold_discovered_AST":cold["program"],
                "memory_candidates":memory_attempts,
                "cold_candidates":cold["attempts"],
                "memory_prior_probe_ms":reuse_ms,
                "cold_invention_ms":cold.get("wall_ms"),
                "test_count":len(test),
                "memory_original_exact":sum(marks),
                "cold_original_exact":sum(coldmarks),
                "memory_all_3_exact":all(marks),
                "cold_all_3_exact":all(coldmarks),
                "causal_exact_added_over_cold":all(marks) and not all(coldmarks),
            })
            if all(marks):
                print("Q3_RELATIONAL_TRANSFER_AUTHOR_ORIGINAL_EXACT",identifier,
                     "prior_reused",reuse_pass,"cold",all(coldmarks),
                     "attempts",memory_attempts,cold["attempts"],flush=True)
        except (ValueError,IndexError,TypeError,KeyError,
                SyntaxError,MemoryError,OverflowError,RecursionError) as e:
            r.update({"status":"INELIGIBLE",
                      "reason":(type(e).__name__+":"+str(e))[:190],
                      "test_count":0})
        results.append(r)
    eligible=[x for x in results if x.get("test_count")==3]
    summary={
        "entire_prior_exposed_codearc_source_originals":len(allids),
        "eligible_originals":len(eligible),
        "source_data_already_exposed_by_NEUMANN_PR712":True,
        "previously_generated_parent_relation_proven":True,
        "source_cross_author":True,
        "prior_operator_reusable_on_seven_training_examples":sum(
            x["prior_symbolic_relation_used"] for x in eligible),
        "prior_memory_original_all3_exact":sum(
            x["memory_all_3_exact"] for x in eligible),
        "cold_synthesizer_original_all3_exact":sum(
            x["cold_all_3_exact"] for x in eligible),
        "memory_additional_originals_over_cold":sum(
            x["causal_exact_added_over_cold"] for x in eligible),
        "memory_attempts_total":sum(
            x["memory_candidates"] for x in eligible),
        "cold_attempts_total":sum(
            x["cold_candidates"] for x in eligible),
        "heldout_exact_memory":sum(
            x["memory_original_exact"] for x in eligible),
        "heldout_exact_cold":sum(
            x["cold_original_exact"] for x in eligible),
        "heldout_possible":3*len(eligible),
        "source_prior_AST_sha256":source_hash,
        "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
    }
    report={
        "schema":"neumann.q3.known-codearc-cross-author-relation-transfer.v1",
        "original_source_benchmark":"Anjiang Wei et al CodeARC original",
        "source_original_data_sha256":CODEARC_SHA,
        "source_parent_program_from_HumanEval_run":PREVIOUS_RELATIONAL_RUN,
        "original_codearc_dataset_NOT_BLIND":True,
        "all_original_records_preserved":True,
        "all_original_tests_read_only_AFTER_both_candidates":True,
        "human_authored_generic_VM":True,
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
        "summary":summary,"rows":results,
    }
    (out/"FIRST.json").write_text(json.dumps(
        report,sort_keys=True,indent=2)+"\n")
    print("Q3_RELATIONAL_CROSS_AUTHOR_CODEARC_SOURCE_EXPOSED_TRANSFER",
          json.dumps(summary,sort_keys=True),flush=True)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--codearc",type=Path,required=True)
    p.add_argument("--prior",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    transfer(a.codearc,a.prior,a.out)
