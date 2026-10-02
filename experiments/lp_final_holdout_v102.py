"""v0.0.102 phase 2: final fresh Q34 holdout and Q3/Q4 closure."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import random
from pathlib import Path
from statistics import median

import torch
from threadpoolctl import threadpool_limits

from experiments.lp_final_adaptive_v101 import (
    MODEL_SEEDS,
    environment,
    investment_per_query,
    observe_reference,
    ranking,
    restore_models,
)
from neumann1.lp_final_holdout_archive_v102 import decode_source, load_final_sources
from neumann1.lp_q34_support_v097 import adaptive_support_checked
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

SOURCE_MANIFEST="docs/experiments/results/v102_final_sources.manifest.json"
V100_MANIFEST="docs/experiments/results/v100_first_refit.manifest.json"
GROUPS=("m64_base","m64_surface","m128_base","m128_surface")
ROUTES=("DIRECT","ORACLE","ADAPTIVE_s100001","ADAPTIVE_s100002")


def protocol():
    return {
        "schema":"neumann.final-q34-holdout-v102.v1",
        "source_manifest":SOURCE_MANIFEST,
        "model_manifest":V100_MANIFEST,
        "model_seeds":list(MODEL_SEEDS),
        "groups":list(GROUPS),
        "routes":list(ROUTES),
        "views":48,
        "cases_per_cell":12,
        "adaptive_support_factors":[2,4],
        "warmups":1,
        "repeats":3,
        "order_seed":102991,
        "budget_s":5.0,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "new_fitting":False,
        "threshold_change":False,
        "support_width_sweep":False,
        "v098_holdout_access":False,
        "v101_development_access":False,
        "second_holdout_authorized":False,
    }


def observe_candidate(raw,route,models,training):
    seed=int(route.rsplit("s",1)[1])
    order,proposal_ms=ranking(raw,models[seed])
    left=protocol()["budget_s"]-proposal_ms/1000.0
    execution=None
    if left>0:
        execution=adaptive_support_checked(
            **raw,ranking=order,budget_s=left,
            factors=tuple(protocol()["adaptive_support_factors"]))
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=proposal_ms+post_ms
    subset=bool(execution and any(
        attempt["result"]["accepted"] for attempt in execution["attempts"]))
    return {
        "accepted":bool(
            execution and execution["accepted"]
            and total_ms<=protocol()["budget_s"]*1000.0),
        "proposal_ms":proposal_ms,
        "post_ms":post_ms,
        "total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(training,seed),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":subset,
        "ranking":order,
        "witness":execution["witness"] if execution else None,
    }


def _medians(records,case_id,route):
    rows=[
        r for r in records
        if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0
    ]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("v102 timed repeat coverage drift")
    investment={r["amortized_investment_ms"] for r in rows}
    if len(investment)!=1:
        raise ValueError("v102 investment drift")
    rankings=[r["ranking"] for r in rows]
    if route.startswith("ADAPTIVE_") and any(x!=rankings[0] for x in rankings[1:]):
        raise ValueError("v102 deterministic ranking drift")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investment)),
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_free":all(not r["fallback_used"] for r in rows),
        "subset_accepted":all(r["subset_accepted"] for r in rows),
    }


def cell_metrics(records,sources,route):
    ids=[s["id"] for s in sources]
    med={(case,r):_medians(records,case,r) for case in ids for r in ROUTES}
    reference_ok=all(
        med[case,"DIRECT"]["all_accepted"] and med[case,"ORACLE"]["all_accepted"]
        for case in ids)
    capability=all(med[case,route]["all_accepted"] for case in ids)
    direct=sum(med[case,"DIRECT"]["total_ms"] for case in ids)
    oracle_post=sum(med[case,"ORACLE"]["post_ms"] for case in ids)
    oracle_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,"ORACLE"]["post_ms"]
        for case in ids)
    post=sum(med[case,route]["post_ms"] for case in ids)
    proposal=sum(med[case,route]["proposal_ms"] for case in ids)
    invest=sum(med[case,route]["investment_ms"] for case in ids)
    discovery=proposal+invest
    savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,route]["post_ms"]
        for case in ids)
    utility=savings/oracle_savings if oracle_savings>0 and savings>0 else None
    burden=discovery/savings if savings>0 else None
    complete=(discovery+post)/direct if direct>0 else None
    passed=bool(
        reference_ok and capability and utility is not None and burden is not None
        and utility>=protocol()["utility_floor"]
        and burden<=protocol()["discovery_burden_max"]
        and complete is not None and complete<1.0)
    return {
        "route":route,"cases":len(ids),
        "reference_capability":reference_ok,"capability":capability,
        "direct_total_ms":direct,"oracle_post_total_ms":oracle_post,
        "oracle_savings_ms":oracle_savings,
        "proposal_total_ms":proposal,
        "amortized_investment_total_ms":invest,
        "effective_discovery_total_ms":discovery,
        "post_total_ms":post,
        "candidate_pre_discovery_savings_ms":savings,
        "utility_recovery":utility,
        "discovery_burden":burden,
        "amortized_complete_ratio":complete,
        "fallback_free_cases":sum(med[case,route]["fallback_free"] for case in ids),
        "subset_accepted_cases":sum(med[case,route]["subset_accepted"] for case in ids),
        "passed":passed,
    }


def summarize(records,sources):
    expected={
        (s["id"],route,repeat)
        for s in sources for route in ROUTES for repeat in (-1,0,1,2)
    }
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("v102 evaluation coverage drift")
    groups={g:[s for s in sources if s["group"]==g] for g in GROUPS}
    if any(len(rows)!=protocol()["cases_per_cell"] for rows in groups.values()):
        raise ValueError("v102 final cell coverage drift")
    candidate_routes=[r for r in ROUTES if r.startswith("ADAPTIVE_")]
    overall={r:cell_metrics(records,sources,r) for r in candidate_routes}
    cells={
        r:{g:cell_metrics(records,group,r) for g,group in groups.items()}
        for r in candidate_routes
    }
    passes={
        r:overall[r]["passed"] and all(cells[r][g]["passed"] for g in GROUPS)
        for r in candidate_routes
    }
    final_pass=all(passes.values())
    return {
        "decision":(
            "CLOSE_Q3_PASS_Q4_PASS_ADVANCE_Q5"
            if final_pass else
            "CLOSE_Q3_Q4_CURRENT_LP_FORMULATION_REJECTED_NO_Q5"
        ),
        "q3_status":(
            "PASS_LP_MECHANISM"
            if final_pass else "REJECTED_CURRENT_LP_FORMULATION"
        ),
        "q4_status":(
            "PASS_LP_MECHANISM"
            if final_pass else "REJECTED_CURRENT_LP_FORMULATION"
        ),
        "advance_q5":final_pass,
        "seed_pass":passes,
        "overall":overall,
        "groups":cells,
        "views":len(sources),
        "second_holdout_authorized":False,
        "v098_holdout_access":False,
        "v101_development_access":False,
    }


def validate_witnesses(report,raws):
    for row in report["records"]:
        if not row["accepted"]:
            continue
        witness=row["witness"]
        if witness is None or not verify_standard_form_certificate(
                **raws[row["case_id"]],**witness)["accepted"]:
            raise ValueError("v102 accepted original witness drift")


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v102 evaluation head required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    expected_runtime={
        "python":[3,12],
        "numpy":"2.3.5",
        "scipy":"1.17.0",
        "scikit_learn":"1.9.1",
        "torch":"2.14.0+cpu",
        "highspy":"1.15.1",
    }
    env=environment()
    if env!=expected_runtime or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"v102 final runtime drift: {env!r}")

    source_report=load_final_sources(SOURCE_MANIFEST)
    sources=source_report["sources"]
    raws={s["id"]:decode_source(s) for s in sources}

    retained=load_first_refit(V100_MANIFEST)
    models,training=restore_models(retained)
    records=[]
    source_by_id={s["id"]:s for s in sources}

    with threadpool_limits(1):
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                source=source_by_id[case_id]
                raw=raws[case_id]
                if route=="DIRECT":
                    row=observe_reference(raw,route)
                elif route=="ORACLE":
                    row=observe_reference(raw,route,source["basis"])
                else:
                    row=observe_candidate(raw,route,models,training)
                records.append({
                    "case_id":case_id,
                    "group":source["group"],
                    "surface":source["surface"],
                    "source_sha256":source["sha256"],
                    "route":route,
                    "repeat":repeat,
                    **row,
                })
            print(f"V102_REPEAT {repeat} {len(records)}",flush=True)

    report={
        "protocol":protocol(),
        "environment":env,
        "frozen_head":frozen_head,
        "source_manifest_identity":{
            "frozen_head":source_report["frozen_head"],
            "source_count":len(sources),
        },
        "model_identity":{
            str(seed):retained["training"][f"QUOTIENT_s{seed}"]["weights_sha256"]
            for seed in MODEL_SEEDS
        },
        "records":records,
        "summary":summarize(records,sources),
        "stage":"completed",
    }
    validate_witnesses(report,raws)
    return report


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v102 final evaluation already exists")
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.final-q34-holdout-v102.archive.v1",
        "file":output.name,
        "frozen_head":report["frozen_head"],
        "rerun":False,
        "gzip_bytes":len(packed),
        "gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),
        "json_sha256":hashlib.sha256(raw).hexdigest(),
        "decision":report["summary"]["decision"],
        "q3_status":report["summary"]["q3_status"],
        "q4_status":report["summary"]["q4_status"],
        "advance_q5":report["summary"]["advance_q5"],
        "summary":report["summary"],
    }
    manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    return m


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-gzip",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--frozen-head",default=os.environ.get("GITHUB_SHA"))
    args=p.parse_args()
    report=run_study(args.frozen_head)
    manifest=write_first(report,args.output_gzip,args.manifest)
    print("V102_FINAL_SUMMARY="+json.dumps(
        manifest["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V102_FINAL_ARCHIVE="+json.dumps(
        {k:v for k,v in manifest.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
