"""Q3 POSTFIRST matched-expressivity audit on frozen original 37-task FIRST.
Scores a classical enumerator granted the same int-expression AST grammar as
the source memory. No rerun counts as another original FIRST. Preserve archive.
"""
from __future__ import annotations
import json,hashlib,pathlib
import typed_new_named_sl_original_first as source
import typed_meta_hole_binder_v2 as binder
import typed_domain_interface_postfirst as typed
import fair_cold_same_typed_subexpression_grammar as full

SOURCE_FIRST="previous/Q3_TYPED_METAGRAMMAR_FRESH_37_ORIGINAL_FIRST.json"

def audit():
    original=json.loads(pathlib.Path(SOURCE_FIRST).read_text())
    if original.get("original_count")!=37 or original.get("target_cohort") is not None:
        raise ValueError("WRONG_FIRST_REPORT_FORMAT")
    if original.get("new_target_registry") is None or len(original["new_target_registry"])!=37:
        raise ValueError("WRONG_FROZEN_TARGET_REGISTRY")
    original_rows={r["id"]:r for r in original["per_task"]}
    rows=[]
    for name in original["new_target_registry"]:
        source_row=original_rows[name]
        r={"id":name}
        if "error" in source_row:
            r["error"]=source_row["error"]
            rows.append(r);continue
        try:
            raw=source.old_runner.get_source("euphony",name)
            if hashlib.sha256(raw.encode()).hexdigest()!=source_row["original_sha256"]:
                raise ValueError("ORIGINAL_SOURCE_CHANGED")
            task=typed.decode_any(raw)
            train,test=source.dataset_split(task["examples"])
            if len(test)!=source_row["heldout_n"]:
                raise ValueError("CHANGED_SPLIT")
            choice=full.solve(task,train,budget=25000)
            r["original_hash_verified"]=True
            r["source_n"]=len(train);r["heldout_n"]=len(test)
            r["return_type"]=task["output"]
            r["memory_first_status"]=source_row["arms"]["learned_typed_meta"]["status"]
            r["memory_first_exact"]=source_row["arms"]["learned_typed_meta"]["heldout"]["exact"]
            r["prior_restricted_cold_exact"]=source_row["arms"]["strong_full"]["heldout"]["exact"]
            r["same_expressivity_classical"]={
              "status":choice["status"],"candidate_checks":choice["checks"],
              "wall_ms":round(choice["ms"],5),"program_ast":choice["ast"],
              "original_heldout":typed.score_any(choice["ast"],test)}
        except Exception as e:r["error"]=type(e).__name__+": "+str(e)[:170]
        rows.append(r)
    ans={"schema":"neumann.q3.match-expressivity-baseline-postfirst-audit.v1",
        "science_status":"POSTFIRST_DEV_ONLY",
        "prior_original_first_run":42373905695,
        "cohort":original["new_target_registry"],"rows":rows,
        "errors":sum(int("error" in r) for r in rows),
        "summary":{"prior_memory_exact":sum(int(r.get("memory_first_exact",False)) for r in rows),
           "prior_restricted_cold_exact":sum(int(r.get("prior_restricted_cold_exact",False)) for r in rows),
           "same_expressivity_cold_exact":sum(int(r.get("same_expressivity_classical",{}).get("original_heldout",{}).get("exact",False)) for r in rows),
           "same_expressivity_cold_submitted":sum(int(r.get("same_expressivity_classical",{}).get("original_heldout",{}).get("submitted",False)) for r in rows),
           "same_expressivity_checks":sum(r.get("same_expressivity_classical",{}).get("candidate_checks",0) for r in rows),
           "same_expressivity_ms":round(sum(r.get("same_expressivity_classical",{}).get("wall_ms",0) for r in rows),5)}}
    pathlib.Path("Q3_FAIR_TYPED_CLASSICAL_POSTFIRST.json").write_text(json.dumps(ans,indent=2))
    print(json.dumps(ans["summary"],indent=2))
    return ans

if __name__=="__main__":audit()
