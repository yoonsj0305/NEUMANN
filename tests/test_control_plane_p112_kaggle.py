"""P1.12 first-only archive and pinned artifact identity contracts."""
import hashlib
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

PATH=Path(__file__).resolve().parents[1]/"scripts/control_plane_p112_kaggle.py"
spec=importlib.util.spec_from_file_location("p112_bootstrap_test",PATH)
bootstrap=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
WEIGHTS="821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae"


def test_isolated_first_namespace_and_frozen_source_identity():
    assert bootstrap.ARCHIVE=="NEUMANN_P112_FIRST_EVIDENCE.zip"
    assert bootstrap.SETUP=="neumann_p112_first_setup.json"
    assert bootstrap.MODEL_ID=="cross-encoder/ms-marco-MiniLM-L6-v2"
    assert bootstrap.MODEL_REVISION=="ce0834f22110de6d9222af7a7a03628121708969"
    assert bootstrap.MODEL_DIR=="NEUMANN_P112_CROSSENCODER_FROZEN"
    assert bootstrap.ARCHIVE!="NEUMANN_P1111_FIRST_EVIDENCE.zip"


def test_missing_frozen_head_does_not_touch_files():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap,"RUNTIME_HEAD",""):
        with pytest.raises(ValueError):
            bootstrap.run(Path(tmp))
        assert list(Path(tmp).iterdir())==[]


def test_manifest_rejects_unregistered_weights():
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)
        for i,name in enumerate(bootstrap.REQUIRED_MODEL_FILES):
            (path/name).write_bytes(("fake%d"%i).encode())
        with pytest.raises(ValueError,match="weight SHA-256 mismatch"):
            bootstrap.build_artifact_manifest(path)
        real_digest=bootstrap.digest_file
        def mocked_digest(file):
            return WEIGHTS if Path(file).name=="model.safetensors" else real_digest(file)
        with patch.object(bootstrap,"digest_file",side_effect=mocked_digest):
            manifest=bootstrap.build_artifact_manifest(path)
        assert manifest["files"]["model.safetensors"]["sha256"]==WEIGHTS
        assert set(manifest["files"])==set(bootstrap.REQUIRED_MODEL_FILES)


def test_first_stage_failure_retained_and_never_replaced():
    with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
        setup,receipt=bootstrap.run(Path(tmp),execute=lambda args,**kwargs:1,launcher_wall_ms=1.0)
        assert setup["status"]=="FAILED_OR_INTERRUPTED"
        assert setup["p111_task_score_reuse"] is False
        assert setup["p111_tasks_as_p112_evidence"] is False
        assert setup["favorable_rerun"] is False
        assert receipt["no_replacement"] is True
        archive=Path(tmp)/bootstrap.ARCHIVE
        raw=archive.read_bytes()
        with zipfile.ZipFile(archive) as z:
            m=json.loads(z.read("archive_manifest.json"))
            assert m["p111_task_score_reuse"] is False
            assert m["p111_tasks_as_p112_evidence"] is False
        with pytest.raises(RuntimeError):
            bootstrap.run(Path(tmp),execute=lambda args,**kwargs:1)
        with pytest.raises(RuntimeError):
            bootstrap.package(Path(tmp))
        assert archive.read_bytes()==raw


def test_recovery_refuses_live_child():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
        data={"runtime_head":"a"*40,"development_only":True,
              "bootstrap_sha256":bootstrap.digest_file(PATH),
              "active_child_pid":123}
        (Path(tmp)/bootstrap.SETUP).write_text(json.dumps(data))
        with patch.object(bootstrap.os,"kill",return_value=None):
            with pytest.raises(RuntimeError):
                bootstrap.package_existing(Path(tmp))
        assert not (Path(tmp)/bootstrap.ARCHIVE).exists()
