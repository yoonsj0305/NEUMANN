import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("torch")
pytest.importorskip("highspy")

from experiments import lp_final_holdout_v102 as runner
from neumann1.lp_final_q34_archive_v102 import load_final_evaluation


MANIFEST="docs/experiments/results/v102_final_evaluation.manifest.json"


@pytest.fixture(scope="module")
def retained_report():
    return load_final_evaluation(MANIFEST)


def test_final_q34_closure_replays_without_model_solver_fit_or_timing(retained_report):
    with (
        patch.object(runner,"run_study",side_effect=AssertionError("no final rerun")),
        patch.object(runner,"observe_candidate",side_effect=AssertionError("no candidate inference")),
    ):
        report=retained_report
    summary=report["summary"]
    assert summary["decision"]=="CLOSE_Q3_PASS_Q4_PASS_ADVANCE_Q5"
    assert summary["q3_status"]=="PASS_LP_MECHANISM"
    assert summary["q4_status"]=="PASS_LP_MECHANISM"
    assert summary["advance_q5"] is True
    assert summary["seed_pass"]=={
        "ADAPTIVE_s100001":True,
        "ADAPTIVE_s100002":True,
    }
    assert summary["views"]==48
    assert len(report["records"])==768


def test_final_q34_all_four_cells_pass_both_seeds(retained_report):
    report=retained_report
    for route,cells in report["summary"]["groups"].items():
        assert set(cells)=={"m64_base","m64_surface","m128_base","m128_surface"}
        assert all(row["passed"] is True for row in cells.values())
        assert all(row["utility_recovery"]>=0.80 for row in cells.values())
        assert all(row["discovery_burden"]<=0.20 for row in cells.values())
        assert all(row["amortized_complete_ratio"]<1.0 for row in cells.values())


def test_pre_source_and_pre_evaluation_invalid_attempts_are_preserved():
    pre=json.loads(Path("docs/experiments/results/v102_invalid_source_registration_attempts.json").read_text())
    assert len(pre["attempts"])==2
    assert all(a["source_generation_entered"] is False for a in pre["attempts"])
    eval_attempt=json.loads(Path("docs/experiments/results/v102_invalid_first_evaluation_attempt.json").read_text())
    assert eval_attempt["timing_observations"]==0
    assert eval_attempt["candidate_inference"] is False
    assert eval_attempt["solver_calls"]==0
    assert eval_attempt["favorable_rerun"] is False
