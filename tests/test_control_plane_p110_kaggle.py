import importlib.util, json, tempfile, zipfile
from pathlib import Path
from unittest.mock import patch
PATH=Path(__file__).resolve().parents[1]/"scripts/control_plane_p110_kaggle.py"
spec=importlib.util.spec_from_file_location("p110_bootstrap_test",PATH); bootstrap=importlib.util.module_from_spec(spec); spec.loader.exec_module(bootstrap)
def test_missing_head_does_no_work():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD",""):
        with __import__("pytest").raises(ValueError): bootstrap.run(Path(tmp))
        assert list(Path(tmp).iterdir())==[]
def test_first_stage_failure_is_packaged_and_immutable():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
        setup,_=bootstrap.run(Path(tmp),execute=lambda args,**kw:1,launcher_wall_ms=1)
        assert setup["status"]=="FAILED_OR_INTERRUPTED" and setup["p19_opened_task_score_reuse"] is False
        raw=(Path(tmp)/bootstrap.ARCHIVE).read_bytes()
        with zipfile.ZipFile(Path(tmp)/bootstrap.ARCHIVE) as z: assert "archive_manifest.json" in z.namelist()
        with __import__("pytest").raises(RuntimeError): bootstrap.run(Path(tmp),execute=lambda args,**kw:1)
        with __import__("pytest").raises(RuntimeError): bootstrap.package(Path(tmp))
        assert (Path(tmp)/bootstrap.ARCHIVE).read_bytes()==raw
def test_recovery_refuses_live_child():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
        data={"runtime_head":"a"*40,"development_only":True,"bootstrap_sha256":bootstrap.digest_file(PATH),"active_child_pid":123}
        (Path(tmp)/bootstrap.SETUP).write_text(json.dumps(data))
        with patch.object(bootstrap.os,"kill",return_value=None):
            with __import__("pytest").raises(RuntimeError): bootstrap.package_existing(Path(tmp))
