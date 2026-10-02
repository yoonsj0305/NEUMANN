"""v0.0.102 fresh EXPAND4 Q34 holdout source registration only.

This module creates and validates the frozen source archive. It never restores a
model, runs learned inference, or executes a timed route comparison.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_basis_headroom_v082 import generate_case
from neumann1.lp_certificate_v081 import verify_standard_form_certificate


SOURCE_RUNTIME={
    "python":[3,12],
    "numpy":"2.3.5",
    "scipy":"1.17.0",
    "highspy":"1.15.1",
}

GROUPS=("m64_base","m64_surface","m128_base","m128_surface")


def protocol():
    return {
        "schema":"neumann.q34-expand4-fresh-source-v102.v1",
        "seed_base":102200,
        "base_cases":24,
        "views":48,
        "groups":{g:12 for g in GROUPS},
        "width_factor":16,
        "conditions":[1,1000],
        "surface_seed_offset":300000,
        "model_access":False,
        "timing":False,
        "route_evaluation":False,
        "v098_holdout_access":False,
        "openblas_coretype":"HASWELL",
        "runtime":SOURCE_RUNTIME,
    }


def base_specs():
    rows=[]
    for i in range(protocol()["base_cases"]):
        rows.append({
            "pair_id":f"fresh102_{i:02d}",
            "rows":64 if i<12 else 128,
            "condition":(1,1000)[i%2],
            "seed":protocol()["seed_base"]+i,
        })
    return rows


def view_specs():
    rows=[]
    for base in base_specs():
        for surface in (False,True):
            rows.append({
                **base,
                "id":f"{base['pair_id']}_{'surface' if surface else 'base'}",
                "group":f"m{base['rows']}_{'surface' if surface else 'base'}",
                "surface":surface,
            })
    return rows


def environment():
    import scipy
    import highspy
    return {
        "python":list(sys.version_info[:2]),
        "numpy":np.__version__,
        "scipy":scipy.__version__,
        "highspy":highspy.Highs().version(),
    }


def _surface(raw,seed):
    A=np.asarray(raw["A"],dtype=float).copy()
    b=np.asarray(raw["b"],dtype=float).copy()
    c=np.asarray(raw["c"],dtype=float).copy()
    m,n=A.shape
    rng=np.random.default_rng(seed)
    order=rng.permutation(m)
    sign=rng.choice([-1.0,1.0],size=m)
    A,b=A[order]*sign[:,None],b[order]*sign
    scaling=np.exp(rng.uniform(-1.5,1.5,size=n))
    A,c=A*scaling,c*scaling
    return {"A":A,"b":b,"c":c}


def generate_base(spec):
    m=spec["rows"]
    case=generate_case({
        "id":spec["pair_id"],"pair_id":spec["pair_id"],"rows":m,
        "width_factor":protocol()["width_factor"],"cols":16*m,
        "condition_number":spec["condition"],"replicate":0,"seed":spec["seed"],
    })
    A,b,c=storage.normalized(case["A"],case["b"],case["c"])
    return {"A":A,"b":b,"c":c},[int(i) for i in case["oracle_basis"]]


def pack_view(spec,raw,basis):
    label=storage.candidate_once(raw,np.asarray(basis),"v102_label_setup")
    if not label["accepted"]:
        raise ValueError("v102 fresh oracle label rejected")
    return {
        **spec,
        "cols":raw["A"].shape[1],
        "sha256":storage.input_digest(raw),
        "arrays":{k:storage.encode_array(v) for k,v in raw.items()},
        "label":label,
    }


def validate_archive(report):
    if report["protocol"]!=protocol() or report["stage"]!="sources_frozen":
        raise ValueError("v102 fresh source protocol/stage drift")
    if report["environment"]!=SOURCE_RUNTIME:
        raise ValueError("v102 fresh source runtime drift")
    if report["openblas_coretype"]!="HASWELL":
        raise ValueError("v102 fresh source BLAS dispatch drift")
    if (not report["threadpools"]
            or any(p["num_threads"]!=1 for p in report["threadpools"])):
        raise ValueError("v102 fresh source numerical threadpool drift")

    expected=view_specs()
    sources=report["sources"]
    if len(sources)!=48 or [s["id"] for s in sources]!=[s["id"] for s in expected]:
        raise ValueError("v102 fresh source coverage drift")
    if len({s["sha256"] for s in sources})!=48:
        raise ValueError("v102 fresh source digest collision")
    counts=Counter(s["group"] for s in sources)
    if counts!={g:12 for g in GROUPS}:
        raise ValueError("v102 fresh group coverage drift")

    pairs={}
    for s,e in zip(sources,expected):
        for k,v in e.items():
            if s[k]!=v:
                raise ValueError("v102 fresh source metadata drift")
        if s["cols"]!=16*s["rows"]:
            raise ValueError("v102 fresh source width drift")
        pairs.setdefault(s["pair_id"],set()).add(s["surface"])
        m,n=s["rows"],s["cols"]
        raw={k:storage.decode_array(s["arrays"][k],shape) for k,shape in (
            ("A",(m,n)),("b",(m,)),("c",(n,)))}
        if storage.input_digest(raw)!=s["sha256"]:
            raise ValueError("v102 fresh source bytes drift")
        if not verify_standard_form_certificate(
                **raw,**s["label"]["witness"])["accepted"]:
            raise ValueError("v102 fresh source oracle witness drift")
    if len(pairs)!=24 or any(v!={False,True} for v in pairs.values()):
        raise ValueError("v102 fresh pair coverage drift")


def build(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v102 source-registration head required")
    env=environment()
    if env!=SOURCE_RUNTIME or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"v102 source runtime/dispatch drift: {env!r}")

    sources=[]
    with threadpool_limits(1):
        pools=threadpool_info()
        if not pools or any(p["num_threads"]!=1 for p in pools):
            raise RuntimeError("v102 source threadpool drift")
        for base in base_specs():
            raw,basis=generate_base(base)
            for surface in (False,True):
                spec={
                    **base,
                    "id":f"{base['pair_id']}_{'surface' if surface else 'base'}",
                    "group":f"m{base['rows']}_{'surface' if surface else 'base'}",
                    "surface":surface,
                }
                view=(
                    _surface(raw,base["seed"]+protocol()["surface_seed_offset"])
                    if surface else raw
                )
                sources.append(pack_view(spec,view,basis))

    report={
        "protocol":protocol(),"environment":env,
        "openblas_coretype":os.environ.get("OPENBLAS_CORETYPE"),
        "frozen_head":frozen_head,"threadpools":pools,
        "sources":sources,"stage":"sources_frozen",
    }
    validate_archive(report)
    return report


def write_first(report,output_gzip,manifest_path):
    output=Path(output_gzip)
    manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v102 fresh holdout source archive already exists")
    validate_archive(report)
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.q34-expand4-fresh-source-v102.archive.v1",
        "file":output.name,"frozen_head":report["frozen_head"],"rerun":False,
        "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),"json_sha256":hashlib.sha256(raw).hexdigest(),
        "base_cases":24,"views":48,"groups":{g:12 for g in GROUPS},
        "model_access":False,"timing":False,"route_evaluation":False,
        "v098_holdout_access":False,
    }
    manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    return m


def load_registered(manifest_path):
    path=Path(manifest_path)
    m=json.loads(path.read_text())
    packed=(path.parent/m["file"]).read_bytes()
    if len(packed)!=m["gzip_bytes"] or hashlib.sha256(packed).hexdigest()!=m["gzip_sha256"]:
        raise ValueError("v102 source gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)!=m["json_bytes"] or hashlib.sha256(raw).hexdigest()!=m["json_sha256"]:
        raise ValueError("v102 source json identity drift")
    report=json.loads(raw)
    if report["frozen_head"]!=m["frozen_head"]:
        raise ValueError("v102 source head drift")
    validate_archive(report)
    return m,report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-gzip",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--frozen-head",default=os.environ.get("GITHUB_SHA"))
    args=p.parse_args()
    report=build(args.frozen_head)
    m=write_first(report,args.output_gzip,args.manifest)
    print("V102_SOURCE_MANIFEST="+json.dumps(
        m,sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
