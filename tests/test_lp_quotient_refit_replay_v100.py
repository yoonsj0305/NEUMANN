from unittest.mock import patch

import pytest

pytest.importorskip("torch")

from experiments import lp_quotient_refit_v100 as runner
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit


MANIFEST="docs/experiments/results/v100_first_refit.manifest.json"


def test_v100_first_result_replays_without_fit_inference_solver_or_timing():
    with (
        patch.object(runner,"run_study",side_effect=AssertionError("no study rerun")),
        patch.object(runner,"fit_one",side_effect=AssertionError("no refit")),
        patch.object(runner,"proposal",side_effect=AssertionError("no inference")),
        patch.object(runner,"observe_reference",side_effect=AssertionError("no solver")),
        patch.object(runner,"observe_candidate",side_effect=AssertionError("no solver")),
    ):
        report=load_first_refit(MANIFEST)
    s=report["summary"]
    assert s["decision"]=="STOP_QUOTIENT_REFIT_NO_FRESH_HOLDOUT"
    assert s["quotient_development_pass"] is False
    assert s["advance_q5"] is False
    assert s["v098_holdout_access"] is False
    assert s["paired_support_invariance"]["OLD_CG5_s100001"]["exact_pairs"]==0
    assert s["paired_support_invariance"]["OLD_CG5_s100002"]["exact_pairs"]==0
    assert s["paired_support_invariance"]["QUOTIENT_s100001"]["exact_pairs"]==16
    assert s["paired_support_invariance"]["QUOTIENT_s100002"]["exact_pairs"]==16
    assert s["groups"]["QUOTIENT_s100001"]["m128_base"]["utility_recovery"]==pytest.approx(0.7876172432249304)
    assert s["groups"]["QUOTIENT_s100001"]["m128_surface"]["utility_recovery"]==pytest.approx(0.7997726225120754)
    assert s["groups"]["QUOTIENT_s100002"]["m128_base"]["utility_recovery"]==pytest.approx(0.7964665921406906)
    assert s["groups"]["QUOTIENT_s100002"]["m128_surface"]["utility_recovery"]==pytest.approx(0.7947491162840227)
    assert s["overall"]["QUOTIENT_s100001"]["passed"] is True
    assert s["overall"]["QUOTIENT_s100002"]["passed"] is True
