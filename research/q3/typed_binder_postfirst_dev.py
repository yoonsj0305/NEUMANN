"""POST-FIRST DEV ONLY on already-opened 36 originals, not a fresh gate.
Tests a generic type-error repair of source-induced template hole binding.
Do not overwrite the prior frozen independent FIRST.
"""
import hashlib,json,pathlib,time
import typed_cross_domain_meta_engine as core
import typed_domain_interface_postfirst as typed
import typed_meta_hole_binder_v2 as binder
import typed_new_named_sl_original_first as old

def run():
    policy=old.frozen_policy()
    rows=[]
    for task_name in old.TARGET:
        row={"id":task_name}
        try:
            raw=old.old_runner.get_source("euphony",task_name)
            task=typed.decode_any(raw)
            train,test=old.dataset_split(task["examples"])
            model=binder.memory_search(policy["learned_productions"],task,train,budget=500)
            cold=typed.search(task,train,allow_branch=True)
            row.update({"output":task["output"],"source_n":len(train),"heldout_n":len(test),
                "learned":{"status":model["status"],"checks":model["checks"],
                           "ast":model["ast"],"ms":round(model["wall_ms"],4),
                           "original_heldout":typed.score_any(model["ast"],test)},
                "cold":{"status":cold["status"],"checks":cold["checks"],
                        "ast":cold["ast"],"ms":round(cold["wall_ms"],4),
                        "original_heldout":typed.score_any(cold["ast"],test)}})
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)[:140]
        rows.append(row)
    report={"schema":"neumann.q3.postfirst-typed-hole-binder-repair.v1",
       "science_status":"POSTFIRST_DEV_ONLY",
       "old_independent_first_run":42373522864,
       "source_method_hash":policy["content_sha256"],
       "rows":rows,
       "summary":{arm:{"exact_tasks":sum(int(r.get(arm,{}).get("original_heldout",{}).get("exact",False)) for r in rows),
                        "submitted":sum(int(r.get(arm,{}).get("original_heldout",{}).get("submitted",False)) for r in rows),
                        "checks":sum(r.get(arm,{}).get("checks",0) for r in rows)}
                  for arm in ("learned","cold")}}
    pathlib.Path("Q3_TYPED_BINDER_POSTFIRST_DEV.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report["summary"],indent=2))

if __name__=="__main__":run()
