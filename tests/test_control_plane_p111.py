import pytest

from neumann1.control_plane_p111 import (
    MODEL, Criteria, contract, semantic_role_ir, select_from_similarities,
)


def test_contract_is_microexecutor_not_generative_controller():
    c = contract()
    assert c["model"]["model_id"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert c["model"]["model_revision"] == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    assert c["model"]["parameters"] == 22713728
    assert c["large_generative_model_on_primary_path"] is False
    assert c["forward_calls_per_ambiguous_item"] == 1
    assert c["generation"] is False
    assert c["actual_model_run"] == "NOT_RUN"
    assert c["p110_task_score_reuse"] is False


def test_ir_keeps_only_target_and_candidate_roles():
    instruction = (
        "X is the primary route and Y is the reserve route. "
        "Resolve 'It' to the emergency path, then return a complete assignment."
    )
    ir = semantic_role_ir(instruction, ["X", "Y"])
    assert ir == {
        "target_role": "emergency path",
        "candidates": [
            {"entity": "X", "role": "primary route"},
            {"entity": "Y", "role": "reserve route"},
        ],
    }
    raw = str(ir)
    for forbidden in ("{14,17}", "differs from", "equals", "DOMAIN", "EQ", "NE"):
        assert forbidden not in raw


def test_ir_supports_three_and_four_candidate_registered_grammar():
    ir3 = semantic_role_ir(
        "A is the intake node, B is the transform node, and C is the output node. "
        "Resolve 'It' to the terminal node, then return a complete assignment.",
        ["A", "B", "C"],
    )
    assert [x["role"] for x in ir3["candidates"]] == [
        "intake node", "transform node", "output node"
    ]

    ir4 = semantic_role_ir(
        "P is the sensor, Q is the controller, R is the actuator, and S is the recorder. "
        "Resolve 'It' to the component that physically changes the system, then return a complete assignment.",
        ["P", "Q", "R", "S"],
    )
    assert ir4["target_role"] == "component that physically changes the system"
    assert [x["entity"] for x in ir4["candidates"]] == ["P", "Q", "R", "S"]


def test_selector_chooses_unique_top_with_margin():
    ir = {
        "target_role": "emergency path",
        "candidates": [
            {"entity": "X", "role": "primary route"},
            {"entity": "Y", "role": "reserve route"},
        ],
    }
    got = select_from_similarities(ir, [0.31, 0.62])
    assert got["selected_entity"] == "Y"
    assert got["margin_cosine"] > 0.05


def test_selector_abstains_on_small_margin():
    ir = {
        "target_role": "terminal node",
        "candidates": [
            {"entity": "A", "role": "intake node"},
            {"entity": "B", "role": "transform node"},
            {"entity": "C", "role": "output node"},
        ],
    }
    with pytest.raises(ValueError, match="margin failure"):
        select_from_similarities(ir, [0.40, 0.41, 0.43])


def test_selector_abstains_if_all_similarity_is_negative():
    ir = {
        "target_role": "state inference",
        "candidates": [
            {"entity": "M", "role": "estimator"},
            {"entity": "N", "role": "controller"},
        ],
    }
    with pytest.raises(ValueError, match="below floor"):
        select_from_similarities(ir, [-0.20, -0.05])


def test_instruction_and_entity_drift_fail_closed():
    with pytest.raises(ValueError):
        semantic_role_ir("X is something.", ["X", "Y"])
    with pytest.raises(ValueError):
        semantic_role_ir(
            "X is the primary route and Y is the reserve route. "
            "Resolve 'It' to the emergency path, then return a complete assignment.",
            ["X", "Z"],
        )
