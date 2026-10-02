"""v0.0.101 frozen quotient support-expansion tournament."""
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
from threadpoolctl import threadpool_limits

from experiments.lp_equivalence_quotient_v099 import quotient_columns
from experiments.lp_model_study_v088 import pack_weights
from experiments.lp_quotient_refit_v100 import (
    SupportMLP,
    _base_problem,
    _surface,
)
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_q34_support_v097 import (
    restricted_original_checked,
    support_with_fallback_checked,
)
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit

V100_MANIFEST="docs/experiments/results/v100_first_refit.manifest.json"
SEEDS=(100001,100002)
FAMILIES=("FIXED2","EXPAND4")
GROUPS=("m64_base","m64_surface","m128_base","m128_surface")
ROUTES=(
    "DIRECT","ORACLE",
    "FIXED2_s100001","FIXED2_s100002",
    "EXPAND4_s100001","EXPAND4_s100002",
)


def protocol():
    return {
        "schema":"neumann.frozen-support-expansion-v101.v1",
        "runtime":{**admission.RUNTIME,"scikit_learn":"1.9.1"},
        "source_checkpoint":"v100_first_refit",
        "model_seeds":list(SEEDS),
        "families":list(FAMILIES),
        "development_seed_base":101200,
        "development_base_cases":16,
        "development_views":32,
        "surface_seed_offset":200000,
        "groups":list(GROUPS),
        "routes":list(ROUTES),
        "fixed_support_factor":2,
        "expanded_support_factor":4,
        "warmups":1,
        "repeats":3,
        "order_seed":101991,
        "budget_s":5.0,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "new_fitting":False,
        "checkpoint_selection":False,
        "v098_holdout_access":False,
        "fresh_holdout":False,
        "advance_q5":False,
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


def _restore_state(model,packed):
    state={}
    for key,row in packed.items():
        raw=base64.b64decode(row["base64"],validate=True)
        array=np.frombuffer(raw,dtype="<f4").reshape(row["shape"]).copy()
        state[key]=torch.tensor(array)
    model.load_state_dict(state,strict=True)


def restore_frozen_quotient():
    report=load_first_refit(V100_MANIFEST)
    models={}
    training={}
    for seed in SEEDS:
        route=f"QUOTIENT_s{seed}"
        row=report["training"][route]
        model=SupportMLP(seed)
        _restore_state(model,row["weights"])
        model.eval()
        if pack_weights(model)[1]!=row["weights_sha256"]:
            raise ValueError("v101 quotient checkpoint identity drift")
        models[seed]=model
        training[seed]={
            "feature_setup_ms":float(row["feature_setup_ms"]),
            "fit_ms":float(row["fit_ms"]),
            "weights_sha256":row["weights_sha256"],
        }
    return models,training


def base_specs():
    return [{
        "pair_id":f"dev101_{i:02d}",
        "rows":64 if i<8 else 128,
        "condition":(1,1000)[i%2],
        "seed":protocol()["development_seed_base"]+i,
    } for i in range(protocol()["development_base_cases"])]


def development_sources():
    sources=[]
    for spec in base_specs():
        raw,basis=_base_problem(spec)
        for surface in (False,True):
            view=(
                _surface(raw,spec["seed"]+protocol()["surface_seed_offset"])
                if surface else raw
            )
            group=f"m{spec['rows']}_{'surface' if surface else 'base'}"
            label=storage.candidate_once(view,basis,"v101_dev_label")
            if not label["accepted"]:
                raise ValueError("v101 development oracle basis rejected")
            sources.append({
                **spec,
                "id":f"{spec['pair_id']}_{'surface' if surface else 'base'}",
                "group":group,
                "surface":surface,
                "raw":view,
                "basis":[int(i) for i in basis],
                "sha256":storage.input_digest(view),
            })
    if len(sources)!=protocol()["development_views"]:
        raise ValueError("v101 development source coverage drift")
    return sources


def frozen_ranking(raw,model):
    started=perf_counter_ns()
    _,cols=quotient_columns(raw)
    tensor=torch.tensor(cols,dtype=torch.float32)
    with torch.inference_mode():
        score=model(tensor)
    if not torch.isfinite(score).all():
        raise ValueError("v101 nonfinite frozen score")
    ranking=torch.argsort(score,descending=True,stable=True).tolist()
    return ranking,(perf_counter_ns()-started)/1e6


def investment_per_query(training,seed):
    row=training[seed]
    return (row["feature_setup_ms"]+row["fit_ms"]) / protocol()["amortization_queries"]


def expand4_checked(raw,ranking,budget_s):
    started=perf_counter_ns()
    m,n=raw["A"].shape

    def remaining():
        return budget_s-(perf_counter_ns()-started)/1e9

    attempts=[]
    witness=None
    accepted=False
    fallback=None
    for factor in (
        protocol()["fixed_support_factor"],
        protocol()["expanded_support_factor"],
    ):
        size=min(n,factor*m)
        left=remaining()
        if left<=0:
            break
        attempt=restricted_original_checked(
            **raw,indices=ranking[:size],budget_s=left)
        attempts.append({
            "support_factor":factor,
            "support_size":size,
            "result":attempt,
        })
        if attempt["accepted"]:
            accepted=True
            witness=attempt["witness"]
            break

    if not accepted and remaining()>0:
        fallback=solve_native_checked(
            **raw,cold_fallback=False,budget_s=remaining())
        if fallback["accepted"]:
            accepted=True
            witness=fallback["attempts"][-1]["witness"]

    total_ms=(perf_counter_ns()-started)/1e6
    return {
        "accepted":bool(accepted and total_ms<=budget_s*1000.0),
        "attempts":attempts,
        "fallback":fallback,
        "fallback_used":fallback is not None,
        "subset_accepted":bool(any(a["result"]["accepted"] for a in attempts)),
        "expanded":len(attempts)>=2,
        "expanded_accepted":bool(
            len(attempts)>=2 and attempts[1]["result"]["accepted"]),
        "witness":witness,
        "total_ms":total_ms,
    }


def observe_reference(raw,route,basis=None):
    budget=protocol()["budget_s"]
    if route=="DIRECT":
        result=solve_native_checked(
            **raw,cold_fallback=False,budget_s=budget)
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
            raise ValueError("v101 oracle basis required")
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
    raise ValueError("v101 reference route required")


def observe_candidate(raw,route,models,training):
    family,seed_text=route.rsplit("_s",1)
    seed=int(seed_text)
    if family not in FAMILIES or seed not in SEEDS:
        raise ValueError("v101 candidate route drift")
    ranking,proposal_ms=frozen_ranking(raw,models[seed])
    m,n=raw["A"].shape
    top2=ranking[:min(n,protocol()["fixed_support_factor"]*m)]
    left=protocol()["budget_s"]-proposal_ms/1000.0
    execution=None
    if left>0:
        if family=="FIXED2":
            execution=support_with_fallback_checked(
                **raw,indices=top2,budget_s=left)
            expanded=False
            expanded_accepted=False
        else:
            execution=expand4_checked(raw,ranking,left)
            expanded=bool(execution["expanded"])
            expanded_accepted=bool(execution["expanded_accepted"])
    else:
        expanded=False
        expanded_accepted=False
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=proposal_ms+post_ms
    return {
        "accepted":bool(
            execution and execution["accepted"]
            and total_ms<=protocol()["budget_s"]*1000.0),
        "proposal_ms":float(proposal_ms),
        "post_ms":post_ms,
        "total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(training,seed),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":bool(execution and execution["subset_accepted"]),
        "expanded":expanded,
        "expanded_accepted":expanded_accepted,
        "ranking":ranking,
        "top2":top2,
        "witness":execution["witness"] if execution else None,
    }


def _medians(records,case_id,route):
    rows=[
        r for r in records
        if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0
    ]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("v101 timed repeat coverage drift")
    investment={r["amortized_investment_ms"] for r in rows}
    if len(investment)!=1:
        raise ValueError("v101 investment drift")
    for field in ("ranking","top2","expanded","expanded_accepted"):
        values=[r[field] for r in rows]
        if any(v!=values[0] for v in values[1:]):
            raise ValueError(f"v101 deterministic {field} drift")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investment)),
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_free":all(not r["fallback_used"] for r in rows),
        "subset_accepted":all(r["subset_accepted"] for r in rows),
        "ranking":rows[0]["ranking"],
        "top2":rows[0]["top2"],
        "expanded":rows[0]["expanded"],
        "expanded_accepted":rows[0]["expanded_accepted"],
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
        if oracle_savings>0 and candidate_savings>0 else None)
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
    expected={
        (s["id"],route,repeat)
        for s in sources for route in ROUTES for repeat in (-1,0,1,2)
    }
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("v101 evaluation coverage drift")
    groups={g:[s for s in sources if s["group"]==g] for g in GROUPS}
    if any(len(v)!=8 for v in groups.values()):
        raise ValueError("v101 group coverage drift")

    candidates=ROUTES[2:]
    overall={r:cell_metrics(records,sources,r) for r in candidates}
    cells={
        r:{g:cell_metrics(records,rows,r) for g,rows in groups.items()}
        for r in candidates
    }

    med={
        (s["id"],route):_medians(records,s["id"],route)
        for s in sources for route in candidates
    }
    pair_map={s["pair_id"]:{} for s in sources}
    for s in sources:
        pair_map[s["pair_id"]][s["surface"]]=s["id"]
    invariance={}
    for route in candidates:
        exact=0
        for views in pair_map.values():
            if set(views)!={False,True}:
                raise ValueError("v101 pair coverage drift")
            if med[views[False],route]["top2"]==med[views[True],route]["top2"]:
                exact+=1
        invariance[route]={"exact_pairs":exact,"pairs":len(pair_map)}

    family_summary={}
    for family in FAMILIES:
        routes=[f"{family}_s{s}" for s in SEEDS]
        required=[]
        for route in routes:
            required.append(overall[route])
            required.extend(cells[route][g] for g in GROUPS)
        passed=all(x["passed"] for x in required) and all(
            invariance[r]["exact_pairs"]==16 for r in routes)
        family_summary[family]={
            "routes":routes,
            "passed":passed,
            "minimum_utility_recovery":min(
                x["utility_recovery"] for x in required),
            "maximum_discovery_burden":max(
                x["discovery_burden"] for x in required),
            "maximum_amortized_complete_ratio":max(
                x["amortized_complete_ratio"] for x in required),
            "minimum_fallback_free_cases":min(
                x["fallback_free_cases"] for x in required),
        }

    for family,row in family_summary.items():
        dominated=[]
        if row["passed"]:
            for other,candidate in family_summary.items():
                if other==family or not candidate["passed"]:
                    continue
                no_worse=(
                    candidate["minimum_utility_recovery"]>=row["minimum_utility_recovery"]
                    and candidate["maximum_discovery_burden"]<=row["maximum_discovery_burden"]
                    and candidate["maximum_amortized_complete_ratio"]<=row["maximum_amortized_complete_ratio"]
                )
                strict=(
                    candidate["minimum_utility_recovery"]>row["minimum_utility_recovery"]
                    or candidate["maximum_discovery_burden"]<row["maximum_discovery_burden"]
                    or candidate["maximum_amortized_complete_ratio"]<row["maximum_amortized_complete_ratio"]
                )
                if no_worse and strict:
                    dominated.append(other)
        row["dominated_by"]=dominated
        row["pareto_survivor"]=bool(row["passed"] and not dominated)

    survivors=[
        f for f,row in family_summary.items() if row["pareto_survivor"]
    ]
    decision=(
        "ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_FROZEN_SUPPORT_SYSTEM"
        if survivors else
        "STOP_FIXED_POINT_SUPPORT_FAMILY"
    )
    return {
        "decision":decision,
        "pareto_survivors":survivors,
        "families":family_summary,
        "overall":overall,
        "groups":cells,
        "paired_top2_invariance":invariance,
        "new_fitting":False,
        "v098_holdout_access":False,
        "fresh_holdout":False,
        "advance_q5":False,
        "global_q3":"OPEN","global_q4":"OPEN",
    }


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v101 frozen head required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    env=environment()
    if env!=protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"v101 runtime drift: {env!r}")

    models,training=restore_frozen_quotient()
    sources=development_sources()
    source_by_id={s["id"]:s for s in sources}
    records=[]
    with threadpool_limits(1):
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                source=source_by_id[case_id]
                if route=="DIRECT":
                    row=observe_reference(source["raw"],route)
                elif route=="ORACLE":
                    row=observe_reference(
                        source["raw"],route,source["basis"])
                else:
                    row=observe_candidate(
                        source["raw"],route,models,training)
                records.append({
                    "case_id":case_id,
                    "pair_id":source["pair_id"],
                    "group":source["group"],
                    "surface":source["surface"],
                    "source_sha256":source["sha256"],
                    "route":route,
                    "repeat":repeat,
                    **row,
                })
            print(f"V101_REPEAT {repeat} {len(records)}",flush=True)

    return {
        "protocol":protocol(),
        "environment":env,
        "frozen_head":frozen_head,
        "training_identity":training,
        "development_specs":base_specs(),
        "development_sources":[{
            k:s[k] for k in (
                "id","pair_id","group","rows","condition",
                "seed","surface","sha256","basis")
        } for s in sources],
        "records":records,
        "summary":summarize(records,sources),
        "stage":"completed",
    }


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v101 first result already exists")
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.frozen-support-expansion-v101.archive.v1",
        "file":output.name,
        "frozen_head":report["frozen_head"],
        "rerun":False,
        "gzip_bytes":len(packed),
        "gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),
        "json_sha256":hashlib.sha256(raw).hexdigest(),
        "decision":report["summary"]["decision"],
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
    print("V101_FIRST_SUMMARY="+json.dumps(
        manifest["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V101_FIRST_ARCHIVE="+json.dumps(
        {k:v for k,v in manifest.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
