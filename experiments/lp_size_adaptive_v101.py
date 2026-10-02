"""v0.0.101: frozen quotient 2m vs verifier-triggered 2m->4m support screen."""
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

from experiments.lp_equivalence_quotient_v099 import quotient_columns
from experiments.lp_model_study_v088 import pack_weights
from experiments.lp_quotient_refit_v100 import SupportMLP
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_basis_headroom_v082 import generate_case
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit
from neumann1.lp_native_warm_start_v086 import solve_native_checked
from neumann1.lp_q34_support_v097 import (
    adaptive_support_checked,
    restricted_original_checked,
    support_with_fallback_checked,
)

V100_MANIFEST="docs/experiments/results/v100_first_refit.manifest.json"
MODEL_SEEDS=(100001,100002)
ROUTES=(
    "DIRECT","ORACLE",
    "FIXED2_s100001","FIXED2_s100002",
    "ADAPT24_s100001","ADAPT24_s100002",
)
CANDIDATES=ROUTES[2:]


def protocol():
    return {
        "schema":"neumann.quotient-size-adaptive-v101.v1",
        "runtime":{**admission.RUNTIME,"scikit_learn":"1.9.1"},
        "v100_manifest":V100_MANIFEST,
        "model_seeds":list(MODEL_SEEDS),
        "development_seed_base":101200,
        "development_cases":16,
        "rows":128,
        "width_factor":16,
        "conditions":[1,1000],
        "routes":list(ROUTES),
        "warmups":1,
        "repeats":3,
        "order_seed":101991,
        "budget_s":5.0,
        "fixed_support_factor":2,
        "adaptive_factors":[2,4],
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "new_fitting":False,
        "optimizer_calls":False,
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


def diagnose_v100():
    """Describe retained m128 misses without inference, solver or timing."""
    report=load_first_refit(V100_MANIFEST)
    sources={s["id"]:s for s in report["development_sources"]}
    out={}
    for seed in MODEL_SEEDS:
        route=f"QUOTIENT_s{seed}"
        pairs={}
        for pair in sorted({s["pair_id"] for s in sources.values()
                            if s["rows"]==128}):
            views=[s for s in sources.values()
                   if s["pair_id"]==pair and s["rows"]==128]
            if len(views)!=2:
                raise ValueError("v100 m128 pair coverage drift")
            rows={}
            supports=[]
            for source in views:
                obs=[r for r in report["records"]
                     if r["case_id"]==source["id"] and r["route"]==route
                     and r["repeat"]>=0]
                if len(obs)!=3:
                    raise ValueError("v100 timed diagnostic coverage drift")
                if any(r["indices"]!=obs[0]["indices"] for r in obs[1:]):
                    raise ValueError("v100 retained support nondeterminism")
                support=obs[0]["indices"]
                supports.append(support)
                basis=set(source["basis"])
                hit=len(basis.intersection(support))
                rows["surface" if source["surface"] else "base"]={
                    "case_id":source["id"],
                    "fallback_used":any(r["fallback_used"] for r in obs),
                    "subset_accepted":all(r["subset_accepted"] for r in obs),
                    "basis_contained":basis.issubset(support),
                    "basis_recall":hit/len(basis),
                    "missing_reference_basis_columns":len(basis)-hit,
                }
            pairs[pair]={
                "support_identical":supports[0]==supports[1],
                "views":rows,
            }
        out[str(seed)]={
            "pairs":pairs,
            "full_fallback_pairs":sum(
                any(v["fallback_used"] for v in p["views"].values())
                for p in pairs.values()),
            "all_pair_supports_identical":all(
                p["support_identical"] for p in pairs.values()),
        }
    return out


def restore_models(v100):
    models={}
    for seed in MODEL_SEEDS:
        source_key=f"QUOTIENT_s{seed}"
        retained=v100["training"][source_key]
        model=SupportMLP(seed)
        state={}
        for name,item in retained["weights"].items():
            raw=base64.b64decode(item["base64"],validate=True)
            a=np.frombuffer(raw,dtype="<f4").reshape(item["shape"]).copy()
            state[name]=torch.tensor(a,dtype=torch.float32)
        model.load_state_dict(state,strict=True)
        model.eval()
        if pack_weights(model)[1]!=retained["weights_sha256"]:
            raise ValueError("v101 frozen quotient checkpoint identity drift")
        models[seed]=model
    return models


def development_specs():
    return [{
        "id":f"v101_dev{i:02d}",
        "rows":protocol()["rows"],
        "condition":protocol()["conditions"][i%2],
        "seed":protocol()["development_seed_base"]+i,
    } for i in range(protocol()["development_cases"])]


def generate_source(spec):
    m=spec["rows"]
    case=generate_case({
        "id":spec["id"],"pair_id":spec["id"],
        "rows":m,"width_factor":protocol()["width_factor"],
        "cols":protocol()["width_factor"]*m,
        "condition_number":spec["condition"],
        "replicate":0,"seed":spec["seed"],
    })
    A,b,c=storage.normalized(case["A"],case["b"],case["c"])
    raw={"A":A,"b":b,"c":c}
    basis=[int(i) for i in case["oracle_basis"]]
    label=storage.candidate_once(raw,basis,"v101_dev_label")
    if not label["accepted"]:
        raise ValueError("v101 development oracle basis rejected")
    return {
        **spec,
        "cols":raw["A"].shape[1],
        "raw":raw,
        "basis":basis,
        "sha256":storage.input_digest(raw),
    }


def investment_per_query(v100,seed):
    row=v100["training"][f"QUOTIENT_s{seed}"]
    return (float(row["feature_setup_ms"])+float(row["fit_ms"])) / protocol()["amortization_queries"]


def proposal(raw,seed,models):
    started=perf_counter_ns()
    _,cols=quotient_columns(raw)
    tensor=torch.tensor(cols,dtype=torch.float32)
    with torch.inference_mode():
        score=models[seed](tensor)
    if not torch.isfinite(score).all():
        raise ValueError("nonfinite v101 quotient score")
    ranking=torch.argsort(score,descending=True,stable=True).tolist()
    return {
        "ranking":ranking,
        "proposal_ms":(perf_counter_ns()-started)/1e6,
    }


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
            "expanded_to_4m":False,"ranking":None,
            "witness":witness,"execution":result,
        }
    if route=="ORACLE":
        if basis is None:
            raise ValueError("oracle basis required")
        result=restricted_original_checked(**raw,indices=list(basis),budget_s=budget)
        return {
            "accepted":bool(result["accepted"]),
            "proposal_ms":0.0,"post_ms":float(result["total_ms"]),
            "total_ms":float(result["total_ms"]),
            "amortized_investment_ms":0.0,
            "fallback_used":False,"subset_accepted":bool(result["accepted"]),
            "expanded_to_4m":False,"ranking":None,
            "witness":result["witness"],"execution":result,
        }
    raise ValueError("reference route required")


def observe_candidate(raw,route,models,v100):
    if route.startswith("FIXED2_s"):
        kind="fixed"
    elif route.startswith("ADAPT24_s"):
        kind="adaptive"
    else:
        raise ValueError("candidate route required")
    seed=int(route.rsplit("s",1)[1])
    p=proposal(raw,seed,models)
    budget=protocol()["budget_s"]
    left=budget-p["proposal_ms"]/1000.0
    execution=None
    m=raw["A"].shape[0]
    if left>0:
        if kind=="fixed":
            execution=support_with_fallback_checked(
                **raw,
                indices=p["ranking"][:protocol()["fixed_support_factor"]*m],
                budget_s=left,
            )
            subset=bool(execution["subset_accepted"])
            expanded=False
        else:
            execution=adaptive_support_checked(
                **raw,ranking=p["ranking"],budget_s=left,
                factors=tuple(protocol()["adaptive_factors"]),
            )
            subset=bool(any(a["result"]["accepted"] for a in execution["attempts"]))
            expanded=bool(any(a["support_size"]==4*m for a in execution["attempts"]))
    else:
        subset=False
        expanded=False
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=float(p["proposal_ms"])+post_ms
    accepted=bool(execution and execution["accepted"] and total_ms<=budget*1000.0)
    return {
        "accepted":accepted,
        "proposal_ms":float(p["proposal_ms"]),
        "post_ms":post_ms,"total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(v100,seed),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":subset,
        "expanded_to_4m":expanded,
        "ranking":p["ranking"],
        "witness":execution["witness"] if execution else None,
        "execution":execution,
    }


def _medians(records,case_id,route):
    rows=[r for r in records
          if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("v101 timed repeat coverage drift")
    for field in ("ranking","fallback_used","subset_accepted","expanded_to_4m",
                  "amortized_investment_ms"):
        if any(r[field]!=rows[0][field] for r in rows[1:]):
            raise ValueError(f"v101 deterministic ledger drift: {field}")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":rows[0]["amortized_investment_ms"],
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_used":rows[0]["fallback_used"],
        "subset_accepted":rows[0]["subset_accepted"],
        "expanded_to_4m":rows[0]["expanded_to_4m"],
        "ranking":rows[0]["ranking"],
    }


def route_metrics(records,sources,route):
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
    utility=(candidate_savings/oracle_savings
             if oracle_savings>0 and candidate_savings>0 else None)
    burden=discovery/candidate_savings if candidate_savings>0 else None
    complete=(discovery+post_total)/direct_total if direct_total>0 else None
    passed=bool(
        reference_ok and capability and utility is not None and burden is not None
        and utility>=protocol()["utility_floor"]
        and burden<=protocol()["discovery_burden_max"]
        and complete is not None and complete<1.0)
    fallback_cases=sum(med[case,route]["fallback_used"] for case in ids)
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
        "full_direct_fallback_cases":fallback_cases,
        "fallback_free_cases":len(ids)-fallback_cases,
        "restricted_success_cases":sum(
            med[case,route]["subset_accepted"] for case in ids),
        "expanded_to_4m_cases":sum(
            med[case,route]["expanded_to_4m"] for case in ids),
        "passed":passed,
    }


def summarize(records,sources):
    if len(sources)!=protocol()["development_cases"]:
        raise ValueError("v101 source count drift")
    expected={(s["id"],route,repeat)
              for s in sources for route in ROUTES for repeat in (-1,0,1,2)}
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("v101 evaluation coverage drift")
    metrics={route:route_metrics(records,sources,route) for route in CANDIDATES}
    tests={}
    for seed in MODEL_SEEDS:
        fixed=metrics[f"FIXED2_s{seed}"]
        adapt=metrics[f"ADAPT24_s{seed}"]
        promoted=bool(
            adapt["passed"]
            and adapt["full_direct_fallback_cases"]==0
            and adapt["full_direct_fallback_cases"]<fixed["full_direct_fallback_cases"]
            and adapt["amortized_complete_ratio"]<fixed["amortized_complete_ratio"]
        )
        tests[str(seed)]={
            "fixed_route":fixed["route"],
            "adaptive_route":adapt["route"],
            "fixed_q34_pass":fixed["passed"],
            "adaptive_q34_pass":adapt["passed"],
            "fixed_full_direct_fallback_cases":fixed["full_direct_fallback_cases"],
            "adaptive_full_direct_fallback_cases":adapt["full_direct_fallback_cases"],
            "fixed_complete_ratio":fixed["amortized_complete_ratio"],
            "adaptive_complete_ratio":adapt["amortized_complete_ratio"],
            "adaptive_promoted":promoted,
        }
    passed=all(x["adaptive_promoted"] for x in tests.values())
    return {
        "decision":(
            "ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_ADAPTIVE_QUOTIENT"
            if passed else "STOP_QUOTIENT_POINT_SUPPORT_FAMILY"
        ),
        "adaptive_development_pass":passed,
        "routes":metrics,
        "seed_tests":tests,
        "development_cases":len(sources),
        "new_fitting":False,
        "v098_holdout_access":False,
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

    v100=load_first_refit(V100_MANIFEST)
    model_loading_started=perf_counter_ns()
    models=restore_models(v100)
    # Checkpoint restoration is reported as setup, not per-query discovery.
    model_loading_ms=(perf_counter_ns()-model_loading_started)/1e6

    sources=[generate_source(s) for s in development_specs()]
    source_by_id={s["id"]:s for s in sources}
    records=[]
    with threadpool_limits(1):
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                source=source_by_id[case_id]
                raw=source["raw"]
                if route=="DIRECT":
                    row=observe_reference(raw,route)
                elif route=="ORACLE":
                    row=observe_reference(raw,route,source["basis"])
                else:
                    row=observe_candidate(raw,route,models,v100)
                records.append({
                    "case_id":case_id,
                    "source_sha256":source["sha256"],
                    "condition":source["condition"],
                    "route":route,"repeat":repeat,**row,
                })
            print(f"V101_REPEAT {repeat} {len(records)}",flush=True)

    public_sources=[{
        k:s[k] for k in ("id","rows","condition","seed","cols","basis","sha256")
    } for s in sources]
    return {
        "protocol":protocol(),
        "environment":env,
        "frozen_head":frozen_head,
        "v100_diagnosis":diagnose_v100(),
        "v100_checkpoint_sha256":{
            str(seed):v100["training"][f"QUOTIENT_s{seed}"]["weights_sha256"]
            for seed in MODEL_SEEDS
        },
        "model_loading_ms":model_loading_ms,
        "development_sources":public_sources,
        "records":records,
        "summary":summarize(records,public_sources),
        "stage":"completed",
        "threadpools":threadpool_info(),
        "torch_threads":{
            "intraop":torch.get_num_threads(),
            "interop":torch.get_num_interop_threads(),
        },
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
        "format":"neumann.quotient-size-adaptive-v101.archive.v1",
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
    print("V101_V100_DIAG="+json.dumps(
        report["v100_diagnosis"],sort_keys=True,separators=(",",":")),flush=True)
    print("V101_FIRST_SUMMARY="+json.dumps(
        m["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V101_FIRST_ARCHIVE="+json.dumps(
        {k:v for k,v in m.items() if k!="summary"},
        sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
