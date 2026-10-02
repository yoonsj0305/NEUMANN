"""First Boot2 negative evidence is immutable, never a rescued accuracy score."""
import json
from pathlib import Path
from experiments.first_evidence_v106 import ROOT, check_blob
from experiments.general_evidence_v106 import replay

DIRECTORY = ROOT / "docs/experiments/results/v106_general_boot2"


def test_original_boot2_every_byte():
    pins = json.loads((ROOT/"docs/experiments/boot2_first_v106.pins.json").read_text())
    for entry in pins["files"]:
        check_blob((ROOT/entry["path"]).read_bytes(),entry)


def test_original_negative_results_and_original_receipts_replay():
    result = replay(DIRECTORY)
    assert result["status"] == "COMPLETE_INTERFACE_DIAGNOSTIC"
    assert result["observations"] == 15
    assert all(a["accepted"] == 0 and a["observations"] == 3 for a in result["by_arm"].values())
    assert result["general_capability_gate"] == "NOT_EVALUATED"
    assert result["neural_replay_calls"] == 0


def test_structural_loop_was_not_exercised():
    records = [json.loads((DIRECTORY/("query_%02d.json"%i)).read_text()) for i in range(15)]
    assert all(r["tool_calls"] == 0 and r["accepted"] is False for r in records)
    assert sum(r["error"].startswith("TimeoutError") for r in records) == 9
