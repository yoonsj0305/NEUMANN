import pytest

from neumann1.control_plane_p112 import (
    MODEL,
    build_joint_pairs,
    contract,
    select_unique_top,
)


def test_contract_changes_semantic_primitive_not_model_scale_class():
    c = contract()
    assert c["model"]["model_id"] == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert c["model"]["model_revision"] == "ce0834f22110de6d9222af7a7a03628121708969"
    assert c["model"]["expected_parameters"] == 22713601
    assert c["cross_encoder_joint_interaction"] is True
    assert c["bi_encoder_cosine_on_primary_path"] is False
    assert c["forward_calls_per_ambiguous_item"] == 1
    assert c["confidence_threshold"] is None
    assert c["confidence_calibration_deferred"] is True
    assert c["actual_model_run"] == "NOT_RUN"
    assert c["p111_task_score_reuse"] is False
    assert c["p111_tasks_as_p112_evidence"] is False


def test_joint_pair_ir_keeps_only_target_and_candidate_roles():
    instruction = (
        "X is the primary route and Y is the reserve route. "
        "Resolve 'It' to the emergency path, then return a complete assignment."
    )
    ir = build_joint_pairs(instruction, ["X", "Y"])
    assert ir == {
        "target_role": "emergency path",
        "pairs": [
            {
                "entity": "X",
                "query": "Target function: emergency path",
                "candidate_text": "Candidate role: primary route",
            },
            {
                "entity": "Y",
                "query": "Target function: emergency path",
                "candidate_text": "Candidate role: reserve route",
            },
        ],
    }
    raw = str(ir)
    for forbidden in ("{14,17}", "differs from", "equals", "DOMAIN", "EQ", "NE"):
        assert forbidden not in raw


def test_joint_pairs_support_three_and_four_candidates():
    ir3 = build_joint_pairs(
        "A is the intake node, B is the transform node, and C is the output node. "
        "Resolve 'It' to the terminal node, then return a complete assignment.",
        ["A", "B", "C"],
    )
    assert len(ir3["pairs"]) == 3
    assert [row["entity"] for row in ir3["pairs"]] == ["A", "B", "C"]

    ir4 = build_joint_pairs(
        "P is the sensor, Q is the controller, R is the actuator, and S is the recorder. "
        "Resolve 'It' to the component that physically changes the system, then return a complete assignment.",
        ["P", "Q", "R", "S"],
    )
    assert len(ir4["pairs"]) == 4
    assert ir4["target_role"] == "component that physically changes the system"


def test_raw_ranking_selects_unique_top_without_margin_gate():
    ir = {
        "target_role": "stage that builds the parse tree",
        "pairs": [
            {"entity": "A", "query": "Target function: stage that builds the parse tree", "candidate_text": "Candidate role: tokenizer"},
            {"entity": "B", "query": "Target function: stage that builds the parse tree", "candidate_text": "Candidate role: syntax analyzer"},
            {"entity": "C", "query": "Target function: stage that builds the parse tree", "candidate_text": "Candidate role: optimizer"},
        ],
    }
    got = select_unique_top(ir, [-1.2, -1.19, -3.0])
    assert got["selected_entity"] == "B"
    assert got["raw_margin_logit"] == pytest.approx(0.01)


def test_exact_top_tie_abstains_fail_closed():
    ir = {
        "target_role": "target",
        "pairs": [
            {"entity": "X", "query": "Target function: target", "candidate_text": "Candidate role: one"},
            {"entity": "Y", "query": "Target function: target", "candidate_text": "Candidate role: two"},
        ],
    }
    with pytest.raises(ValueError, match="tie"):
        select_unique_top(ir, [0.5, 0.5])


def test_nonfinite_or_shape_drift_fails_closed():
    ir = {
        "target_role": "target",
        "pairs": [
            {"entity": "X", "query": "Target function: target", "candidate_text": "Candidate role: one"},
            {"entity": "Y", "query": "Target function: target", "candidate_text": "Candidate role: two"},
        ],
    }
    with pytest.raises(ValueError):
        select_unique_top(ir, [0.2])
    with pytest.raises(ValueError):
        select_unique_top(ir, [float("nan"), 0.1])


def test_model_identity_parameter_formula_is_explicit():
    # Frozen six-layer MiniLM BERT with pooler plus one 384->1 classifier head.
    assert MODEL["expected_parameters"] == 22713216 + 384 + 1
