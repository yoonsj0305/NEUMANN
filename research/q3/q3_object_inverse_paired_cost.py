"""Matched original SOURCE-only execution-cost comparison of object synthesis.

Compare OLD forward object enumerator and NEW inverse-witness enumerator
with the exact same 128 disjoint original training source tasks and
source-heldout checks, same runner, same base grammar and max 350ms cap.
This is a RETAINED cohort benchmark, NOT a fresh evaluation, NOT a
frontier/strong classical 10x claim, and it never uses original TEST gold.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import statistics
import sys
from time import perf_counter_ns

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from q3_arc2_object_blind_first import freeze_options
from q3_arc2_training_original_test_freeze import checked_upstream
from neumann1.scene_graph_inventor import ObjectGrammarInventor as Inverse
from neumann1._q3_forward_raw import ObjectGrammarInventor as ForwardRaw
from neumann1._q3_forward_pruned import ObjectGrammarInventor as ForwardPruned
from neumann1 import arc2_meta_grid_reasoner as old


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",type=pathlib.Path,required=True)
    p.add_argument("--n",type=int,default=128)
    p.add_argument("--cohort",choices=("first","second","third"),default="third")
    p.add_argument("--max-source-ms",type=int,default=350)
    p.add_argument("--output",type=pathlib.Path,
                   default=pathlib.Path("q3_object_paired_cost.json"))
    a=p.parse_args()
    exclude,salt=freeze_options(a.cohort)
    root=checked_upstream(a.upstream)
    selected=sorted(
        [x for x in root.glob("*.json") if x.stem not in exclude],
        key=lambda x:hashlib.sha256((salt+x.name).encode()).hexdigest())[:a.n]
    if len(selected)!=a.n:raise ValueError("independent source cohort missing")
    ledger=[]
    for path in selected:
        source=json.loads(path.read_text())["train"]
        if len(source)<3:
            ledger.append({"source_id":path.stem,"status":"SKIPPED"})
            continue
        pairs=[(old.G(r["input"]),old.G(r["output"])) for r in source]
        kwargs={"verification":[pairs[-1]],"max_programs":2}
        timing=[]
        for model in (ForwardRaw, ForwardPruned, Inverse):
            t0=perf_counter_ns()
            result=model(max_source_ms=a.max_source_ms).invent(
                pairs[:-1],**kwargs)
            timing.append((result,(perf_counter_ns()-t0)/1e6))
        raw,raw_elapsed=timing[0]
        pruned,pruned_elapsed=timing[1]
        inverse,inverse_elapsed=timing[2]
        ledger.append({
            "source_id":path.stem,"status":"CHECKED",
            "raw_forward_source_fit":raw.source_fit,
            "shape_pruned_source_fit":pruned.source_fit,
            "inverse_source_fit":inverse.source_fit,
            "raw_forward_ms":round(raw_elapsed,5),
            "shape_pruned_ms":round(pruned_elapsed,5),
            "inverse_ms":round(inverse_elapsed,5),
            "raw_source_checks":raw.source_checks,
            "pruned_source_checks":pruned.source_checks,
            "inverse_witness_checks":inverse.source_checks,
        })
    valid=[r for r in ledger if r["status"]=="CHECKED"]
    old_raw=sum(r["raw_forward_ms"] for r in valid)
    old_pruned=sum(r["shape_pruned_ms"] for r in valid)
    new=sum(r["inverse_ms"] for r in valid)
    summary={
        "cohort":a.cohort,
        "retained_source_cases":len(selected),
        "source_checked":len(valid),"skipped":len(ledger)-len(valid),
        "raw_forward_source_fits":sum(r["raw_forward_source_fit"] for r in valid),
        "shape_pruned_source_fits":sum(r["shape_pruned_source_fit"] for r in valid),
        "inverse_source_fits":sum(r["inverse_source_fit"] for r in valid),
        "raw_forward_total_seconds":round(old_raw/1000,5),
        "shape_pruned_total_seconds":round(old_pruned/1000,5),
        "inverse_total_seconds":round(new/1000,5),
        "raw_to_inverse_paired_speedup":round(old_raw/new,2) if new else None,
        "shape_pruned_to_inverse_paired_speedup":round(old_pruned/new,2) if new else None,
        "raw_forward_median_ms":round(statistics.median(
            r["raw_forward_ms"] for r in valid),5),
        "pruned_median_ms":round(statistics.median(
            r["shape_pruned_ms"] for r in valid),5),
        "inverse_median_ms":round(statistics.median(
            r["inverse_ms"] for r in valid),5),
        "external_target_gold_used":False,
        "retained_after_prior_evaluation":True,
        "global_q4_pass":False,
    }
    result={
        "schema":"NEUMANN.Q4.object-inverse-retained-paired-cost.v1",
        "raw_forward_commit":"c0569e915de56128f87d40df05c6c6b68552c747",
        "shape_pruned_commit":"de59b6bcec4a37f0acbfdc0c2fd55f54f811b676",
        "invalid_comparison_note":"Earlier c193e291 was ALREADY inverse, so its 1x comparison is withdrawn.",
        "new_module_current_head":True,
        "summary":summary,"records":ledger,
        "limits":["Both are custom grammar enumeration, NOT strong specialist baseline.",
                  "This cost is source-only and omits all data acquisition and full runtime.",
                  "Original task test gold was never used; source splits seen in prior experiment.",
                  "No frontier solving or unrelated mathematics claim."],
    }
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":main()
