"""v0.0.101 final training-free adaptive Q34 development gate."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import random
import sys
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import numpy as np
import torch
from threadpoolctl import threadpool_info, threadpool_limits

from experiments.lp_quotient_refit_v100 import SupportMLP, _base_problem, _surface, point_features
from neumann1 import lp_model_admission_v087 as admission
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_q34_support_v097 import adaptive_support_checked, restricted_original_checked, support_with_fallback_checked
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit

V100_MANIFEST="docs/experiments/results/v100_first_refit.manifest.json"
MODEL_SEEDS=(100001,100002)
GROUPS=("m64_base","m64_surface","m128_base","m128_surface")
ROUTES=("DIRECT","ORACLE","STATIC_s100001","STATIC_s100002","ADAPTIVE_s100001","ADAPTIVE_s100002")


def protocol():
    return {
        "schema":"neumann.final-adaptive-q34-v101.v1",
        "runtime":{**admission.RUNTIME,"scikit_learn":"1.9.1"},
        "model_source":V100_MANIFEST,
        "model_seeds":list(MODEL_SEEDS),
        "development_seed_base":100300,
        "development_base_cases":16,
        "development_views":32,
        "surface_seed_offset":300000,
        "groups":list(GROUPS),
        "routes":list(ROUTES),
        "static_support_factor":2,
        "adaptive_support_factors":[2,4],
        "warmups":1,
        "repeats":3,
        "order_seed":101991,
        "budget_s":5.0,
        "utility_floor":0.80,
        "discovery_burden_max":0.20,
        "amortization_queries":10000,
        "new_fitting":False,
        "threshold_change":False,
        "v098_holdout_access":False,
        "fresh_holdout":False,
        "advance_q5":False,
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


def restore_models(report):
    models={}
    training={}
    for seed in MODEL_SEEDS:
        key=f"QUOTIENT_s{seed}"
        row=report["training"][key]
        model=SupportMLP(seed)
        state={}
        for name,value in row["weights"].items():
            raw=base64.b64decode(value["base64"],validate=True)
            arr=np.frombuffer(raw,dtype="<f4").reshape(value["shape"]).copy()
            state[name]=torch.tensor(arr)
        model.load_state_dict(state,strict=True)
        model.eval()
        models[seed]=model
        training[seed]=row
    return models,training


def specs():
    out=[]
    for i in range(protocol()["development_base_cases"]):
        rows=64 if i<8 else 128
        out.append({
            "pair_id":f"v101dev{i:02d}",
            "rows":rows,
            "condition":(1,1000)[i%2],
            "seed":protocol()["development_seed_base"]+i,
        })
    return out


def development_sources():
    sources=[]
    for spec in specs():
        raw,basis=_base_problem(spec)
        for surface in (False,True):
            view=_surface(raw,spec["seed"]+protocol()["surface_seed_offset"]) if surface else raw
            group=f"m{spec['rows']}_{'surface' if surface else 'base'}"
            label=restricted_original_checked(**view,indices=list(basis),budget_s=protocol()["budget_s"])
            if not label["accepted"]:
                raise ValueError("v101 oracle basis rejected")
            sources.append({
                **spec,
                "id":f"{spec['pair_id']}_{'surface' if surface else 'base'}",
                "group":group,
                "surface":surface,
                "raw":view,
                "basis":list(basis),
            })
    if len(sources)!=protocol()["development_views"]:
        raise ValueError("v101 source coverage drift")
    return sources


def investment_per_query(training,seed):
    row=training[seed]
    return (float(row["feature_setup_ms"])+float(row["fit_ms"])) / protocol()["amortization_queries"]


def ranking(raw,model):
    started=perf_counter_ns()
    cols=point_features(raw,"QUOTIENT")
    tensor=torch.tensor(cols,dtype=torch.float32)
    with torch.inference_mode():
        score=model(tensor)
    if not torch.isfinite(score).all():
        raise ValueError("nonfinite v101 quotient scores")
    order=torch.argsort(score,descending=True,stable=True).tolist()
    return order,(perf_counter_ns()-started)/1e6


def observe_reference(raw,route,basis=None):
    from neumann1.lp_native_warm_start_v086 import solve_native_checked
    budget=protocol()["budget_s"]
    if route=="DIRECT":
        result=solve_native_checked(**raw,cold_fallback=False,budget_s=budget)
        witness=result["attempts"][-1]["witness"] if result["accepted"] else None
        return {"accepted":bool(result["accepted"]),"proposal_ms":0.0,"post_ms":float(result["total_ms"]),
                "total_ms":float(result["total_ms"]),"amortized_investment_ms":0.0,
                "fallback_used":False,"subset_accepted":False,"ranking":None,"witness":witness}
    if route=="ORACLE":
        result=restricted_original_checked(**raw,indices=list(basis),budget_s=budget)
        return {"accepted":bool(result["accepted"]),"proposal_ms":0.0,"post_ms":float(result["total_ms"]),
                "total_ms":float(result["total_ms"]),"amortized_investment_ms":0.0,
                "fallback_used":False,"subset_accepted":bool(result["accepted"]),
                "ranking":None,"witness":result["witness"]}
    raise ValueError("reference route required")


def observe_candidate(raw,route,models,training):
    adaptive=route.startswith("ADAPTIVE_")
    seed=int(route.rsplit("s",1)[1])
    order,proposal_ms=ranking(raw,models[seed])
    budget=protocol()["budget_s"]
    left=budget-proposal_ms/1000.0
    execution=None
    m=raw["A"].shape[0]
    subset=False
    if left>0:
        if adaptive:
            execution=adaptive_support_checked(**raw,ranking=order,budget_s=left,
                                               factors=tuple(protocol()["adaptive_support_factors"]))
            subset=bool(any(a["result"]["accepted"] for a in execution["attempts"]))
        else:
            indices=order[:min(len(order),protocol()["static_support_factor"]*m)]
            execution=support_with_fallback_checked(**raw,indices=indices,budget_s=left)
            subset=bool(execution["subset_accepted"])
    post_ms=float(execution["total_ms"]) if execution else 0.0
    total_ms=proposal_ms+post_ms
    return {
        "accepted":bool(execution and execution["accepted"] and total_ms<=budget*1000.0),
        "proposal_ms":proposal_ms,"post_ms":post_ms,"total_ms":total_ms,
        "amortized_investment_ms":investment_per_query(training,seed),
        "fallback_used":bool(execution and execution["fallback_used"]),
        "subset_accepted":subset,"ranking":order,
        "witness":execution["witness"] if execution else None,
    }


def _medians(records,case_id,route):
    rows=[r for r in records if r["case_id"]==case_id and r["route"]==route and r["repeat"]>=0]
    if len(rows)!=protocol()["repeats"]:
        raise ValueError("v101 timed repeat coverage drift")
    rankings=[r["ranking"] for r in rows]
    if route not in ("DIRECT","ORACLE") and any(x!=rankings[0] for x in rankings[1:]):
        raise ValueError("v101 deterministic ranking drift")
    investment={r["amortized_investment_ms"] for r in rows}
    if len(investment)!=1:
        raise ValueError("v101 investment drift")
    return {
        "proposal_ms":median(r["proposal_ms"] for r in rows),
        "post_ms":median(r["post_ms"] for r in rows),
        "total_ms":median(r["total_ms"] for r in rows),
        "investment_ms":next(iter(investment)),
        "all_accepted":all(r["accepted"] for r in rows),
        "fallback_free":all(not r["fallback_used"] for r in rows),
        "subset_accepted":all(r["subset_accepted"] for r in rows),
        "ranking":rankings[0] if route not in ("DIRECT","ORACLE") else None,
    }


def cell_metrics(records,sources,route):
    ids=[s["id"] for s in sources]
    med={(case,r):_medians(records,case,r) for case in ids for r in ROUTES}
    reference_ok=all(med[case,"DIRECT"]["all_accepted"] and med[case,"ORACLE"]["all_accepted"] for case in ids)
    capability=all(med[case,route]["all_accepted"] for case in ids)
    direct=sum(med[case,"DIRECT"]["total_ms"] for case in ids)
    oracle_post=sum(med[case,"ORACLE"]["post_ms"] for case in ids)
    oracle_savings=sum(med[case,"DIRECT"]["total_ms"]-med[case,"ORACLE"]["post_ms"] for case in ids)
    post=sum(med[case,route]["post_ms"] for case in ids)
    proposal=sum(med[case,route]["proposal_ms"] for case in ids)
    invest=sum(med[case,route]["investment_ms"] for case in ids)
    discovery=proposal+invest
    savings=sum(med[case,"DIRECT"]["total_ms"]-med[case,route]["post_ms"] for case in ids)
    utility=savings/oracle_savings if oracle_savings>0 and savings>0 else None
    burden=discovery/savings if savings>0 else None
    complete=(discovery+post)/direct if direct>0 else None
    passed=bool(reference_ok and capability and utility is not None and burden is not None
                and utility>=protocol()["utility_floor"]
                and burden<=protocol()["discovery_burden_max"]
                and complete is not None and complete<1.0)
    return {
        "route":route,"cases":len(ids),"reference_capability":reference_ok,"capability":capability,
        "direct_total_ms":direct,"oracle_post_total_ms":oracle_post,"oracle_savings_ms":oracle_savings,
        "proposal_total_ms":proposal,"amortized_investment_total_ms":invest,
        "effective_discovery_total_ms":discovery,"post_total_ms":post,
        "candidate_pre_discovery_savings_ms":savings,"utility_recovery":utility,
        "discovery_burden":burden,"amortized_complete_ratio":complete,
        "fallback_free_cases":sum(med[case,route]["fallback_free"] for case in ids),
        "subset_accepted_cases":sum(med[case,route]["subset_accepted"] for case in ids),
        "passed":passed,
    }


def summarize(records,sources):
    expected={(s["id"],route,repeat) for s in sources for route in ROUTES for repeat in (-1,0,1,2)}
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError("v101 evaluation coverage drift")
    groups={g:[s for s in sources if s["group"]==g] for g in GROUPS}
    if any(len(v)!=8 for v in groups.values()):
        raise ValueError("v101 group coverage drift")

    candidates=[r for r in ROUTES if r not in ("DIRECT","ORACLE")]
    overall={r:cell_metrics(records,sources,r) for r in candidates}
    cells={r:{g:cell_metrics(records,ss,r) for g,ss in groups.items()} for r in candidates}

    med={(s["id"],r):_medians(records,s["id"],r) for s in sources for r in candidates}
    pairs={s["pair_id"]:{} for s in sources}
    for s in sources:
        pairs[s["pair_id"]][s["surface"]]=s["id"]
    invariance={}
    for route in candidates:
        exact=0
        for views in pairs.values():
            if med[views[False],route]["ranking"]==med[views[True],route]["ranking"]:
                exact+=1
        invariance[route]={"exact_ranking_pairs":exact,"pairs":len(pairs)}

    static_pass=all(overall[f"STATIC_s{s}"]["passed"] and all(cells[f"STATIC_s{s}"][g]["passed"] for g in GROUPS)
                    for s in MODEL_SEEDS)
    adaptive_pass=all(overall[f"ADAPTIVE_s{s}"]["passed"] and all(cells[f"ADAPTIVE_s{s}"][g]["passed"] for g in GROUPS)
                      for s in MODEL_SEEDS)

    recovered={}
    for seed in MODEL_SEEDS:
        st=f"STATIC_s{seed}"; ad=f"ADAPTIVE_s{seed}"
        static_m128=sum(cells[st][g]["fallback_free_cases"] for g in ("m128_base","m128_surface"))
        adaptive_m128=sum(cells[ad][g]["fallback_free_cases"] for g in ("m128_base","m128_surface"))
        recovered[str(seed)]=adaptive_m128-static_m128

    if static_pass:
        decision="ADMIT_FINAL_FRESH_Q34_HOLDOUT_STATIC"; survivor="STATIC"
    elif adaptive_pass and all(v>=1 for v in recovered.values()):
        decision="ADMIT_FINAL_FRESH_Q34_HOLDOUT_ADAPTIVE"; survivor="ADAPTIVE"
    else:
        decision="CLOSE_Q3_Q4_CURRENT_LP_FORMULATION_REJECTED"; survivor=None

    return {
        "decision":decision,"survivor":survivor,"overall":overall,"groups":cells,
        "paired_ranking_invariance":invariance,
        "adaptive_m128_fallback_free_gain":recovered,
        "static_development_pass":static_pass,"adaptive_development_pass":adaptive_pass,
        "advance_fresh_holdout":survivor is not None,
        "q3_status":"OPEN_PENDING_FINAL_HOLDOUT" if survivor else "REJECTED_CURRENT_LP_FORMULATION",
        "q4_status":"OPEN_PENDING_FINAL_HOLDOUT" if survivor else "REJECTED_CURRENT_LP_FORMULATION",
        "advance_q5":False,"v098_holdout_access":False,
    }


def validate_original_witnesses(report):
    by_id={s["id"]:s for s in development_sources()}
    for r in report["records"]:
        if not r["accepted"]:
            continue
        source=by_id[r["case_id"]]
        if r["witness"] is None:
            raise ValueError("accepted row missing witness")
        if not verify_standard_form_certificate(**source["raw"],**r["witness"])["accepted"]:
            raise ValueError("v101 original witness drift")


def run_study(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v101 frozen head required")
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    env=environment()
    if env!=protocol()["runtime"] or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"v101 runtime drift: {env!r}")
    retained=load_first_refit(V100_MANIFEST)
    models,training=restore_models(retained)
    sources=development_sources()
    source_by_id={s["id"]:s for s in sources}
    records=[]
    with threadpool_limits(1):
        for repeat in (-1,0,1,2):
            order=[(s["id"],route) for s in sources for route in ROUTES]
            random.Random(protocol()["order_seed"]+repeat).shuffle(order)
            for case_id,route in order:
                s=source_by_id[case_id]
                if route=="DIRECT":
                    row=observe_reference(s["raw"],route)
                elif route=="ORACLE":
                    row=observe_reference(s["raw"],route,s["basis"])
                else:
                    row=observe_candidate(s["raw"],route,models,training)
                records.append({"case_id":case_id,"pair_id":s["pair_id"],"group":s["group"],
                                "surface":s["surface"],"route":route,"repeat":repeat,**row})
            print(f"V101_REPEAT {repeat} {len(records)}",flush=True)
    report={
        "protocol":protocol(),"environment":env,"frozen_head":frozen_head,
        "v100_training_identity":{str(seed):retained["training"][f"QUOTIENT_s{seed}"]["weights_sha256"]
                                  for seed in MODEL_SEEDS},
        "development_specs":specs(),"records":records,
        "summary":summarize(records,sources),"stage":"completed","threadpools":threadpool_info(),
    }
    validate_original_witnesses(report)
    return report


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip); manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v101 first result already exists")
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(packed)
    m={"format":"neumann.final-adaptive-q34-v101.archive.v1","file":output.name,
       "frozen_head":report["frozen_head"],"rerun":False,
       "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
       "json_bytes":len(raw),"json_sha256":hashlib.sha256(raw).hexdigest(),
       "decision":report["summary"]["decision"],"summary":report["summary"]}
    manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    return m


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-gzip",required=True); p.add_argument("--manifest",required=True)
    p.add_argument("--frozen-head",default=os.environ.get("GITHUB_SHA"))
    args=p.parse_args()
    report=run_study(args.frozen_head)
    m=write_first(report,args.output_gzip,args.manifest)
    print("V101_FIRST_SUMMARY="+json.dumps(m["summary"],sort_keys=True,separators=(",",":")),flush=True)
    print("V101_FIRST_ARCHIVE="+json.dumps({k:v for k,v in m.items() if k!="summary"},
                                           sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
