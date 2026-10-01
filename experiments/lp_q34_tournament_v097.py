"""One-shot v0.0.97 Q34 support-system tournament.

The development protocol is frozen in docs/experiments/v0.0.97-preregistration.md.
This runner never fits a model and never loads v0.0.88 final sources.
"""
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
from threadpoolctl import threadpool_limits

from experiments.lp_input_compaction_v094 import features
from experiments.lp_shortlist_screen_v089 import raw_source, restore_models
from experiments.lp_state_models_v087 import tensor_input
from neumann1 import lp_model_admission_v087 as admission
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_q34_support_v097 import (
    adaptive_support_checked,
    restricted_original_checked,
    support_with_fallback_checked,
)

SEEDS=(87001,87002)
ROUTES=(
    "DIRECT","ORACLE","A_DETERMINISTIC",
    "B_POINT_s87001","B_POINT_s87002",
    "C_FULL_s87001","C_FULL_s87002",
    "D_ADAPTIVE_s87001","D_ADAPTIVE_s87002",
)
CANDIDATES=ROUTES[2:]


def protocol():
    return {
        "schema":"neumann.q34-support-tournament-v097.v1",
        "runtime":admission.RUNTIME,
        "source_manifest":"docs/experiments/results/v088_completed.manifest.json",
        "source_slice":"opened_train_first_16",
        "cases":16,
        "routes":list(ROUTES),
        "seeds":list(SEEDS),
        "warmups":1,
        "repeats":3,
        "order_seed":97991,
        "budget_s":5.0,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "adaptive_factors":[1,2,4],
        "new_fitting":False,
        "checkpoint_selection":False,
        "final_evaluation":False,
        "energy_claim":False,
        "memory_claim":False,
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


def learned_investment_per_query(training, training_setup_ms, route):
    if route.startswith(("B_POINT_s","D_ADAPTIVE_s")):
        seed=int(route.rsplit("s",1)[1])
        key=f"point16_s{seed}"
    elif route.startswith("C_FULL_s"):
        seed=int(route.rsplit("s",1)[1])
        key=f"full16_s{seed}"
    else:
        return 0.0
    return (float(training_setup_ms)+float(training[key]["fit_ms"])) / protocol()["amortization_queries"]


def proposal(raw, route, models):
    """Target-free proposal authority. Hidden labels cannot enter this function."""
    started=perf_counter_ns()
    D,rows,cols=features(raw)
    m,n=D.shape
    if route=="A_DETERMINISTIC":
        ranking=np.argsort(cols[:,1],kind="stable").tolist()
        payload={"indices":ranking[:min(n,2*m)]}
    else:
        tensors=tensor_input(D,rows,cols)
        if route.startswith(("B_POINT_s","D_ADAPTIVE_s")):
            seed=int(route.rsplit("s",1)[1])
            model=models[f"point16_s{seed}"]
            with torch.inference_mode():
                scores=model.head(model.cols(tensors[2])).squeeze(1)
            if not torch.isfinite(scores).all():
                raise ValueError("nonfinite point scores")
            ranking=torch.argsort(scores,descending=True,stable=True).tolist()
            payload={"ranking":ranking} if route.startswith("D_ADAPTIVE_s") else {
                "indices":ranking[:min(n,2*m)]
            }
        elif route.startswith("C_FULL_s"):
            seed=int(route.rsplit("s",1)[1])
            model=models[f"full16_s{seed}"]
            with torch.inference_mode():
                out=model(*tensors)
            scores=out["scores"]
            if not torch.isfinite(scores).all():
                raise ValueError("nonfinite full-information scores")
            ranking=torch.argsort(scores,descending=True,stable=True).tolist()
            payload={"indices":ranking[:min(n,2*m)]}
        else:
            raise ValueError(f"not a candidate route: {route}")
    return {**payload,"proposal_ms":(perf_counter_ns()-started)/1e6}


def observe_reference(raw, route, oracle_indices=None):
    """Reference routes are separate so candidate code has no label/oracle parameter."""
    budget=protocol()["budget_s"]
    if route=="DIRECT":
        result=solve_native_checked(**raw,cold_fallback=False,budget_s=budget)
        witness=result["attempts"][-1]["witness"] if result["accepted"] else None
        return {
            "accepted":bool(result["accepted"]),"proposal_ms":0.0,
            "post_ms":float(result["total_ms"]),"total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,"fallback_used":False,
            "subset_accepted":False,"proposal":None,"execution":result,"witness":witness,
        }
    if route=="ORACLE":
        if oracle_indices is None:
            raise ValueError("oracle support required")
        basis=list(oracle_indices)
        result=restricted_original_checked(**raw,indices=basis,budget_s=budget)
        return {
            "accepted":bool(result["accepted"]),"proposal_ms":0.0,
            "post_ms":float(result["total_ms"]),"total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,"fallback_used":False,
            "subset_accepted":bool(result["accepted"]),
            "proposal":{"indices":basis,"oracle":True},"execution":result,
            "witness":result["witness"],
        }
    raise ValueError("reference route required")


def observe_candidate(raw, route, models, training, training_setup_ms):
    """Candidate execution has no hidden-label input and shares one original verifier."""
    budget=protocol()["budget_s"]
    investment=learned_investment_per_query(training,training_setup_ms,route)
    p=proposal(raw,route,models)
    proposal_ms=float(p["proposal_ms"])
    remaining=budget-proposal_ms/1000.0
    execution=None
    if remaining>0:
        if route.startswith("D_ADAPTIVE_s"):
            execution=adaptive_support_checked(
                **raw,ranking=p["ranking"],budget_s=remaining,
                factors=tuple(protocol()["adaptive_factors"]))
        else:
            execution=support_with_fallback_checked(
                **raw,indices=p["indices"],budget_s=remaining)
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=proposal_ms+post_ms
    accepted=bool(execution and execution["accepted"] and total_ms<=budget*1000.0)
    if route.startswith("D_ADAPTIVE_s"):
        subset_accepted=bool(execution and any(
            a["result"]["accepted"] for a in execution["attempts"]))
    else:
        subset_accepted=bool(execution and execution["subset_accepted"])
    return {
        "accepted":accepted,"proposal_ms":proposal_ms,"post_ms":post_ms,
        "total_ms":total_ms,"amortized_investment_ms":investment,
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":subset_accepted,
        "proposal":{k:v for k,v in p.items() if k!="proposal_ms"},
        "execution":execution,
        "witness":execution["witness"] if execution else None,
    }


def _medians(records,case_id,route):
    rows=[r for r in records if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("timed repeat coverage drift")
    investments={r["amortized_investment_ms"] for r in rows}
    if len(investments)!=1:
        raise ValueError("investment drift across repeats")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investments)),
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_free":all(not r["fallback_used"] for r in rows),
        "subset_accepted":all(r["subset_accepted"] for r in rows),
    }


def summarize(records,sources):
    ids=[s["id"] for s in sources]
    expected={(case,route,repeat) for case in ids for route in ROUTES for repeat in (-1,0,1,2)}
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("tournament coverage drift")
    for r in records:
        if (type(r["accepted"]) is not bool or not math.isfinite(r["total_ms"])
                or not math.isfinite(r["proposal_ms"]) or not math.isfinite(r["post_ms"])
                or r["total_ms"]<=0 or r["proposal_ms"]<0 or r["post_ms"]<0):
            raise ValueError("invalid observation cost")
        if r["total_ms"]+1e-6<r["proposal_ms"]+r["post_ms"]:
            raise ValueError("complete cost ledger drift")

    med={(case,route):_medians(records,case,route) for case in ids for route in ROUTES}
    reference_ok=all(
        med[case,"DIRECT"]["all_accepted"] and med[case,"ORACLE"]["all_accepted"]
        for case in ids)
    direct_total=sum(med[case,"DIRECT"]["total_ms"] for case in ids)
    oracle_post=sum(med[case,"ORACLE"]["post_ms"] for case in ids)
    oracle_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,"ORACLE"]["post_ms"] for case in ids)

    route_metrics={}
    for route in CANDIDATES:
        capability=all(med[case,route]["all_accepted"] for case in ids)
        post_total=sum(med[case,route]["post_ms"] for case in ids)
        proposal_total=sum(med[case,route]["proposal_ms"] for case in ids)
        investment_total=sum(med[case,route]["investment_ms"] for case in ids)
        discovery_total=proposal_total+investment_total
        candidate_savings=sum(
            med[case,"DIRECT"]["total_ms"]-med[case,route]["post_ms"] for case in ids)
        utility=(candidate_savings/oracle_savings
                 if oracle_savings>0 and candidate_savings>0 else None)
        burden=(discovery_total/candidate_savings if candidate_savings>0 else None)
        online=(proposal_total+post_total)/direct_total if direct_total>0 else None
        complete=(discovery_total+post_total)/direct_total if direct_total>0 else None
        passed=bool(
            reference_ok and capability and utility is not None and burden is not None
            and utility>=protocol()["utility_floor"]
            and burden<=protocol()["discovery_burden_max"]
            and complete is not None and complete<1.0)
        route_metrics[route]={
            "capability":capability,
            "proposal_total_ms":proposal_total,
            "amortized_investment_total_ms":investment_total,
            "effective_discovery_total_ms":discovery_total,
            "post_total_ms":post_total,
            "candidate_pre_discovery_savings_ms":candidate_savings,
            "utility_recovery":utility,
            "discovery_burden":burden,
            "online_complete_ratio":online,
            "amortized_complete_ratio":complete,
            "fallback_free_cases":sum(med[case,route]["fallback_free"] for case in ids),
            "subset_accepted_cases":sum(med[case,route]["subset_accepted"] for case in ids),
            "passed":passed,
        }

    family_routes={
        "A_DETERMINISTIC":["A_DETERMINISTIC"],
        "B_POINT":[f"B_POINT_s{s}" for s in SEEDS],
        "C_FULL":[f"C_FULL_s{s}" for s in SEEDS],
        "D_ADAPTIVE":[f"D_ADAPTIVE_s{s}" for s in SEEDS],
    }
    families={}
    for family,routes in family_routes.items():
        rows=[route_metrics[r] for r in routes]
        utilities=[r["utility_recovery"] for r in rows]
        burdens=[r["discovery_burden"] for r in rows]
        families[family]={
            "routes":routes,
            "capability":all(r["capability"] for r in rows),
            "utility_recovery":min(utilities) if all(v is not None for v in utilities) else None,
            "discovery_burden":max(burdens) if all(v is not None for v in burdens) else None,
            "amortized_complete_ratio":max(r["amortized_complete_ratio"] for r in rows),
            "fallback_free_cases":min(r["fallback_free_cases"] for r in rows),
            "passed":all(r["passed"] for r in rows),
        }

    for name,row in families.items():
        dominated=[]
        if row["capability"] and row["utility_recovery"] is not None and row["discovery_burden"] is not None:
            for other,c in families.items():
                if other==name or not c["capability"] or c["utility_recovery"] is None or c["discovery_burden"] is None:
                    continue
                no_worse=(c["utility_recovery"]>=row["utility_recovery"]
                          and c["amortized_complete_ratio"]<=row["amortized_complete_ratio"]
                          and c["discovery_burden"]<=row["discovery_burden"])
                strict=(c["utility_recovery"]>row["utility_recovery"]
                        or c["amortized_complete_ratio"]<row["amortized_complete_ratio"]
                        or c["discovery_burden"]<row["discovery_burden"])
                if no_worse and strict:
                    dominated.append(other)
        row["dominated_by"]=dominated
        row["pareto_survivor"]=not dominated

    survivors=[name for name,row in families.items() if row["passed"] and row["pareto_survivor"]]
    if not reference_ok:
        decision="REFERENCE_CAPABILITY_UNREACHED"
    elif survivors:
        decision="ADMIT_FRESH_Q34_HOLDOUT"
    else:
        decision="NO_FROZEN_FAMILY_Q34_CANDIDATE"
    return {
        "decision":decision,
        "reference_capability":reference_ok,
        "direct_total_ms":direct_total,
        "oracle_post_total_ms":oracle_post,
        "oracle_savings_ms":oracle_savings,
        "oracle_post_ratio":oracle_post/direct_total if direct_total>0 else None,
        "routes":route_metrics,
        "families":families,
        "pareto_q34_survivors":survivors,
        "development_only":True,
        "q34_global_pass":False,
        "global_q3":"OPEN",
        "global_q4":"OPEN",
    }


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character frozen git head required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    env=environment()
    if env!=protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"runtime drift: {env!r}")

    study=load_study(protocol()["source_manifest"])
    model_start=perf_counter_ns()
    models=restore_models(study["training"])
    model_loading_ms=(perf_counter_ns()-model_start)/1e6
    source_start=perf_counter_ns()
    sources=study["train_sources"][:protocol()["cases"]]
    raws={s["id"]:raw_source(s) for s in sources}
    source_loading_ms=(perf_counter_ns()-source_start)/1e6
    source_by_id={s["id"]:s for s in sources}

    report={
        "protocol":protocol(),"environment":env,"frozen_head":frozen_head,
        "source_ids":[{"id":s["id"],"sha256":s["sha256"]} for s in sources],
        "training_setup_ms":study["training_setup_ms"],
        "training_identity":{k:v["weights_sha256"] for k,v in study["training"].items()},
        "model_loading_ms":model_loading_ms,"source_loading_ms":source_loading_ms,
        "records":[],"stage":"running",
    }
    with threadpool_limits(1):
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                raw=raws[case_id]
                if route=="ORACLE":
                    row=observe_reference(raw,route,source_by_id[case_id]["label"]["indices"])
                elif route=="DIRECT":
                    row=observe_reference(raw,route)
                else:
                    row=observe_candidate(
                        raw,route,models,study["training"],study["training_setup_ms"])
                report["records"].append({
                    "case_id":case_id,"route":route,"repeat":repeat,**row})
            print(f"V097_REPEAT {repeat} {len(report['records'])}",flush=True)
    report["summary"]=summarize(report["records"],sources)
    report["stage"]="completed"
    return report


def validate_report(report):
    if report["protocol"]!=protocol() or report["stage"]!="completed":
        raise ValueError("protocol/stage drift")
    if report["environment"]!=protocol()["runtime"]:
        raise ValueError("environment drift")
    study=load_study(protocol()["source_manifest"])
    sources=study["train_sources"][:protocol()["cases"]]
    identities=[{"id":s["id"],"sha256":s["sha256"]} for s in sources]
    if report["source_ids"]!=identities:
        raise ValueError("source identity drift")
    if report["training_setup_ms"]!=study["training_setup_ms"]:
        raise ValueError("training setup drift")
    if report["training_identity"]!={k:v["weights_sha256"] for k,v in study["training"].items()}:
        raise ValueError("checkpoint identity drift")
    raws={s["id"]:raw_source(s) for s in sources}
    source_by_id={s["id"]:s for s in sources}
    for r in report["records"]:
        raw=raws[r["case_id"]]
        expected=learned_investment_per_query(
            study["training"],study["training_setup_ms"],r["route"])
        if abs(r["amortized_investment_ms"]-expected)>1e-12:
            raise ValueError("investment drift")
        if r["accepted"]:
            if r["witness"] is None or not verify_standard_form_certificate(
                    **raw,**r["witness"])["accepted"]:
                raise ValueError("accepted original witness drift")
        if r["route"]=="ORACLE":
            basis=list(source_by_id[r["case_id"]]["label"]["indices"])
            if r["proposal"]!={"indices":basis,"oracle":True}:
                raise ValueError("oracle support drift")
    if report["summary"]!=summarize(report["records"],sources):
        raise ValueError("summary drift")


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("first tournament output already exists")
    validate_report(report)
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.q34-support-tournament-v097.archive.v1",
        "file":output.name,"rerun":False,"frozen_head":report["frozen_head"],
        "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),"json_sha256":hashlib.sha256(raw).hexdigest(),
        "decision":report["summary"]["decision"],"summary":report["summary"],
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
    print("V097_FIRST_SUMMARY="+json.dumps(
        manifest["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V097_FIRST_ARCHIVE="+json.dumps(
        {k:v for k,v in manifest.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
