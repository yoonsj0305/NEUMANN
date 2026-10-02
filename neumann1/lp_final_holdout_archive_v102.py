"""Byte-exact loader for the registered v0.0.102 final fresh holdout sources.

This loader validates source bytes and registration authority. It performs no
candidate inference, fitting, timing, or route evaluation.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from experiments.lp_final_holdout_sources_v102 import protocol
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

EXPECTED_FORMAT="neumann.final-q34-holdout-sources-v102.archive.v1"
EXPECTED_HEAD="d052774cf98d0116101f4bf273794d7eb802483a"
MAX_JSON_BYTES=128*1024*1024


def load_final_sources(manifest_path):
    path=Path(manifest_path)
    manifest=json.loads(path.read_text())
    required={
        "candidate_inference","cell_counts","file","format","frozen_head",
        "gzip_bytes","gzip_sha256","json_bytes","json_sha256","model_access",
        "rerun","route_evaluation","source_count","timing",
    }
    if set(manifest)!=required:
        raise ValueError("v102 source manifest schema drift")
    if manifest["format"]!=EXPECTED_FORMAT or manifest["rerun"] is not False:
        raise ValueError("v102 source archive identity drift")
    if manifest["frozen_head"]!=EXPECTED_HEAD:
        raise ValueError("v102 source frozen head drift")
    for key in ("model_access","candidate_inference","timing","route_evaluation"):
        if manifest[key] is not False:
            raise ValueError("v102 source registration authority drift")
    if manifest["source_count"]!=48 or manifest["cell_counts"]!={
        "m64_base":12,"m64_surface":12,"m128_base":12,"m128_surface":12
    }:
        raise ValueError("v102 source coverage drift")
    name=manifest["file"]
    if type(name) is not str or Path(name).name!=name:
        raise ValueError("unsafe v102 source filename")
    packed=(path.parent/name).read_bytes()
    if len(packed)!=manifest["gzip_bytes"] or hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]:
        raise ValueError("v102 source gzip drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("v102 source archive too large")
    if len(raw)!=manifest["json_bytes"] or hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]:
        raise ValueError("v102 source json drift")
    report=json.loads(raw)
    if report["protocol"]!=protocol() or report["frozen_head"]!=EXPECTED_HEAD or report["stage"]!="registered":
        raise ValueError("v102 source report drift")
    if len(report["sources"])!=48:
        raise ValueError("v102 source report count drift")
    for source in report["sources"]:
        m,n=source["rows"],source["cols"]
        problem={
            "A":storage.decode_array(source["arrays"]["A"],(m,n)),
            "b":storage.decode_array(source["arrays"]["b"],(m,)),
            "c":storage.decode_array(source["arrays"]["c"],(n,)),
        }
        if storage.input_digest(problem)!=source["sha256"]:
            raise ValueError("v102 source input digest drift")
        cert=source["oracle_registration_certificate"]
        if not cert["accepted"] or not verify_standard_form_certificate(
                **problem,**cert["witness"])["accepted"]:
            raise ValueError("v102 source oracle registration drift")
        if list(source["basis"])!=list(cert["basis"]):
            raise ValueError("v102 source basis registration drift")
    return report


def decode_source(source):
    m,n=source["rows"],source["cols"]
    raw={
        "A":storage.decode_array(source["arrays"]["A"],(m,n)),
        "b":storage.decode_array(source["arrays"]["b"],(m,)),
        "c":storage.decode_array(source["arrays"]["c"],(n,)),
    }
    if storage.input_digest(raw)!=source["sha256"]:
        raise ValueError("v102 decoded source digest drift")
    return raw
