"""v0.0.98 fresh Q34 holdout evaluation for frozen B_POINT only."""
from __future__ import annotations

import argparse
import base64
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

from experiments.lp_q34_holdout_register_v098 import load_registered
from experiments.lp_q34_tournament_v097 import proposal
from experiments.lp_shortlist_screen_v089 import raw_source
from experiments.lp_state_models_v087 import roster
from experiments.lp_model_study_v088 import pack_weights
from neumann1 import lp_model_admission_v087 as admission
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_q34_support_v097 import restricted_original_checked, support_with_fallback_checked

SEEDS=(87001,87002)
ROUTES=("DIRECT","ORACLE","B_POINT_s87001","B_POINT_s87002")
GROUPS=("iid64","size_surface_shift128")
SOURCE_MANIFEST="docs/experiments/results/v098_fresh_holdout_sources.manifest.json"


def protocol():
    return {
        "schema":"neumann.q34-fresh-holdout-eval-v098.v1",
        "runtime":admission.RUNTIME,
        "source_manifest":SOURCE_MANIFEST,
        "source_cases":24,
        "groups":list(GROUPS),
        "routes":list(ROUTES),
        "seeds":list(SEEDS),
        "warmups":1,
        "repeats":3,
        "order_seed":98991,
        "budget_s":5.0,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "new_fitting":False,
        "checkpoint_selection":False,
        "support_factor":2,
        "final_q34_holdout":True,
        "global_q3":"OPEN",
        "global_q4":"OPEN",
    }


def environment():
    import scipy
    import highspy
    return {
        "python":list(sys.version_info[:2]),
        "numpy":np.__version__,
        "scipy":scipy.__version__,
        "torch":torch.__version__,
        "highspy":highspy.Highs().version(),
    }



def restore_point_models(training):
    """Restore only the two frozen Pareto-survivor checkpoints."""
    models={}
    for seed in SEEDS:
        key=f"point16_s{seed}"
        model=roster(seed)["point16"]
        state={
            k:torch.tensor(np.frombuffer(
                base64.b64decode(v["base64"],validate=True),dtype="<f4"
            ).reshape(v["shape"]).copy())
            for k,v in training[key]["weights"].items()
        }
        model.load_state_dict(state,strict=True)
        if pack_weights(model)[1]!=training[key]["weights_sha256"]:
            raise ValueError("fresh point checkpoint restore drift")
        models[key]=model.eval()
    return models


def investment_per_query(training,setup_ms,route):
    if not route.startswith("B_POINT_s"):
        return 0.0
    seed=int(route.rsplit("s",1)[1])
    key=f"point16_s{seed}"
    return (float(setup_ms)+float(training[key]["fit_ms"])) / protocol()["amortization_queries"]


def observe_reference(raw,route,oracle_indices=None):
    budget=protocol()["budget_s"]
    if route=="DIRECT":
        result=solve_native_checked(**raw,cold_fallback=False,budget_s=budget)
        witness=result["attempts"][-1]["witness"] if result["accepted"] else None
        return {
            "accepted":bool(result["accepted"]),"proposal_ms":0.0,
            "post_ms":float(result["total_ms"]),"total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,"fallback_used":False,
            "subset_accepted":False,"witness":witness,"execution":result,
        }
    if route=="ORACLE":
        if oracle_indices is None:
            raise ValueError("oracle support required")
        result=restricted_original_checked(
            **raw,indices=list(oracle_indices),budget_s=budget)
        return {
            "accepted":bool(result["accepted"]),"proposal_ms":0.0,
            "post_ms":float(result["total_ms"]),"total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,"fallback_used":False,
            "subset_accepted":bool(result["accepted"]),"witness":result["witness"],
            "execution":result,
        }
    raise ValueError("reference route required")


def observe_candidate(raw,route,models,training,setup_ms):
    if not route.startswith("B_POINT_s"):
        raise ValueError("frozen B_POINT route required")
    budget=protocol()["budget_s"]
    p=proposal(raw,route,models)
    proposal_ms=float(p["proposal_ms"])
    left=budget-proposal_ms/1000.0
    execution=None
    if left>0:
        execution=support_with_fallback_checked(
            **raw,indices=p["indices"],budget_s=left)
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=proposal_ms+post_ms
    accepted=bool(execution and execution["accepted"] and total_ms<=budget*1000.0)
    return {
        "accepted":accepted,"proposal_ms":proposal_ms,"post_ms":post_ms,
        "total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(training,setup_ms,route),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":bool(execution and execution["subset_accepted"]),
        "witness":execution["witness"] if execution else None,
        "execution":execution,
    }


def _medians(records,case_id,route):
    rows=[r for r in records
          if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("fresh timed repeat coverage drift")
    investments={r["amortized_investment_ms"] for r in rows}
    if len(investments)!=1:
        raise ValueError("fresh investment drift")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investments)),
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
    direct_total=sum(med[case,"DIRECT"]["total_ms"] for case in ids)
    oracle_post=sum(med[case,"ORACLE"]["post_ms"] for case in ids)
    oracle_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,"ORACLE"]["post_ms"] for case in ids)
    post_total=sum(med[case,route]["post_ms"] for case in ids)
    proposal_total=sum(med[case,route]["proposal_ms"] for case in ids)
    invest_total=sum(med[case,route]["investment_ms"] for case in ids)
    discovery_total=proposal_total+invest_total
    candidate_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,route]["post_ms"] for case in ids)
    utility=(candidate_savings/oracle_savings
             if oracle_savings>0 and candidate_savings>0 else None)
    burden=(discovery_total/candidate_savings if candidate_savings>0 else None)
    complete=(discovery_total+post_total)/direct_total if direct_total>0 else None
    passed=bool(
        reference_ok and capability and utility is not None and burden is not None
        and utility>=protocol()["utility_floor"]
        and burden<=protocol()["discovery_burden_max"]
        and complete is not None and complete<1.0)
    return {
        "route":route,"cases":len(ids),"reference_capability":reference_ok,
        "capability":capability,"direct_total_ms":direct_total,
        "oracle_post_total_ms":oracle_post,"oracle_savings_ms":oracle_savings,
        "proposal_total_ms":proposal_total,
        "amortized_investment_total_ms":invest_total,
        "effective_discovery_total_ms":discovery_total,
        "post_total_ms":post_total,
        "candidate_pre_discovery_savings_ms":candidate_savings,
        "utility_recovery":utility,"discovery_burden":burden,
        "amortized_complete_ratio":complete,
        "fallback_free_cases":sum(med[case,route]["fallback_free"] for case in ids),
        "subset_accepted_cases":sum(med[case,route]["subset_accepted"] for case in ids),
        "passed":passed,
    }


def summarize(records,sources):
    if len(sources)!=24:
        raise ValueError("fresh source count drift")
    expected={(s["id"],route,repeat)
              for s in sources for route in ROUTES for repeat in (-1,0,1,2)}
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("fresh evaluation coverage drift")
    for r in records:
        if (type(r["accepted"]) is not bool or not math.isfinite(r["total_ms"])
                or not math.isfinite(r["proposal_ms"]) or not math.isfinite(r["post_ms"])
                or r["total_ms"]<=0):
            raise ValueError("fresh observation drift")
    groups={g:[s for s in sources if s["group"]==g] for g in GROUPS}
    if any(len(v)!=12 for v in groups.values()):
        raise ValueError("fresh group coverage drift")

    cells={}
    route_overall={}
    for seed in SEEDS:
        route=f"B_POINT_s{seed}"
        route_overall[route]=cell_metrics(records,sources,route)
        cells[route]={g:cell_metrics(records,group,route) for g,group in groups.items()}

    reference_ok=all(
        route_overall[r]["reference_capability"] for r in route_overall)
    all_cells=[
        route_overall[r]["passed"] for r in route_overall
    ]+[
        cells[r][g]["passed"] for r in cells for g in GROUPS
    ]
    if not reference_ok:
        decision="Q34_FRESH_REFERENCE_CAPABILITY_UNREACHED"
        advance=False
    elif all(all_cells):
        decision="Q34_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
        advance=True
    else:
        decision="Q34_FRESH_HOLDOUT_FAIL_NO_Q5"
        advance=False
    return {
        "decision":decision,"advance_q5":advance,
        "lp_q34_mechanism_pass":advance,
        "overall":route_overall,"groups":cells,
        "fresh_cases":24,"development_tuning_on_holdout":False,
        "global_q3":"OPEN","global_q4":"OPEN",
    }


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character evaluation head required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    env=environment()
    if env!=protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"fresh evaluation runtime drift: {env!r}")

    source_manifest,source_report=load_registered(protocol()["source_manifest"])
    sources=source_report["sources"]
    source_by_id={s["id"]:s for s in sources}
    raws={s["id"]:raw_source(s) for s in sources}

    retained=load_study("docs/experiments/results/v088_completed.manifest.json")
    load_started=perf_counter_ns()
    models=restore_point_models(retained["training"])
    model_loading_ms=(perf_counter_ns()-load_started)/1e6
    point_identity={
        f"point16_s{s}":retained["training"][f"point16_s{s}"]["weights_sha256"]
        for s in SEEDS
    }
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
        "training_setup_ms":retained["training_setup_ms"],
        "point_checkpoint_identity":point_identity,
        "model_loading_ms":model_loading_ms,
        "records":[],"stage":"running",
    }

    with threadpool_limits(1):
        report["threadpools"]=threadpool_info()
        if (not report["threadpools"]
                or any(p["num_threads"]!=1 for p in report["threadpools"])):
            raise RuntimeError("fresh evaluation threadpool drift")
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                raw=raws[case_id]
                if route=="ORACLE":
                    row=observe_reference(
                        raw,route,source_by_id[case_id]["label"]["indices"])
                elif route=="DIRECT":
                    row=observe_reference(raw,route)
                else:
                    row=observe_candidate(
                        raw,route,models,retained["training"],
                        retained["training_setup_ms"])
                report["records"].append({
                    "case_id":case_id,"group":source_by_id[case_id]["group"],
                    "route":route,"repeat":repeat,**row,
                })
            print(f"V098_REPEAT {repeat} {len(report['records'])}",flush=True)
    report["summary"]=summarize(report["records"],sources)
    report["stage"]="completed"
    return report


def validate_report(report):
    if report["protocol"]!=protocol() or report["stage"]!="completed":
        raise ValueError("fresh evaluation protocol/stage drift")
    if report["environment"]!=protocol()["runtime"]:
        raise ValueError("fresh evaluation environment drift")
    if report["torch_threads"]!={"intraop":1,"interop":1}:
        raise ValueError("fresh torch thread drift")
    if (not report["threadpools"]
            or any(p["num_threads"]!=1 for p in report["threadpools"])):
        raise ValueError("fresh numerical threadpool drift")
    source_manifest,source_report=load_registered(protocol()["source_manifest"])
    expected_source={
        "frozen_head":source_manifest["frozen_head"],
        "gzip_sha256":source_manifest["gzip_sha256"],
        "json_sha256":source_manifest["json_sha256"],
    }
    if report["source_archive_identity"]!=expected_source:
        raise ValueError("fresh source archive identity drift")
    sources=source_report["sources"]
    raws={s["id"]:raw_source(s) for s in sources}

    retained=load_study("docs/experiments/results/v088_completed.manifest.json")
    expected_points={
        f"point16_s{s}":retained["training"][f"point16_s{s}"]["weights_sha256"]
        for s in SEEDS
    }
    if report["point_checkpoint_identity"]!=expected_points:
        raise ValueError("fresh point checkpoint identity drift")
    if report["training_setup_ms"]!=retained["training_setup_ms"]:
        raise ValueError("fresh training setup drift")

    for r in report["records"]:
        raw=raws[r["case_id"]]
        expected=investment_per_query(
            retained["training"],retained["training_setup_ms"],r["route"])
        if abs(r["amortized_investment_ms"]-expected)>1e-12:
            raise ValueError("fresh investment attribution drift")
        if r["accepted"] and (
            r["witness"] is None or not verify_standard_form_certificate(
                **raw,**r["witness"])["accepted"]):
            raise ValueError("fresh accepted witness drift")
    if report["summary"]!=summarize(report["records"],sources):
        raise ValueError("fresh summary drift")


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("fresh Q34 result already exists")
    validate_report(report)
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.q34-fresh-holdout-eval-v098.archive.v1",
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
    print("V098_FRESH_SUMMARY="+json.dumps(
        m["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V098_FRESH_ARCHIVE="+json.dumps(
        {k:v for k,v in m.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
