"""Q3 SOURCE-only external ARC-AGI-2 grammar-gap diagnostic.

Uses the official independently authored TRAINING folder only, at a pinned
upstream revision. Training pairs in each task are split into source-fit
(train[:-1]) and independent SOURCE-verification (train[-1]).
Never opens data/evaluation or the task's own test gold.

This is NOT an untouched public-eval FIRST and not a global Q3/Q4/Q6 PASS.
The strongest baseline here is the original full 626-program grammar (with
per-task recolor adapter). The proposed composer is an expanded grammar.
Task-specific source verifier may still overfit the unseen test grid.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import subprocess
import time
from collections import Counter

from neumann1.composed_grid_inventor import ComposedGridInventor
from neumann1 import arc2_meta_grid_reasoner as old

PINNED_ARC2="f3283f727488ad98fe575ea6a5ac981e4a188e49"
SALT="NEUMANN-Q3-2026-11-08-ARC2-TRAIN-SOURCE-SPLIT-NOVEL-COMPOSITION-v1"


def _old_predict(program,adapter,x):
    y=old.predict(x,program)
    if y is not None and adapter["kind"]=="recolor":
        y=old.recolor(y,adapter["mapping"])
    return y


def evaluate_source_case(record, *, max_geometries=12, max_relational_ms=120):
    pairs=[(old.G(x["input"]),old.G(x["output"]))
           for x in record["train"]]
    if len(pairs)<3:
        return {"status":"SKIP_INSUFFICIENT_SOURCE",
                "train_pairs":len(pairs)}
    train=pairs[:-1]
    source_input,source_answer=pairs[-1]
    t0=time.perf_counter_ns()
    matches,checks=old.fit_task(
        train,range(len(old.PROGRAMS)),len(old.PROGRAMS),
        max_hits=len(old.PROGRAMS))
    classical_true=any(
        _old_predict(old.PROGRAMS[index],adapter,source_input)==source_answer
        for index,adapter in matches)
    classical_ms=(time.perf_counter_ns()-t0)/1e6
    t0=time.perf_counter_ns()
    result=ComposedGridInventor(
        max_geometries=max_geometries,
        max_relational_ms=max_relational_ms).solve(
            train,(source_input,))
    composed_ms=(time.perf_counter_ns()-t0)/1e6
    invented_valid=bool(
        result.invented_program is not None
        and result.invented_program.apply(source_input)==source_answer)
    outputs_valid=any(
        candidate[0]==source_answer for candidate in result.candidates)
    return {
        "status":"EVALUATED",
        "train_pairs":len(train),"source_verification_pairs":1,
        "classical_source_fit":bool(matches),
        "classical_source_verified":classical_true,
        "invented_source_fit":result.invented_source_fit,
        "invented_source_verified":invented_valid,
        "new_composition_only_verified":invented_valid and not classical_true,
        "actual_returned_candidate_verified":outputs_valid,
        "classical_checks":checks,
        "classical_search_ms":round(classical_ms,5),
        "composed_full_source_search_ms":round(composed_ms,5),
        "relational_attempts":result.relational_invention_attempts,
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--upstream",type=pathlib.Path,required=True)
    cli.add_argument("--n",type=int,default=96)
    cli.add_argument("--max-rel-ms",type=int,default=120)
    cli.add_argument("--output",type=pathlib.Path,
                     default=pathlib.Path("/tmp/neumann_q3_arc2_train_diagnostic.json"))
    args=cli.parse_args()
    if not 1<=args.n<=128:
        raise ValueError("source diagnostic has a fixed finite budget")
    sha=subprocess.check_output(
        ["git","-C",str(args.upstream),"rev-parse","HEAD"],text=True).strip()
    if sha!=PINNED_ARC2:
        raise ValueError("external author revision changed")
    root=args.upstream/"data"/"training"
    if not root.is_dir():
        raise ValueError("only independent original training sources allowed")
    paths=sorted(root.glob("*.json"),
                 key=lambda p:hashlib.sha256(
                     (SALT+p.name).encode()).hexdigest())[:args.n]
    if len(paths)!=args.n:
        raise ValueError("source data missing")
    ledger=[]
    for path in paths:
        data=json.loads(path.read_text())
        record=evaluate_source_case(
            data,max_geometries=12,max_relational_ms=args.max_rel_ms)
        record["source_id"]=path.stem
        record["source_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        ledger.append(record)
    examined=[r for r in ledger if r["status"]=="EVALUATED"]
    s={
        "source_cases_selected":len(paths),
        "source_cases_checked":len(examined),
        "source_skipped":len(paths)-len(examined),
        "classical_source_verified":sum(r["classical_source_verified"] for r in examined),
        "invented_source_fitted":sum(r["invented_source_fit"] for r in examined),
        "invented_source_verified":sum(r["invented_source_verified"] for r in examined),
        "new_composition_only_source_verified":sum(
            r["new_composition_only_verified"] for r in examined),
        "original_prediction_candidate_source_verified":sum(
            r["actual_returned_candidate_verified"] for r in examined),
        "classical_source_search_seconds":round(sum(
            r["classical_search_ms"] for r in examined)/1000,5),
        "composed_source_search_seconds":round(sum(
            r["composed_full_source_search_ms"] for r in examined)/1000,5),
    }
    report={
        "schema":"NEUMANN.Q3.ARC2.invented-composition.training-only-diagnostic.v1",
        "upstream_commit":PINNED_ARC2,
        "source_selection_salt":SALT,
        "used_official_public_evaluation_originals":False,
        "used_original_test_answers":False,
        "source_holdout_pairs_in_each_task":1,
        "summary":s,"records":ledger,
        "adjudication":"SOURCE_ONLY_DEVELOPMENT_NOT_Q3_GLOBAL",
        "known_limits":[
            "Potential exposure of original source training task family to earlier NEUMANN studies",
            "All candidate primitives and high-level composition schema are human-coded",
            "Full runtime/energy and training/model optimization costs not included",
            "Does not prove equal-grammar novelty against optimal specialist synthesis",
            "Source withheld training pair is not genuine official unseen evaluation",
        ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(s,indent=2))
    return report


if __name__=="__main__":main()
