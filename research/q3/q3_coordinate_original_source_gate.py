"""Reproducible REAL-original SOURCE evidence for Q3 coordinate-grammar invention.

Same 50 author SOURCE tasks pinned before this new experiment, selected in
the existing 2026-11-10 SHA-salted official ARC-AGI-2 registry. The developer
has already inspected some SOURCE examples; this is a *POSTFIRST* structural
candidate test, NOT first-seen original Q3 generalization.

Discover from TRAIN SOURCE only, execute on heldout independent SOURCE in
no-network Docker, freeze programs and hashes before any original test gold.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_coordinate_morphisms import induce_coordinate_morphisms
from neumann1.q3_structure_factorization import induce_structural_factors
from neumann1.q3_residual_composition import induce_source_compositions
from neumann1.q3_object_graph_invention import induce_object_graph_factors

SCHEMA="NEUMANN.Q3.SOURCE-INFERRED-COORDINATE-MORPHISM.v1"
UPSTREAM="f3283f727488ad98fe575ea6a5ac981e4a188e49"


def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def invent(original_source,out):
    r=json.loads(Path(original_source).read_text())
    if (r.get("schema")!="NEUMANN.Q3.ORIGINAL-ARC2-SOURCE-TEACHING.v1"
        or r.get("upstream_revision")!=UPSTREAM
        or r.get("original_source_count")!=50
        or r.get("no_target_gold_in_payload") is not True):
        raise ValueError("not previously frozen author original SOURCE")
    runner=IsolatedPython(max_seconds=8)
    receipts=[]
    for task in r["records"]:
        original=task["source_id"]
        source=task["source_pairs"]
        train=source[:-1]
        checks=source[-1:]
        seen={canonical(x) for x,y in train}
        if canonical(checks[0][0]) in seen:
            receipts.append({"id":original,"status":"ABSTAIN_SOURCE_ID_OVERLAP"})
            continue
        methods=induce_coordinate_morphisms(train,max_candidates=4)
        certified=[]
        for candidate in methods:
            check=runner.evaluate(
                candidate.program,[x for x,y in checks])
            if (check.status=="EXECUTED"
                    and len(check.outputs)==len(checks)
                    and all(source_same_value(got,y) for got,(_,y)
                            in zip(check.outputs,checks))):
                certified.append({
                    "program":candidate.program,
                    "program_sha256":hashlib.sha256(
                        candidate.program.encode()).hexdigest(),
                    "representation":candidate.representation,
                    "source_check_count":len(checks),
                    "source_train_count":len(train),
                    "independent_source_certified":True,
                })
        receipts.append({
            "id":original,
            "status":("SOURCE_VERIFIED" if certified
                      else "NO_SOURCE_VERIFIED_MORPHISM"),
            "candidate_count":len(methods),
            "certified":certified,
            "original_author_file_sha256":
                task["original_author_file_sha256"],
        })
        if certified:
            print("Q3_NEW_COORDINATE_EXECUTABLE_ORIGINAL_SOURCE",
                  original[:8],[(c["representation"],
                     c["program_sha256"]) for c in certified],flush=True)
    out_data={
        "schema":SCHEMA,
        "original_source_file_sha256":sha(original_source),
        "original_revision":UPSTREAM,
        "source_originals":len(r["records"]),
        "source_verified_count":sum(
            bool(x.get("certified")) for x in receipts),
        "prior_exposure":"PREVIOUSLY_EXPOSED_SOURCE_DEV",
        "target_gold_accessed":False,
        "receipts":receipts,
        "q3_global":"OPEN",
    }
    Path(out).write_text(canonical(out_data)+"\n")
    print("Q3_COORDINATE_ORIGINAL_SOURCE_FREEZE",
          {"tested":len(receipts),
           "source_certified":out_data["source_verified_count"],
           "sha256":sha(out)},flush=True)


def blind(original_dir,methods,out):
    source=json.loads(Path(methods).read_text())
    if source["schema"]!=SCHEMA or source["target_gold_accessed"] is not False:
        raise ValueError("frozen method identity required")
    root=Path(original_dir)
    entries=[]
    for item in source["receipts"]:
        if not item.get("certified"):
            continue
        path=root/(item["id"]+".json")
        if sha(path)!=item["original_author_file_sha256"]:
            raise ValueError("original author revision changed")
        r=json.loads(path.read_text())
        entries.append({
            "id":item["id"],
            "original_file_sha256":sha(path),
            "target_inputs":[p["input"] for p in r["test"]],
        })
    output={
        "schema":SCHEMA+".BLIND",
        "original_revision":UPSTREAM,
        "methods_sha256":sha(methods),
        "entries":entries,
        "target_gold_not_serialized":True,
        "scope":"POSTFIRST_ALREADY_EXPOSED_SOURCE",
    }
    Path(out).write_text(canonical(output)+"\n")


def predict(blind_file,methods,out):
    b=json.loads(Path(blind_file).read_text())
    m=json.loads(Path(methods).read_text())
    if (b["schema"]!=SCHEMA+".BLIND"
        or b["methods_sha256"]!=sha(methods)
        or b["target_gold_not_serialized"] is not True):
        raise ValueError("no original-blind provenance")
    runner=IsolatedPython(max_seconds=8)
    byid={x["id"]:x for x in m["receipts"]}
    receipts=[]
    for entry in b["entries"]:
        task=byid[entry["id"]]
        predictions=[]
        for candidate in task["certified"]:
            result=runner.evaluate(
                candidate["program"],entry["target_inputs"])
            predictions.append({
                "program_sha256":candidate["program_sha256"],
                "representation":candidate["representation"],
                "status":result.status,
                "values":list(result.outputs)
                    if result.status=="EXECUTED" else [],
            })
        receipts.append({"id":entry["id"],
                         "program_predictions":predictions})
    result={
        "schema":SCHEMA+".PREDICTIONS",
        "blind_sha256":sha(blind_file),
        "methods_sha256":sha(methods),
        "original_gold_read":False,
        "receipts":receipts,
        "q3_global":"OPEN",
    }
    Path(out).write_text(canonical(result)+"\n")
    print("Q3_POSTFIRST_ORIGINAL_PREDICTIONS_FROZEN",
          sha(out),len(receipts),flush=True)


def score(author_root,blind_file,methods,predictions,expected_sha,out):
    if sha(predictions)!=expected_sha:
        raise ValueError("model predictions changed after original gold open")
    p=json.loads(Path(predictions).read_text())
    b=json.loads(Path(blind_file).read_text())
    m=json.loads(Path(methods).read_text())
    if (p["schema"]!=SCHEMA+".PREDICTIONS"
        or p["blind_sha256"]!=sha(blind_file)
        or p["methods_sha256"]!=sha(methods)
        or p["original_gold_read"] is not False
        or b["target_gold_not_serialized"] is not True):
        raise ValueError("invalid SOURCE-only author original receipt")
    root=Path(author_root)
    ids={r["id"]:r for r in b["entries"]}
    scores=[]
    for item in p["receipts"]:
        entry=ids[item["id"]]
        path=root/(item["id"]+".json")
        if sha(path)!=entry["original_file_sha256"]:
            raise ValueError("author original changed")
        gold=[r["output"] for r in json.loads(path.read_text())["test"]]
        exact=[]
        for cand in item["program_predictions"]:
            guesses=cand["values"]
            passed=(
                cand["status"]=="EXECUTED"
                and len(guesses)==len(gold)
                and all(source_same_value(a,b) for a,b in
                        zip(guesses,gold)))
            exact.append({"program_sha256":cand["program_sha256"],
                          "exact_original":passed})
        scores.append({"id":item["id"],"programs":exact,
                       "solved":any(x["exact_original"] for x in exact)})
    summary={
        "source_certified_originals":len(scores),
        "exact_originals":sum(item["solved"] for item in scores),
        "scientific_scope":"PREVIOUSLY_EXPOSED_AUTHOR_SOURCE_DEV",
        "prediction_sha256":expected_sha,
        "q3_global":"OPEN"}
    Path(out).write_text(canonical({
        "summary":summary,"records":scores})+"\n")
    print("Q3_ORIGINAL_AUTHOR_COORDINATE_MORPHISM",
          summary,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    sp=parser.add_subparsers(dest="cmd",required=True)
    for name in ("invent","blind","predict","score"):
        p=sp.add_parser(name)
        p.add_argument("--out",required=True)
        if name=="invent":
            p.add_argument("--source",required=True)
        if name in ("blind","predict","score"):
            p.add_argument("--methods",required=True)
            p.add_argument("--blind",required=name!="blind")
        if name in ("blind","score"):
            p.add_argument("--author-root",required=True)
        if name=="score":
            p.add_argument("--predictions",required=True)
            p.add_argument("--expected-sha",required=True)
    a=parser.parse_args()
    if a.cmd=="invent":
        invent(a.source,a.out)
    elif a.cmd=="blind":
        blind(a.author_root,a.methods,a.out)
    elif a.cmd=="predict":
        predict(a.blind,a.methods,a.out)
    else:
        score(a.author_root,a.blind,a.methods,a.predictions,a.expected_sha,a.out)
