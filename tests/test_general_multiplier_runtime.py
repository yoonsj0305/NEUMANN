"""Architecture Multiplier runtime contracts. No model weights or accelerator."""
import json

from experiments.general_multiplier_tasks import model_view, multiplier_tasks
from neumann1.general_multiplier_contract import MultiplierBudget
from neumann1.general_multiplier_runtime import (
    certify_representation,
    parse_action,
    run_observation,
)


class FixtureCore:
    def __init__(self, raws):
        self.raws = iter(raws)
        self.identity = {
            "weights_frozen": True,
            "accelerator_class": True,
            "revision": "fixture",
            "artifact_sha256": "fixture",
            "device_type": "cuda",
        }

    def count_tokens(self, messages, thinking):
        assert thinking is True
        return 100

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        raw = next(self.raws)
        return {
            "raw": raw,
            "input_tokens": 100,
            "output_tokens": 12,
            "thinking_enabled": thinking,
            "generation_ms": 1.0,
            "deadline_reached": False,
            "peak_accelerator_memory_bytes": 1024,
        }


def action(value):
    return json.dumps(value, separators=(",", ":"))


def test_parser_accepts_only_registered_action_shapes():
    assert parse_action('{"a":"f","v":"18"}') == {"a":"f","v":"18"}
    assert parse_action('{"a":"t","t":"m"}') == {"a":"t","t":"m"}
    assert parse_action('{"a":"r","k":["expression","bindings"],"x":"m"}') == {
        "a":"r","k":["expression","bindings"],"x":"m"
    }
    assert parse_action('<|channel>thought scratch<|channel>final{"a":"f","v":"18"}<turn|>') == {
        "a":"f","v":"18"
    }


def test_direct_correct_final_reaches_original_checker_without_tools():
    task, private = multiplier_tasks()[0]
    result = run_observation(
        task, private, model_view(task), "DIRECT",
        FixtureCore([action({"a":"f","v":"18"})]),
    )
    assert result["accepted"]
    assert result["model_calls"] == 1
    assert result["tool_calls"] == 0
    assert any(event["kind"] == "verification" for event in result["events"])


def test_tool_math_route_executes_same_original_problem():
    task, private = multiplier_tasks()[0]
    result = run_observation(
        task, private, model_view(task), "TOOL",
        FixtureCore([action({"a":"t","t":"m"})]),
    )
    assert result["accepted"]
    assert result["tool_calls"] == 1
    starts = [event["tool"] for event in result["events"] if event["kind"] == "tool_start"]
    assert starts == ["arithmetic"]


def test_neumann_requires_and_certifies_exact_pointer_representation():
    task, private = multiplier_tasks()[0]
    result = run_observation(
        task, private, model_view(task), "NEUMANN",
        FixtureCore([action({"a":"r","k":["expression","bindings"],"x":"m"})]),
    )
    assert result["accepted"]
    assert result["tool_calls"] == 2
    starts = [event["tool"] for event in result["events"] if event["kind"] == "tool_start"]
    assert starts == ["reduce_pointer", "arithmetic"]


def test_neumann_cannot_skip_representation_even_with_correct_final():
    task, private = multiplier_tasks()[0]
    budget = MultiplierBudget(model_calls=1)
    result = run_observation(
        task, private, model_view(task), "NEUMANN",
        FixtureCore([action({"a":"f","v":"18"})]),
        budget,
    )
    assert not result["accepted"]
    assert result["tool_calls"] == 0
    assert not any(event["kind"] == "verification" for event in result["events"])


def test_direct_cannot_use_tool():
    task, private = multiplier_tasks()[0]
    result = run_observation(
        task, private, model_view(task), "DIRECT",
        FixtureCore([action({"a":"t","t":"m"})]),
        MultiplierBudget(model_calls=1),
    )
    assert not result["accepted"]
    assert result["tool_calls"] == 0
    assert "DIRECT" in result["error"]


def test_wrong_direct_final_is_terminal_and_hidden_checker_feedback_is_not_retried():
    task, private = multiplier_tasks()[0]
    core = FixtureCore([action({"a":"f","v":"17"}), action({"a":"f","v":"18"})])
    result = run_observation(task, private, model_view(task), "DIRECT", core)
    assert not result["accepted"]
    assert result["model_calls"] == 1
    assert result["answer"] == "17"


def test_bad_neumann_pointer_cannot_be_filled_in_by_runtime():
    task, _private = multiplier_tasks()[0]
    try:
        certify_representation(task, {"a":"r","k":["expression"],"x":"m"})
    except ValueError as exc:
        assert "exactly" in str(exc)
    else:
        raise AssertionError("insufficient representation was accepted")


def test_coding_tool_source_is_checked_on_hidden_original_tests():
    task, private = multiplier_tasks()[4]
    source = "def solve(items):\n return len(set(x for x in items if x < 0))"
    result = run_observation(
        task, private, model_view(task), "TOOL",
        FixtureCore([action({"a":"t","t":"p","s":source})]),
    )
    assert result["accepted"]
    assert result["answer"] == source


def test_model_view_receipt_hash_is_independent_of_runtime_labels():
    task, _ = multiplier_tasks()[0]
    view = model_view(task)
    assert "id" not in view and "family" not in view
