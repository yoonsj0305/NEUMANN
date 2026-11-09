"""Q3 source-born AST algebra on independent-author ARC originals.

This script first removes test outputs from the official ARC-AGI-2 TRAINING
originals pinned at f3283f727488ad98fe575ea6a5ac981e4a188e49.

DEVELOPMENT: task 00576224 is a source-observed example used to inspect
missing programmable index correspondences (never claim it as independent first-generalized).
FIRST: 32 hash-frozen, new originals not in the prior 608 or previous 32. No test gold is available to proposer.
A separate invocation opens author targets only AFTER prediction SHA freeze.

Strong comparison: 626 cold programs, geometric/relational composition, and
all prior full ObjectGapRouter programs when source demonstration count
allows. New source-born branch gets one fewer train I/O as an independent
source verifier; all baselines may see all provided training I/O.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from research.q3.q3_arc2_training_original_test_freeze import (
    PINNED_ARC2,checked_upstream,sha_bytes)
from research.q3.q3_arc2_parallel_bulk_fifth import fifth_manifest
from neumann1.arc2_meta_grid_reasoner import G,PROGRAMS,fit_task,predict,recolor
from neumann1.composed_grid_inventor import ComposedGridInventor
from neumann1.object_gap_router import ObjectGapRouter
from neumann1.source_born_representation_inventor import SourceBornRepresentationInventor

DEVELOPMENT=("00576224",)
OLD_SALT="NEUMANN_Q3_FIRST_FACE_GRAPH_2026_11_09_v1"
SALT="NEUMANN_Q3_SOURCE_BORN_2026_11_09_v1"
EXTRA_EXCLUDED={"00576224","0e671a1a","a65b410d",
                "d6542281","ce8d95cc","20818e16",
                "5833af48","90c28cc7","272f95fa","00576224"}


def prepare(upstream,blind,n=32):
    root=checked_upstream(upstream)
    old_exclusions,_=fifth_manifest()
    excluded=old_exclusions|EXTRA_EXCLUDED
    available=[p for p in root.glob("*.json") if p.stem not in excluded]
    # The previous spatial FACE 32 FIRST originals have already had test
    # gold scored. Those IDs must never become "new" independent evidence.
    previous=sorted(available,key=lambda p:hashlib.sha256(
        (OLD_SALT+p.name).encode()).hexdigest())[:32]
    excluded|={p.stem for p in previous}
    untouched=[p for p in available if p.stem not in excluded]
    chosen=sorted(untouched,key=lambda p:hashlib.sha256(
        (SALT+p.name).encode()).hexdigest())[:n]
    if n<1 or len(chosen)!=n or len(set(p.stem for p in chosen))!=n:
        raise ValueError("invalid independent original cohort")
    selected=[(pathlib.Path(root)/(x+".json"),"DEVELOPMENT")
              for x in DEVELOPMENT]
    selected += [(p,"FIRST_UNSEEN") for p in chosen]
    blind.mkdir(parents=True,exist_ok=True)
    records=[]
    for original,cohort in selected:
        source=json.loads(original.read_text())
        censored={
            "train":source["train"],
            "test":[{"input":a["input"]} for a in source["test"]]}
        target=blind/original.name
        target.write_text(json.dumps(censored,separators=(",",":")))
        records.append({
            "id":original.stem,"cohort":cohort,
            "author_sha256":sha_bytes(original.read_bytes()),
            "blind_sha256":sha_bytes(target.read_bytes())})
    (blind/"manifest.json").write_text(json.dumps({
        "author_commit":PINNED_ARC2,"salt":SALT,
        "excluded_originals":len(excluded),
        "every_test_output_removed":True,
        "records":records},indent=2)+"\n")
    print("SOURCE-ONLY COHORT FROZEN",len(records),
          "UNSEEN",n,"EXCLUDED",len(excluded))


def _unique(*groups,cap=2):
    out=[]
    for group in groups:
        for result in group:
            if result not in out:
                out.append(result)
                if len(out)>=cap:return out
    return out


def _prior(pairs,targets):
    results=[]
    # Allow all source demonstrations to known search paths, a stronger
    # comparator than the single-demo + independent-verifier source-born path.
    try:
        fitted,_=fit_task(
            pairs,range(len(PROGRAMS)),len(PROGRAMS),
            max_hits=len(PROGRAMS))
        for j,adapter in fitted:
            trial=[]
            for raw in targets:
                v=predict(raw,PROGRAMS[j])
                if v is not None and adapter["kind"]=="recolor":
                    v=recolor(v,adapter["mapping"])
                trial.append(v)
            if all(x is not None for x in trial):
                candidate=tuple(trial)
                if candidate not in results:results.append(candidate)
                if len(results)>=2:break
    except (ValueError,TypeError,ArithmeticError):
        pass
    if len(pairs)>=2:
        try:
            composed=ComposedGridInventor(
                max_geometries=12,max_relational_ms=120).solve(
                    pairs,targets)
            results=_unique(results,composed.candidates)
        except (ValueError,TypeError,ArithmeticError):pass
    if len(pairs)>=3:
        try:
            existing=ObjectGapRouter(
                max_relational_ms=120,max_object_ms=350,
                max_causal_ms=350,max_bulk_ms=350,
                enable_source_born=False).solve(
                    pairs[:-1],(pairs[-1],),targets)
            results=_unique(results,existing.candidates)
        except (ValueError,TypeError,ArithmeticError):
            pass
    return results[:2]


def propose(blind,out):
    manifest=json.loads((blind/"manifest.json").read_text())
    if not manifest["every_test_output_removed"]:
        raise ValueError("target outputs were not removed")
    records=[]
    for item in manifest["records"]:
        src=blind/(item["id"]+".json")
        if sha_bytes(src.read_bytes())!=item["blind_sha256"]:
            raise ValueError("blind-source mutation")
        data=json.loads(src.read_text())
        if any("output" in item for item in data["test"]):
            raise ValueError("target leakage into source-only proposer")
        pairs=tuple((G(x["input"]),G(x["output"])) for x in data["train"])
        targets=tuple(G(t["input"]) for t in data["test"])
        if len(pairs)<2 or not targets:
            records.append({**item,"status":"ABSTAIN_SOURCE_INSUFFICIENT"})
            continue
        prior=_prior(pairs,targets)
        source=SourceBornRepresentationInventor(max_ms=2500).invent(
            pairs[:-1],independent_source_checks=(pairs[-1],))
        fresh=[]
        if source.programs:
            attempt=tuple(source.programs[0].apply(x) for x in targets)
            if all(p is not None for p in attempt):
                fresh.append(attempt)
        records.append({
            **item,"status":"PREDICTED",
            "prior":prior,"new_representation":fresh,
            "integrated":_unique(prior,fresh),
            "new_source_status":source.status,
            "new_operator_ast":repr(source.programs[0].ast) if source.programs else None,
            "test_count":len(targets)})
    payload={
        "schema":"NEUMANN.Q3.SOURCE-BORN-REPRESENTATION.ORIGINAL-FIRST.v1",
        "independent_author_commit":PINNED_ARC2,
        "all_test_answers_excluded_from_proposer":True,
        "source_development_task":DEVELOPMENT,
        "first_unseen_salt":SALT,
        "records":records}
    out.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print("Q3 SOURCE-BORN SOURCE-FIRST FROZEN",sha_bytes(out.read_bytes()),
          "SOURCE FIT",sum(bool(r.get("new_representation")) for r in records))


def score(upstream,predictions,sha,out):
    if sha_bytes(predictions.read_bytes())!=sha:
        raise ValueError("frozen prediction hash mismatch")
    root=checked_upstream(upstream)
    payload=json.loads(predictions.read_text())
    if (payload["independent_author_commit"]!=PINNED_ARC2 or
            not payload["all_test_answers_excluded_from_proposer"] or
            payload["first_unseen_salt"]!=SALT):
        raise ValueError("source provenance invalid")
    scored=[]
    for row in payload["records"]:
        if row["status"]!="PREDICTED":
            scored.append({"id":row["id"],"cohort":row["cohort"],
                           "status":row["status"]})
            continue
        original=root/(row["id"]+".json")
        if sha_bytes(original.read_bytes())!=row["author_sha256"]:
            raise ValueError("source author changed")
        raw=json.loads(original.read_text())
        expected=tuple(G(t["output"]) for t in raw["test"])
        if len(expected)!=row["test_count"]:
            raise ValueError("original test target count changed")
        exact=lambda proposals:any(
            tuple(G(x) for x in candidate)==expected
            for candidate in proposals)
        prior=exact(row["prior"])
        newly=exact(row["new_representation"])
        integrated=exact(row["integrated"])
        scored.append({
            "id":row["id"],"cohort":row["cohort"],
            "status":"SCORED","source_fit":bool(row["new_representation"]),
            "prior":prior,"new":newly,"integrated":integrated,
            "residual":newly and not prior,
            "integrated_regression":prior and not integrated})
    groups={}
    for s in scored:
        g=groups.setdefault(s["cohort"],{
            "selected":0,"scored":0,"prior_correct":0,
            "new_correct":0,"new_residual":0,
            "integrated_correct":0,"integrated_regression":0,
            "new_source_fits":0})
        g["selected"]+=1
        if s["status"]!="SCORED":continue
        g["scored"]+=1
        g["prior_correct"]+=int(s["prior"])
        g["new_correct"]+=int(s["new"])
        g["new_residual"]+=int(s["residual"])
        g["integrated_correct"]+=int(s["integrated"])
        g["integrated_regression"]+=int(s["integrated_regression"])
        g["new_source_fits"]+=int(s["source_fit"])
    report={
        "sha256_frozen_before_gold":sha,"cohorts":groups,
        "independent_author_training_originals":True,
        "official_arc_evaluation":False,
        "unrestricted_q3_q6_pass":False,
        "not_a_new_mathematical_theorem":True}
    out.write_text(json.dumps({
        "report":report,"scored":scored},indent=2)+"\n")
    print("Q3 ORIGINAL SOURCE-BORN-REPRESENTATION SCORE",json.dumps(report,sort_keys=True))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare")
    p.add_argument("--upstream",type=pathlib.Path,required=True)
    p.add_argument("--blind",type=pathlib.Path,required=True)
    p.add_argument("--n",type=int,default=32)
    p=sub.add_parser("propose")
    p.add_argument("--blind",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p=sub.add_parser("score")
    p.add_argument("--upstream",type=pathlib.Path,required=True)
    p.add_argument("--predictions",type=pathlib.Path,required=True)
    p.add_argument("--sha",required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    args=ap.parse_args()
    if args.cmd=="prepare":prepare(args.upstream,args.blind,args.n)
    elif args.cmd=="propose":propose(args.blind,args.output)
    else:score(args.upstream,args.predictions,args.sha,args.output)
