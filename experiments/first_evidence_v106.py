"""Immutable first attempts: byte verification only, never inference or fitting."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "docs/experiments/first_evidence_v106.pins.json"


def check_blob(raw, entry):
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if len(raw) != entry["size"] or digest != entry["sha"]:
        raise ValueError("first evidence changed: " + entry["path"])


def verify(root=ROOT):
    pins = json.loads(PINS.read_text())
    for entry in pins["files"]:
        check_blob((Path(root) / entry["path"]).read_bytes(), entry)
    general = json.loads((Path(root) / "docs/experiments/results/v106_general_development_first/report.json").read_text())
    assert general["status"] == "INCOMPLETE"
    assert general["observations"] == 0 and general["expected_observations"] == 15
    assert general["general_capability_gate"] == "NOT_EVALUATED"
    assert general["frontier_calls"] == 0 and general["new_training"] is False
    bp = json.loads((Path(root) / "docs/experiments/results/m106_bp_transfer_first/summary.json").read_text())
    terminal = json.loads((Path(root) / "docs/experiments/results/m106_bp_transfer_first/terminal.json").read_text())
    assert terminal["observations"] == 256 and terminal["events"] == 537
    assert not bp["joint_pass"] and not bp["global_questions_closed"]
    assert set(bp["decisions"].values()) == {"STOP_FROZEN_TRANSFER_NO_REFIT"}
    assert all(cost["capability"] for cell in bp["cells"] for cost in cell["costs"].values())
    return {"files":len(pins["files"]),"general":"INCOMPLETE_0_OF_15","bp":"STOP_FROZEN_TRANSFER_NO_REFIT"}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
