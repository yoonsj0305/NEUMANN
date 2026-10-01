"""v0.0.99 label-free equivalence-quotient representation audit."""
from __future__ import annotations

import base64
import math

import numpy as np
import torch

from experiments import lp_feature_probe_v093 as f
from experiments.lp_input_compaction_v094 import features as current_cg5_features
from experiments.lp_shortlist_screen_v089 import raw_source
from experiments.lp_state_models_v087 import roster
from experiments.lp_model_study_v088 import pack_weights
from neumann1.lp_model_study_archive_v088 import load_study

SEEDS=(87001,87002)
VIEWS=("signed_row","positive_column","combined")
TRAIN_MANIFEST="docs/experiments/results/v088_completed.manifest.json"


def protocol():
    return {
        "schema":"neumann.lp-equivalence-quotient-v099.v1",
        "opened_sources":48,
        "views":list(VIEWS),
        "metamorphic_seed_base":99900,
        "quotient_drift_max":1e-8,
        "channel_std_min":1e-8,
        "size_slot_ratio_max":1.20,
        "new_fitting":False,
        "solver_calls":False,
        "labels_used":False,
        "v098_holdout_access":False,
        "global_q3":"OPEN",
        "global_q4":"OPEN",
    }


def quotient_columns(raw):
    D,b,q=f.normalized(**raw)
    m,n=D.shape
    y,a=f.dual_fit(D,q,np.arange(n),"cg",5)
    z=f.cg(lambda x:D@(D.T@x),b,5)
    cs=max(1.0,float(np.sqrt(np.mean(q*q))))
    bs=max(1.0,float(np.linalg.norm(b)))
    bunit=np.abs(b)/bs
    cols=np.column_stack((
        q/cs,
        (q-D.T@y-a)/cs,
        (D.T@z)/bs,
        (D.T@b)/bs,
        np.abs(D).T@bunit,
        np.abs(D).sum(0)/math.sqrt(m),
        np.full(n,m/n),
        np.ones(n),
    ))
    if cols.shape!=(n,8) or not np.isfinite(cols).all():
        raise ValueError("nonfinite or malformed quotient point features")
    return D,cols


def equivalent_view(raw,view,seed):
    if view not in VIEWS:
        raise ValueError("unregistered equivalence view")
    rng=np.random.default_rng(seed)
    A=np.asarray(raw["A"],dtype=float).copy()
    b=np.asarray(raw["b"],dtype=float).copy()
    c=np.asarray(raw["c"],dtype=float).copy()
    m,n=A.shape
    if view in ("signed_row","combined"):
        order=rng.permutation(m)
        signs=rng.choice(np.array([-1.0,1.0]),size=m)
        A=A[order]*signs[:,None]
        b=b[order]*signs
    if view in ("positive_column","combined"):
        scaling=np.exp(rng.uniform(-1.5,1.5,size=n))
        A=A*scaling
        c=c*scaling
    return {"A":A,"b":b,"c":c}


def restore_point_models(training):
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
        model.eval()
        if pack_weights(model)[1]!=training[key]["weights_sha256"]:
            raise ValueError("point checkpoint identity drift")
        models[key]=model
    return models


def current_support(cols,model,m):
    tensor=torch.tensor(cols,dtype=torch.float32)
    with torch.inference_mode():
        score=model.head(model.cols(tensor)).squeeze(1)
    if not torch.isfinite(score).all():
        raise ValueError("nonfinite frozen point score")
    order=torch.argsort(score,descending=True,stable=True)
    return order[:min(len(order),2*m)].tolist(),score.numpy()


def _jaccard(a,b):
    a,b=set(a),set(b)
    return len(a&b)/len(a|b) if a or b else 1.0


def analyze():
    retained=load_study(TRAIN_MANIFEST)
    sources=retained["train_sources"]
    if len(sources)!=protocol()["opened_sources"]:
        raise ValueError("opened training source coverage drift")
    models=restore_point_models(retained["training"])

    records=[]
    quotient_values=[]
    by_m={32:[],64:[]}
    current_channel_max=np.zeros(8,dtype=float)
    quotient_channel_max=np.zeros(8,dtype=float)
    support_exact={seed:0 for seed in SEEDS}
    support_jaccard={seed:[] for seed in SEEDS}

    for case_index,source in enumerate(sources):
        raw=raw_source(source)
        m,n=raw["A"].shape
        if m not in by_m:
            raise ValueError("unexpected opened size")
        _,_,current_base=current_cg5_features(raw)
        _,quotient_base=quotient_columns(raw)
        quotient_values.append(quotient_base)
        by_m[m].append(quotient_base[:,5])
        base_support={}
        for seed in SEEDS:
            base_support[seed],_=current_support(
                current_base,models[f"point16_s{seed}"],m)

        for view_index,view in enumerate(VIEWS):
            seed=protocol()["metamorphic_seed_base"]+case_index*len(VIEWS)+view_index
            transformed=equivalent_view(raw,view,seed)
            _,_,current_view=current_cg5_features(transformed)
            _,quotient_view=quotient_columns(transformed)
            current_delta=np.max(np.abs(current_view-current_base),axis=0)
            quotient_delta=np.max(np.abs(quotient_view-quotient_base),axis=0)
            current_channel_max=np.maximum(current_channel_max,current_delta)
            quotient_channel_max=np.maximum(quotient_channel_max,quotient_delta)

            row={
                "case_id":source["id"],
                "case_index":case_index,
                "rows":m,
                "cols":n,
                "view":view,
                "seed":seed,
                "current_max_abs_drift":float(np.max(current_delta)),
                "quotient_max_abs_drift":float(np.max(quotient_delta)),
                "current_channel_max_abs_drift":current_delta.tolist(),
                "quotient_channel_max_abs_drift":quotient_delta.tolist(),
                "point_support":{},
            }
            for model_seed in SEEDS:
                support,_=current_support(
                    current_view,models[f"point16_s{model_seed}"],m)
                exact=support==base_support[model_seed]
                jac=_jaccard(support,base_support[model_seed])
                support_exact[model_seed]+=int(exact)
                support_jaccard[model_seed].append(jac)
                row["point_support"][str(model_seed)]={
                    "exact":exact,"jaccard":jac,
                }
            records.append(row)

    all_q=np.concatenate(quotient_values,axis=0)
    first6_std=np.std(all_q[:,:6],axis=0)
    med32=float(np.median(np.concatenate(by_m[32])))
    med64=float(np.median(np.concatenate(by_m[64])))
    size_ratio=max(med32,med64)/min(med32,med64)
    max_q=float(np.max(quotient_channel_max))
    finite=bool(np.isfinite(all_q).all())
    passed=bool(
        finite
        and max_q<=protocol()["quotient_drift_max"]
        and np.all(first6_std>protocol()["channel_std_min"])
        and size_ratio<=protocol()["size_slot_ratio_max"]
    )
    return {
        "protocol":protocol(),
        "decision":(
            "ADMIT_QUOTIENT_POINT_REFIT_ON_OPENED_DEV"
            if passed else
            "REJECT_QUOTIENT_REPRESENTATION_BEFORE_TRAINING"
        ),
        "quotient_pass":passed,
        "records":records,
        "summary":{
            "equivalent_views":len(records),
            "current_channel_max_abs_drift":current_channel_max.tolist(),
            "current_max_abs_drift":float(np.max(current_channel_max)),
            "quotient_channel_max_abs_drift":quotient_channel_max.tolist(),
            "quotient_max_abs_drift":max_q,
            "quotient_first6_global_std":first6_std.tolist(),
            "slot6_median_m32":med32,
            "slot6_median_m64":med64,
            "slot6_size_ratio":size_ratio,
            "finite":finite,
            "current_point_support_exact":{
                str(seed):support_exact[seed] for seed in SEEDS
            },
            "current_point_support_exact_rate":{
                str(seed):support_exact[seed]/len(records) for seed in SEEDS
            },
            "current_point_support_mean_jaccard":{
                str(seed):float(np.mean(support_jaccard[seed])) for seed in SEEDS
            },
        },
        "new_fitting":False,
        "solver_calls":0,
        "labels_used":False,
        "v098_holdout_access":False,
        "global_q3":"OPEN",
        "global_q4":"OPEN",
    }
