from unittest.mock import patch

import pytest

pytest.importorskip("torch")

from experiments import lp_frozen_support_expansion_v101 as runner
from neumann1.lp_frozen_support_expansion_archive_v101 import load_first_expansion


MANIFEST="docs/experiments/results/v101_first_expansion.manifest.json"


def test_v101_first_result_replays_without_fit_inference_solver_or_timing():
    with (
        patch.object(runner,"run_study",side_effect=AssertionError("no study rerun")),
        patch.object(runner,"restore_frozen_quotient",side_effect=AssertionError("no model restore")),
        patch.object(runner,"frozen_ranking",side_effect=AssertionError("no inference")),
        patch.object(runner,"observe_reference",side_effect=AssertionError("no solver")),
        patch.object(runner,"observe_candidate",side_effect=AssertionError("no solver")),
    ):
        report=load_first_expansion(MANIFEST)
    s=report["summary"]
    assert s["decision"]=="ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_FROZEN_SUPPORT_SYSTEM"
    assert s["fresh_holdout_candidate"]==["EXPAND4"]
    assert s["pareto_survivors"]==["EXPAND4"]
    assert s["families"]["EXPAND4"]["passed"] is True
    assert s["families"]["FIXED2"]["passed"] is False
    assert s["families"]["EXPAND4"]["minimum_utility_recovery"]==pytest.approx(0.8669935649657865)
    assert s["families"]["EXPAND4"]["maximum_discovery_burden"]==pytest.approx(0.030060390089731503)
    assert s["families"]["EXPAND4"]["maximum_amortized_complete_ratio"]==pytest.approx(0.2212432511707686)
    assert s["overall"]["EXPAND4_s100001"]["fallback_free_cases"]==32
    assert s["overall"]["EXPAND4_s100002"]["fallback_free_cases"]==32
    assert s["overall"]["EXPAND4_s100001"]["expanded_accepted_cases"]==4
    assert s["overall"]["EXPAND4_s100002"]["expanded_accepted_cases"]==4
    assert all(row["earned"] for row in s["expansion_rescue_evidence"].values())
    assert s["fresh_holdout"] is False
    assert s["advance_q5"] is False
    assert s["global_q3"]==s["global_q4"]=="OPEN"
