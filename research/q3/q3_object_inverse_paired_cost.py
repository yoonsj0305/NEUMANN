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
from neumann1._q3_forward_reference import ObjectGrammarInventor as Forward
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
        t0=perf_counter_ns()
        forward=Forward(max_source_ms=a.max_source_ms).invent(
            pairs[:-1],**kwargs)
        elapsed_fwd=(perf_counter_ns()-t0)/1e6
        t0=perf_counter_ns()
        inverse=Inverse(max_source_ms=a.max_source_ms).invent(
            pairs[:-1],**kwargs)
        elapsed_inv=(perf_counter_ns()-t0)/1e6
        ledger.append({
            "source_id":path.stem,"status":"CHECKED",
            "forward_source_fit":forward.source_fit,
            "inverse_source_fit":inverse.source_fit,
            "forward_ms":round(elapsed_fwd,5),
            "inverse_ms":round(elapsed_inv,5),
            "forward_candidates":forward.source_checks,
            "inverse_witness_checks":inverse.source_checks,
        })
    valid=[r for r in ledger if r["status"]=="CHECKED"]
    old_total=sum(r["forward_ms"] for r in valid)
    new_total=sum(r["inverse_ms"] for r in valid)
    summary={
        "cohort":a.cohort,
        "retained_source_cases":len(selected),
        "source_checked":len(valid),"skipped":len(ledger)-len(valid),
        "old_forward_source_fits":sum(r["forward_source_fit"] for r in valid),
        "new_inverse_source_fits":sum(r["inverse_source_fit"] for r in valid),
        "inverse_source_fits_not_old":sum(
            r["inverse_source_fit"] and not r["forward_source_fit"] for r in valid),
        "forward_source_fits_missed":sum(
            r["forward_source_fit"] and not r["inverse_source_fit"] for r in valid),
        "forward_total_seconds":round(old_total/1000,5),
        "inverse_total_seconds":round(new_total/1000,5),
        "paired_source_speedup":round(old_total/new_total,2) if new_total else None,
        "forward_median_ms":round(statistics.median(r["forward_ms"] for r in valid),4),
        "inverse_median_ms":round(statistics.median(r["inverse_ms"] for r in valid),4),
        "external_target_gold_used":False,
        "retained_after_prior_evaluation":True,
        "global_q4_pass":False,
    }
    result={
        "schema":"NEUMANN.Q4.object-inverse-retained-paired-cost.v1",
        "old_module_commit":"c193e291f37936a59c74f12be60479f62ad8a73f",
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
