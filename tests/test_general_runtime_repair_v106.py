"""Synthetic protocol tests only. No weights, inference, fitting or holdout."""
import json

from neumann1.general_runtime_v106 import development_tasks, run
from neumann1.general_runtime_repair_v106 import (
    REPAIR_ID,
    Runtime01ProtocolAdapter,
    normalize_action_text,
)


class RawCore:
    identity = {
        "weights_frozen": True,
        "revision": "fixture",
        "artifact_sha256": "fixture",
        "evidence_kind": "synthetic_control",
    }

    def __init__(self, texts):
        self.texts = iter(texts)
        self.identity = dict(type(self).identity)
        self.generate_thinking = []
        self.count_thinking = []
        self.prompts = []

    def count_tokens(self, messages, thinking):
        self.count_thinking.append(thinking)
        self.prompts.append(messages[0]["content"])
        return 100

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        self.generate_thinking.append(thinking)
        self.prompts.append(messages[0]["content"])
        text = next(self.texts)
        return {
            "raw": text + "<turn|>",
            "action_text": text,
            "input_tokens": 100,
            "output_tokens": 12,
        }

    def audit(self):
        return {"unchanged": True}


def test_bare_answer_object_is_framed_without_changing_answer():
    task, private = development_tasks()[0]
    original = "```json\n" + json.dumps({"answer": private["exact"]}) + "\n```"
    base = RawCore([original])
    repaired = Runtime01ProtocolAdapter(base)
    result = run(task, private, "B0", repaired)

    assert result["accepted"]
    receipt = result["events"][1]["receipt"]
    assert receipt["original_action_text"] == original
    assert receipt["runtime01_repair"]["rewrite"] == "insert_action:final"
    assert json.loads(receipt["action_text"])["answer"] == private["exact"]


def test_tool_shape_is_framed_and_b2_reaches_a_real_tool_path():
    task, private = development_tasks()[0]
    public = task["public"]
    first = json.dumps({
        "tool": "arithmetic",
        "args": {"expression": public["expression"], "bindings": public["bindings"]},
    })
    second = json.dumps({"answer": private["exact"]})
    base = RawCore([first, second])
    result = run(task, private, "B2", Runtime01ProtocolAdapter(base))

    assert result["accepted"]
    assert result["tool_calls"] == 1
    assert result["model_calls"] == 2
    assert any(event["kind"] == "tool_result" for event in result["events"])


def test_neumann_representation_shape_executes_without_narration_retry():
    task, private = development_tasks()[0]
    action = json.dumps({
        "ir": {"family": "math_logic", "expression": task["public"]["expression"]},
        "executor": "arithmetic",
    })
    base = RawCore([action])
    result = run(task, private, "N", Runtime01ProtocolAdapter(base))

    assert result["accepted"]
    assert result["model_calls"] == 1
    assert result["tool_calls"] == 2
    assert result["answer"] == private["exact"]


def test_hidden_thinking_is_forced_off_and_charged_prompt_is_shared():
    task, private = development_tasks()[0]
    base = RawCore([json.dumps({"answer": private["exact"]})])
    result = run(task, private, "B1", Runtime01ProtocolAdapter(base))

    assert result["accepted"]
    assert base.count_thinking == [False]
    assert base.generate_thinking == [False]
    receipt = result["events"][1]["receipt"]
    assert receipt["runtime01_repair"] == {
        "id": REPAIR_ID,
        "requested_thinking": True,
        "effective_thinking": False,
        "rewrite": "insert_action:final",
    }
    assert all("hidden thinking is disabled" in prompt for prompt in base.prompts)


def test_malformed_or_ambiguous_objects_are_not_silently_rescued():
    assert normalize_action_text('{"foo":"bar"}')[1] is None
    assert normalize_action_text('{"answer":"18","tool":"arithmetic","args":{}}')[1] is None
    assert normalize_action_text("plain answer 18")[1] is None

    task, private = development_tasks()[0]
    result = run(task, private, "B0", Runtime01ProtocolAdapter(RawCore(['{"foo":"bar"}'])))
    assert not result["accepted"]
    assert result["error"] == "invalid one-shot response"


def test_existing_valid_action_is_byte_preserved_at_adapter_boundary():
    text = '{"action":"final","answer":"18"}'
    normalized, rewrite = normalize_action_text(text)
    assert normalized == text
    assert rewrite is None
