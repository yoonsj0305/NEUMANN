"""AUTHOR-original Q3 two-example gate: fit SOURCE, freeze, blind predict, score.

22/100 frozen original ARC2 tasks have exactly two SOURCE examples. They
cannot have *independent SOURCE* holdout without leaving only one training
example. This pipeline therefore explicitly labels SOURCE-fit as UNVERIFIED;
it requires independent original-author TEST after candidates and predictions
are frozen. Never promote SOURCE-fit as SOURCE-certified or Q3 PASS.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_structure_factorization import induce_structural_factors
from neumann1.q3_object_graph_invention import induce_object_graph_factors
from neumann1.q3_residual_composition import induce_source_compositions
from neumann1.q3_source_residual_probes import induce_source_residual_probes
from neumann1.q3_coordinate_morphisms import induce_coordinate_morphisms
from neumann1.q3_periodic_residual_invention import induce_periodic_residual_rules

UPSTREAM="f3283f727488ad98fe575ea6a5ac981e4a188e49"
SCHEMA="NEUMANN.Q3.TWO-SOURCE-ORIGINAL-PROSPECTIVE.v1"


def _canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,
                      allow_nan=False)


def _hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _save(path,value):
    Path(path).write_text(_canonical(value)+"\n")


def _read(path):
    return json.loads(Path(path).read_text())


def _same(a,b):
    return len(a)==len(b) and all(source_same_value(x,y)
                                  for x,y in zip(a,b))


def fit(source_path,out):
    source=_read(source_path)
    if (source.get("original_source_count")!=100
        or source.get("upstream_revision")!=UPSTREAM
        or source.get("source_scope")!="PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY"
        or source.get("no_target_gold_in_payload") is not True):
        raise ValueError("expected frozen 100 author SOURCE only")
    runner=IsolatedPython(max_seconds=8)
    rows=[]
    for record in source["records"]:
        pairs=record["source_pairs"]
        if len(pairs)!=2:
            continue
        methods=(
            *induce_structural_factors(pairs,max_candidates=4),
            *induce_object_graph_factors(pairs,max_candidates=4),
            *induce_source_compositions(pairs,max_candidates=4),
            *induce_source_residual_probes(pairs,max_probes=4),
            *induce_coordinate_morphisms(pairs,max_candidates=4),
            *induce_periodic_residual_rules(pairs,max_candidates=4),
        )
        fitted=[]
        already=set()
        for method in methods:
            digest=sha256(method.program.encode()).hexdigest()
            if digest in already:
                continue
            already.add(digest)
            actual=runner.evaluate(method.program,[x for x,y in pairs])
            if actual.status!="EXECUTED" or not _same(
                    actual.outputs,[y for x,y in pairs]):
                continue
            fitted.append({"program":method.program,"program_sha256":digest,
                           "representation":method.representation,
                           "description_length":method.description_length})
        fitted.sort(key=lambda x:(x["description_length"],
                                 x["representation"],x["program_sha256"]))
        # This cap is frozen before any original AUTHOR TEST outputs.
        rows.append({"id":record["source_id"],
                     "original_author_file_sha256":
                       record["original_author_file_sha256"],
                     "available_source_pairs":2,
                     "independent_source_certified":False,
                     "fitted":fitted[:2]})
    if len(rows)!=22:
        raise ValueError("frozen two-example count unexpectedly changed")
    result={"schema":SCHEMA,"phase":"SOURCE_FIT_ONLY_UNVERIFIED",
            "frozen_source_sha256":_hash(source_path),"source_cohort":100,
            "two_example_originals":len(rows),
            "with_source_fitted_programs":sum(bool(r["fitted"]) for r in rows),
            "independent_source_certified":0,
            "original_target_gold_read":False,"q3_global":"OPEN","records":rows}
    _save(out,result)
    print("Q3_TWO_SOURCE_PRETEST_METHODS_FROZEN",
          {k:v for k,v in result.items() if k!="records"},flush=True)


def blind(author_root,methods_path,out):
    methods=_read(methods_path)
    if methods.get("schema")!=SCHEMA or methods.get("phase")!=(
            "SOURCE_FIT_ONLY_UNVERIFIED"):
        raise ValueError("SOURCE-frozen method file required")
    entries=[]
    for row in methods["records"]:
        if not row["fitted"]:
            continue
        path=Path(author_root)/(row["id"]+".json")
        if _hash(path)!=row["original_author_file_sha256"]:
            raise ValueError("original author file hash mismatch")
        o=_read(path)
        entries.append({"id":row["id"],
                        "target_inputs":[e["input"] for e in o["test"]]})
    _save(out,{"schema":SCHEMA,"phase":"TEST_INPUTS_ONLY",
               "source_methods_sha256":_hash(methods_path),
               "target_gold_not_serialized":True,"entries":entries})


def predict(methods_path,blind_path,out):
    methods=_read(methods_path)
    blind=_read(blind_path)
    if (methods["schema"]!=SCHEMA or blind["schema"]!=SCHEMA
        or blind["phase"]!="TEST_INPUTS_ONLY"
        or blind["source_methods_sha256"]!=_hash(methods_path)):
        raise ValueError("frozen method/input mismatch")
    by_id={r["id"]:r for r in methods["records"]}
    runner=IsolatedPython(max_seconds=8)
    rows=[]
    for row in blind["entries"]:
        guesses=[]
        for method in by_id[row["id"]]["fitted"]:
            result=runner.evaluate(method["program"],row["target_inputs"])
            guesses.append({"program_sha256":method["program_sha256"],
                            "status":result.status,
                            "outputs":result.outputs
                            if result.status=="EXECUTED" else None})
        rows.append({"id":row["id"],"program_predictions":guesses})
    _save(out,{"schema":SCHEMA,"phase":"PREDICTIONS_BEFORE_GOLD",
               "source_methods_sha256":_hash(methods_path),
               "blind_inputs_sha256":_hash(blind_path),
               "original_target_gold_read":False,"entries":rows})


def score(author_root,methods_path,blind_path,predictions_path,
          expected_sha,out):
    if _hash(predictions_path)!=expected_sha:
        raise ValueError("prediction SHA mismatch")
    methods=_read(methods_path)
    blind=_read(blind_path)
    pred=_read(predictions_path)
    if (pred.get("schema")!=SCHEMA
        or pred.get("phase")!="PREDICTIONS_BEFORE_GOLD"
        or pred.get("original_target_gold_read") is not False
        or pred.get("source_methods_sha256")!=_hash(methods_path)
        or pred.get("blind_inputs_sha256")!=_hash(blind_path)):
        raise ValueError("gold leaked or provenance mismatch")
    refs={r["id"]:r for r in methods["records"]}
    by_input={r["id"]:r for r in blind["entries"]}
    rows=[]
    for row in pred["entries"]:
        ident=row["id"]
        original_path=Path(author_root)/(ident+".json")
        if _hash(original_path)!=refs[ident]["original_author_file_sha256"]:
            raise ValueError("author file tampered")
        data=_read(original_path)
        author_tests=data["test"]
        if not _same([x["input"] for x in author_tests],
                     by_input[ident]["target_inputs"]):
            raise ValueError("TEST input mismatch")
        targets=[x["output"] for x in author_tests]
        exact=False
        for attempt in row["program_predictions"]:
            if (attempt["status"]=="EXECUTED"
                and attempt["outputs"] is not None
                and _same(attempt["outputs"],targets)):
                exact=True
        rows.append({"id":ident,"original_exact":exact})
    result={"schema":SCHEMA,"phase":"POSTFROZEN_AUTHOR_SCORE",
            "scientific_scope":"DEVELOPMENT_PREVIOUSLY_EXPOSED_100_AUTHOR_SOURCE",
            "two_example_denominator":22,
            "full_original_cohort_denominator":100,
            "original_test_exact":sum(x["original_exact"] for x in rows),
            "source_fitted_not_independently_source_certified":True,
            "prediction_sha256":expected_sha,
            "q3_global":"OPEN","records":rows}
    _save(out,result)
    print("Q3_TWO_SOURCE_POSTFROZEN_AUTHOR_EXACT",
          {k:v for k,v in result.items() if k!="records"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=("fit","blind","predict","score"))
    p.add_argument("--source")
    p.add_argument("--methods")
    p.add_argument("--blind")
    p.add_argument("--predictions")
    p.add_argument("--author-root")
    p.add_argument("--expected-sha")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if args.phase=="fit":fit(args.source,args.out)
    if args.phase=="blind":blind(args.author_root,args.methods,args.out)
    if args.phase=="predict":predict(args.methods,args.blind,args.out)
    if args.phase=="score":
        score(args.author_root,args.methods,args.blind,args.predictions,
              args.expected_sha,args.out)
