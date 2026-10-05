"""P1.11.1 identity-repair bootstrap retention contracts."""
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/control_plane_p1111_kaggle.py"
spec = importlib.util.spec_from_file_location("p1111_bootstrap_test", PATH)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)

HISTORICAL = "d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0"


def test_repair_namespace_never_collides_with_historical_p111_first():
    assert bootstrap.ARCHIVE == "NEUMANN_P1111_FIRST_EVIDENCE.zip"
    assert bootstrap.SETUP == "neumann_p1111_first_setup.json"
    assert bootstrap.OUTPUT == "neumann_p1111_first"
    assert bootstrap.ARCHIVE != "NEUMANN_P111_FIRST_EVIDENCE.zip"
    assert bootstrap.SETUP != "neumann_p111_first_setup.json"


def test_missing_head_does_no_work():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap, "RUNTIME_HEAD", ""):
        with pytest.raises(ValueError):
            bootstrap.run(Path(tmp))
        assert list(Path(tmp).iterdir()) == []


def test_artifact_manifest_stays_compatible_with_frozen_p111_runner():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for index, name in enumerate(bootstrap.REQUIRED_MODEL_FILES):
            (root / name).write_bytes(("artifact-%d" % index).encode())
        manifest = bootstrap.build_artifact_manifest(root)
        assert manifest["schema"] == "neumann.control-plane-p111-model-artifacts.v1"
        assert manifest["model_id"] == bootstrap.MODEL_ID
        assert manifest["model_revision"] == bootstrap.MODEL_REVISION
        assert set(manifest["files"]) == set(bootstrap.REQUIRED_MODEL_FILES)


def test_first_repair_stage_failure_is_packaged_with_zero_inference_provenance():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap, "RUNTIME_HEAD", "a" * 40):
        setup, receipt = bootstrap.run(
            Path(tmp),
            execute=lambda args, **kwargs: 1,
            launcher_wall_ms=1,
        )
        assert setup["status"] == "FAILED_OR_INTERRUPTED"
        assert setup["identity_repair_revision"] == "P1.11.1"
        assert setup["historical_first_archive_sha256"] == HISTORICAL
        assert setup["historical_first_observations"] == 0
        assert setup["historical_first_model_calls"] == 0
        assert setup["historical_first_neural_forward_calls"] == 0
        assert setup["task_scores_seen_before_repair"] is False
        assert setup["repair_scope"] == "MODEL_PARAMETER_IDENTITY_ONLY"
        assert setup["replacement_of_historical_first"] is False
        assert setup["favorable_rerun"] is False
        assert receipt["no_replacement"] is True

        archive = Path(tmp) / bootstrap.ARCHIVE
        raw = archive.read_bytes()
        with zipfile.ZipFile(archive) as zipped:
            manifest = json.loads(zipped.read("archive_manifest.json"))
            assert manifest["schema"] == "neumann.control-plane-p1111-archive.v1"
            assert manifest["identity_repair_revision"] == "P1.11.1"
            assert manifest["historical_first_archive_sha256"] == HISTORICAL
            assert manifest["historical_observations"] == 0
            assert manifest["historical_model_calls"] == 0
            assert manifest["historical_neural_forward_calls"] == 0
            assert manifest["task_scores_seen_before_repair"] is False

        with pytest.raises(RuntimeError):
            bootstrap.run(Path(tmp), execute=lambda args, **kwargs: 1)
        with pytest.raises(RuntimeError):
            bootstrap.package(Path(tmp))
        assert archive.read_bytes() == raw


def test_recovery_refuses_live_child():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap, "RUNTIME_HEAD", "a" * 40):
        data = {
            "runtime_head": "a" * 40,
            "development_only": True,
            "bootstrap_sha256": bootstrap.digest_file(PATH),
            "active_child_pid": 123,
        }
        (Path(tmp) / bootstrap.SETUP).write_text(json.dumps(data))
        with patch.object(bootstrap.os, "kill", return_value=None):
            with pytest.raises(RuntimeError):
                bootstrap.package_existing(Path(tmp))
        assert not (Path(tmp) / bootstrap.ARCHIVE).exists()
