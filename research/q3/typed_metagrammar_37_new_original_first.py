"""Q3 type-directed metavariable binding: new 37 unopened original FIRST.

New source-independent target registry is the complete alphabetical tail of
official SyGuS-Org 2019 PBE-SLIA euphony after the previously opened
'get-last-name-from-name-with-comma.sl'. Only filenames were inspected.
Immutable from_2018 source-grown meta-grammar is downloaded from the prior
FIRST, not relearned from any euphony tasks.
"""
from __future__ import annotations
import json,hashlib,time,pathlib
import typed_new_named_sl_original_first as old
import typed_meta_hole_binder_v2 as learned
import typed_domain_interface_postfirst as typed

TARGET=[
 "get-last-name-from-name.sl","get-last-word.sl",
 "get-middle-name-from-full-name.sl","join-cells-with-comma.sl",
 "join-first-and-last-name.sl","most-frequently-occurring-text.sl",
 "phone-5-short.sl","phone-6-short.sl","phone-7-short.sl","phone-9-short.sl",
 "position-of-2nd-3rd-etc-instance-of-character.sl",
 "remove-characters-from-left.sl","remove-characters-from-right.sl",
 "remove-file-extension-from-filename.sl",
 "remove-leading-and-trailing-spaces-from-text.sl",
 "remove-text-by-matching.sl","remove-text-by-position.sl",
 "remove-unwanted-characters.sl","replace-one-character-with-another.sl",
 "split-numbers-from-units-of-measure_1.sl",
 "split-numbers-from-units-of-measure_2.sl",
 "split-text-and-numbers.sl",
 "split-text-string-at-specific-character.sl",
 "stackoverflow1.sl","stackoverflow10.sl","stackoverflow11.sl",
 "stackoverflow2.sl","stackoverflow3.sl","stackoverflow4.sl",
 "stackoverflow5.sl","stackoverflow6.sl","stackoverflow7.sl",
 "stackoverflow8.sl","stackoverflow9.sl",
 "strip-html-from-text-or-numbers.sl",
 "strip-non-numeric-characters.sl",
 "strip-numeric-characters-from-cell.sl"]
assert len(TARGET)==37 and len(set(TARGET))==37
assert set(TARGET).isdisjoint(old.TARGET)
assert set(TARGET).isdisjoint(old.old_runner.TARGET)

def experiment():
    prior=old.frozen_policy()
    print("FROZEN_BEFORE_TARGET",prior["content_sha256"])
    start=time.perf_counter_ns();rows=[]
    for name in TARGET:
        r={"id":name}
        try:
            source=old.old_runner.get_source("euphony",name)
            task=typed.decode_any(source)
            train,test=old.dataset_split(task["examples"])
            memory=learned.memory_search(prior["learned_productions"],task,train,budget=500)
            cold=typed.search(task,train,allow_branch=False)
            strong=typed.search(task,train,allow_branch=True)
            hybrid=memory if memory["ast"] is not None else strong
            r.update({"original_sha256":hashlib.sha256(source.encode()).hexdigest(),
              "nargs":task["nargs"],"return_type":task["output"],
              "original_examples":len(task["examples"]),
              "source_n":len(train),"heldout_n":len(test),
              "hybrid_origin":"MEMORY" if memory["ast"] is not None else "FALLBACK",
              "hybrid_actual_checks":memory["checks"]+(0 if memory["ast"] is not None else strong["checks"]),
              "hybrid_actual_ms":round(memory["wall_ms"]+(0 if memory["ast"] is not None else strong["wall_ms"]),5)})
            r["arms"]={}
            for key,sol in (("learned_typed_meta",memory),("cold_base",cold),
                            ("strong_full",strong),("sequential_hybrid",hybrid)):
                r["arms"][key]={"status":sol["status"],"checks":sol["checks"],
                    "elapsed_ms":round(sol["wall_ms"],5),
                    "program_ast":sol["ast"],
                    "train_exact":typed.score_any(sol["ast"],train)["exact"],
                    "heldout":typed.score_any(sol["ast"],test)}
        except Exception as e:r["error"]=type(e).__name__+": "+str(e)[:160]
        rows.append(r)
    methods=["learned_typed_meta","cold_base","strong_full","sequential_hybrid"]
    out={"schema":"neumann.q3.typed-holes-novel-source-original-first.v1",
         "source_grammar_provenance_run":42373106360,
         "prior_original_first_runs":[42373106360,42373522864],
         "new_target_registry":TARGET,
         "pinned_source_repo_commit":old.old_runner.UPSTREAM,
         "frozen_source_grammar_sha256":prior["content_sha256"],
         "original_count":len(TARGET),
         "eligible":sum(int("arms" in r) for r in rows),
         "errors":sum(int("error" in r) for r in rows),
         "per_task":rows,
         "summary":{
            k:{"exact_tasks":sum(int(r.get("arms",{}).get(k,{}).get("heldout",{}).get("exact",False)) for r in rows),
               "submitted":sum(int(r.get("arms",{}).get(k,{}).get("heldout",{}).get("submitted",False)) for r in rows),
               "candidate_checks":sum(r.get("arms",{}).get(k,{}).get("checks",0) for r in rows),
               "discovery_ms":round(sum(r.get("arms",{}).get(k,{}).get("elapsed_ms",0) for r in rows),4)}
            for k in methods},
         "actual_hybrid_checks":sum(r.get("hybrid_actual_checks",0) for r in rows),
         "actual_hybrid_ms":round(sum(r.get("hybrid_actual_ms",0) for r in rows),4),
         "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
         "scope":"One to two original heldout examples, no formal functional proof; same SyGuS official competition, separate problem subgroup. Source learned grammar has 2 automatically induced rules; type inference and runtime are human-written."}
    pathlib.Path("Q3_TYPED_METAGRAMMAR_FRESH_37_ORIGINAL_FIRST.json").write_text(json.dumps(out,indent=2))
    print(json.dumps({"target_originals":len(TARGET),"eligible":out["eligible"],"errors":out["errors"],
        "summary":out["summary"],"actual_hybrid_checks":out["actual_hybrid_checks"],
        "actual_hybrid_ms":out["actual_hybrid_ms"]},indent=2))
    return out

if __name__=="__main__":experiment()
