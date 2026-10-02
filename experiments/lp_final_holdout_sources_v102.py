"""v0.0.102 phase 1: register final fresh holdout sources with no model access."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_basis_headroom_v082 import generate_case


GROUPS=("m64_base","m64_surface","m128_base","m128_surface")


def protocol():
    return {
        "schema":"neumann.final-q34-holdout-sources-v102.v1",
        "runtime":{
            "python":[3,12],
            "numpy":"2.3.5",
            "scipy":"1.17.0",
            "highspy":"1.15.1",
        },
        "seed_base":100500,
        "base_cases":24,
        "views":48,
        "surface_seed_offset":400000,
        "width_factor":16,
        "groups":list(GROUPS),
        "model_access":False,
        "candidate_inference":False,
        "timing":False,
        "route_evaluation":False,
        "v098_holdout_access":False,
        "v101_development_access":False,
    }


def environment():
    import scipy
    import highspy
    return {
        "python":list(sys.version_info[:2]),
        "numpy":np.__version__,
        "scipy":scipy.__version__,
        "highspy":highspy.Highs().version(),
    }


def specs():
    out=[]
    for i in range(protocol()["base_cases"]):
        rows=64 if i<12 else 128
        out.append({
            "pair_id":f"v102hold{i:02d}",
            "rows":rows,
            "cols":16*rows,
            "condition":(1,1000)[i%2],
            "seed":protocol()["seed_base"]+i,
        })
    return out


def _base(spec):
    m=spec["rows"]
    case=generate_case({
        "id":spec["pair_id"],"pair_id":spec["pair_id"],
        "rows":m,"width_factor":protocol()["width_factor"],
        "cols":protocol()["width_factor"]*m,
        "condition_number":spec["condition"],
        "replicate":0,"seed":spec["seed"],
    })
    A,b,c=storage.normalized(case["A"],case["b"],case["c"])
    return {"A":A,"b":b,"c":c},[int(i) for i in case["oracle_basis"]]


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


def pack_source(spec,raw,basis,surface):
    group=f"m{spec['rows']}_{'surface' if surface else 'base'}"
    label=storage.candidate_once(raw,basis,"v102_holdout_oracle_registration")
    if not label["accepted"]:
        raise ValueError("v102 registered Oracle basis rejected")
    return {
        **spec,
        "id":f"{spec['pair_id']}_{'surface' if surface else 'base'}",
        "group":group,
        "surface":surface,
        "sha256":storage.input_digest(raw),
        "arrays":{k:storage.encode_array(v) for k,v in raw.items()},
        "basis":list(basis),
        "oracle_registration_certificate":label,
    }


def generate_sources():
    rows=[]
    for spec in specs():
        raw,basis=_base(spec)
        rows.append(pack_source(spec,raw,basis,False))
        surface=_surface(raw,spec["seed"]+protocol()["surface_seed_offset"])
        rows.append(pack_source(spec,surface,basis,True))
    if len(rows)!=protocol()["views"]:
        raise ValueError("v102 holdout view count drift")
    counts={g:sum(r["group"]==g for r in rows) for g in GROUPS}
    if counts!={g:12 for g in GROUPS}:
        raise ValueError("v102 holdout cell coverage drift")
    return rows


def write_first(output_gzip,manifest_path,frozen_head):
    if type(frozen_head) is not str or len(frozen_head)!=40:
        raise ValueError("40-character v102 registration head required")
    if environment()!=protocol()["runtime"]:
        raise RuntimeError("v102 source runtime drift")
    output=Path(output_gzip); manifest=Path(manifest_path)
    if output.exists() or manifest.exists():
        raise FileExistsError("v102 holdout source archive already exists")
    report={
        "protocol":protocol(),
        "environment":environment(),
        "frozen_head":frozen_head,
        "specs":specs(),
        "sources":generate_sources(),
        "stage":"registered",
    }
    raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(packed)
    m={
        "format":"neumann.final-q34-holdout-sources-v102.archive.v1",
        "file":output.name,
        "frozen_head":frozen_head,
        "rerun":False,
        "gzip_bytes":len(packed),
        "gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "json_bytes":len(raw),
        "json_sha256":hashlib.sha256(raw).hexdigest(),
        "source_count":len(report["sources"]),
        "cell_counts":{g:sum(s["group"]==g for s in report["sources"]) for g in GROUPS},
        "model_access":False,
        "candidate_inference":False,
        "timing":False,
        "route_evaluation":False,
    }
    manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    return m


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-gzip",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--frozen-head",default=os.environ.get("GITHUB_SHA"))
    args=p.parse_args()
    m=write_first(args.output_gzip,args.manifest,args.frozen_head)
    print("V102_SOURCE_MANIFEST="+json.dumps(m,sort_keys=True,separators=(",",":")),flush=True)


if __name__=="__main__":
    main()
