"""Q3 genuine model-authored latent hypothesis vs direct code original SOURCE.

Pre-registered six original AUTHOR SOURCE task IDs, no TARGET gold.
Direct arm has 2 executable proposals. Latent arm spends one inference to
construct a hypothesis and one on a full executable algorithm. Same 0.5B
checkpoint/seed/source/verifier; two model calls in each arm. Token
budgets differ slightly and are tracked as max 2*(320) vs 220+320.
Neither arm has a human-written target algorithm.
"""
from __future__ import annotations

import argparse,gc,hashlib,json,time
from pathlib import Path

from neumann1.q3_latent_hypothesis_policy import LatentCausalHypothesisPolicy
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
from neumann1.open_program_inventor import GenerativeProgramInventor,IsolatedPython

IDS=("67e8384a","a87f7484","c909285e",
     "575b1a71","c8f0f002","c8b7cc0f")


def run(source_file,out,revision):
    payload=Path(source_file).read_bytes()
    cohort=json.loads(payload)
    if cohort.get("original_source_count")!=100 or (
            cohort.get("no_target_gold_in_payload") is not True):
        raise ValueError("hash-frozen original author SOURCE only")
    lookup={x["source_id"]:x for x in cohort["records"]}
    if not set(IDS)<=set(lookup):
        raise ValueError("pre-registered original task IDs absent")
    runner=IsolatedPython(max_seconds=8)
    rows={i:{"id":i} for i in IDS}
    for label,mode,budget in (
        ("direct_raw","raw",2),
        ("latent_causal_edits","lossless-causal-edits",1),
    ):
        base=LocalCausalCodePolicy(
            model_revision=revision,max_new_tokens=320,
            temperature=0.3,seed=1007,max_context_tokens=4096)
        policy=(LatentCausalHypothesisPolicy(base)
                if label=="latent_causal_edits" else base)
        for task_id in IDS:
            pairs=lookup[task_id]["source_pairs"]
            if not 3<=len(pairs)<=32:
                raise ValueError("independent SOURCE split unavailable")
            t0=time.perf_counter()
            d=GenerativeProgramInventor(
                policy,runner,max_proposals=budget
            ).discover(pairs[:-1],
                       independent_source_checks=pairs[-1:],
                       source_observer=mode)
            rows[task_id][label]={
                "source_verified":bool(d.verified),
                "status":d.status,
                "model_calls_budget":2,
                "program_attempts":len(d.attempts),
                "source_train_best":max(
                    (x.source_correct for x in d.attempts),default=0),
                "source_train_count":len(pairs)-1,
                "program_sha256":d.frozen_sha256,
                "wall_seconds":round(time.perf_counter()-t0,3),
                "attempt_statuses":[a.status for a in d.attempts],
            }
            print("Q3_LATENT_CAUSAL_AUTHOR_SOURCE",label,task_id,
                  rows[task_id][label],flush=True)
        del policy,base
        gc.collect()
    outcomes=[rows[k] for k in IDS]
    summary={
        "schema":"NEUMANN.Q3.MODEL-LATENT-CAUSAL-POLICY-SOURCE.v1",
        "original_source_sha256":hashlib.sha256(payload).hexdigest(),
        "original_SOURCE_ids":list(IDS),
        "fixed_Qwen_revision":revision,
        "same_pretrained_weights":True,
        "same_verifier":True,
        "model_calls_per_task":2,
        "max_hypothesis_tokens":220,
        "max_program_tokens":320,
        "same_max_source_input_tokens":4096,
        "direct_source_certified":sum(
            r["direct_raw"]["source_verified"] for r in outcomes),
        "latent_source_certified":sum(
            r["latent_causal_edits"]["source_verified"] for r in outcomes),
        "latent_exclusive":sum(
            r["latent_causal_edits"]["source_verified"] and not
            r["direct_raw"]["source_verified"] for r in outcomes),
        "direct_exclusive":sum(
            r["direct_raw"]["source_verified"] and not
            r["latent_causal_edits"]["source_verified"] for r in outcomes),
        "model_authored_latent_hypotheses":True,
        "original_TARGET_gold_read":False,
        "global_Q3":"OPEN",
    }
    Path(out).write_text(json.dumps(
        {"summary":summary,"rows":outcomes},sort_keys=True,
        separators=(",",":"))+"\n")
    print("Q3_SAME_ONE_CORE_LATENT_CAUSAL_ABLATION",summary,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--revision",required=True)
    args=parser.parse_args()
    run(args.source,args.out,args.revision)
