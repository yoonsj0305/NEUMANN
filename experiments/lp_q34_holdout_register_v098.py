"""v0.0.98 fresh Q34 holdout source registration only.

This module creates and validates the frozen source archive. It never restores a
model, runs learned inference, or executes the timed Q34 comparison.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
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


def protocol():
    return {
        "schema":"neumann.q34-fresh-holdout-source-v098.v1",
        "seed_base":98200,
        "cases":24,
        "groups":{"iid64":12,"size_surface_shift128":12},
        "width_factor":16,
        "conditions":[1,1000],
        "model_access":False,
        "timing":False,
        "route_evaluation":False,
        "openblas_coretype":"HASWELL",
        "runtime":SOURCE_RUNTIME,
    }


def specs():
    rows=[]
    for i in range(24):
        shifted=i>=12
        rows.append({
            "id":f"fresh{i:02d}",
            "group":"size_surface_shift128" if shifted else "iid64",
            "rows":128 if shifted else 64,
            "condition":(1,1000)[i%2],
            "seed":98200+i,
            "surface":shifted,
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


def generate(spec):
    m=spec["rows"]
    case=generate_case({
        "id":spec["id"],"pair_id":spec["id"],"rows":m,
        "width_factor":16,"cols":16*m,
        "condition_number":spec["condition"],"replicate":0,"seed":spec["seed"],
    })
    A,b,c=storage.normalized(case["A"],case["b"],case["c"])
    if spec["surface"]:
        rng=np.random.default_rng(spec["seed"]+100000)
        order=rng.permutation(m)
        sign=rng.choice([-1.0,1.0],size=m)
        A,b=A[order]*sign[:,None],b[order]*sign
        scaling=np.exp(rng.uniform(-1.5,1.5,size=A.shape[1]))
        A,c=A*scaling,c*scaling
    raw={"A":A,"b":b,"c":c}
    label=storage.candidate_once(raw,np.asarray(case["oracle_basis"]),"v098_label_setup")
    if not label["accepted"]:
        raise ValueError("fresh holdout oracle label rejected")
    return raw,label


def pack_source(spec,raw,label):
    return {
        **spec,"cols":raw["A"].shape[1],"sha256":storage.input_digest(raw),
        "arrays":{k:storage.encode_array(v) for k,v in raw.items()},
        "label":label,
    }


def validate_archive(report):
    if report["protocol"]!=protocol() or report["stage"]!="sources_frozen":
        raise ValueError("fresh source protocol/stage drift")
    if report["environment"]!=SOURCE_RUNTIME:
        raise ValueError("fresh source runtime drift")
    if report["openblas_coretype"]!="HASWELL":
        raise ValueError("fresh source BLAS dispatch drift")
    if (not report["threadpools"]
            or any(p["num_threads"]!=1 for p in report["threadpools"])):
        raise ValueError("fresh source numerical threadpool drift")
    expected=specs()
    sources=report["sources"]
    if len(sources)!=24 or [s["id"] for s in sources]!=[s["id"] for s in expected]:
        raise ValueError("fresh source coverage drift")
    if len({s["sha256"] for s in sources})!=24:
        raise ValueError("fresh source digest collision")
    for s,e in zip(sources,expected):
        for k,v in e.items():
            if s[k]!=v:
                raise ValueError("fresh source metadata drift")
        if s["cols"]!=16*s["rows"]:
            raise ValueError("fresh source width drift")
        m,n=s["rows"],s["cols"]
        raw={k:storage.decode_array(s["arrays"][k],shape) for k,shape in (
            ("A",(m,n)),("b",(m,)),("c",(n,)))}
        if storage.input_digest(raw)!=s["sha256"]:
            raise ValueError("fresh source bytes drift")
        if not verify_standard_form_certificate(**raw,**s["label"]["witness"])["accepted"]:
            raise ValueError("fresh source oracle witness drift")


def build(frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character source-registration head required")
    env=environment()
    if env!=SOURCE_RUNTIME or os.environ.get("OPENBLAS_CORETYPE")!="HASWELL":
        raise RuntimeError(f"fresh source runtime/dispatch drift: {env!r}")
    sources=[]
    with threadpool_limits(1):
        pools=threadpool_info()
        if not pools or any(p["num_threads"]!=1 for p in pools):
            raise RuntimeError("fresh source threadpool drift")
        for spec in specs():
            raw,label=generate(spec)
            sources.append(pack_source(spec,raw,label))
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
        raise FileExistsError("fresh holdout source archive already exists")
    validate_archive(report)
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.q34-fresh-holdout-source-v098.archive.v1",
        "file":output.name,"frozen_head":report["frozen_head"],"rerun":False,
        "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),"json_sha256":hashlib.sha256(raw).hexdigest(),
        "cases":24,"groups":{"iid64":12,"size_surface_shift128":12},
        "model_access":False,"timing":False,"route_evaluation":False,
    }
    manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    return m


def load_registered(manifest_path):
    path=Path(manifest_path)
    m=json.loads(path.read_text())
    packed=(path.parent/m["file"]).read_bytes()
    if len(packed)!=m["gzip_bytes"] or hashlib.sha256(packed).hexdigest()!=m["gzip_sha256"]:
        raise ValueError("fresh source gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)!=m["json_bytes"] or hashlib.sha256(raw).hexdigest()!=m["json_sha256"]:
        raise ValueError("fresh source json identity drift")
    report=json.loads(raw)
    if report["frozen_head"]!=m["frozen_head"]:
        raise ValueError("fresh source head drift")
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
    print("V098_SOURCE_MANIFEST="+json.dumps(m,sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
