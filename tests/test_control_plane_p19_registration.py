import json
from pathlib import Path

import pytest

from experiments.control_plane_p19_registration import (
    EXPECTED_B_FORWARDS,
    EXPECTED_CANDIDATE_COUNTS,
    check_construction,
    development_architecture,
    proposal,
)


def test_p19_construction_is_model_free_and_fresh():
    got = check_construction()
    assert got["registration_construction_valid"] is True
    assert got["a_tasks"] == 4
    assert got["b_tasks"] == 4
    assert got["candidate_counts"] == EXPECTED_CANDIDATE_COUNTS
    assert got["b_planned_forward_calls"] == EXPECTED_B_FORWARDS
    assert got["b_planned_forward_calls_total"] == 38
    assert got["out_of_grammar_stops"] == 4
    assert got["p18_model_score_reuse"] is False
    assert got["model_inference"] is False
    assert got["weights_loaded"] is False


def test_p19_architecture_keeps_history_blocked():
    arch = development_architecture()
    assert arch["first_only"] is True
    assert arch["actual_gemma_run"] == "NOT_RUN"
    assert arch["p18_opened_tasks_model_score_reuse"] is False
    assert arch["semantic_abstention_is_accounting_complete_if_receipt_complete"] is True


def test_p19_proposal_is_pre_score_and_has_pinned_sources():
    got = proposal()
    assert got["scores_seen_at_registration"] is False
    assert got["first_only"] is True
    assert got["candidate_counts"] == EXPECTED_CANDIDATE_COUNTS
    assert got["gate"]["b_neural_forward_calls_exact"] == 38
    assert got["gate"]["tool_calls_min"] == 7
    assert got["gate"]["tool_calls_max"] == 8
    assert got["source_sha256"]
    assert all(len(x) == 64 for x in got["source_sha256"].values())
