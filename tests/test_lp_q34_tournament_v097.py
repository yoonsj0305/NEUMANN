import copy
import pytest

pytest.importorskip("torch")
pytest.importorskip("highspy")

from experiments.lp_q34_tournament_v097 import protocol, summarize


def test_v097_protocol_freezes_joint_gate_and_no_fit():
    p = protocol()
    assert p["new_fitting"] is False
    assert p["final_evaluation"] is False
    assert p["utility_floor"] == 0.80
    assert p["discovery_burden_max"] == 0.20
    assert p["complete_ratio_max"] == 1.0
    assert p["warmups"] == 1 and p["repeats"] == 3
    assert p["adaptive_factors"] == [1, 2, 4]
    assert p["requires_both_seeds"] is True


def fake_retained():
    training = {}
    for seed in (87001, 87002):
        training[f"point16_s{seed}"] = {"fit_ms": 10.0}
        training[f"full16_s{seed}"] = {"fit_ms": 20.0}
    return {"training_setup_ms": 5.0, "training": training}


def fake_records(candidate_post=2.0, candidate_disc=0.1):
    sources = [{"id": f"train{i}"} for i in range(16)]
    routes = protocol()["routes"]
    rows = []
    for repeat in (-1, 0, 1, 2):
        for source in sources:
            for route in routes:
                if route == "DIRECT":
                    disc, post = 0.0, 10.0
                elif route == "ORACLE":
                    disc, post = 0.0, 1.0
                else:
                    disc, post = candidate_disc, candidate_post
                rows.append({"case_id": source["id"], "route": route, "repeat": repeat,
                             "accepted": True, "discovery_ms": disc,
                             "post_ms": post, "total_ms": disc+post,
                             "no_full_fallback": route not in ("DIRECT",)})
    return rows, sources


def test_summary_joint_gate_can_admit_all_efficient_families():
    rows, sources = fake_records()
    result = summarize(rows, sources, fake_retained())
    assert result["decision"] == "ADMIT_FRESH_Q34_HOLDOUT"
    assert result["pareto_q34_survivors"]
    assert all(r["passed"] for r in result["route_metrics"].values())


def test_summary_rejects_expensive_discovery_even_with_good_post_cost():
    rows, sources = fake_records(candidate_post=2.0, candidate_disc=4.0)
    result = summarize(rows, sources, fake_retained())
    assert result["decision"] == "NO_FROZEN_FAMILY_Q34_CANDIDATE"
    assert not any(r["passed"] for r in result["route_metrics"].values())
