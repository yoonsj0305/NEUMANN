"""Q3 exact frozen ORIGINAL-source failure census, POST-FIRST only.

Reads immutable #718 post-first artifact and classifies missing correctness
without changing ANY submitted programs, source examples, domain grammars,
or cold baselines. Scientific conclusion must distinguish:
- unavailable/unsupported source cases,
- no source-valid representation found,
- source-consistent but wrong out-of-support original holdouts,
- source-correct with old typed/fold operators,
- actual learned-relational-memory use (or absence).
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

SCHEMA="neumann.q3.postfirst-full-29-original-structural-error-census.v1"
EXTERNAL_RUN=42365349653


def diagnose(first:Path,out:Path):
    if out.exists():raise ValueError("DO_NOT_OVERWRITE_FAILURE_CENSUS")
    out.mkdir(parents=True)
    raw=json.loads(first.read_text())
    report=raw["rows"]
    summary=raw["summary"]
    if len(report)!=29 or summary["eligible_full_32_holdout_families"]!=23:
        raise ValueError("SOURCE_NOT_FROZEN_FULL_29_POSTFIRST")
    buckets=defaultdict(list);generator_counts=defaultdict(Counter)
    rows=[]
    for item in report:
        name=item["source_task"]
        if item["status"]!="EVALUATED":
            kind="UNSUPPORTED_IO_OR_MISSING"
            if not item.get("reason"):
                raise ValueError("UNEXPLAINED_UNSUPPORTED_ORIGINAL")
            record={"task":name,"outcome":kind,"reason":item["reason"]}
        else:
            warm=item["warm"];cold=item["cold"]
            candidate=warm.get("program")
            exact=item["warm_heldout"]["exact"]
            if exact:
                kind="HELDOUT_ALL_32_EXACT"
            elif candidate is None:
                kind="NO_SOURCE_CONSISTENT_PROGRAM"
            else:
                kind="TRAIN_FIT_BUT_HELDOUT_COUNTEREXAMPLE"
            records={
                "task":name,"outcome":kind,
                "typed_signature":item.get("typed_signature"),
                "source_train_count":item.get("source_train_total"),
                "heldout_count":item.get("source_heldout_total"),
                "original_test_correct":item["warm_heldout"]["original_heldout_correct"],
                "candidate_origin":candidate["origin"] if candidate else None,
                "candidate_AST":candidate["executable_AST"] if candidate else None,
                "candidate_count":warm.get("candidate_count",0),
                "source_memory_selected":item["source_memory_used"],
                "source_memory_additional_correct":item["memory_accuracy_lift_exact"],
                "source_generator_receipts":warm["trials"],
                "same_core_cold_exact":item["cold_heldout"]["exact"],
                "source_plus_memory_ms":warm.get("elapsed_ms"),
                "source_only_cold_ms":cold.get("elapsed_ms"),
            }
            record=records
            for t in warm["trials"]:
                generator_counts[t["source"]][t.get("status","source_proof")]+=1
        buckets[kind].append(name)
        rows.append(record)
    counts={k:len(v) for k,v in buckets.items()}
    assert sum(counts.values())==29,counts
    assert counts.get("HELDOUT_ALL_32_EXACT",0)==3
    assert (counts.get("NO_SOURCE_CONSISTENT_PROGRAM",0)+
            counts.get("TRAIN_FIT_BUT_HELDOUT_COUNTEREXAMPLE",0))==20
    by_origin=Counter(
       (r.get("candidate_origin") or "NO_PROGRAM") for r in rows
       if r["outcome"]=="HELDOUT_ALL_32_EXACT")
    total_trial=Counter(t["source"] for r in rows
                        if r["outcome"]!="UNSUPPORTED_IO_OR_MISSING"
                        for t in r.get("source_generator_receipts",[]))
    result={
        "schema":SCHEMA,
        "original_first_external_action":42365072610,
        "source_full_29_postfirst_action":EXTERNAL_RUN,
        "no_source_program_modified":True,
        "new_original_heldout_NOT_CREATED":True,
        "not_independent_blind_repeat":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "counts":counts,
        "task_lists":dict(buckets),
        "correct_candidate_constructors":dict(by_origin),
        "generator_attempted_families":dict(total_trial),
        "generator_statuses":{k:dict(v)
                              for k,v in generator_counts.items()},
        "source_memory_selected_correct":sum(
            r.get("source_memory_selected",False)
            for r in rows if r["outcome"]=="HELDOUT_ALL_32_EXACT"),
        "source_memory_causal_additions":sum(
            r.get("source_memory_additional_correct",False) for r in rows),
        "original_29_first_attributable_pass":"ENGINEERING_INTEGRATION_ONLY",
        "rows":rows,
    }
    (out/"FAILURE_CENSUS.json").write_text(json.dumps(
        result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("Q3_GP_29_TASKS_CAUSAL_FAILURE_CENSUS",json.dumps({
        "classes":counts,
        "correct_origins":dict(by_origin),
        "memory_correct":result["source_memory_selected_correct"],
        "memory_added":result["source_memory_causal_additions"],
        "generator_statuses":result["generator_statuses"]},
        sort_keys=True),flush=True)
    for key,names in buckets.items():
        print("Q3_FAILURE_CLASS",key,names,flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    diagnose(a.input,a.out)
