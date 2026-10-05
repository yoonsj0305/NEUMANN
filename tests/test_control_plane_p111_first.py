"""P1.11 opened-development registration/gate contracts; CPU-only."""
from experiments.control_plane_p111_registration import (
    registration, check_construction, GATE, BOUNDARY, COUNTS,
)
from experiments.control_plane_p111_runtime import evaluate, totals


def synthetic_rows(accepted=None, abstained=None):
    accepted = [True] * 12 if accepted is None else list(accepted)
    abstained = set() if abstained is None else set(abstained)
    rows = []
    for index, count in enumerate(COUNTS):
        is_abstain = index in abstained
        ok = accepted[index] and not is_abstain
        rows.append({
            "task_id": "p111d_b%02d" % (index + 1),
            "accepted": ok,
            "executed": not is_abstain,
            "selected_candidate": None if is_abstain else 0,
            "selected_route": None if is_abstain else "CSP",
            "raw_top_candidate": 0,
            "status": (
                "SEMANTIC_ABSTAINED"
                if is_abstain
                else ("ACCEPTED" if ok else "REJECTED_BY_ORIGINAL_VERIFIER")
            ),
            "accounting_complete": True,
            "selector_complete": True,
            "model_calls": 1,
            "neural_forward_calls": 1,
            "generated_calls": 0,
            "input_rows": count + 1,
            "input_tokens": 10,
            "padded_tokens": 12,
            "tool_calls": 0 if is_abstain else 1,
            "verifier_calls": 0 if is_abstain else 1,
            "feasibility_calls": count,
            "feasibility_nodes": count,
            "feasibility_constraint_checks": count,
            "witness_cache_hits": 0 if is_abstain else 1,
            "lexical_baseline": {
                "target_tokens": ["semantic"],
                "candidates": [],
                "unique_selection": None,
                "max_overlap": 0,
            },
            "extraction_ms": 1.0,
            "feasibility_ms": 1.0,
            "ir_ms": 1.0,
            "lexical_ms": 1.0,
            "selection_ms": 2.0,
            "compile_ms": 0.0 if is_abstain else 1.0,
            "routing_ms": 0.0 if is_abstain else 1.0,
            "execution_ms": 0.0 if is_abstain else 1.0,
            "verification_ms": 0.0 if is_abstain else 1.0,
            "complete_ms": 10.0,
        })
    return rows


def test_fresh_registration_and_nonlexical_construction():
    reg, rows, refs = registration()
    assert reg["scores_seen_at_registration"] is False
    assert reg["first_only"] is True
    assert reg["p110_task_score_reuse"] is False
    assert reg["architecture"]["model_parameters"] == 22713216
    assert reg["architecture"]["model_state_elements_total"] == 22713728
    assert reg["architecture"]["non_parameter_state_elements"] == 512
    assert reg["identity_repair"] == {
        "revision": "P1.11.1",
        "historical_archive_sha256": "d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0",
        "historical_verdict": "NOT_EVALUATED",
        "historical_reason": "INCOMPLETE_OR_COVERAGE_DRIFT",
        "historical_error": "P1.11 frozen model parameter-count drift",
        "historical_observations": 0,
        "historical_model_calls": 0,
        "historical_neural_forward_calls": 0,
        "task_scores_seen": False,
        "task_or_gate_changed": False,
        "repair_scope": "MODEL_PARAMETER_IDENTITY_ONLY",
    }
    assert len(rows) == len(refs) == 12
    result = check_construction()
    assert result["candidate_counts"] == COUNTS
    assert result["total_expected_forward_calls"] == 12
    assert result["feasibility_calls_expected"] == 35
    assert result["multi_feasible_tasks"] == 12
    assert result["lexical_unique_selections"] == 0
    assert result["exact_overlap_candidate_pairs"] == 0
    assert result["out_of_grammar_stops"] == 4
    assert result["model_inference"] is False
    assert result["weights_loaded"] is False


def test_nine_of_twelve_passes_development_gate_only():
    _, _, refs = registration()
    rows = synthetic_rows(abstained={1, 6, 10})
    decision = evaluate(rows, refs, True, True, 1000.0)
    assert decision["verdict"] == "PASS"
    assert decision["accepted"] == 9
    assert decision["path_cost"]["neural_forward_calls"] == 12
    assert decision["p2_registration_admitted"] is False
    assert decision["decision3_admitted"] is False


def test_eight_of_twelve_fails_capability_gate():
    _, _, refs = registration()
    rows = synthetic_rows(abstained={0, 1, 2, 3})
    decision = evaluate(rows, refs, True, True, 1000.0)
    assert decision["verdict"] == "FAIL"
    assert decision["reason"] == "P111_SEMANTIC_CAPABILITY_FAILURE"
    assert decision["accepted"] == 8


def test_exact_control_path_is_twelve_forwards_and_thirtyfive_feasibility_calls():
    rows = synthetic_rows()
    aggregate = totals(rows)
    assert aggregate["model_calls"] == 12
    assert aggregate["neural_forward_calls"] == 12
    assert aggregate["feasibility_calls"] == 35
    assert GATE["lexical_unique_selections_exact"] == 0


def test_accounting_and_wall_drift_fail_closed():
    _, _, refs = registration()
    rows = synthetic_rows()
    rows[4]["neural_forward_calls"] = 2
    assert evaluate(rows, refs, True, True, 1000.0)["reason"] == "CONTROL_WORK_ACCOUNTING_FAILURE"

    rows = synthetic_rows()
    rows[0]["lexical_baseline"]["unique_selection"] = "X"
    assert evaluate(rows, refs, True, True, 1000.0)["reason"] == "CONTROL_WORK_ACCOUNTING_FAILURE"

    rows = synthetic_rows()
    rows[0]["complete_ms"] = GATE["per_item_wall_ms"] + 1
    assert evaluate(rows, refs, True, True, 1000.0)["reason"] == "TASK_WALL_CAP"

    assert evaluate(synthetic_rows(), refs, False, True, 1000.0)["verdict"] == "NOT_EVALUATED"


def test_boundary_never_admits_downstream():
    for key in ("p2_registration_admitted", "p2_admitted", "decision3_admitted"):
        assert BOUNDARY[key] is False
    assert BOUNDARY["global_questions_closed"] == []
