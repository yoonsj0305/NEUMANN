"""Q3 cross-cohort cost-aware METHOD DELETION gate.

Use three immutable prior independent-original results to decide whether
the learned AST ranking or learned constant macro has *incremental correct
solutions* and lower candidate/runtime costs over strong simple classical.
If no proven benefit, delete both search stages (degraded safe classical).
The next, not previously scored comparator bvsgt has 15 untouched tasks;
its bvshl1 file was earlier manually inspected and is therefore EXCLUDED.
"""
from __future__ import annotations
import hashlib,json,pathlib,time
import formal_bv4_zeroarity_second_unopened_first as patched
base=patched.base

HISTORY_A="history/a/Q3_FORMAL_TARGET_FIRST.json"
HISTORY_B="history/b/Q3_FORMAL_SECOND_ORIGINAL_FIRST.json"
HISTORY_C="history/c/Q3_MACRO_GENERALIZATION_NEW_ORIGINAL_FIRST.json"
SOURCE_METHOD="policy/Q3_FORMAL_SOURCE_FROZEN.json"
TARGET=[f"find_inv_bvsgt_{x}_4bit.sl" for x in base.OPS if x!="bvshl1"]
assert len(TARGET)==15
assert len(set(TARGET))==15
CONFIG="Q3_COST_AWARE_DELETION_POLICY_BEFORE_TEST.json"

def load_reports():
    a=json.loads(pathlib.Path(HISTORY_A).read_text())
    b=json.loads(pathlib.Path(HISTORY_B).read_text())
    c=json.loads(pathlib.Path(HISTORY_C).read_text())
    if not (a.get("target_registry")==base.TARGET and
            b.get("new_registry")==patched.TARGET and
            c.get("source_proof_run")==42432876840):
        raise ValueError("HISTORICAL_ORIGINAL_PROVENANCE_MISMATCH")
    return a,b,c

def learn_policy():
    a,b,c=load_reports()
    if a["target_errors"]>8 or b["errors"]!=0 or c["errors"]!=0:
        raise ValueError("UNTRUSTED_HISTORICAL_RESULTS")
    history=[
      {"source":"a","memory_solved":a["summary"]["learned"]["proved"],
       "cold_solved":a["summary"]["strong_cold"]["proved"],
       "memory_checks":a["summary"]["learned"]["candidate_checks"],
       "cold_checks":a["summary"]["strong_cold"]["candidate_checks"],
       "memory_ms":a["summary"]["learned"]["search_ms"],
       "cold_ms":a["summary"]["strong_cold"]["search_ms"]},
      {"source":"b","memory_solved":b["summary"]["memory_policy"]["proved"],
       "cold_solved":b["summary"]["strong_cold_same_grammar"]["proved"],
       "memory_checks":b["summary"]["memory_policy"]["checks"],
       "cold_checks":b["summary"]["strong_cold_same_grammar"]["checks"],
       "memory_ms":b["summary"]["memory_policy"]["search_ms"],
       "cold_ms":b["summary"]["strong_cold_same_grammar"]["search_ms"]},
      {"source":"c","memory_solved":c["summary"]["macro_first"]["full_256_proved"],
       "cold_solved":c["summary"]["fixed_grammar_cold"]["full_256_proved"],
       "memory_checks":c["summary"]["macro_first"]["checks"],
       "cold_checks":c["summary"]["fixed_grammar_cold"]["checks"],
       "memory_ms":c["summary"]["macro_first"]["search_ms"],
       "cold_ms":c["summary"]["fixed_grammar_cold"]["search_ms"]}]
    # Aggressively delete any stage whose learned utility has not
    # materially cleared the cost threshold on independent cohorts.
    total_memory=sum(x["memory_solved"] for x in history)
    total_cold=sum(x["cold_solved"] for x in history)
    total_learned_ms=sum(x["memory_ms"] for x in history)
    total_cold_ms=sum(x["cold_ms"] for x in history)
    selected=("learned" if total_memory>total_cold and
              total_learned_ms<total_cold_ms else "cold")
    proof={"schema":"neumann.q3.method-deletion-before-new-formal-group.v1",
       "history_runs":[42432369260,42432544881,42433082556],
       "historical_costs":history,"selection":selected,
       "trained_total_solved":{"learned":total_memory,"cold":total_cold},
       "trained_total_discovery_ms":{"learned":round(total_learned_ms,5),
                                     "cold":round(total_cold_ms,5)},
       "contract":"Only frozen past original scores; no new bvsgt content at selection. Reject any unverified exploratory policy and keep classical fallback."}
    proof["sha256"]=base.sha(proof)
    pathlib.Path(CONFIG).write_text(json.dumps(proof,indent=2))
    print("PRETARGET_SELECTED_POLICY",selected,"FROZEN_HASH",proof["sha256"])
    return proof

def target():
    policy=json.loads(pathlib.Path(CONFIG).read_text())
    fingerprint=policy.pop("sha256")
    if base.sha(policy)!=fingerprint:raise ValueError("POLICY_MODIFIED_AFTER_FREEZE")
    src=json.loads(pathlib.Path(SOURCE_METHOD).read_text())
    origfp=src.pop("sha256")
    if base.sha(src)!=origfp:raise ValueError("SOURCE_METHOD_TAMPERING")
    asts,sigs=base.library()
    order_cold=[asts[i] for i in src["cold_ordering"]]
    order_learned=[asts[i] for i in src["learned_ordering"]]
    rows=[]
    for task in TARGET:
        row={"id":task}
        try:
            raw=base.fetch(task)
            formula=base.allowed_table(base.parse_benchmark(raw))
            row["source_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            for key,order in (("cold",order_cold),("learning_policy",order_learned)):
                st=time.perf_counter_ns()
                program,checks=base.solve(formula,order,sigs)
                row[key]={"full_256_proved":program is not None,
                  "checks":checks,"search_ms":round((time.perf_counter_ns()-st)/1e6,5),
                  "program":program}
            chosen=policy["selection"]
            row["selected_actual"]=row["cold"] if chosen=="cold" else row["learning_policy"]
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)[:180]
        rows.append(row)
    summary={key:{"full_256_proved":sum(int(r.get(key,{}).get("full_256_proved",False)) for r in rows),
                  "candidate_checks":sum(r.get(key,{}).get("checks",0) for r in rows),
                  "search_ms":round(sum(r.get(key,{}).get("search_ms",0) for r in rows),5)}
             for key in ("cold","learning_policy","selected_actual")}
    result={"schema":"neumann.q3.degraded-method-router-fresh-formal-15-original-first.v1",
      "pretarget_routing_method_sha256":fingerprint,
      "new_bvsgt_target_registry":TARGET,"excluded_known_task":"find_inv_bvsgt_bvshl1_4bit.sl",
      "formal_input_count_per_task":256,"selection":policy["selection"],
      "summary":summary,"error_count":sum("error" in r for r in rows),
      "records":rows,"scientific_scope":"Validated cost-aware method deletion; no generic meta-invention claim."}
    pathlib.Path("Q3_METHOD_DELETION_EXTERNAL_FIRST.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"task_count":len(TARGET),"policy":policy["selection"],
      "errors":result["error_count"],"summary":summary},indent=2))
    return result

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:learn_policy()
    elif sys.argv[1:]==["target"]:target()
    else:raise SystemExit("use source or target")
