"""Q3 external first on a NEW original CodeARC cohort, disjoint from old 84.

The first failed Q3 generic interpreter read only problems selected by
sha256('NEUMANN-Q3-FIRST/'+id) % 17 == 0. This NEW original gate selects
the SAME original hash %17 == 1. No explicit task IDs or gold heldout outputs
appear in the inventor. 7 TRAIN and 3 TEST original code executions.

Independent evaluator keeps full train/cold/no-new experiments and freezes
programs BEFORE parsing indices 7,8,9. Retains only programs that later
exactly match all 3 original tests; therefore any warm library transfer is
development-style ONLINE learning, not a pristine one-shot model test.
"""
from __future__ import annotations
from collections import defaultdict,Counter
from hashlib import sha256
from pathlib import Path
import argparse,json,time
from research.q3.codearc_universal_meta_external_first import parse_case
from research.q3.typed_semantic_delta_inventor import (
    TypeGuidedInventor,execute,same,digest,
)

SCHEMA="neumann.q3.typed-delta-codearc-source-distinct-first.v1"
DATA_SHA="3f08820594d4825c78bbdcc3b8eb2e6c8c0285fb3de966e900463b53f1723962"

def hash_bucket(identifier):
    return int(sha256(("NEUMANN-Q3-FIRST/"+str(identifier))
              .encode()).hexdigest()[:8],16)%17

def fresh_target(identifier):
    return identifier>20 and hash_bucket(identifier)==1

def evaluate(file:Path,out:Path,shard=0,shards=2):
    if out.exists():raise ValueError("NEVER_OVERWRITE_EXTERNAL_FIRST")
    if not 0<=shard<shards:raise ValueError("INVALID_SHARD")
    if sha256(file.read_bytes()).hexdigest()!=DATA_SHA:
        raise RuntimeError("PINNED_EXTERNAL_ORIGINAL_CHANGED")
    out.mkdir(parents=True)
    data=defaultdict(dict);allids=set()
    for line in file.open(encoding="utf8"):
        if not line.strip():continue
        row=json.loads(line)
        try:
            if row.get("type")!="annotated":continue
            pid=int(row["problem_id"]);idx=int(row["index"])
            allids.add(pid)
            if fresh_target(pid) and 0<=idx<=9:
                data[pid][idx]=row
        except (ValueError,TypeError,KeyError):continue
    cohort=sorted(i for i in allids if fresh_target(i))
    assigned=cohort[shard::shards]
    language=TypeGuidedInventor(enable_structure_memory=True)
    records=[]
    for pid in assigned:
        source=data[pid]
        rec={"original_id":pid,
             "source_code_function_name_not_supplied":True,
             "train_indices":list(range(7)),
             "test_indices":[7,8,9],
             "status":"UNSET"}
        try:
            if any(i not in source for i in range(10)):
                raise ValueError("MISSING_ORIGINAL_IO")
            train=[parse_case(source[i]) for i in range(7)]
            if not all(len(args)==len(train[0][0]) for args,y in train):
                raise ValueError("VARIABLE_ARITY")
            # SOURCE ONLY: all independent programs generated before TEST parse.
            chosen=language.propose(train,allow_new_representations=True)
            without=TypeGuidedInventor(enable_structure_memory=False).propose(
                train,allow_new_representations=False)
            cold=TypeGuidedInventor(enable_structure_memory=False).propose(
                train,allow_new_representations=True)
            rec.update({"status":chosen["status"],
                        "generated_operator_AST":chosen["program"],
                        "old_core_ablated_AST":without["program"],
                        "new_without_memory_AST":cold["program"],
                        "core_ablated_status":without["status"],
                        "cold_status":cold["status"],
                        "proposals_with_memory":chosen["attempts"],
                        "proposals_without_new_representations":without["attempts"],
                        "proposals_cold_new":cold["attempts"],
                        "train_ms":chosen.get("ms"),
                        "cold_train_ms":cold.get("ms"),
                        "train_all_7_exact":chosen["program"] is not None and
                          all(same(execute(chosen["program"],args),goal)
                              for args,goal in train),
                        "program_frozen_hash":digest(chosen["program"])
                            if chosen["program"] else None})
            # Only NOW parse actual heldout gold.
            test=[parse_case(source[i]) for i in (7,8,9)]
            if any(len(args)!=len(train[0][0]) for args,y in test):
                raise ValueError("TEST_ARITY_DRIFT")
            def marks(program):
                return [program is not None and
                        same(execute(program,args),goal) for args,goal in test]
            direct=marks(chosen["program"])
            base=marks(without["program"])
            no_memory=marks(cold["program"])
            rec.update({
                "status":"EXACT" if all(direct) else
                       "WRONG_OR_ABSTAIN",
                "test_total":len(test),
                "test_exact":sum(direct),
                "all_3_test_exact":all(direct),
                "old_core_test_exact":sum(base),
                "old_core_all_3_exact":all(base),
                "cold_new_test_exact":sum(no_memory),
                "cold_new_all_3_exact":all(no_memory),
                "verified_test_exact":all(direct),
                "earned_new_representation": bool(
                    chosen["program"] and
                    chosen["program"]["kind"] in (
                     "DerivedSequenceFilter","DerivedPolynomial") and
                    all(direct) and not all(base)),
                "source_method":chosen["status"],
            })
            if all(direct):
                language.retain_independently_verified({
                    "program":chosen["program"],
                    "verified_test_exact":True})
            if all(direct):
                print("ORIGINAL_EXTERNAL_EXACT",pid,
                      chosen["program"]["kind"],
                      "BEATS_NO_NEW",not all(base),
                      "PROPOSALS",chosen["attempts"],flush=True)
        except (ValueError,TypeError,KeyError,SyntaxError,
                OverflowError,MemoryError,RecursionError) as e:
            rec["status"]="INELIGIBLE"
            rec["error"]=(type(e).__name__+":"+str(e))[:220]
            rec["test_total"]=0
            rec["test_exact"]=0
            rec["all_3_test_exact"]=False
        records.append(rec)
    eligible=[r for r in records if r.get("test_total")==3]
    summary={
        "source_total_originals":len(allids),
        "prior_dev_cohort_rule":"old digest mod17 == 0",
        "fresh_unexposed_cohort_rule":"same digest mod17 == 1",
        "cohort_total":len(cohort),
        "shard":shard,"shards":shards,
        "assigned_originals":len(assigned),
        "eligible_originals":len(eligible),
        "originals_exact_all_3":sum(r["all_3_test_exact"] for r in eligible),
        "originals_exact_old_core":sum(r["old_core_all_3_exact"] for r in eligible),
        "originals_exact_no_memory":sum(
            r["cold_new_all_3_exact"] for r in eligible),
        "invented_new_representation_exact_and_baseline_failed":sum(
            r.get("earned_new_representation",False) for r in eligible),
        "original_test_examples_exact":sum(r["test_exact"] for r in eligible),
        "original_test_examples_total":len(eligible)*3,
        "wrong_or_abstain":sum(not r["all_3_test_exact"] for r in eligible),
        "retained_verified_programs":len(language.verified_programs),
        "distinct_generated_operator_kinds":dict(Counter(
            r.get("generated_operator_AST",{}).get("kind")
            for r in eligible if r.get("generated_operator_AST") is not None)),
        "total_proposals_memory":sum(
            r.get("proposals_with_memory",0) for r in eligible),
        "total_proposals_no_memory":sum(
            r.get("proposals_cold_new",0) for r in eligible),
    }
    report={
        "schema":SCHEMA,
        "external_source":"anjiangwei/CodeARC-Invocations",
        "original_dataset_sha256":DATA_SHA,
        "source_pinned_revision":"119512573bf96148cbb95e99cf7cdd21c06153e4",
        "source_test_gold_parsed_only_after_all_model_proposals":True,
        "no_external_source_function_name_or_gold_code_given":True,
        "two_general_premade_hypothesis_family_algorithms_human_authored":True,
        "first_prior_cohort_test_outputs_not_reused":True,
        "model_weights_changed":False,
        "online_memory_requires_actual_heldout_verification":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"rows":records,
        "full_source_id_cohort":cohort,
    }
    (out/"FIRST.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"VERIFIED_GROWN_LANGUAGE.json").write_text(
        json.dumps(language.export(),indent=2,sort_keys=True)+"\n")
    print("Q3_NEW_CODEARC_EXTERNAL_FIRST",json.dumps(summary,sort_keys=True),
          flush=True)
    return report

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--dataset",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    a.add_argument("--shard",default=0,type=int)
    a.add_argument("--shards",default=2,type=int)
    x=a.parse_args()
    evaluate(x.dataset,x.out,x.shard,x.shards)
