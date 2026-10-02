import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("torch")
pytest.importorskip("highspy")

from experiments import lp_expand4_holdout_v102 as runner
from neumann1.lp_expand4_holdout_archive_v102 import load_first_evaluation


MANIFEST="docs/experiments/results/v102_first_evaluation.manifest.json"


def test_v102_first_fresh_evaluation_replays_without_execution():
    with (
        patch.object(runner,"run_study",side_effect=AssertionError("no evaluation rerun")),
        patch.object(runner,"observe_candidate",side_effect=AssertionError("no model route")),
        patch.object(runner,"solve_native_checked",side_effect=AssertionError("no solver")),
        patch.object(runner,"expand4_checked",side_effect=AssertionError("no support execution")),
        patch.object(runner,"frozen_ranking",side_effect=AssertionError("no inference")),
    ):
        report=load_first_evaluation(MANIFEST)

    assert len(report["records"])==48*4*4
    s=report["summary"]
    assert s["decision"]=="Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
    assert s["advance_q5"] is True
    assert s["lp_q34_mechanism_pass"] is True
    assert s["fresh_views"]==48
    assert s["development_tuning_on_holdout"] is False
    assert s["v098_holdout_access"] is False
    assert s["global_q3"]==s["global_q4"]=="OPEN"
    assert s["seed_pass"]=={
        "EXPAND4_s100001":True,
        "EXPAND4_s100002":True,
    }
    assert s["paired_top2_invariance"]=={
        "EXPAND4_s100001":{"exact_pairs":24,"pairs":24},
        "EXPAND4_s100002":{"exact_pairs":24,"pairs":24},
    }
    assert all(
        row["passed"]
        for route in s["groups"].values()
        for row in route.values()
    )
    assert all(row["fallback_free_cases"]==48 for row in s["overall"].values())
    assert s["overall"]["EXPAND4_s100001"]["utility_recovery"]==pytest.approx(0.8216881622363271)
    assert s["overall"]["EXPAND4_s100002"]["utility_recovery"]==pytest.approx(0.8227717507533571)


def test_v102_fresh_gate_worst_cell_still_clears_thresholds():
    report=load_first_evaluation(MANIFEST)
    rows=[
        row
        for route in report["summary"]["groups"].values()
        for row in route.values()
    ]
    assert min(row["utility_recovery"] for row in rows)==pytest.approx(0.8055909772660025)
    assert max(row["discovery_burden"] for row in rows)==pytest.approx(0.034522320671816764)
    assert max(row["amortized_complete_ratio"] for row in rows)==pytest.approx(0.25287665440991375)
    assert min(row["fallback_free_cases"] for row in rows)==12


def test_v102_invalid_first_evaluation_remains_zero_observation():
    notice=json.loads(Path(
        "docs/experiments/results/v102_invalid_first_evaluation_attempt.json"
    ).read_text())
    assert notice["status"]=="INVALID_PRE_MEASUREMENT_AUTHORITY_KEY_NORMALIZATION"
    assert notice["route_observations"]==0
    assert notice["timing_observations"]==0
    assert notice["warmups_completed"]==0
    assert notice["result_archive_created"] is False
    assert notice["favorable_rerun"] is False
