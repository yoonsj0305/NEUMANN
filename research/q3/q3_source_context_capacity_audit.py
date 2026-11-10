"""Measure whether Q3 open-code model silently loses SOURCE evidence at 1536 tokens.

This is a *capacity diagnostic* on a previously exposed original AUTHOR SOURCE
cohort, not an invention success. Never reads original TARGET gold.
"""
from __future__ import annotations
import argparse,hashlib,json,statistics
from pathlib import Path

from neumann1.q3_prompt_contract import source_discovery_prompt,model_prefix


def audit(source_file,out,model_revision):
    from transformers import AutoTokenizer
    source=json.loads(Path(source_file).read_text())
    assert source["original_source_count"]==100
    assert source["no_target_gold_in_payload"] is True
    tokenizer=AutoTokenizer.from_pretrained(
        "Qwen/Qwen2.5-Coder-0.5B-Instruct",
        revision=model_revision,trust_remote_code=False)
    records=[]
    for r in source["records"]:
        pair=r["source_pairs"]
        if len(pair)<3:
            continue
        train=pair[:-1]
        # The deployed prompt is now compact; reconstruct the OLD spaced
        # representation explicitly to preserve before/after comparability.
        compact=source_discovery_prompt(train)
        original=compact
        for x,y in train:
            for prefix,obj in (("Source input: ",x),
                               ("Expected source output: ",y)):
                spaced=prefix+json.dumps(obj,ensure_ascii=True)
                tight=prefix+json.dumps(
                    obj,ensure_ascii=True,separators=(",",":"))
                original=original.replace(tight,spaced)
        a=len(tokenizer(
            model_prefix(tokenizer,original),
            add_special_tokens=False,truncation=False)["input_ids"])
        b=len(tokenizer(
            model_prefix(tokenizer,compact),
            add_special_tokens=False,truncation=False)["input_ids"])
        records.append({
            "id":r["source_id"],"source_pairs":len(pair),
            "tokens_original":a,"tokens_compact":b,
            "original_over_1536":a>1536,"compact_over_1536":b>1536})
    if len(records)!=78:
        raise ValueError("original SOURCE eligible count differs from frozen 78")
    def stats(k):
        x=sorted(v[k] for v in records)
        return {"min":x[0],"median":statistics.median(x),
                "p90":x[int(0.9*(len(x)-1))],"max":x[-1]}
    summary={
        "source_cohort":100,"independent_source_eligible":len(records),
        "original_prompt_tokens":stats("tokens_original"),
        "compact_prompt_tokens":stats("tokens_compact"),
        "silent_truncation_exposure_original":sum(
            r["original_over_1536"] for r in records),
        "silent_truncation_exposure_compact":sum(
            r["compact_over_1536"] for r in records),
        "over_budget_rescued_by_lossless_json_compaction":sum(
            r["original_over_1536"] and not r["compact_over_1536"]
            for r in records),
        "lossless_source_json_compaction_only":True,
        "original_TARGET_gold_accessed":False,"q3_global":"OPEN",
        "model_revision":model_revision,
        "registry_sha256":hashlib.sha256(Path(source_file).read_bytes()).hexdigest(),
    }
    Path(out).write_text(json.dumps(
        {"summary":summary,"rows":records},sort_keys=True,
        separators=(",",":"))+"\n")
    print("Q3_100_SOURCE_CONTEXT_CAPACITY_AUDIT",summary,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--model-revision",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    audit(a.source,a.out,a.model_revision)
