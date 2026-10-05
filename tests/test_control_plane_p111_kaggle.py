"""P1.11 bootstrap retention and artifact-manifest contracts."""
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/control_plane_p111_kaggle.py"
spec = importlib.util.spec_from_file_location("p111_bootstrap_test", PATH)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def test_missing_head_does_no_work():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap, "RUNTIME_HEAD", ""):
        with pytest.raises(ValueError):
            bootstrap.run(Path(tmp))
        assert list(Path(tmp).iterdir()) == []


def test_artifact_manifest_covers_and_hashes_exact_required_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for index, name in enumerate(bootstrap.REQUIRED_MODEL_FILES):
            (root / name).write_bytes(("artifact-%d" % index).encode())
        manifest = bootstrap.build_artifact_manifest(root)
        assert manifest["model_id"] == bootstrap.MODEL_ID
        assert manifest["model_revision"] == bootstrap.MODEL_REVISION
        assert set(manifest["files"]) == set(bootstrap.REQUIRED_MODEL_FILES)
        for name, row in manifest["files"].items():
            assert row["bytes"] == (root / name).stat().st_size
            assert row["sha256"] == bootstrap.digest_file(root / name)


def test_first_stage_failure_is_packaged_and_never_replaced():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap, "RUNTIME_HEAD", "a" * 40):
        def fail(args, **kwargs):
            return 1

        setup, receipt = bootstrap.run(
            Path(tmp), execute=fail, launcher_wall_ms=1
        )
        assert setup["status"] == "FAILED_OR_INTERRUPTED"
        assert setup["p110_task_score_reuse"] is False
        assert receipt["no_replacement"] is True

        raw = (Path(tmp) / bootstrap.ARCHIVE).read_bytes()
        with zipfile.ZipFile(Path(tmp) / bootstrap.ARCHIVE) as zipped:
            assert "archive_manifest.json" in zipped.namelist()

        with pytest.raises(RuntimeError):
            bootstrap.run(Path(tmp), execute=fail)
        with pytest.raises(RuntimeError):
            bootstrap.package(Path(tmp))
        assert (Path(tmp) / bootstrap.ARCHIVE).read_bytes() == raw


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
