"""Q3 causal model-capacity gate: SAME one invention loop, 0.5B vs 1.5B.

Disjoint original ARC-AGI-2 AUTHOR SOURCE-only evaluation. No domain-specific
generator, no hidden TARGET gold, no human edits based on target. Frozen six
IDs were prechosen by SHA-salted 20261110 policy ablation before this test.

Hypothesis: the ability to infer executable causal programs is limited by
the 0.5B pretrained generator, not simply by SOURCE-feedback wiring.
"""
from __future__ import annotations

import argparse,gc,hashlib,json,time
from pathlib import Path

from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
from neumann1.open_program_inventor import GenerativeProgramInventor,IsolatedPython

IDS=(
    "67e8384a","a87f7484","c909285e",
    "575b1a71","c8f0f002","c8b7cc0f",
)


def _canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def compare(source_file,small_revision,large_revision,out):
    data=json.loads(Path(source_file).read_text())
    if (data.get("original_source_count")!=100 or
            data.get("no_target_gold_in_payload") is not True):
        raise ValueError("frozen original SOURCE-only registry required")
    tasks={r["source_id"]:r for r in data["records"]}
    if not set(IDS)<=set(tasks):
        raise ValueError("pre-registered IDs not in SOURCE-only cohort")
    for ident in IDS:
        if not 3<=len(tasks[ident]["source_pairs"])<=32:
            raise ValueError("independent SOURCE check not possible")
    runner=IsolatedPython(max_seconds=8)
    rows={x:{"id":x} for x in IDS}
    for arm,model_name,revision in (
        ("A_0p5B","Qwen/Qwen2.5-Coder-0.5B-Instruct",small_revision),
        ("L_1p5B","Qwen/Qwen2.5-Coder-1.5B-Instruct",large_revision),
    ):
        start=time.perf_counter()
        policy=LocalCausalCodePolicy(
            model_name=model_name,model_revision=revision,
            max_new_tokens=320,temperature=0.3,seed=1007,
            max_context_tokens=4096)
        load_wall_s=time.perf_counter()-start
        print("Q3_MODEL_CAPACITY_MODEL_LOADED",arm,load_wall_s,flush=True)
        for ident in IDS:
            r=tasks[ident]
            pairs=r["source_pairs"]
            start=time.perf_counter()
            discovered=GenerativeProgramInventor(
                policy,runner,max_proposals=2
            ).discover(
                pairs[:-1],independent_source_checks=pairs[-1:])
            elapsed=time.perf_counter()-start
            row=rows[ident]
            row[arm]={
                "source_verified":bool(discovered.verified),
                "status":discovered.status,
                "attempts":[{"status":a.status,
                             "source_correct":a.source_correct,
                             "source_total":a.source_total}
                            for a in discovered.attempts],
                "independent_check_count":len(pairs[-1:]),
                "wall_seconds":elapsed,
                "program_sha256":discovered.frozen_sha256,
            }
            print("Q3_MODEL_CAPACITY_ORIGINAL_SOURCE",arm,ident,
                  {"verified":discovered.verified,"status":discovered.status,
                   "wall_s":round(elapsed,3)},flush=True)
        del policy
        gc.collect()
    records=[rows[k] for k in IDS]
    a=sum(r["A_0p5B"]["source_verified"] for r in records)
    b=sum(r["L_1p5B"]["source_verified"] for r in records)
    summary={
        "schema":"NEUMANN.Q3.ONE-CORE-MODEL-CAPACITY-SOURCE.v1",
        "original_cohort_sha256":hashlib.sha256(
            Path(source_file).read_bytes()).hexdigest(),
        "frozen_ids":list(IDS),
        "six_real_author_source":6,
        "base_small_model_revision":small_revision,
        "base_large_model_revision":large_revision,
        "same_tokens_cap":4096,
        "same_sampling_temperature":0.3,
        "same_proposals_per_task":2,
        "small_model_source_verified":a,
        "large_model_source_verified":b,
        "large_exclusive":sum(
            r["L_1p5B"]["source_verified"]
            and not r["A_0p5B"]["source_verified"] for r in records),
        "large_regressions":sum(
            r["A_0p5B"]["source_verified"]
            and not r["L_1p5B"]["source_verified"] for r in records),
        "capacity_hypothesis_dev_gate_pass":b>a and b>=1,
        "original_author_TARGET_gold_read":False,
        "q3_global":"OPEN",
    }
    Path(out).write_text(_canonical({
        "summary":summary,"records":records})+"\n")
    print("Q3_TWO_MODEL_REAL_ORIGINAL_SOURCE_CAPACITY_VERDICT",
          summary,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--small-revision",required=True)
    p.add_argument("--large-revision",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    compare(a.source,a.small_revision,a.large_revision,a.out)
