"""Runtime-0.1 repair contract fixtures only. No weights or inference."""
import copy
import json

import pytest

from neumann1.general_runtime_v106 import development_tasks
from neumann1.general_runtime_repair_v1061 import (
    RepairLimits,
    _representation,
    parse_final,
    run_repair,
)


class ScriptedNativeCore:
    identity = {
        "weights_frozen": True,
        "revision": "fixture",
        "artifact_sha256": "fixture",
        "evidence_kind": "synthetic_control",
        "interface": "native_fixture",
    }

    def __init__(self, responses):
        self.responses = iter(responses)
        self.identity = dict(type(self).identity)
        self.calls = []

    def count_tokens(self, messages, tools, thinking):
        self.calls.append(("count", thinking, [t["function"]["name"] for t in tools]))
        return 100

    def generate(self, messages, tools, max_tokens, thinking, deadline_ms):
        self.calls.append(("generate", thinking, max_tokens, [t["function"]["name"] for t in tools]))
        parsed = next(self.responses)
        return {
            "raw": json.dumps(parsed),
            "parsed": parsed,
            "parser_error": None,
            "input_tokens": 100,
            "output_tokens": 12,
            "deadline_reached": False,
        }


def final(answer):
    return {"role": "assistant", "content": json.dumps({"answer": answer}), "tool_calls": []}


def tool(name, arguments):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"type": "function", "function": {"name": name, "arguments": arguments}}],
    }


def representation(task):
    family = task["family"]
    public = task["public"]
    common = {"family": family}
    if family == "math_logic":
        return {
            **common,
            "expression": public["expression"],
            "bindings": public["bindings"],
            "executor": "arithmetic",
        }
    if family == "constraint_planning":
        return {
            **common,
            "domains": public["domains"],
            "constraints": public["constraints"],
            "executor": "csp",
        }
    return {
        **common,
        "requirement": public["requirement"],
        "executor": "python",
        "source": "def solve(items):\n return sum(set(x for x in items if x % 2 == 0))",
    }


def test_final_normalization_accepts_only_registered_envelopes():
    assert parse_final('{"answer":18}') == 18
    assert parse_final('```json\n{"answer":"x"}\n```') == "x"
    assert parse_final('{"action":"final","answer":{"A":0}}') == {"A": 0}
    with pytest.raises(ValueError):
        parse_final('18')
    with pytest.raises(ValueError):
        parse_final('{"result":18}')


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("arm", ["N", "B3"])
def test_native_representation_executes_and_checks_original(index, arm):
    task, private = development_tasks()[index]
    core = ScriptedNativeCore([tool("represent", representation(task))])
    result = run_repair(task, private, arm, core)
    assert result["accepted"]
    assert result["model_calls"] == 1
    assert result["tool_calls"] == 2
    assert result["reasoning_policy"] == "native_actions_hidden_thinking_disabled"
    assert all(call[1] is False for call in core.calls)


def test_b2_one_native_tool_then_final():
    task, private = development_tasks()[0]
    args = {"expression": task["public"]["expression"], "bindings": task["public"]["bindings"]}
    core = ScriptedNativeCore([tool("arithmetic", args), final("18")])
    result = run_repair(task, private, "B2", core)
    assert result["accepted"]
    assert result["model_calls"] == 2
    assert result["tool_calls"] == 1
    second_generate = [c for c in core.calls if c[0] == "generate"][1]
    assert second_generate[3] == []


def test_action_calls_are_bounded_and_never_enable_hidden_thinking():
    task, private = development_tasks()[0]
    core = ScriptedNativeCore([final("18")])
    limits = RepairLimits(per_call_tokens=37)
    result = run_repair(task, private, "B0", core, limits)
    assert result["accepted"]
    generated = [c for c in core.calls if c[0] == "generate"]
    assert generated == [("generate", False, 37, [])]


def test_missing_representation_fields_are_not_silently_restored():
    task, _ = development_tasks()[0]
    with pytest.raises(ValueError):
        _representation(task, {"family": "math_logic", "executor": "arithmetic"})
    wrong = representation(task)
    wrong["bindings"] = {"a": 999}
    with pytest.raises(ValueError):
        _representation(task, wrong)


def test_planning_and_coding_representation_must_match_original():
    code, _ = development_tasks()[1]
    args = representation(code)
    args["requirement"] += " changed"
    with pytest.raises(ValueError):
        _representation(code, args)

    plan, _ = development_tasks()[2]
    args = representation(plan)
    args["constraints"] = []
    with pytest.raises(ValueError):
        _representation(plan, args)


def test_b0_tool_call_is_rejected_not_executed():
    task, private = development_tasks()[0]
    args = {"expression": task["public"]["expression"], "bindings": task["public"]["bindings"]}
    result = run_repair(task, private, "B0", ScriptedNativeCore([tool("arithmetic", args)]))
    assert not result["accepted"]
    assert result["tool_calls"] == 0
    assert "restriction" in result["error"]


def test_multiple_native_calls_in_one_turn_are_rejected():
    task, private = development_tasks()[0]
    parsed = tool("arithmetic", {"expression": "1", "bindings": {}})
    parsed["tool_calls"].append(copy.deepcopy(parsed["tool_calls"][0]))
    result = run_repair(task, private, "B2", ScriptedNativeCore([parsed]))
    assert not result["accepted"]
    assert result["tool_calls"] == 0
    assert "exactly one" in result["error"]


@pytest.mark.parametrize("arm", ["B0", "B1", "B2", "B3"])
def test_wrong_final_is_retained_as_failure(arm):
    task, private = development_tasks()[0]
    result = run_repair(task, private, arm, ScriptedNativeCore([final("17")]), RepairLimits(model_calls=1))
    assert not result["accepted"]
    assert result["answer"] == "17"
    assert any(event["kind"] == "verification" for event in result["events"])


def test_neumann_cannot_skip_representation():
    task, private = development_tasks()[0]
    result = run_repair(task, private, "N", ScriptedNativeCore([final("18")]), RepairLimits(model_calls=1))
    assert not result["accepted"]
    assert "represent" in result["error"]


def test_identity_drift_fails_after_charged_generation():
    task, private = development_tasks()[0]
    core = ScriptedNativeCore([final("18")])
    original = core.generate

    def drift(*args):
        receipt = original(*args)
        core.identity["revision"] = "changed"
        return receipt

    core.generate = drift
    result = run_repair(task, private, "B0", core)
    assert not result["accepted"]
    assert result["output_tokens"] == 12
    assert "drift" in result["error"]


def test_deadline_receipt_cannot_be_promoted_to_success():
    task, private = development_tasks()[0]
    core = ScriptedNativeCore([final("18")])

    def expired(*args):
        receipt = ScriptedNativeCore.generate(core, *args)
        receipt["deadline_reached"] = True
        return receipt

    core.generate = expired
    result = run_repair(task, private, "B0", core)
    assert not result["accepted"]
    assert result["token_accounting_complete"]
    assert "deadline" in result["error"]
