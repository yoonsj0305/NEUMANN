import json

from neumann1.control_plane_p12 import PERMUTATIONS
from experiments.control_plane_p18_postmortem import analyze_record


def _matrix(preferred=0):
    rows = []
    for p in PERMUTATIONS:
        aligned = [-2.0, -2.0, -2.0, -2.0]
        aligned[preferred] = -0.1
        coded = [None] * 4
        for semantic_index in range(4):
            coded[p[semantic_index]] = aligned[semantic_index]
        rows.append(coded)
    return rows


def test_complete_overwall_receipt_yields_nonadmissible_latent_choice_only():
    matrix = _matrix(1)
    record = {
        "task_id": "x",
        "stratum": "B_MULTI_FEASIBLE_SEMANTIC",
        "status": "FAILED",
        "accepted": False,
        "selected_candidate": None,
        "eligible_indexes": [0, 1, 2],
        "model_calls": 1,
        "neural_forward_calls": 36,
        "evaluated_tokens": 1,
        "accounting_complete": False,
        "error": "ValueError: semantic selector wall cap",
        "selector_receipt": {
            "status": "COMPLETE",
            "complete_ms": 180001.0,
            "passes": [
                {"mode": "batch4", "status": "COMPLETE", "complete_ms": 1.0, "matrix": matrix},
                {"mode": "unbatched1", "status": "COMPLETE", "complete_ms": 2.0, "matrix": matrix},
                {"mode": "reverse_batch4", "status": "COMPLETE", "complete_ms": 3.0, "matrix": matrix},
            ],
        },
    }
    got = analyze_record(record)
    assert got["post_hoc_non_admissible"] is True
    assert got["model_inference"] is False
    assert got["latent_masked_choice"] == 1
    assert got["historical_selected_candidate"] is None
    assert got["matches_historical_choice"] is None


def test_partial_receipt_never_invents_choice():
    record = {
        "task_id": "x",
        "stratum": "B_MULTI_FEASIBLE_SEMANTIC",
        "status": "FAILED",
        "accepted": False,
        "selected_candidate": None,
        "eligible_indexes": [0, 1],
        "selector_receipt": {"status": "FAILED", "passes": []},
    }
    got = analyze_record(record)
    assert got["diagnostic_status"] == "INCOMPLETE_SELECTOR_RECEIPT"
    assert "latent_masked_choice" not in got
