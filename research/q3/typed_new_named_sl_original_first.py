"""Q3 NEW FRESH original FIRST after type-interface repair.
Fresh metadata-selected first 36 named SyGuS PBE-SLIA euphony problems,
disjoint from 24 FIRST numeric tasks; no target content inspected prior to
frozen source code. Original constraint test 1-2 cases, weak semantics gate.
Source grammar exact file from immutable earlier FIRST action artifact.
"""
from __future__ import annotations
import json,hashlib,time,pathlib
import cross_domain_string_original_first as old_runner
import typed_cross_domain_meta_engine as core
import typed_domain_interface_postfirst as typed

SOURCE_META_FILE="prior/Q3_SOURCE_ONLY_TYPED_META_GRAMMAR_FROZEN.json"
PRIOR_GIT_RUN=42373106360
TARGET=[
 "cell-contains-all-of-many-things.sl",
 "cell-contains-number.sl",
 "cell-contains-one-of-many-things.sl",
 "cell-contains-one-of-many-with-exclusions.sl",
 "cell-contains-some-words-but-not-others.sl",
 "cell-contains-specific-text.sl",
 "cell-equals-one-of-many-things.sl",
 "change-negative-numbers-to-positive.sl",
 "clean-and-reformat-telephone-numbers.sl",
 "compare-two-strings.sl",
 "convert-numbers-to-text.sl",
 "convert-text-to-numbers.sl",
 "count-consecutive-monthly-orders.sl",
 "count-line-breaks-in-cell.sl",
 "count-specific-characters-in-a-cell.sl",
 "count-specific-words-in-a-cell.sl",
 "count-total-characters-in-a-cell.sl",
 "count-total-words-in-a-cell.sl",
 "create-email-address-from-name.sl",
 "create-email-address-with-name-and-domain.sl",
 "exceljet1.sl","exceljet2.sl","exceljet3.sl","exceljet4.sl",
 "extract-nth-word-from-text-string.sl",
 "extract-text-between-parentheses.sl",
 "extract-word-containing-specific-text.sl",
 "extract-word-that-begins-with-specific-character.sl",
 "find-nth-occurrence-of-character.sl",
 "get-domain-from-email-address_2.sl",
 "get-domain-name-from-url.sl",
 "get-first-name-from-name-with-comma.sl",
 "get-first-name-from-name.sl",
 "get-first-word.sl",
 "get-last-line-in-cell.sl",
 "get-last-name-from-name-with-comma.sl"]
assert len(TARGET)==36 and len(set(TARGET))==36
assert set(TARGET).isdisjoint(old_runner.TARGET)

def dataset_split(pairs):
    # With only 3-4 original examples one heldout is weak but do not
    # increase false confidence. 2 train + 1 original holdout minimum.
    ordered=sorted(pairs,key=lambda a:hashlib.sha256(core.canonical(a[0]).encode()).hexdigest())
    if len(ordered)<3:raise ValueError("TOO_FEW_ORIGINAL_EXAMPLES")
    n_hold=2 if len(ordered)>=8 else 1
    return ordered[:-n_hold],ordered[-n_hold:]

def frozen_policy():
    obj=json.loads(pathlib.Path(SOURCE_META_FILE).read_text())
    chk=obj["content_sha256"]
    compare={k:v for k,v in obj.items() if k!="content_sha256"}
    if core.sha(compare)!=chk:raise ValueError("BAD_IMMUTABLE_SOURCE_HASH")
    if obj.get("source_ids")!=old_runner.SOURCE:raise ValueError("WRONG_SOURCE_COHORT")
    if obj.get("provenance_source_group")!="from_2018":raise ValueError("BAD_SOURCE_PROVENANCE")
    return obj

def experiment():
    policy=frozen_policy()
    print("PRE_TARGET_FROZEN_SOURCE_SHA256",policy["content_sha256"])
    time0=time.perf_counter_ns()
    rows=[]
    for filename in TARGET:
        rec={"id":filename}
        try:
            raw=old_runner.get_source("euphony",filename)
            task=typed.decode_any(raw)
            train,test=dataset_split(task["examples"])
            mem=typed.memory_search_any(policy["learned_productions"],task,train,budget=500)
            cold=typed.search(task,train,allow_branch=False)
            strong=typed.search(task,train,allow_branch=True)
            hybrid=mem if mem["ast"] is not None else strong
            rec.update({"original_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "original_examples":len(task["examples"]),"source_n":len(train),
                "heldout_n":len(test),"nargs":task["nargs"],"return_type":task["output"],
                "grammar_ops":task["ops"],
                "hybrid_path":"memory" if mem["ast"] is not None else "full_fallback",
                "hybrid_actual_checks":mem["checks"]+(0 if mem["ast"] is not None else strong["checks"]),
                "hybrid_actual_ms":mem["wall_ms"]+(0 if mem["ast"] is not None else strong["wall_ms"])})
            rec["arms"]={}
            for name,sol in [("source_memory",mem),("cold_typed",cold),
                             ("strong_cold_full",strong),("hybrid",hybrid)]:
                rec["arms"][name]={
                    "status":sol["status"],"candidate_checks":sol["checks"],
                    "search_ms":round(sol["wall_ms"],6),
                    "submitted_AST":sol["ast"],
                    "train_exact":typed.score_any(sol["ast"],train)["exact"],
                    "original_heldout":typed.score_any(sol["ast"],test)}
        except Exception as e:
            rec["error"]=type(e).__name__+": "+str(e)[:170]
        rows.append(rec)
    methods=("source_memory","cold_typed","strong_cold_full","hybrid")
    report={"schema":"neumann.q3.typed-multi-output-new-original-first.v1",
      "external_repo":"SyGuS-Org/benchmarks","upstream_sha":old_runner.UPSTREAM,
      "prior_source_run":PRIOR_GIT_RUN,"frozen_source_metagrammar_hash":policy["content_sha256"],
      "source_verified_programs":len(policy["verified_program_ids"]),
      "new_metagrammar_productions":len(policy["learned_productions"]),
      "target_cohort":TARGET,"all_originals":len(rows),
      "eligible":sum(int("arms" in row) for row in rows),
      "errors":sum(int("error" in row) for row in rows),
      "summary":{method:{
           "exact_tasks":sum(int(row.get("arms",{}).get(method,{}).get("original_heldout",{}).get("exact",False)) for row in rows),
           "submitted_tasks":sum(int(row.get("arms",{}).get(method,{}).get("original_heldout",{}).get("submitted",False)) for row in rows),
           "checks":sum(row.get("arms",{}).get(method,{}).get("candidate_checks",0) for row in rows),
           "search_ms":round(sum(row.get("arms",{}).get(method,{}).get("search_ms",0) for row in rows),4)}
        for method in methods},
      "hybrid_actual_checks":sum(row.get("hybrid_actual_checks",0) for row in rows),
      "hybrid_actual_ms":round(sum(row.get("hybrid_actual_ms",0) for row in rows),4),
      "per_task":rows,
      "wall_ms":round((time.perf_counter_ns()-time0)/1e6,3),
      "limits":"Only 1-2 original heldout examples, no proof of semantics; core enumerator/VM/schema are human-authored; same competition family (not proven independent authors); benchmark target data not read before freeze."}
    pathlib.Path("Q3_TYPED_INDEPENDENT_NEW_NAMED_FIRST.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"all":len(rows),"eligible":report["eligible"],"errors":report["errors"],
        "source_meta_hash":policy["content_sha256"],
        "results":report["summary"],"hybrid_actual_checks":report["hybrid_actual_checks"],
        "hybrid_actual_ms":report["hybrid_actual_ms"]},indent=2))
    return report

if __name__=="__main__":experiment()
