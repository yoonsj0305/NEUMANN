"""Byte-exact replay for the first valid v0.0.97 Q34 tournament.

This module validates retained bytes and original-problem witnesses only.
It never runs model inference, a solver, fitting, or timing.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from experiments.lp_q34_tournament_v097 import validate_report


EXPECTED_FORMAT="neumann.q34-support-tournament-v097.archive.v1"
EXPECTED_FROZEN_HEAD="d7ae02ca0418a4b93020e0e8fbf2ecbcd5b1e975"
EXPECTED_DECISION="ADMIT_FRESH_Q34_HOLDOUT"
MAX_JSON_BYTES=64*1024*1024


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
    if len(packed)!=manifest["gzip_bytes"] or hashlib.sha256(packed).hexdigest()!=manifest["gzip_sha256"]:
        raise ValueError("gzip identity drift")
    raw=gzip.decompress(packed)
    if len(raw)>MAX_JSON_BYTES:
        raise ValueError("decoded archive too large")
    if len(raw)!=manifest["json_bytes"] or hashlib.sha256(raw).hexdigest()!=manifest["json_sha256"]:
        raise ValueError("decoded identity drift")
    report=json.loads(raw)
    if report["frozen_head"]!=manifest["frozen_head"]:
        raise ValueError("report head drift")
    validate_report(report)
    if report["summary"]!=manifest["summary"] or report["summary"]["decision"]!=manifest["decision"]:
        raise ValueError("summary/decision drift")
    return report
