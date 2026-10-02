"""v0.0.100 matched quotient-point refit and development Q34 screen."""
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
from torch import nn
from torch.nn import functional as F
from threadpoolctl import threadpool_info, threadpool_limits

from experiments.lp_equivalence_quotient_v099 import quotient_columns
from experiments.lp_input_compaction_v094 import features as current_cg5_features
from experiments.lp_model_study_v088 import pack_weights
from experiments.lp_shortlist_screen_v089 import raw_source
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_basis_headroom_v082 import generate_case
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study

TRAIN_MANIFEST="docs/experiments/results/v088_completed.manifest.json"
MODEL_SEEDS=(100001,100002)
KINDS=("OLD_CG5","QUOTIENT")
GROUPS=("m64_base","m64_surface","m128_base","m128_surface")
ROUTES=(
    "DIRECT","ORACLE",
    "OLD_CG5_s100001","OLD_CG5_s100002",
    "QUOTIENT_s100001","QUOTIENT_s100002",
)


def protocol():
    return {
        "schema":"neumann.quotient-point-refit-v100.v1",
        "runtime":admission.RUNTIME,
        "train_sources":48,
        "model_seeds":list(MODEL_SEEDS),
        "kinds":list(KINDS),
        "width":16,
        "parameters":433,
        "epochs":12,
        "optimizer":"Adam",
        "lr":0.001,
        "weight_decay":0.0,
        "positive_weight":15.0,
        "train_order_seed_base":100091,
        "checkpoint":"last_epoch_only",
        "development_seed_base":100200,
        "development_base_cases":16,
        "development_views":32,
        "surface_seed_offset":200000,
        "groups":list(GROUPS),
        "routes":list(ROUTES),
        "warmups":1,
        "repeats":3,
        "order_seed":100991,
        "budget_s":5.0,
        "support_factor":2,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "v088_final_access":False,
        "v098_holdout_access":False,
        "fresh_holdout":False,
        "advance_q5":False,
        "global_q3":"OPEN",
        "global_q4":"OPEN",
    }


class SupportMLP(nn.Module):
    def __init__(self,seed):
        super().__init__()
        torch.manual_seed(seed)
        self.cols=nn.Sequential(
            nn.Linear(8,16),nn.ReLU(),
            nn.Linear(16,16),nn.ReLU(),
        )
        self.head=nn.Linear(16,1)

    def forward(self,cols):
        return self.head(self.cols(cols)).squeeze(1)


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


def point_features(raw,kind):
    if kind=="OLD_CG5":
        _,_,cols=current_cg5_features(raw)
    elif kind=="QUOTIENT":
        _,cols=quotient_columns(raw)
    else:
        raise ValueError("unregistered point representation")
    if cols.ndim!=2 or cols.shape[1]!=8 or not np.isfinite(cols).all():
        raise ValueError("point feature drift")
    return cols


def train_data(sources,kind):
    started=perf_counter_ns()
    data=[]
    for source in sources:
        raw=raw_source(source)
        cols=point_features(raw,kind)
        target=np.zeros(cols.shape[0],dtype=np.float32)
        target[np.asarray(source["label"]["indices"],dtype=int)]=1.0
        data.append((
            torch.tensor(cols,dtype=torch.float32),
            torch.tensor(target,dtype=torch.float32),
        ))
    return data,(perf_counter_ns()-started)/1e6


def fit_one(sources,kind,seed):
    data,setup_ms=train_data(sources,kind)
    model=SupportMLP(seed)
    if sum(p.numel() for p in model.parameters())!=protocol()["parameters"]:
        raise ValueError("support model parameter drift")
    optimizer=torch.optim.Adam(
        model.parameters(),lr=protocol()["lr"],
        weight_decay=protocol()["weight_decay"])
    weight=torch.tensor(protocol()["positive_weight"],dtype=torch.float32)
    started=perf_counter_ns()
    epochs=[]
    model.train()
    for epoch in range(protocol()["epochs"]):
        order=list(range(len(data)))
        random.Random(protocol()["train_order_seed_base"]+epoch).shuffle(order)
        losses=[]
        for i in order:
            cols,target=data[i]
            optimizer.zero_grad(set_to_none=True)
            logits=model(cols)
            objective=F.binary_cross_entropy_with_logits(
                logits,target,pos_weight=weight)
            if not torch.isfinite(objective):
                raise ValueError("nonfinite quotient-refit loss")
            objective.backward()
            optimizer.step()
            losses.append(float(objective.detach()))
        epochs.append({
            "epoch":epoch+1,
            "mean_loss":sum(losses)/len(losses),
        })
    model.eval()
    fit_ms=(perf_counter_ns()-started)/1e6
    weights,sha=pack_weights(model)
    return model,{
        "kind":kind,"seed":seed,"parameters":protocol()["parameters"],
        "feature_setup_ms":setup_ms,"fit_ms":fit_ms,
        "epochs":epochs,"weights":weights,"weights_sha256":sha,
    }


def base_specs():
    out=[]
    for i in range(16):
        rows=64 if i<8 else 128
        out.append({
            "pair_id":f"dev{i:02d}",
            "rows":rows,
            "condition":(1,1000)[i%2],
            "seed":protocol()["development_seed_base"]+i,
        })
    return out


def _base_problem(spec):
    m=spec["rows"]
    case=generate_case({
        "id":spec["pair_id"],"pair_id":spec["pair_id"],
        "rows":m,"width_factor":16,"cols":16*m,
        "condition_number":spec["condition"],
        "replicate":0,"seed":spec["seed"],
    })
    A,b,c=storage.normalized(case["A"],case["b"],case["c"])
    return {"A":A,"b":b,"c":c},list(case["oracle_basis"])


def _surface(raw,seed):
    rng=np.random.default_rng(seed)
    A=np.asarray(raw["A"],dtype=float).copy()
    b=np.asarray(raw["b"],dtype=float).copy()
    c=np.asarray(raw["c"],dtype=float).copy()
    m,n=A.shape
    order=rng.permutation(m)
    signs=rng.choice(np.array([-1.0,1.0]),size=m)
    A=A[order]*signs[:,None]
    b=b[order]*signs
    scaling=np.exp(rng.uniform(-1.5,1.5,size=n))
    A=A*scaling
    c=c*scaling
    return {"A":A,"b":b,"c":c}


def development_sources():
    sources=[]
    for spec in base_specs():
        raw,basis=_base_problem(spec)
        for surface in (False,True):
            view=_surface(
                raw,spec["seed"]+protocol()["surface_seed_offset"]
            ) if surface else raw
            group=(
                f"m{spec['rows']}_surface"
                if surface else f"m{spec['rows']}_base"
            )
            source={
                **spec,
                "id":f"{spec['pair_id']}_{'surface' if surface else 'base'}",
                "group":group,
                "surface":surface,
                "raw":view,
                "basis":basis,
                "sha256":storage.input_digest(view),
            }
            label=storage.candidate_once(view,basis,"v100_dev_label")
            if not label["accepted"]:
                raise ValueError("v100 development oracle basis rejected")
            source["label"]=label
            sources.append(source)
    if len(sources)!=protocol()["development_views"]:
        raise ValueError("v100 development coverage drift")
    return sources


def investment_per_query(training,route):
    if route in ("DIRECT","ORACLE"):
        return 0.0
    key=route
    row=training[key]
    return (row["feature_setup_ms"]+row["fit_ms"]) / protocol()["amortization_queries"]


def proposal(raw,route,models):
    if route.startswith("OLD_CG5_"):
        kind="OLD_CG5"
    elif route.startswith("QUOTIENT_"):
        kind="QUOTIENT"
    else:
        raise ValueError("candidate route required")
    started=perf_counter_ns()
    cols=point_features(raw,kind)
    tensor=torch.tensor(cols,dtype=torch.float32)
    with torch.inference_mode():
        score=models[route](tensor)
    if not torch.isfinite(score).all():
        raise ValueError("nonfinite v100 score")
    m=raw["A"].shape[0]
    order=torch.argsort(score,descending=True,stable=True)
    indices=order[:min(len(order),protocol()["support_factor"]*m)].tolist()
    return {
        "indices":indices,
        "proposal_ms":(perf_counter_ns()-started)/1e6,
    }


def observe_reference(raw,route,basis=None):
    from neumann1.lp_native_warm_start_v086 import solve_native_checked
    from neumann1.lp_q34_support_v097 import restricted_original_checked
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
            "indices":None,"witness":witness,"execution":result,
        }
    if route=="ORACLE":
        if basis is None:
            raise ValueError("oracle basis required")
        result=restricted_original_checked(
            **raw,indices=list(basis),budget_s=budget)
        return {
            "accepted":bool(result["accepted"]),
            "proposal_ms":0.0,"post_ms":float(result["total_ms"]),
            "total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,
            "fallback_used":False,"subset_accepted":bool(result["accepted"]),
            "indices":list(basis),"witness":result["witness"],
            "execution":result,
        }
    raise ValueError("reference route required")


def observe_candidate(raw,route,models,training):
    from neumann1.lp_q34_support_v097 import support_with_fallback_checked
    budget=protocol()["budget_s"]
    p=proposal(raw,route,models)
    left=budget-p["proposal_ms"]/1000.0
    execution=None
    if left>0:
        execution=support_with_fallback_checked(
            **raw,indices=p["indices"],budget_s=left)
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=p["proposal_ms"]+post_ms
    accepted=bool(
        execution and execution["accepted"] and total_ms<=budget*1000.0)
    return {
        "accepted":accepted,
        "proposal_ms":float(p["proposal_ms"]),
        "post_ms":post_ms,"total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(training,route),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":bool(execution and execution["subset_accepted"]),
        "indices":p["indices"],
        "witness":execution["witness"] if execution else None,
        "execution":execution,
    }


def _medians(records,case_id,route):
    rows=[
        r for r in records
        if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0
    ]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("v100 timed repeat coverage drift")
    investment={r["amortized_investment_ms"] for r in rows}
    if len(investment)!=1:
        raise ValueError("v100 investment drift")
    indices=[r["indices"] for r in rows]
    if any(x!=indices[0] for x in indices[1:]):
        raise ValueError("v100 deterministic proposal drift")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investment)),
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_free":all(not r["fallback_used"] for r in rows),
        "subset_accepted":all(r["subset_accepted"] for r in rows),
        "indices":indices[0],
    }


def cell_metrics(records,sources,route):
    ids=[s["id"] for s in sources]
    med={(case,r):_medians(records,case,r) for case in ids for r in ROUTES}
    reference_ok=all(
        med[case,"DIRECT"]["all_accepted"] and
        med[case,"ORACLE"]["all_accepted"] for case in ids)
    capability=all(med[case,route]["all_accepted"] for case in ids)
    direct_total=sum(med[case,"DIRECT"]["total_ms"] for case in ids)
    oracle_post=sum(med[case,"ORACLE"]["post_ms"] for case in ids)
    oracle_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,"ORACLE"]["post_ms"]
        for case in ids)
    post_total=sum(med[case,route]["post_ms"] for case in ids)
    proposal_total=sum(med[case,route]["proposal_ms"] for case in ids)
    invest_total=sum(med[case,route]["investment_ms"] for case in ids)
    discovery=proposal_total+invest_total
    candidate_savings=sum(
        med[case,"DIRECT"]["total_ms"]-med[case,route]["post_ms"]
        for case in ids)
    utility=(
        candidate_savings/oracle_savings
        if oracle_savings>0 and candidate_savings>0 else None)
    burden=discovery/candidate_savings if candidate_savings>0 else None
    complete=(discovery+post_total)/direct_total if direct_total>0 else None
    passed=bool(
        reference_ok and capability and utility is not None and burden is not None
        and utility>=protocol()["utility_floor"]
        and burden<=protocol()["discovery_burden_max"]
        and complete is not None and complete<1.0
    )
    return {
        "route":route,"cases":len(ids),
        "reference_capability":reference_ok,"capability":capability,
        "direct_total_ms":direct_total,"oracle_post_total_ms":oracle_post,
        "oracle_savings_ms":oracle_savings,
        "proposal_total_ms":proposal_total,
        "amortized_investment_total_ms":invest_total,
        "effective_discovery_total_ms":discovery,
        "post_total_ms":post_total,
        "candidate_pre_discovery_savings_ms":candidate_savings,
        "utility_recovery":utility,"discovery_burden":burden,
        "amortized_complete_ratio":complete,
        "fallback_free_cases":sum(
            med[case,route]["fallback_free"] for case in ids),
        "subset_accepted_cases":sum(
            med[case,route]["subset_accepted"] for case in ids),
        "passed":passed,
    }


def summarize(records,sources):
    if len(sources)!=protocol()["development_views"]:
        raise ValueError("v100 source count drift")
    expected={
        (s["id"],route,repeat)
        for s in sources for route in ROUTES for repeat in (-1,0,1,2)
    }
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("v100 evaluation coverage drift")
    groups={g:[s for s in sources if s["group"]==g] for g in GROUPS}
    if any(len(v)!=8 for v in groups.values()):
        raise ValueError("v100 group coverage drift")

    routes=[r for r in ROUTES if r not in ("DIRECT","ORACLE")]
    cells={}
    overall={}
    for route in routes:
        overall[route]=cell_metrics(records,sources,route)
        cells[route]={
            g:cell_metrics(records,group,route) for g,group in groups.items()
        }

    med={
        (s["id"],route):_medians(records,s["id"],route)
        for s in sources for route in routes
    }
    pair_map={s["pair_id"]:{} for s in sources}
    for s in sources:
        pair_map[s["pair_id"]][s["surface"]]=s["id"]
    invariance={}
    for route in routes:
        exact=0
        for pair,views in pair_map.items():
            if set(views)!={False,True}:
                raise ValueError("v100 pair coverage drift")
            if med[views[False],route]["indices"]==med[views[True],route]["indices"]:
                exact+=1
        invariance[route]={"exact_pairs":exact,"pairs":len(pair_map)}

    quotient_routes=[f"QUOTIENT_s{s}" for s in MODEL_SEEDS]
    quotient_pass=all(
        overall[r]["passed"]
        and all(cells[r][g]["passed"] for g in GROUPS)
        and invariance[r]["exact_pairs"]==16
        for r in quotient_routes
    )
    decision=(
        "ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_QUOTIENT"
        if quotient_pass else
        "STOP_QUOTIENT_REFIT_NO_FRESH_HOLDOUT"
    )
    return {
        "decision":decision,
        "quotient_development_pass":quotient_pass,
        "overall":overall,"groups":cells,
        "paired_support_invariance":invariance,
        "development_views":len(sources),
        "v098_holdout_access":False,
        "advance_q5":False,
        "global_q3":"OPEN","global_q4":"OPEN",
    }


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v100 frozen head required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    env=environment()
    if env!=protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"v100 runtime drift: {env!r}")

    retained=load_study(TRAIN_MANIFEST)
    train_sources=retained["train_sources"]
    if len(train_sources)!=48:
        raise ValueError("v100 train source drift")

    models={}
    training={}
    with threadpool_limits(1):
        for kind in KINDS:
            for seed in MODEL_SEEDS:
                route=f"{kind}_s{seed}"
                model,row=fit_one(train_sources,kind,seed)
                models[route]=model
                training[route]=row

        dev=development_sources()
        source_by_id={s["id"]:s for s in dev}
        records=[]
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in dev for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                source=source_by_id[case_id]
                raw=source["raw"]
                if route=="DIRECT":
                    row=observe_reference(raw,route)
                elif route=="ORACLE":
                    row=observe_reference(raw,route,source["basis"])
                else:
                    row=observe_candidate(raw,route,models,training)
                records.append({
                    "case_id":case_id,"pair_id":source["pair_id"],
                    "group":source["group"],"surface":source["surface"],
                    "source_sha256":source["sha256"],
                    "route":route,"repeat":repeat,**row,
                })
            print(f"V100_REPEAT {repeat} {len(records)}",flush=True)

    report={
        "protocol":protocol(),"environment":env,
        "frozen_head":frozen_head,
        "training":training,
        "development_specs":base_specs(),
        "development_sources":[{
            k:s[k] for k in (
                "id","pair_id","group","rows","condition","seed",
                "surface","sha256","basis")
        } for s in dev],
        "records":records,
        "summary":summarize(records,dev),
        "stage":"completed",
        "threadpools":threadpool_info(),
        "torch_threads":{
            "intraop":torch.get_num_threads(),
            "interop":torch.get_num_interop_threads(),
        },
    }
    return report


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v100 first result already exists")
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.quotient-point-refit-v100.archive.v1",
        "file":output.name,"frozen_head":report["frozen_head"],"rerun":False,
        "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),"json_sha256":hashlib.sha256(raw).hexdigest(),
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
    m=write_first(report,args.output_gzip,args.manifest)
    print("V100_FIRST_SUMMARY="+json.dumps(
        m["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V100_FIRST_ARCHIVE="+json.dumps(
        {k:v for k,v in m.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
