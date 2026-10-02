"""Externally pinned first v104 bytes; no admission execution entry point."""
from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from experiments.q5_register import evidence_module

FIRST_HEAD = "17d83a4dd22faf8a5799b68a82c8ef2456d414fa"
SOURCES_RAW_SHA256 = "aeefb46c2814a1886520adf9ea6f1ab862efa2c2166f1bf8c18ce4edcb066473"
SOURCES_SHA256 = "e53a3538d39a1b7d3156b1b1cb988582fb903fd69cf92cb4bd96c006c73a477f"
REPORT_RAW_SHA256 = "97884fa0c0093e3e6b96931fc9fd359a34a07c67eb0b87d2bd5a5a51f644697a"
REPORT_SHA256 = "64c17943f05216c58901dedfb1bd90537f3097ad5f7d39d230cea2bfd6a3d6f4"
LAST_EVENT_SHA256 = "c6b0430da9be00ad3747d2529c638e655c13716dc8a6f58f2475cd70c8c2f239"
DECISIONS = {"assignment": "STOP_FAMILY_NO_ORACLE_HEADROOM",
             "basis_pursuit": "ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING"}


def pin(directory):
    ev = evidence_module(); directory = Path(directory)
    raw_source=(directory/"sources.json").read_bytes()
    raw_report=(directory/"report.json").read_bytes()
    if ev.digest(raw_source)!=SOURCES_RAW_SHA256 or ev.digest(raw_report)!=REPORT_RAW_SHA256:
        raise ValueError("first v104 raw archive replacement")
    manifest,report=json.loads(raw_source),json.loads(raw_report)
    events,terminal=ev.read_events(directory)
    reservation=json.loads((directory/"reservation.json").read_text())
    if (manifest["frozen_head"]!=FIRST_HEAD or report["frozen_head"]!=FIRST_HEAD
            or ev.digest(ev.canonical(manifest))!=SOURCES_SHA256
            or ev.digest(ev.canonical(report))!=REPORT_SHA256
            or report["sources_sha256"]!=SOURCES_SHA256
            or terminal!={"status":"completed","events":941,"last_sha256":LAST_EVENT_SHA256,
                "report_sha256":REPORT_SHA256,"observations":448}
            or reservation!={"schema":"neumann.q5-attempt.v1","stage":"v104_transfer_admission_first",
                "frozen_head":FIRST_HEAD,"rerun":False}
            or report["summary"]["decisions"]!=DECISIONS
            or report["summary"]["global_q5_closed"] is not False
            or report["summary"]["cross_domain_pass"] is not False):
        raise ValueError("first v104 receipt/decision replacement")
    return manifest,report,events


def replay_first(directory):
    _,report,_=pin(directory)
    from experiments import q5_transfer_admission as audit
    forbidden=AssertionError("first v104 replay cannot generate, solve, forward or query")
    with ExitStack() as stack:
        for target in ("experiments.q5_transfer_admission.generate",
                       "experiments.q5_transfer_admission.query",
                       "experiments.q5_transfer_admission.oracle_checked",
                       "experiments.q5_transfer_admission.assignment_checked",
                       "experiments.q5_transfer_admission.Worker"):
            stack.enter_context(patch(target,side_effect=forbidden))
        derived=audit.replay(directory)
    from experiments.q5_replay import equal
    if not equal(derived,report["summary"]):
        raise ValueError("first v104 semantic decision drift")
    return {"status":"FIRST_V104_WITNESSES_AND_COMPLETE_COSTS_REPLAY_PASS",
        "observations":448,"failed_observations":derived["failed_observations"],
        "decisions":derived["decisions"],"cells":derived["cells"],
        "new_generation":0,"new_forward":0,"new_solver_calls":0,
        "global_q5_closed":False,"cross_domain_pass":False}


def main():
    p=argparse.ArgumentParser();p.add_argument("--directory",required=True)
    a=p.parse_args();print(json.dumps(replay_first(a.directory),sort_keys=True))


if __name__=="__main__":main()
