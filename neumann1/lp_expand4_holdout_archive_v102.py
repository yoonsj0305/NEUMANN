"""Byte-exact retained replay for the first valid v0.0.102 fresh Q34 evaluation.

This validates immutable archive bytes, source/authority identities, accepted
original-problem witnesses, frozen checkpoint identities and derived summaries.
It never fits a model, runs inference, calls a solver, or performs timing.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path

from experiments import lp_expand4_holdout_v102 as runner
from experiments.lp_expand4_holdout_register_v102 import load_registered
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_frozen_support_expansion_archive_v101 import load_first_expansion


EXPECTED_FORMAT="neumann.q34-expand4-fresh-eval-v102.archive.v1"
EXPECTED_HEAD="46af13c3d7d9b1a87f0a0db8511f5972511beb16"
EXPECTED_DECISION="Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
EXPECTED_ADVANCE=True
EXPECTED_WEIGHTS={
    "100001":"c19ad47a4fd310ba469308529ff87134c6ea5de3066ad5750c4af54d658457ea",
    "100002":"20d012c6536cdb4041f6620307b5dbb1c1f3ab56f9438cbff971123a657c3ab5",
}
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


def _training_identity_from_authority():
    authority=load_first_expansion(runner.AUTHORITY_MANIFEST)
    training=authority["training_identity"]
    normalized={str(k):v for k,v in training.items()}
    if set(normalized)!=set(EXPECTED_WEIGHTS):
        raise ValueError("v102 authority seed identity drift")
    for seed,sha in EXPECTED_WEIGHTS.items():
        if normalized[seed]["weights_sha256"]!=sha:
            raise ValueError("v102 frozen weight identity drift")
    return authority,normalized


def _validate_replay(report):
    if report["protocol"]!=runner.protocol() or report["stage"]!="completed":
        raise ValueError("v102 replay protocol/stage drift")
    if report["environment"]!=runner.protocol()["runtime"]:
        raise ValueError("v102 replay environment drift")
    if report["torch_threads"]!={"intraop":1,"interop":1}:
        raise ValueError("v102 replay torch thread drift")
    if (not report["threadpools"]
            or any(p["num_threads"]!=1 for p in report["threadpools"])):
        raise ValueError("v102 replay numerical threadpool drift")

    source_manifest,source_report=load_registered(runner.SOURCE_MANIFEST)
    expected_source={
        "frozen_head":source_manifest["frozen_head"],
        "gzip_sha256":source_manifest["gzip_sha256"],
        "json_sha256":source_manifest["json_sha256"],
    }
    if report["source_archive_identity"]!=expected_source:
        raise ValueError("v102 replay source identity drift")

    authority_manifest=json.loads(Path(runner.AUTHORITY_MANIFEST).read_text())
    expected_authority={
        "frozen_head":authority_manifest["frozen_head"],
        "gzip_sha256":authority_manifest["gzip_sha256"],
        "json_sha256":authority_manifest["json_sha256"],
        "decision":authority_manifest["decision"],
    }
    if report["authority_archive_identity"]!=expected_authority:
        raise ValueError("v102 replay authority archive drift")

    _,training=_training_identity_from_authority()
    report_training={str(k):v for k,v in report["training_identity"].items()}
    if report_training!=training:
        raise ValueError("v102 replay frozen training identity drift")

    sources=source_report["sources"]
    if len(sources)!=48:
        raise ValueError("v102 replay source count drift")
    source_by_id={s["id"]:s for s in sources}
    raws={s["id"]:runner.raw_source(s) for s in sources}

    expected_keys={
        (s["id"],route,repeat)
        for s in sources for route in runner.ROUTES for repeat in (-1,0,1,2)
    }
    keys=[(r["case_id"],r["route"],r["repeat"]) for r in report["records"]]
    if len(keys)!=len(set(keys)) or set(keys)!=expected_keys:
        raise ValueError("v102 replay observation coverage drift")

    for r in report["records"]:
        source=source_by_id[r["case_id"]]
        if (r["pair_id"]!=source["pair_id"] or r["group"]!=source["group"]
                or r["surface"]!=source["surface"]):
            raise ValueError("v102 replay source metadata drift")
        raw=raws[r["case_id"]]
        expected_investment=0.0
        if r["route"].startswith("EXPAND4_s"):
            seed=r["route"].rsplit("s",1)[1]
            row=training[seed]
            expected_investment=(row["feature_setup_ms"]+row["fit_ms"])/runner.protocol()["amortization_queries"]
        if not math.isclose(
                r["amortized_investment_ms"],expected_investment,
                rel_tol=0.0,abs_tol=1e-12):
            raise ValueError("v102 replay investment drift")
        if r["accepted"] and (
            r["witness"] is None
            or not verify_standard_form_certificate(**raw,**r["witness"])["accepted"]
        ):
            raise ValueError("v102 replay accepted witness drift")

    derived=runner.summarize(report["records"],sources)
    if not _numeric_equal(report["summary"],derived):
        raise ValueError("v102 replay summary drift beyond cross-runtime tolerance")
    if report["summary"]["decision"]!=EXPECTED_DECISION:
        raise ValueError("v102 replay decision drift")
    if report["summary"]["advance_q5"] is not EXPECTED_ADVANCE:
        raise ValueError("v102 replay Q5 authority drift")


def load_first_evaluation(manifest_path):
    path=Path(manifest_path)
    manifest=json.loads(path.read_text())
    required={
        "format","file","frozen_head","rerun","gzip_bytes","gzip_sha256",
        "json_bytes","json_sha256","decision","advance_q5","summary",
    }
    if set(manifest)!=required:
        raise ValueError("v102 evaluation manifest schema drift")
    if manifest["format"]!=EXPECTED_FORMAT or manifest["rerun"] is not False:
        raise ValueError("v102 evaluation archive identity drift")
    if manifest["frozen_head"]!=EXPECTED_HEAD:
        raise ValueError("v102 evaluation frozen head drift")
    if manifest["decision"]!=EXPECTED_DECISION:
        raise ValueError("v102 evaluation first decision drift")
    if manifest["advance_q5"] is not EXPECTED_ADVANCE:
        raise ValueError("v102 evaluation advance authority drift")

    name=manifest["file"]
    if type(name) is not str or Path(name).name!=name:
        raise ValueError("unsafe v102 evaluation archive filename")
    packed=(path.parent/name).read_bytes()
    if (len(packed)!=manifest["gzip_bytes"]
            or hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]):
        raise ValueError("v102 evaluation gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("v102 evaluation decoded archive too large")
    if (len(raw)!=manifest["json_bytes"]
            or hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]):
        raise ValueError("v102 evaluation json identity drift")

    report=json.loads(raw)
    if report["frozen_head"]!=manifest["frozen_head"]:
        raise ValueError("v102 evaluation report head drift")
    _validate_replay(report)
    if (not _numeric_equal(report["summary"],manifest["summary"])
            or report["summary"]["decision"]!=manifest["decision"]
            or report["summary"]["advance_q5"] is not manifest["advance_q5"]):
        raise ValueError("v102 evaluation manifest summary drift")
    return report
