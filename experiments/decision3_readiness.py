"""Model-free Decision-3 readiness checker.

This command never imports Hugging Face datasets, opens task rows, or performs
model/provider inference. It only checks the frozen Decision-2 replay,
Decision-3 metadata registry and interface-readiness marker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(d2_replay=None):
    root=Path(__file__).resolve().parents[1]
    registry_path=root/"docs/experiments/decision3_source_registry_v1.json"
    interface_path=root/"docs/experiments/decision3_interface_readiness_v1.json"
    registry=_load(registry_path)
    interface=_load(interface_path)

    base={
        "schema":"neumann.decision3-readiness.v1",
        "source_registry_sha256":_hash(registry_path),
        "interface_marker_sha256":_hash(interface_path),
        "sealed_rows_opened":False,
        "model_inference_performed":False,
        "frontier_calls":0,
    }

    if d2_replay is None:
        return {
            **base,
            "status":"WAIT_DECISION2_EVIDENCE",
            "next":"Run the frozen AM1 one-shot first; do not unseal Decision-3 data.",
        }

    replay=_load(d2_replay)
    valid=replay.get("valid") is True
    decision=(replay.get("recomputed_decision_2") or {}).get("verdict")
    if not valid:
        return {
            **base,
            "status":"BLOCKED_INVALID_DECISION2_REPLAY",
            "decision2_valid":False,
        }
    if decision!="PASS":
        return {
            **base,
            "status":"BLOCKED_DECISION2_NOT_PASS",
            "decision2_valid":True,
            "decision2_verdict":decision,
            "next":"Architecture pivot; Decision-3 sealed data remains closed.",
        }
    if registry.get("task_rows_opened_during_preparation")!=0:
        return {**base,"status":"BLOCKED_SOURCE_REGISTRY_CONTAMINATION"}
    if interface.get("task_agnostic_interface") is not True:
        return {
            **base,
            "status":"BLOCKED_TASK_SPECIFIC_INTERFACE",
            "decision2_valid":True,
            "decision2_verdict":decision,
            "reason":interface.get("reason"),
            "next":"Do not open sealed data. Any generic-interface change must return to opened matched validation first.",
        }
    return {
        **base,
        "status":"READY_TO_ARM_ONE_SEALED_EVALUATION",
        "decision2_valid":True,
        "decision2_verdict":decision,
        "next":"Freeze candidate/provider identities and unseal exactly once.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--d2-replay")
    p.add_argument("--output")
    args=p.parse_args()
    result=check(args.d2_replay)
    payload=json.dumps(result,sort_keys=True,indent=2)
    print(payload)
    if args.output:
        Path(args.output).write_text(payload+"\n",encoding="utf-8")
    # WAIT/BLOCKED are expected scientific states, not shell crashes.
    raise SystemExit(0)


if __name__=="__main__":
    main()
