import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("torch")
pytest.importorskip("highspy")

from experiments import lp_q34_tournament_v097 as runner
from neumann1.lp_q34_archive_v097 import load_first_tournament


MANIFEST="docs/experiments/results/v097_first_tournament.manifest.json"


def test_first_q34_tournament_replays_without_execution():
    with (
        patch.object(runner,"run_study",side_effect=AssertionError("no tournament rerun")),
        patch.object(runner,"proposal",side_effect=AssertionError("no model inference")),
        patch.object(runner,"solve_native_checked",side_effect=AssertionError("no solver")),
        patch.object(runner,"support_with_fallback_checked",side_effect=AssertionError("no solver")),
        patch.object(runner,"adaptive_support_checked",side_effect=AssertionError("no solver")),
    ):
        report=load_first_tournament(MANIFEST)
    assert len(report["records"])==16*9*4
    summary=report["summary"]
    assert summary["decision"]=="ADMIT_FRESH_Q34_HOLDOUT"
    assert summary["pareto_q34_survivors"]==["B_POINT"]
    assert summary["families"]["B_POINT"]["passed"] is True
    assert summary["families"]["B_POINT"]["fallback_free_cases"]==16
    assert summary["families"]["B_POINT"]["utility_recovery"]==pytest.approx(0.9090572121754934)
    assert summary["families"]["B_POINT"]["discovery_burden"]==pytest.approx(0.04597737054891446)
    assert summary["families"]["B_POINT"]["amortized_complete_ratio"]==pytest.approx(0.21227808742653945)
    assert summary["families"]["A_DETERMINISTIC"]["passed"] is False
    assert summary["q34_global_pass"] is False
    assert summary["global_q3"]==summary["global_q4"]=="OPEN"


def test_first_manifest_cannot_be_relabelled(tmp_path):
    root=Path("docs/experiments/results")
    manifest=json.loads((root/"v097_first_tournament.manifest.json").read_text())
    (tmp_path/manifest["file"]).symlink_to((root/manifest["file"]).resolve())
    manifest["decision"]="NO_FROZEN_FAMILY_Q34_CANDIDATE"
    path=tmp_path/"bad.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="decision"):
        load_first_tournament(path)


def test_invalid_attempt_is_retained_as_zero_observation_setup_failure():
    notice=json.loads(Path("docs/experiments/results/v097_invalid_first_attempt.json").read_text())
    assert notice["status"]=="INVALID_PRE_MEASUREMENT_INVOCATION"
    assert notice["timing_observations"]==0
    assert notice["warmups_completed"]==0
    assert notice["solver_calls"]==0
    assert notice["result_archive_created"] is False
    assert notice["favorable_rerun"] is False
