import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("torch")

from experiments import lp_q34_holdout_v098 as runner
from neumann1.lp_q34_archive_v098 import (
    load_first_fresh_evaluation,
    load_fresh_sources,
)

SOURCE="docs/experiments/results/v098_fresh_holdout_sources.manifest.json"
EVAL="docs/experiments/results/v098_fresh_holdout_eval.manifest.json"


def test_v098_registered_sources_are_model_free_and_byte_exact():
    manifest,report=load_fresh_sources(SOURCE)
    assert manifest["cases"]==24
    assert manifest["groups"]=={"iid64":12,"size_surface_shift128":12}
    assert manifest["model_access"] is False
    assert manifest["timing"] is False
    assert manifest["route_evaluation"] is False
    assert report["stage"]=="sources_frozen"
    assert len(report["sources"])==24


def test_v098_first_fresh_evaluation_replays_without_execution():
    with (
        patch.object(runner,"run_study",side_effect=AssertionError("no holdout rerun")),
        patch.object(runner,"proposal",side_effect=AssertionError("no model inference")),
        patch.object(runner,"solve_native_checked",side_effect=AssertionError("no solver")),
        patch.object(runner,"support_with_fallback_checked",side_effect=AssertionError("no solver")),
    ):
        report=load_first_fresh_evaluation(EVAL)
    assert len(report["records"])==24*4*4
    s=report["summary"]
    assert s["decision"]=="Q34_FRESH_HOLDOUT_FAIL_NO_Q5"
    assert s["advance_q5"] is False
    assert s["lp_q34_mechanism_pass"] is False
    assert s["development_tuning_on_holdout"] is False
    assert s["groups"]["B_POINT_s87001"]["iid64"]["passed"] is True
    assert s["groups"]["B_POINT_s87002"]["iid64"]["passed"] is True
    assert s["groups"]["B_POINT_s87001"]["size_surface_shift128"]["passed"] is False
    assert s["groups"]["B_POINT_s87002"]["size_surface_shift128"]["passed"] is False
    assert s["groups"]["B_POINT_s87001"]["size_surface_shift128"]["utility_recovery"]==pytest.approx(0.7562632952304174)
    assert s["groups"]["B_POINT_s87002"]["size_surface_shift128"]["utility_recovery"]==pytest.approx(0.661419054735059)
    assert s["overall"]["B_POINT_s87001"]["utility_recovery"]==pytest.approx(0.7721443888448278)
    assert s["overall"]["B_POINT_s87002"]["utility_recovery"]==pytest.approx(0.6788843965026439)
    assert s["global_q3"]==s["global_q4"]=="OPEN"


def test_v098_first_decision_cannot_be_relabelled(tmp_path):
    root=Path("docs/experiments/results")
    manifest=json.loads((root/"v098_fresh_holdout_eval.manifest.json").read_text())
    (tmp_path/manifest["file"]).symlink_to((root/manifest["file"]).resolve())
    manifest["decision"]="Q34_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
    manifest["advance_q5"]=True
    path=tmp_path/"tampered.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="decision"):
        load_first_fresh_evaluation(path)
