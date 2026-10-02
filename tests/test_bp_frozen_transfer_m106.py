"""Synthetic cost/coverage faults; no registered input generation or inference."""
import copy
import pytest
from experiments.bp_frozen_transfer_m106 import ROUTES, protocol, schedule, specs, summarize


def fixture():
    records = [{"case_id":case,"route":route,"phase":phase,"repeat":repeat,
                "accepted":True,"total_ms":10 if route in ROUTES[:2] else 5}
               for case,route,phase,repeat in schedule()]
    return records, {r:0 for r in ROUTES}, {str(s):{"feature_setup_ms":0,"fit_ms":0,"weights_sha256":"fixture"} for s in (100001,100002)}


def test_preregistered_new_sources_and_exact_checkpoints():
    assert len(specs()) == 16 and [s["seed"] for s in specs()] == list(range(106300,106316))
    assert protocol()["model_seeds"] == [100001,100002]
    assert protocol()["new_fitting"] is False and protocol()["oracle_access"] is False
    assert len(schedule()) == 256
    assert all(r[2]=="warmup" for r in schedule()[:64])
    assert all(r[2]=="timed" for r in schedule()[64:])


def test_both_checkpoints_required_and_no_global_closure():
    r,c,t = fixture(); report = summarize(r,c,t)
    assert report["joint_pass"] and report["global_questions_closed"] == []
    assert report["computational_cross_domain"] is False


def test_failure_never_disappears_from_cost_gate():
    r,c,t = fixture(); r[0]["accepted"] = False
    report = summarize(r,c,t)
    assert not report["joint_pass"]
    assert any(any(v is None for v in cell["ratios"].values()) for cell in report["cells"])


def test_existing_training_and_cold_cost_can_kill_headroom():
    r,c,t = fixture(); t["100002"]["fit_ms"] = 1000000
    report = summarize(r,c,t)
    assert report["decisions"]["EXPAND4_s100001"] == "BOUNDED_TRANSFER_PASS"
    assert report["decisions"]["EXPAND4_s100002"] == "STOP_FROZEN_TRANSFER_NO_REFIT"
    assert not report["joint_pass"]


def test_partial_and_duplicate_coverage_rejected():
    r,c,t = fixture()
    with pytest.raises(ValueError): summarize(r[:-1],c,t)
    r[0] = r[1]
    with pytest.raises(ValueError): summarize(r,c,t)
