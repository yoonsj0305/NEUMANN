"""Replay the final v0.0.102 Q34 closure without model inference, solver calls, fitting, or timing."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from experiments.lp_final_holdout_v102 import protocol
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_final_holdout_archive_v102 import decode_source, load_final_sources
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit

EXPECTED_FORMAT="neumann.final-q34-holdout-v102.archive.v1"
EXPECTED_HEAD="f65231bc9e05c2c92f095db91b13c3f4805b595f"
EXPECTED_DECISION="CLOSE_Q3_PASS_Q4_PASS_ADVANCE_Q5"
EXPECTED_Q3="PASS_LP_MECHANISM"
EXPECTED_Q4="PASS_LP_MECHANISM"
MAX_JSON_BYTES=64*1024*1024
SOURCE_MANIFEST="docs/experiments/results/v102_final_sources.manifest.json"
MODEL_MANIFEST="docs/experiments/results/v100_first_refit.manifest.json"


def load_final_evaluation(manifest_path):
    path=Path(manifest_path)
    manifest=json.loads(path.read_text())
    required={
        "advance_q5","decision","file","format","frozen_head",
        "gzip_bytes","gzip_sha256","json_bytes","json_sha256",
        "q3_status","q4_status","rerun","summary",
    }
    if set(manifest)!=required:
        raise ValueError("v102 final manifest schema drift")
    if manifest["format"]!=EXPECTED_FORMAT or manifest["rerun"] is not False:
        raise ValueError("v102 final archive identity drift")
    if manifest["frozen_head"]!=EXPECTED_HEAD:
        raise ValueError("v102 final frozen head drift")
    if (
        manifest["decision"]!=EXPECTED_DECISION
        or manifest["q3_status"]!=EXPECTED_Q3
        or manifest["q4_status"]!=EXPECTED_Q4
        or manifest["advance_q5"] is not True
    ):
        raise ValueError("v102 final closure decision drift")
    name=manifest["file"]
    if type(name) is not str or Path(name).name!=name:
        raise ValueError("unsafe v102 final archive filename")
    packed=(path.parent/name).read_bytes()
    if len(packed)!=manifest["gzip_bytes"] or hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]:
        raise ValueError("v102 final gzip drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("v102 final decoded archive too large")
    if len(raw)!=manifest["json_bytes"] or hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]:
        raise ValueError("v102 final json drift")
    report=json.loads(raw)
    if report["protocol"]!=protocol() or report["frozen_head"]!=EXPECTED_HEAD or report["stage"]!="completed":
        raise ValueError("v102 final report protocol drift")
    if report["summary"]!=manifest["summary"]:
        raise ValueError("v102 final retained summary drift")
    summary=report["summary"]
    if (
        summary["decision"]!=EXPECTED_DECISION
        or summary["q3_status"]!=EXPECTED_Q3
        or summary["q4_status"]!=EXPECTED_Q4
        or summary["advance_q5"] is not True
        or summary["second_holdout_authorized"] is not False
        or summary["v098_holdout_access"] is not False
        or summary["v101_development_access"] is not False
        or not all(summary["seed_pass"].values())
    ):
        raise ValueError("v102 final closure semantics drift")
    for route,cells in summary["groups"].items():
        if not route.startswith("ADAPTIVE_") or not all(row["passed"] for row in cells.values()):
            raise ValueError("v102 final required-cell pass drift")

    sources=load_final_sources(SOURCE_MANIFEST)
    by_id={s["id"]:s for s in sources["sources"]}
    raws={case:decode_source(source) for case,source in by_id.items()}
    retained=load_first_refit(MODEL_MANIFEST)
    expected_model={
        str(seed):retained["training"][f"QUOTIENT_s{seed}"]["weights_sha256"]
        for seed in (100001,100002)
    }
    if report["model_identity"]!=expected_model:
        raise ValueError("v102 final frozen model identity drift")
    if len(report["records"])!=48*4*4:
        raise ValueError("v102 final record count drift")

    for row in report["records"]:
        if row["case_id"] not in raws or row["source_sha256"]!=by_id[row["case_id"]]["sha256"]:
            raise ValueError("v102 final source identity drift")
        if row["accepted"] is not True or row["witness"] is None:
            raise ValueError("v102 final accepted capability drift")
        if not verify_standard_form_certificate(**raws[row["case_id"]],**row["witness"])["accepted"]:
            raise ValueError("v102 final original witness drift")
    return report
