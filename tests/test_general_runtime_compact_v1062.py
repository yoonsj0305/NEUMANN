"""Runtime-0.2 compact repair contracts only. No model weights or inference."""
import json

import pytest

from neumann1.general_runtime_v106 import development_tasks
from neumann1.general_runtime_compact_v1062 import (
    CompactLimits,
    build_messages,
    certify_pointer_representation,
    parse_action,
    run_compact,
)


class ScriptedRawCore:
    identity = {
        "weights_frozen": True,
        "revision": "fixture",
        "artifact_sha256": "fixture",
        "evidence_kind": "synthetic_control",
        "interface": "compact_raw_fixture",
    }

    def __init__(self, raws, prompt_tokens=100, output_tokens=12):
        self.raws = iter(raws)
        self.prompt_tokens = prompt_tokens
        self.output_tokens = output_tokens
        self.identity = dict(type(self).identity)
        self.calls = []

    def count_tokens(self, messages, thinking):
        self.calls.append(("count", thinking, len(messages)))
        return self.prompt_tokens

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        self.calls.append(("generate", thinking, max_tokens, deadline_ms))
        return {
            "raw": next(self.raws),
            "input_tokens": self.prompt_tokens,
            "output_tokens": min(self.output_tokens, max_tokens),
            "deadline_reached": False,
        }


def action(value):
    return json.dumps(value, separators=(",", ":"))


def rep(task, source=None):
    family = task["family"]
    if family == "math_logic":
        out = {"a": "r", "k": ["expression", "bindings"], "x": "m"}
    elif family == "constraint_planning":
        out = {"a": "r", "k": ["domains", "constraints"], "x": "c"}
    else:
        out = {"a": "r", "k": ["requirement"], "x": "p", "s": source}
    return out


def compute(task, source=None):
    family = task["family"]
    out = {"a": "c", "t": {"math_logic": "m", "constraint_planning": "c", "coding": "p"}[family]}
    if family == "coding":
        out["s"] = source
    return out


def test_compact_parser_accepts_registered_final_forms_only():
    assert parse_action('{"a":"f","v":18}') == {"a": "f", "v": 18}
    assert parse_action('{"answer":"18"}') == {"a": "f", "v": "18"}
    assert parse_action('{"action":"final","answer":18}') == {"a": "f", "v": 18}
    with pytest.raises(ValueError):
        parse_action('18')
    with pytest.raises(ValueError):
        parse_action('{"a":"x"}')


def test_pointer_certificate_requires_exact_public_field_selection():
    task, _ = development_tasks()[0]
    cert = certify_pointer_representation(task, rep(task))
    assert cert["selected_public_fields"] == ["bindings", "expression"]
    assert "unused" not in cert["ir"]["bindings"]

    bad = rep(task)
    bad["k"] = ["expression"]
    with pytest.raises(ValueError):
        certify_pointer_representation(task, bad)

    bad = rep(task)
    bad["x"] = "c"
    with pytest.raises(ValueError):
        certify_pointer_representation(task, bad)


def test_build_messages_contains_original_task_and_no_native_schema_surface():
    task, _ = development_tasks()[0]
    messages = build_messages(task, "N")
    assert messages[1]["role"] == "user"
    assert task["id"] in messages[1]["content"]
    assert "tools" not in messages[0] and "tools" not in messages[1]


def test_direct_final_still_checked_on_original_task():
    task, private = development_tasks()[0]
    core = ScriptedRawCore([action({"a": "f", "v": "18"})])
    result = run_compact(task, private, "B0", core)
    assert result["accepted"]
    assert result["model_calls"] == 1 and result["tool_calls"] == 0
    assert any(event["kind"] == "verification" for event in result["events"])


@pytest.mark.parametrize("index", [0, 2])
def test_b2_one_compact_compute_is_auto_submitted_to_original_checker(index):
    task, private = development_tasks()[index]
    core = ScriptedRawCore([action(compute(task))])
    result = run_compact(task, private, "B2", core)
    assert result["accepted"]
    assert result["model_calls"] == 1
    assert result["tool_calls"] == 1
    assert any(event["kind"] == "verification" and event["accepted"] for event in result["events"])


def test_b2_python_source_is_tool_candidate_not_runtime_generated_answer():
    task, private = development_tasks()[1]
    source = "def solve(items):\n return sum(set(x for x in items if x%2==0))"
    core = ScriptedRawCore([action(compute(task, source))])
    result = run_compact(task, private, "B2", core)
    assert result["accepted"]
    assert result["answer"] == source
    assert result["tool_calls"] == 1


@pytest.mark.parametrize("index", [0, 1, 2])
def test_neumann_pointer_representation_executes_and_checks_original(index):
    task, private = development_tasks()[index]
    source = "def solve(items):\n return sum(set(x for x in items if x%2==0))" if index == 1 else None
    core = ScriptedRawCore([action(rep(task, source))])
    result = run_compact(task, private, "N", core)
    assert result["accepted"]
    assert result["model_calls"] == 1
    assert result["tool_calls"] == 2
    assert all(call[1] is False for call in core.calls)


def test_b3_cannot_bypass_tool_path_with_direct_final():
    task, private = development_tasks()[0]
    result = run_compact(task, private, "B3", ScriptedRawCore([action({"a": "f", "v": "18"})]))
    assert not result["accepted"]
    assert result["tool_calls"] == 0
    assert "tool/representation" in result["error"]


def test_neumann_can_repair_rejected_pointer_once_without_hidden_restoration():
    task, private = development_tasks()[0]
    wrong = {"a": "r", "k": ["expression"], "x": "m"}
    core = ScriptedRawCore([action(wrong), action(rep(task))], prompt_tokens=100)
    result = run_compact(task, private, "N", core)
    assert result["accepted"]
    assert result["model_calls"] == 2
    assert result["tool_calls"] == 3
    assert any(
        event["kind"] == "tool_result"
        and event.get("tool") == "reduce_pointer"
        and "error" in event.get("result", {})
        for event in result["events"]
    )


def test_prompt_admission_blocks_before_any_generation():
    task, private = development_tasks()[0]
    core = ScriptedRawCore([action({"a": "f", "v": "18"})], prompt_tokens=241)
    result = run_compact(task, private, "B0", core, CompactLimits(admission_tokens=240))
    assert not result["accepted"]
    assert result["admission_blocked"]
    assert result["model_calls"] == 0
    assert result["input_tokens"] == 0
    assert "PROMPT_ADMISSION_BLOCKED" in result["error"]


def test_prompt_at_admission_boundary_is_allowed():
    task, private = development_tasks()[0]
    core = ScriptedRawCore([action({"a": "f", "v": "18"})], prompt_tokens=240)
    result = run_compact(task, private, "B0", core)
    assert result["accepted"]
    assert result["max_prompt_tokens"] == 240


def test_raw_parser_failure_is_retained_without_answer_inference():
    task, private = development_tasks()[0]
    core = ScriptedRawCore(['{"a":"f","v":'])
    result = run_compact(task, private, "B0", core)
    assert not result["accepted"]
    assert result["answer"] is None
    assert any(event["kind"] == "action_rejected" for event in result["events"])


def test_deadline_receipt_cannot_be_promoted_to_success():
    task, private = development_tasks()[0]
    core = ScriptedRawCore([action({"a": "f", "v": "18"})])

    def expired(messages, max_tokens, thinking, deadline_ms):
        receipt = ScriptedRawCore.generate(core, messages, max_tokens, thinking, deadline_ms)
        receipt["deadline_reached"] = True
        return receipt

    core.generate = expired
    result = run_compact(task, private, "B0", core)
    assert not result["accepted"]
    assert result["token_accounting_complete"]
    assert "deadline" in result["error"]


def test_identity_drift_fails_after_charged_generation():
    task, private = development_tasks()[0]
    core = ScriptedRawCore([action({"a": "f", "v": "18"})])
    original = core.generate

    def drift(*args):
        receipt = original(*args)
        core.identity["revision"] = "changed"
        return receipt

    core.generate = drift
    result = run_compact(task, private, "B0", core)
    assert not result["accepted"]
    assert result["output_tokens"] == 12
    assert "drift" in result["error"]
