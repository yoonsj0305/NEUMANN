"""Synthetic arithmetic examples only; these are not NEUMANN measurements."""
from copy import deepcopy

import pytest

from neumann1.candidate_budget import COMPONENTS, screen


def fixture():
    return {"resource_axis": "synthetic seconds", "target_multiplier": 10,
            "reuse_counts": [1, 100],
            "baselines": [{"id": "direct", "qualified": True,
                           "receipt": "synthetic fixture", "investment": 0, "per_item": 100}],
            "candidates": [{"id": "compile", "investment": 100,
                            "fixed_floor": {key: (1 if key == "verify" else 0) for key in COMPONENTS},
                            "floor_receipt": "synthetic fixture", "failed_path_floor": 0,
                            "fallback_rate": 0, "fallback_cost": 100,
                            "discovery_cost": None}]}


def test_upfront_investment_can_reverse_cold_and_reused_decisions():
    rows = screen(fixture())["rows"]
    assert rows[0]["status"] == "BUDGET_INFEASIBLE_UNDER_DECLARED_FLOORS"
    assert rows[1]["discovery_budget_per_item"] == "8"
    assert rows[1]["status"].startswith("HEADROOM_ONLY")


def test_fallback_and_failed_attempts_consume_the_same_budget():
    envelope = fixture()
    candidate = envelope["candidates"][0]
    candidate.update(investment=0, fallback_rate="0.09", failed_path_floor="0.1")
    assert screen(envelope)["rows"][0]["discovery_budget_per_item"] == "-0.10"


def test_strong_cache_baseline_can_remove_apparent_advantage():
    envelope = fixture()
    envelope["baselines"].append({"id": "tool_cache", "qualified": True,
                                  "receipt": "synthetic", "investment": 200, "per_item": 5})
    rows = screen(envelope)["rows"]
    assert rows[0]["baseline"] == "direct"
    assert rows[1]["baseline"] == "tool_cache"
    assert rows[1]["discovery_budget_per_item"] == "-1.3"


def test_zero_discovery_boundary_is_not_a_capability_pass():
    envelope = fixture()
    envelope["candidates"][0]["investment"] = 9
    row = screen(envelope)["rows"][0]
    assert row["discovery_budget_per_item"] == "0"
    assert row["status"].startswith("HEADROOM_ONLY")


def test_measured_discovery_is_charged_without_converting_headroom_to_success():
    envelope = fixture()
    envelope["candidates"][0]["discovery_cost"] = 9
    assert screen(envelope)["rows"][1]["measured_discovery_exceeds_budget"] is True


def test_missing_capable_baseline_and_unknown_floors_never_become_zero():
    envelope = fixture()
    envelope["baselines"][0]["qualified"] = False
    assert all(row["status"] == "NEEDS_QUALIFIED_BASELINE" for row in screen(envelope)["rows"])
    envelope["baselines"][0]["qualified"] = True
    envelope["candidates"][0]["fixed_floor"]["verify"] = None
    assert all(row["status"] == "NEEDS_COST_FLOORS" for row in screen(envelope)["rows"])


@pytest.mark.parametrize("invalid", [True, -1, "NaN", "Infinity", "oops"])
def test_invalid_measurements_rejected(invalid):
    envelope = fixture()
    envelope["baselines"][0]["per_item"] = invalid
    with pytest.raises(ValueError):
        screen(envelope)


def test_qualified_baseline_requires_provenance():
    envelope = fixture()
    envelope["baselines"][0]["receipt"] = None
    with pytest.raises(ValueError):
        screen(envelope)


@pytest.mark.parametrize("counts", [[True], [0], [-1], [1.5], []])
def test_reuse_counts_cannot_be_silently_coerced(counts):
    envelope = fixture()
    envelope["reuse_counts"] = counts
    with pytest.raises(ValueError):
        screen(envelope)


def test_batch_does_not_mutate_input_or_promote_missing_candidate_data():
    envelope = fixture()
    candidate = deepcopy(envelope["candidates"][0])
    candidate.update(id="unknown", investment=None)
    envelope["candidates"].append(candidate)
    before = deepcopy(envelope)
    rows = screen(envelope)["rows"]
    assert len(rows) == 4
    assert rows[2]["status"] == "NEEDS_COST_FLOORS"
    assert envelope == before
