"""Retained v0.0.101 archive replay without fitting, inference, solver, or timing."""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path

from experiments.lp_frozen_support_expansion_v101 import protocol, summarize

EXPECTED_FORMAT="neumann.frozen-support-expansion-v101.archive.v1"
EXPECTED_HEAD="e6fb888c1ef216085832ea723bbac4ad8953ca22"
EXPECTED_DECISION="ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_FROZEN_SUPPORT_SYSTEM"
MAX_JSON_BYTES=64*1024*1024


def _numeric_equal(a,b):
    if type(a) is not type(b):
        return False
    if isinstance(a,float):
        return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
    if isinstance(a,dict):
        return set(a)==set(b) and all(_numeric_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):
        return len(a)==len(b) and all(_numeric_equal(x,y) for x,y in zip(a,b))
    return a==b


def load_first_expansion(manifest_path):
    path=Path(manifest_path)
    manifest=json.loads(path.read_text())
    required={
        "format","file","frozen_head","rerun","gzip_bytes","gzip_sha256",
        "json_bytes","json_sha256","decision","summary",
    }
    if set(manifest)!=required:
        raise ValueError("v101 manifest schema drift")
    if manifest["format"]!=EXPECTED_FORMAT or manifest["rerun"] is not False:
        raise ValueError("v101 archive identity drift")
    if manifest["frozen_head"]!=EXPECTED_HEAD:
        raise ValueError("v101 frozen head drift")
    if manifest["decision"]!=EXPECTED_DECISION:
        raise ValueError("v101 first decision drift")
    name=manifest["file"]
    if type(name) is not str or Path(name).name!=name:
        raise ValueError("unsafe v101 archive filename")
    packed=(path.parent/name).read_bytes()
    if len(packed)!=manifest["gzip_bytes"]:
        raise ValueError("v101 gzip length drift")
    if hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]:
        raise ValueError("v101 gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("v101 decoded archive too large")
    if len(raw)!=manifest["json_bytes"]:
        raise ValueError("v101 json length drift")
    if hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]:
        raise ValueError("v101 json identity drift")
    report=json.loads(raw)
    if report["protocol"]!=protocol():
        raise ValueError("v101 protocol drift")
    if report["frozen_head"]!=EXPECTED_HEAD or report["stage"]!="completed":
        raise ValueError("v101 report identity drift")
    replay=summarize(report["records"],report["development_sources"])
    if not _numeric_equal(replay,report["summary"]):
        raise ValueError("v101 summary drift beyond cross-runtime float tolerance")
    if not _numeric_equal(report["summary"],manifest["summary"]):
        raise ValueError("v101 manifest summary drift")
    if (replay["decision"]!=EXPECTED_DECISION
            or report["summary"]["decision"]!=manifest["decision"]):
        raise ValueError("v101 replay decision drift")
    return report
