"""P1.9 bootstrap faults retain evidence without subprocess/model execution."""
import importlib.util, json, tempfile, zipfile
from pathlib import Path
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[1]/"scripts/control_plane_p19_kaggle.py"
spec=importlib.util.spec_from_file_location("p19_bootstrap_test",PATH)
bootstrap=importlib.util.module_from_spec(spec); spec.loader.exec_module(bootstrap)

def test_missing_head_does_no_work():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD",""):
        try: bootstrap.run(Path(tmp))
        except ValueError: pass
        else: raise AssertionError("missing head must fail")
        assert list(Path(tmp).iterdir())==[]

def test_first_stage_failure_packaged_and_never_replaced():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
        def fail(args,**kw): return 1
        setup,receipt=bootstrap.run(Path(tmp),execute=fail,launcher_wall_ms=1)
        assert setup["status"]=="FAILED_OR_INTERRUPTED"
        assert setup["p2_admitted"] is False and setup["p18_opened_task_score_reuse"] is False
        raw=(Path(tmp)/bootstrap.ARCHIVE).read_bytes()
        with zipfile.ZipFile(Path(tmp)/bootstrap.ARCHIVE) as z:
            assert "archive_manifest.json" in z.namelist()
        try: bootstrap.run(Path(tmp),execute=fail)
        except RuntimeError: pass
        else: raise AssertionError("first attempt must not be replaced")
        try: bootstrap.package(Path(tmp))
        except RuntimeError: pass
        else: raise AssertionError("archive must not be replaced")
        assert (Path(tmp)/bootstrap.ARCHIVE).read_bytes()==raw

def test_recovery_refuses_live_child():
    with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
        data={"runtime_head":"a"*40,"development_only":True,"bootstrap_sha256":bootstrap.digest_file(PATH),"active_child_pid":123}
        (Path(tmp)/bootstrap.SETUP).write_text(json.dumps(data))
        with patch.object(bootstrap.os,"kill",return_value=None):
            try: bootstrap.package_existing(Path(tmp))
            except RuntimeError: pass
            else: raise AssertionError("live child recovery must fail")
        assert not (Path(tmp)/bootstrap.ARCHIVE).exists()
