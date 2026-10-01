import json
import pytest

pytest.importorskip("torch")

from experiments.lp_q34_ceiling_v096 import analyze, protocol


def test_v096_first_representation_ceiling_replay():
    result = analyze()
    assert result["protocol"] == protocol()
    assert result["decision"] in {
        "EARLY_REPRESENTATION_CEILING_BELOW_Q34_FLOOR",
        "FULL_INFORMATION_RESCUES_CURRENT_DISCOVERER",
        "DISCOVERER_BOTTLENECK_DOMINATES_EARLY_SUPPORT_LOSS",
    }
    assert len(result["tests"]) == 2
    for row in result["tests"]:
        assert row["early_off_full_basis_containment"] == 48
        assert row["early_off_containment_rate"] == 1.0
        assert 0 <= row["early_on_full_basis_containment"] <= 48
        assert 0.0 <= row["early_on_mean_label_recall"] <= 1.0
        assert 0 <= row["point_certificates"] <= 48
        assert 0 <= row["full_certificates"] <= 48
        assert 0 <= row["compact_certificates"] <= 48
        assert len(row["rows"]) == 48
    expected = {
        87001: (46, 0.9583333333333334, 0.9993489583333334, 46, 0.9993489583333334, 1, 0, 0, 0),
        87002: (46, 0.9583333333333334, 0.9993489583333334, 47, 0.9996744791666666, 0, 0, 1, -1),
    }
    for row in result["tests"]:
        (contain, rate, mean_recall, full_short, full_short_recall,
         point_cert, full_cert, compact_cert, gain) = expected[row["seed"]]
        assert row["early_on_full_basis_containment"] == contain
        assert row["early_on_containment_rate"] == pytest.approx(rate, abs=1e-15)
        assert row["early_on_mean_label_recall"] == pytest.approx(mean_recall, abs=1e-15)
        assert row["full_graph_shortlist_containment"] == full_short
        assert row["full_graph_mean_label_recall"] == pytest.approx(full_short_recall, abs=1e-15)
        assert (row["point_certificates"], row["full_certificates"], row["compact_certificates"]) == (point_cert, full_cert, compact_cert)
        assert row["full_information_certificate_gain"] == gain
        assert row["representation_ceiling_adequate"] is True
        assert row["full_information_rescue"] is False
    assert result["decision"] == "DISCOVERER_BOTTLENECK_DOMINATES_EARLY_SUPPORT_LOSS"
    assert result["cost_claim"] is False
    assert result["q34_pass_claim"] is False
    assert result["global_q3"] == result["global_q4"] == "OPEN"
    print("V096_FIRST_REPLAY=" + json.dumps(result, separators=(",", ":")))


def test_q34_ceiling_protocol_is_frozen_before_result():
    p = protocol()
    assert p["utility_floor"] == 0.80
    assert p["full_information_certificate_gain"] == 4
    assert p["new_fitting"] is False
    assert p["new_inference"] is False
    assert p["new_solver_calls"] is False
    assert p["timing"] is False
    assert p["q34_pass_claim"] is False
