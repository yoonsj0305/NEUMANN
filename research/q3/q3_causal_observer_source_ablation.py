"""Q3 actual original-author SOURCE causal observation ablation.

Two arms use identical local pretrained Qwen weights, token budget,
generation budget and the single open Python invention core.
Only the representation of the same SOURCE information differs:
raw JSON output versus lossless JSON input-to-output structural edits.
No handwritten answer generator, TARGET gold, named operator or family route.
"""
from __future__ import annotations

import argparse,gc,hashlib,json,time
from pathlib import Path

from neumann1.open_program_inventor import GenerativeProgramInventor,IsolatedPython
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy

IDS=(
    "67e8384a","a87f7484","c909285e",
    "575b1a71","c8f0f002","c8b7cc0f",
)


def _canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def compare(source_path,out,revision):
    blob=Path(source_path).read_bytes()
    data=json.loads(blob)
    if (data.get("original_source_count")!=100 or
        data.get("no_target_gold_in_payload") is not True or
        data.get("source_scope")!=
            "PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY"):
        raise ValueError("original frozen SOURCE-only registry required")
    indexed={r["source_id"]:r for r in data["records"]}
    if not set(IDS)<=set(indexed):
        raise ValueError("pre-registered task identity missing")
    rows={ident:{"id":ident} for ident in IDS}
    runner=IsolatedPython(max_seconds=8)
    for arm,mode in (
        ("raw_source","raw"),
        ("lossless_causal_edits","lossless-causal-edits"),
    ):
        model=LocalCausalCodePolicy(
            model_revision=revision,max_new_tokens=320,
            temperature=0.3,seed=1007,max_context_tokens=4096)
        for ident in IDS:
            item=indexed[ident]
            pairs=item["source_pairs"]
            if not 3<=len(pairs)<=32:
                raise ValueError("independent SOURCE split unavailable")
            train=pairs[:-1];checks=pairs[-1:]
            t0=time.perf_counter()
            discovery=GenerativeProgramInventor(
                model,runner,max_proposals=2
            ).discover(train,independent_source_checks=checks,
                       source_observer=mode)
            row=rows[ident]
            row[arm]={
                "source_verified":bool(discovery.verified),
                "status":discovery.status,
                "attempts":[{
                    "status":a.status,
                    "source_correct":a.source_correct,
                    "source_total":a.source_total,
                    "program_chars":len(a.program or ""),
                    "program_sha256":a.sha256,
                } for a in discovery.attempts],
                "wall_seconds":round(time.perf_counter()-t0,3),
            }
            print("Q3_LOSSLESS_CAUSAL_OBSERVER_ORIGINAL_SOURCE",
                  arm,ident,{
                      "verified":discovery.verified,
                      "status":discovery.status,
                      "best_source_correct":max(
                          (a.source_correct for a in discovery.attempts),
                          default=0),
                  },flush=True)
        del model
        gc.collect()
    results=[rows[k] for k in IDS]
    summary={
        "schema":"NEUMANN.Q3.LOSSLESS-CAUSAL-OBSERVER-SOURCE.v1",
        "frozen_source_sha256":hashlib.sha256(blob).hexdigest(),
        "frozen_original_task_ids":list(IDS),
        "model_revision":revision,
        "same_model_same_verifier":True,
        "same_context_cap":4096,
        "same_max_new_tokens":320,
        "same_max_program_attempts":2,
        "raw_source_verified":sum(r["raw_source"]["source_verified"]
                                  for r in results),
        "causal_edits_source_verified":sum(
            r["lossless_causal_edits"]["source_verified"] for r in results),
        "causal_edits_exclusive":sum(
            r["lossless_causal_edits"]["source_verified"] and
            not r["raw_source"]["source_verified"] for r in results),
        "raw_source_exclusive":sum(
            r["raw_source"]["source_verified"] and
            not r["lossless_causal_edits"]["source_verified"]
            for r in results),
        "original_TARGET_gold_read":False,
        "q3_global":"OPEN",
    }
    Path(out).write_text(_canon({"summary":summary,"records":results})+"\n")
    print("Q3_REAL_ONE_CORE_LOSSLESS_CAUSAL_OBSERVER_VERDICT",
          summary,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--revision",required=True)
    a=p.parse_args()
    compare(a.source,a.out,a.revision)
