"""v0.0.102 fresh Q34 evaluation for the frozen EXPAND4 system only."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import sys
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import numpy as np
import torch
from threadpoolctl import threadpool_info, threadpool_limits

from experiments.lp_expand4_holdout_register_v102 import GROUPS, load_registered
from experiments.lp_frozen_support_expansion_v101 import (
    expand4_checked,
    frozen_ranking,
    investment_per_query,
    restore_frozen_quotient,
)
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_frozen_support_expansion_archive_v101 import load_first_expansion
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_q34_support_v097 import restricted_original_checked


SEEDS=(100001,100002)
ROUTES=("DIRECT","ORACLE","EXPAND4_s100001","EXPAND4_s100002")
SOURCE_MANIFEST="docs/experiments/results/v102_fresh_sources.manifest.json"
AUTHORITY_MANIFEST="docs/experiments/results/v101_first_expansion.manifest.json"


def protocol():
    return {
        "schema":"neumann.q34-expand4-fresh-eval-v102.v1",
        "runtime":{**admission.RUNTIME,"scikit_learn":"1.9.1"},
        "source_manifest":SOURCE_MANIFEST,
        "authority_manifest":AUTHORITY_MANIFEST,
        "source_views":48,
        "groups":list(GROUPS),
        "routes":list(ROUTES),
        "model_seeds":list(SEEDS),
        "warmups":1,
        "repeats":3,
        "order_seed":102991,
        "budget_s":5.0,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "fixed_support_factor":2,
        "expanded_support_factor":4,
        "new_fitting":False,
        "checkpoint_selection":False,
        "support_factor_tuning":False,
        "v098_holdout_access":False,
        "final_q34_holdout":True,
        "global_q3":"OPEN",
        "global_q4":"OPEN",
    }


def environment():
    import scipy
    import sklearn
    import highspy
    return {
        "python":list(sys.version_info[:2]),
        "numpy":np.__version__,
        "scipy":scipy.__version__,
        "scikit_learn":sklearn.__version__,
        "torch":torch.__version__,
        "highspy":highspy.Highs().version(),
    }


def raw_source(source):
    m=source["rows"]
    n=source["cols"]
    return {k:storage.decode_array(source["arrays"][k],shape) for k,shape in (
        ("A",(m,n)),("b",(m,)),("c",(n,)))}


def authority_and_models():
    authority=load_first_expansion(AUTHORITY_MANIFEST)
    summary=authority["summary"]
    if summary["decision"]!="ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_FROZEN_SUPPORT_SYSTEM":
        raise ValueError("v102 authority decision drift")
    if summary["fresh_holdout_candidate"]!=["EXPAND4"]:
        raise ValueError("v102 authority candidate drift")
    models,training=restore_frozen_quotient()
    if authority["training_identity"]!=training:
        raise ValueError("v102 frozen checkpoint/training identity drift")
    return authority,models,training


def observe_reference(raw,route,basis=None):
    budget=protocol()["budget_s"]
    if route=="DIRECT":
        result=solve_native_checked(**raw,cold_fallback=False,budget_s=budget)
        witness=result["attempts"][-1]["witness"] if result["accepted"] else None
        return {
            "accepted":bool(result["accepted"]),
            "proposal_ms":0.0,"post_ms":float(result["total_ms"]),
            "total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,
            "fallback_used":False,"subset_accepted":False,
            "expanded":False,"expanded_accepted":False,
            "ranking":None,"top2":None,"witness":witness,
        }
    if route=="ORACLE":
        if basis is None:
            raise ValueError("v102 oracle basis required")
        result=restricted_original_checked(
            **raw,indices=list(basis),budget_s=budget)
        return {
            "accepted":bool(result["accepted"]),
            "proposal_ms":0.0,"post_ms":float(result["total_ms"]),
            "total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,
            "fallback_used":False,"subset_accepted":bool(result["accepted"]),
            "expanded":False,"expanded_accepted":False,
            "ranking":None,"top2":None,"witness":result["witness"],
        }
    raise ValueError("v102 reference route required")


def observe_candidate(raw,route,models,training):
    if not route.startswith("EXPAND4_s"):
        raise ValueError("v102 frozen EXPAND4 route required")
    seed=int(route.rsplit("s",1)[1])
    if seed not in SEEDS:
        raise ValueError("v102 unknown frozen seed")
    budget=protocol()["budget_s"]
    ranking,proposal_ms=frozen_ranking(raw,models[seed])
    m,n=raw["A"].shape
    if len(ranking)!=n or len(set(ranking))!=n:
        raise ValueError("v102 ranking drift")
    top2=ranking[:min(n,2*m)]
    left=budget-proposal_ms/1000.0
    execution=None
    if left>0:
        execution=expand4_checked(raw,ranking,left)
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=proposal_ms+post_ms
    accepted=bool(execution and execution["accepted"] and total_ms<=budget*1000.0)
    return {
        "accepted":accepted,
        "proposal_ms":float(proposal_ms),"post_ms":post_ms,"total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(training,seed),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":bool(execution and execution["subset_accepted"]),
        "expanded":bool(execution and execution["expanded"]),
        "expanded_accepted":bool(execution and execution["expanded_accepted"]),
        "ranking":ranking,"top2":top2,
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
    for field in ("ranking","top2","expanded","expanded_accepted"):
        values=[r[field] for r in rows]
        if any(v!=values[0] for v in values[1:]):
            raise ValueError(f"v102 deterministic {field} drift")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investment)),
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_free":all(not r["fallback_used"] for r in rows),
        "subset_accepted":all(r["subset_accepted"] for r in rows),
        "expanded":rows[0]["expanded"],
        "expanded_accepted":rows[0]["expanded_accepted"],
        "ranking":rows[0]["ranking"],
        "top2":rows[0]["top2"],
    }


def cell_metrics(records,sources,route):
    ids=[s["id"] for s in sources]
    med={(case,r):_medians(records,case,r) for case in ids for r in ROUTES}
    reference_ok=all(
        med[case,"DIRECT"]["all_accepted"] and med[case,"ORACLE"]["all_accepted"]
        for case in ids)
    capability=all(med[case,route]["all_accepted"] for case in ids)
    direct_total=sum(med[case,"DIRECT"]["total_ms"] for case in ids)
    oracle_post=sum(med[case,"ORACLE"]["post_ms"] for case in ids)
    oracle_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,"ORACLE"]["post_ms"]
        for case in ids)
    post_total=sum(med[case,route]["post_ms"] for case in ids)
    proposal_total=sum(med[case,route]["proposal_ms"] for case in ids)
    investment_total=sum(med[case,route]["investment_ms"] for case in ids)
    discovery=proposal_total+investment_total
    candidate_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,route]["post_ms"]
        for case in ids)
    utility=(
        candidate_savings/oracle_savings
        if oracle_savings>0 and candidate_savings>0 else None
    )
    burden=discovery/candidate_savings if candidate_savings>0 else None
    complete=(discovery+post_total)/direct_total if direct_total>0 else None
    passed=bool(
        reference_ok and capability
        and utility is not None and utility>=protocol()["utility_floor"]
        and burden is not None and burden<=protocol()["discovery_burden_max"]
        and complete is not None and complete<1.0
    )
    return {
        "route":route,"cases":len(ids),
        "reference_capability":reference_ok,"capability":capability,
        "direct_total_ms":direct_total,"oracle_post_total_ms":oracle_post,
        "oracle_savings_ms":oracle_savings,
        "proposal_total_ms":proposal_total,
        "amortized_investment_total_ms":investment_total,
        "effective_discovery_total_ms":discovery,
        "post_total_ms":post_total,
        "candidate_pre_discovery_savings_ms":candidate_savings,
        "utility_recovery":utility,"discovery_burden":burden,
        "amortized_complete_ratio":complete,
        "fallback_free_cases":sum(
            med[case,route]["fallback_free"] for case in ids),
        "subset_accepted_cases":sum(
            med[case,route]["subset_accepted"] for case in ids),
        "expanded_cases":sum(
            bool(med[case,route]["expanded"]) for case in ids),
        "expanded_accepted_cases":sum(
            bool(med[case,route]["expanded_accepted"]) for case in ids),
        "passed":passed,
    }


def summarize(records,sources):
    if len(sources)!=protocol()["source_views"]:
        raise ValueError("v102 source count drift")
    expected={
        (s["id"],route,repeat)
        for s in sources for route in ROUTES for repeat in (-1,0,1,2)
    }
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("v102 evaluation coverage drift")
    for r in records:
        if (type(r["accepted"]) is not bool
                or not math.isfinite(r["total_ms"])
                or not math.isfinite(r["proposal_ms"])
                or not math.isfinite(r["post_ms"])
                or r["total_ms"]<=0):
            raise ValueError("v102 observation drift")

    groups={g:[s for s in sources if s["group"]==g] for g in GROUPS}
    if any(len(rows)!=12 for rows in groups.values()):
        raise ValueError("v102 group coverage drift")

    routes=[f"EXPAND4_s{s}" for s in SEEDS]
    overall={r:cell_metrics(records,sources,r) for r in routes}
    cells={
        r:{g:cell_metrics(records,rows,r) for g,rows in groups.items()}
        for r in routes
    }

    med={
        (s["id"],route):_medians(records,s["id"],route)
        for s in sources for route in routes
    }
    pair_map={}
    for s in sources:
        pair_map.setdefault(s["pair_id"],{})[s["surface"]]=s["id"]
    if len(pair_map)!=24 or any(set(v)!={False,True} for v in pair_map.values()):
        raise ValueError("v102 pair coverage drift")

    invariance={}
    for route in routes:
        exact=sum(
            med[views[False],route]["top2"]==med[views[True],route]["top2"]
            for views in pair_map.values()
        )
        invariance[route]={"exact_pairs":exact,"pairs":24}

    seed_pass={}
    for route in routes:
        required=[overall[route]]+[cells[route][g] for g in GROUPS]
        seed_pass[route]=bool(
            all(row["passed"] for row in required)
            and invariance[route]["exact_pairs"]==24
        )

    reference_ok=all(
        overall[r]["reference_capability"] for r in routes
    ) and all(
        cells[r][g]["reference_capability"] for r in routes for g in GROUPS
    )
    if not reference_ok:
        decision="Q34_EXPAND4_FRESH_REFERENCE_CAPABILITY_UNREACHED"
        advance=False
    elif all(seed_pass.values()):
        decision="Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
        advance=True
    else:
        decision="Q34_EXPAND4_FRESH_HOLDOUT_FAIL_NO_Q5"
        advance=False

    return {
        "decision":decision,
        "advance_q5":advance,
        "lp_q34_mechanism_pass":advance,
        "seed_pass":seed_pass,
        "overall":overall,
        "groups":cells,
        "paired_top2_invariance":invariance,
        "fresh_views":48,
        "development_tuning_on_holdout":False,
        "v098_holdout_access":False,
        "global_q3":"OPEN","global_q4":"OPEN",
    }


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v102 evaluation head required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    env=environment()
    if env!=protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"v102 evaluation runtime drift: {env!r}")

    source_manifest,source_report=load_registered(SOURCE_MANIFEST)
    sources=source_report["sources"]
    source_by_id={s["id"]:s for s in sources}
    raws={s["id"]:raw_source(s) for s in sources}

    authority,models,training=authority_and_models()
    authority_manifest=json.loads(Path(AUTHORITY_MANIFEST).read_text())
    report={
        "protocol":protocol(),"environment":env,"frozen_head":frozen_head,
        "torch_threads":{
            "intraop":torch.get_num_threads(),
            "interop":torch.get_num_interop_threads(),
        },
        "source_archive_identity":{
            "frozen_head":source_manifest["frozen_head"],
            "gzip_sha256":source_manifest["gzip_sha256"],
            "json_sha256":source_manifest["json_sha256"],
        },
        "authority_archive_identity":{
            "frozen_head":authority_manifest["frozen_head"],
            "gzip_sha256":authority_manifest["gzip_sha256"],
            "json_sha256":authority_manifest["json_sha256"],
            "decision":authority_manifest["decision"],
        },
        "training_identity":training,
        "records":[],"stage":"running",
    }

    with threadpool_limits(1):
        report["threadpools"]=threadpool_info()
        if (not report["threadpools"]
                or any(p["num_threads"]!=1 for p in report["threadpools"])):
            raise RuntimeError("v102 evaluation threadpool drift")
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                source=source_by_id[case_id]
                raw=raws[case_id]
                if route=="DIRECT":
                    row=observe_reference(raw,route)
                elif route=="ORACLE":
                    row=observe_reference(raw,route,source["label"]["indices"])
                else:
                    row=observe_candidate(raw,route,models,training)
                report["records"].append({
                    "case_id":case_id,"pair_id":source["pair_id"],
                    "group":source["group"],"surface":source["surface"],
                    "route":route,"repeat":repeat,**row,
                })
            print(f"V102_REPEAT {repeat} {len(report['records'])}",flush=True)

    report["summary"]=summarize(report["records"],sources)
    report["stage"]="completed"
    return report


def validate_report(report):
    if report["protocol"]!=protocol() or report["stage"]!="completed":
        raise ValueError("v102 evaluation protocol/stage drift")
    if report["environment"]!=protocol()["runtime"]:
        raise ValueError("v102 evaluation environment drift")
    if report["torch_threads"]!={"intraop":1,"interop":1}:
        raise ValueError("v102 torch thread drift")
    if (not report["threadpools"]
            or any(p["num_threads"]!=1 for p in report["threadpools"])):
        raise ValueError("v102 numerical threadpool drift")

    source_manifest,source_report=load_registered(SOURCE_MANIFEST)
    expected_source={
        "frozen_head":source_manifest["frozen_head"],
        "gzip_sha256":source_manifest["gzip_sha256"],
        "json_sha256":source_manifest["json_sha256"],
    }
    if report["source_archive_identity"]!=expected_source:
        raise ValueError("v102 source archive identity drift")

    authority_manifest=json.loads(Path(AUTHORITY_MANIFEST).read_text())
    expected_authority={
        "frozen_head":authority_manifest["frozen_head"],
        "gzip_sha256":authority_manifest["gzip_sha256"],
        "json_sha256":authority_manifest["json_sha256"],
        "decision":authority_manifest["decision"],
    }
    if report["authority_archive_identity"]!=expected_authority:
        raise ValueError("v102 authority archive identity drift")

    authority,_,training=authority_and_models()
    if report["training_identity"]!=training:
        raise ValueError("v102 frozen training identity drift")

    sources=source_report["sources"]
    raws={s["id"]:raw_source(s) for s in sources}
    for r in report["records"]:
        raw=raws[r["case_id"]]
        expected=0.0
        if r["route"].startswith("EXPAND4_s"):
            seed=int(r["route"].rsplit("s",1)[1])
            expected=investment_per_query(training,seed)
        if abs(r["amortized_investment_ms"]-expected)>1e-12:
            raise ValueError("v102 investment attribution drift")
        if r["accepted"] and (
            r["witness"] is None or not verify_standard_form_certificate(
                **raw,**r["witness"])["accepted"]
        ):
            raise ValueError("v102 accepted witness drift")

    if report["summary"]!=summarize(report["records"],sources):
        raise ValueError("v102 summary drift")


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v102 fresh Q34 result already exists")
    validate_report(report)
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.q34-expand4-fresh-eval-v102.archive.v1",
        "file":output.name,"frozen_head":report["frozen_head"],"rerun":False,
        "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),"json_sha256":hashlib.sha256(raw).hexdigest(),
        "decision":report["summary"]["decision"],
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
    m=write_first(report,args.output_gzip,args.manifest)
    print("V102_FRESH_SUMMARY="+json.dumps(
        m["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V102_FRESH_ARCHIVE="+json.dumps(
        {k:v for k,v in m.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
