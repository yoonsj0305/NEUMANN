"""Zero-cost local AM1 preparation contracts. No GPU or model weights required."""
from pathlib import Path

import pytest

from experiments.general_multiplier_evidence_replay import verify_terminal_hashes
from experiments.general_multiplier_local_preflight import classify, parse_nvidia_smi
from neumann1.general_python_worker_v106 import execute


def test_nvidia_smi_parser_retains_name_vram_and_driver():
    rows = parse_nvidia_smi("0, NVIDIA GeForce RTX TEST, 16384, 999.1\n")
    assert rows == [{
        "index": 0,
        "name": "NVIDIA GeForce RTX TEST",
        "memory_total_mib": 16384,
        "driver": "999.1",
    }]


def test_preflight_classifies_hardware_before_runtime():
    gpu = [{"index":0,"name":"fixture","memory_total_mib":16384,"driver":"x"}]
    assert classify(gpu, {"installed": False}) == "HARDWARE_OK_RUNTIME_NOT_INSTALLED"
    assert classify(gpu, {
        "installed": True,
        "cuda_available": True,
        "bf16_supported": True,
        "selected_device_memory_mib": 16384,
    }) == "READY"


def test_preflight_refuses_low_vram_without_quantization_escape():
    gpu = [{"index":0,"name":"fixture","memory_total_mib":8192,"driver":"x"}]
    assert classify(gpu, {"installed": False}) == "INSUFFICIENT_VRAM_FOR_FROZEN_BF16_AM1"


def test_bounded_python_worker_logic_is_platform_independent():
    result = execute({
        "source": "def solve(items):\n return sum(items)",
        "arguments": [[1, 2, 3], []],
    })
    assert result == [6, 0]


def test_bounded_python_worker_still_rejects_imports():
    with pytest.raises(ValueError):
        execute({
            "source": "import os\ndef solve(items):\n return 0",
            "arguments": [[]],
        })


def test_terminal_hash_replay_detects_byte_change(tmp_path):
    evidence = tmp_path / "report.json"
    evidence.write_text('{"ok":true}\n', encoding="utf-8")
    import hashlib
    good = hashlib.sha256(evidence.read_bytes()).hexdigest()
    assert verify_terminal_hashes(tmp_path, {"files":{"report.json":good}}) == {}
    evidence.write_text('{"ok":false}\n', encoding="utf-8")
    mismatch = verify_terminal_hashes(tmp_path, {"files":{"report.json":good}})
    assert "report.json" in mismatch
