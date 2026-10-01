"""Byte-exact replay for v0.0.98 fresh Q34 source registration and evaluation.

Archive bytes, source/checkpoint identities, original-problem witnesses, and the
discrete FAIL decision are exact. Derived floating summaries are recomputed
without model inference, fitting, solver execution, or timing and compared with
1e-12 tolerance for Python 3.11/3.12 summation ulps.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path

from experiments import lp_q34_holdout_v098 as runner
from experiments.lp_q34_holdout_register_v098 import load_registered
from experiments.lp_shortlist_screen_v089 import raw_source
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study

SOURCE_FORMAT="neumann.q34-fresh-holdout-source-v098.archive.v1"
SOURCE_HEAD="16192baff13a23ade8a52927399268652a419811"
SOURCE_GZIP_SHA="d7e1b401d955ef7ded8763536b3b32d5d38b9c333de8df28bab0cfb55f7fd5bb"
SOURCE_JSON_SHA="f8933476e4ad443e0b81c3e2131f0c9b69d2f708b981c81d93d51f228dfe3dff"
EVAL_FORMAT="neumann.q34-fresh-holdout-eval-v098.archive.v1"
EVAL_HEAD="f924080b1c2a76c5bb46bd9ae2a9132dc34379b3"
EVAL_DECISION="Q34_FRESH_HOLDOUT_FAIL_NO_Q5"
EVAL_GZIP_SHA="588780775aee6ff4712b89b003c232884343a74f0113a9a25c859490d30242c7"
EVAL_JSON_SHA="478bd9bcf2e85b04ac718296e68013b8e907d7bb27d78102b5d4624da1518123"
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


def load_fresh_sources(manifest_path):
    manifest,report=load_registered(manifest_path)
    if manifest["format"]!=SOURCE_FORMAT or manifest["frozen_head"]!=SOURCE_HEAD:
        raise ValueError("fresh source identity drift")
    if manifest["gzip_sha256"]!=SOURCE_GZIP_SHA or manifest["json_sha256"]!=SOURCE_JSON_SHA:
        raise ValueError("fresh source first-byte identity drift")
    if manifest["rerun"] is not False:
        raise ValueError("fresh source rerun drift")
    if manifest["model_access"] is not False or manifest["timing"] is not False:
        raise ValueError("fresh source authority drift")
    if manifest["route_evaluation"] is not False:
        raise ValueError("fresh source route-evaluation drift")
    return manifest,report


def _validate_eval_replay(report,source_report):
    if report["protocol"]!=runner.protocol() or report["stage"]!="completed":
        raise ValueError("fresh evaluation protocol/stage drift")
    if report["environment"]!=runner.protocol()["runtime"]:
        raise ValueError("fresh evaluation environment drift")
    if report["torch_threads"]!={"intraop":1,"interop":1}:
        raise ValueError("fresh evaluation torch-thread drift")
    if not report["threadpools"] or any(p["num_threads"]!=1 for p in report["threadpools"]):
        raise ValueError("fresh evaluation numerical-thread drift")

    sources=source_report["sources"]
    raws={s["id"]:raw_source(s) for s in sources}
    source_manifest,_=load_fresh_sources(runner.protocol()["source_manifest"])
    expected_source={
        "frozen_head":source_manifest["frozen_head"],
        "gzip_sha256":source_manifest["gzip_sha256"],
        "json_sha256":source_manifest["json_sha256"],
    }
    if report["source_archive_identity"]!=expected_source:
        raise ValueError("fresh source linkage drift")

    retained=load_study("docs/experiments/results/v088_completed.manifest.json")
    expected_points={
        f"point16_s{s}":retained["training"][f"point16_s{s}"]["weights_sha256"]
        for s in runner.SEEDS
    }
    if report["point_checkpoint_identity"]!=expected_points:
        raise ValueError("fresh point checkpoint identity drift")
    if report["training_setup_ms"]!=retained["training_setup_ms"]:
        raise ValueError("fresh training setup drift")

    expected_keys={
        (s["id"],route,repeat)
        for s in sources for route in runner.ROUTES for repeat in (-1,0,1,2)
    }
    actual_keys=[(r["case_id"],r["route"],r["repeat"]) for r in report["records"]]
    if len(actual_keys)!=len(expected_keys) or set(actual_keys)!=expected_keys:
        raise ValueError("fresh retained observation coverage drift")

    for r in report["records"]:
        raw=raws[r["case_id"]]
        expected=runner.investment_per_query(
            retained["training"],retained["training_setup_ms"],r["route"])
        if not math.isclose(
                r["amortized_investment_ms"],expected,rel_tol=0.0,abs_tol=1e-12):
            raise ValueError("fresh investment drift")
        if r["accepted"] and (
                r["witness"] is None or not verify_standard_form_certificate(
                    **raw,**r["witness"])["accepted"]):
            raise ValueError("fresh accepted original witness drift")

    derived=runner.summarize(report["records"],sources)
    if not _numeric_equal(report["summary"],derived):
        raise ValueError("fresh summary drift beyond cross-runtime float tolerance")


def load_first_fresh_evaluation(manifest_path):
    path=Path(manifest_path)
    manifest=json.loads(path.read_text())
    required={
        "format","file","frozen_head","rerun","gzip_bytes","gzip_sha256",
        "json_bytes","json_sha256","decision","advance_q5","summary",
    }
    if set(manifest)!=required:
        raise ValueError("fresh evaluation manifest schema drift")
    if manifest["format"]!=EVAL_FORMAT or manifest["frozen_head"]!=EVAL_HEAD:
        raise ValueError("fresh evaluation identity drift")
    if manifest["rerun"] is not False:
        raise ValueError("fresh evaluation rerun drift")
    if manifest["decision"]!=EVAL_DECISION or manifest["advance_q5"] is not False:
        raise ValueError("fresh evaluation first decision drift")
    if manifest["gzip_sha256"]!=EVAL_GZIP_SHA or manifest["json_sha256"]!=EVAL_JSON_SHA:
        raise ValueError("fresh evaluation first-byte identity drift")

    name=manifest["file"]
    if type(name) is not str or Path(name).name!=name:
        raise ValueError("unsafe fresh evaluation filename")
    packed=(path.parent/name).read_bytes()
    if (len(packed)!=manifest["gzip_bytes"]
            or hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]):
        raise ValueError("fresh evaluation gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("fresh evaluation decoded archive too large")
    if (len(raw)!=manifest["json_bytes"]
            or hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]):
        raise ValueError("fresh evaluation decoded identity drift")
    report=json.loads(raw)
    if report["frozen_head"]!=manifest["frozen_head"]:
        raise ValueError("fresh evaluation report head drift")

    _,source_report=load_fresh_sources(runner.protocol()["source_manifest"])
    _validate_eval_replay(report,source_report)
    if (not _numeric_equal(report["summary"],manifest["summary"])
            or report["summary"]["decision"]!=manifest["decision"]
            or report["summary"]["advance_q5"] is not False):
        raise ValueError("fresh evaluation summary/decision drift")
    return report
