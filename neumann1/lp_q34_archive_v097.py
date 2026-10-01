"""Byte-exact replay for the first valid v0.0.97 Q34 tournament.

The archive bytes, identities and original-problem witnesses are exact. Derived
floating summaries are recomputed solver-free and compared numerically because
the first run used Python 3.12 while legacy sequence CI uses Python 3.11; their
float sum implementations may differ by a few ulps.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path

from experiments import lp_q34_tournament_v097 as runner
from experiments.lp_shortlist_screen_v089 import raw_source
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study


EXPECTED_FORMAT="neumann.q34-support-tournament-v097.archive.v1"
EXPECTED_FROZEN_HEAD="d7ae02ca0418a4b93020e0e8fbf2ecbcd5b1e975"
EXPECTED_DECISION="ADMIT_FRESH_Q34_HOLDOUT"
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


def _validate_replay(report):
    if report["protocol"]!=runner.protocol() or report["stage"]!="completed":
        raise ValueError("protocol/stage drift")
    if report["environment"]!=runner.protocol()["runtime"]:
        raise ValueError("environment drift")
    study=load_study(runner.protocol()["source_manifest"])
    sources=study["train_sources"][:runner.protocol()["cases"]]
    identities=[{"id":s["id"],"sha256":s["sha256"]} for s in sources]
    if report["source_ids"]!=identities:
        raise ValueError("source identity drift")
    if report["training_setup_ms"]!=study["training_setup_ms"]:
        raise ValueError("training setup drift")
    expected_training={k:v["weights_sha256"] for k,v in study["training"].items()}
    if report["training_identity"]!=expected_training:
        raise ValueError("checkpoint identity drift")

    raws={s["id"]:raw_source(s) for s in sources}
    source_by_id={s["id"]:s for s in sources}
    for r in report["records"]:
        raw=raws[r["case_id"]]
        expected=runner.learned_investment_per_query(
            study["training"],study["training_setup_ms"],r["route"])
        if not math.isclose(
                r["amortized_investment_ms"],expected,rel_tol=0.0,abs_tol=1e-12):
            raise ValueError("investment drift")
        if r["accepted"] and (
                r["witness"] is None or not verify_standard_form_certificate(
                    **raw,**r["witness"])["accepted"]):
            raise ValueError("accepted original witness drift")
        if r["route"]=="ORACLE":
            basis=list(source_by_id[r["case_id"]]["label"]["indices"])
            if r["proposal"]!={"indices":basis,"oracle":True}:
                raise ValueError("oracle support drift")

    derived=runner.summarize(report["records"],sources)
    if not _numeric_equal(report["summary"],derived):
        raise ValueError("summary drift beyond cross-runtime float tolerance")


def load_first_tournament(manifest_path):
    path=Path(manifest_path)
    manifest=json.loads(path.read_text())
    required={
        "format","file","rerun","frozen_head","gzip_bytes","gzip_sha256",
        "json_bytes","json_sha256","decision","summary",
    }
    if set(manifest)!=required:
        raise ValueError("manifest schema drift")
    if manifest["format"]!=EXPECTED_FORMAT or manifest["rerun"] is not False:
        raise ValueError("archive identity drift")
    if manifest["frozen_head"]!=EXPECTED_FROZEN_HEAD:
        raise ValueError("frozen head drift")
    if manifest["decision"]!=EXPECTED_DECISION:
        raise ValueError("first decision drift")
    name=manifest["file"]
    if type(name) is not str or Path(name).name!=name:
        raise ValueError("unsafe archive filename")
    packed=(path.parent/name).read_bytes()
    if (len(packed)!=manifest["gzip_bytes"]
            or hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]):
        raise ValueError("gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("decoded archive too large")
    if (len(raw)!=manifest["json_bytes"]
            or hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]):
        raise ValueError("decoded identity drift")
    report=json.loads(raw)
    if report["frozen_head"]!=manifest["frozen_head"]:
        raise ValueError("report head drift")
    _validate_replay(report)
    if (not _numeric_equal(report["summary"],manifest["summary"])
            or report["summary"]["decision"]!=manifest["decision"]):
        raise ValueError("summary/decision drift")
    return report
