"""Control-flow fixtures only. No weights, inference, training or holdout."""
import copy
import json
from unittest.mock import patch

import pytest
from neumann1.general_runtime_v106 import Limits, development_tasks, reduce_original, run, sha, verify_original, _python


class ScriptedCore:
    identity = {"weights_frozen": True, "revision": "fixture", "artifact_sha256": "fixture", "evidence_kind": "synthetic_control"}
    def __init__(self, actions):
        self.actions = iter(actions)
        self.identity = dict(type(self).identity)
    def count_tokens(self, messages, thinking): return 100
    def generate(self, messages, max_tokens, thinking, deadline_ms):
        return {"raw": json.dumps(next(self.actions)), "input_tokens": 100, "output_tokens": 10}


def plan(task):
    ir = {"family": task["family"], **{k:v for k,v in task["public"].items() if k != "background"}}
    return {"action": "represent", "ir": ir, "executor": {"math_logic":"arithmetic", "constraint_planning":"csp", "coding":"python"}[task["family"]],
            "source": "def solve(items):\n return sum(set(x for x in items if x % 2 == 0))"}


@pytest.mark.parametrize("index", [0,1,2])
@pytest.mark.parametrize("arm", ["N", "B3"])
def test_shared_plan_execution_and_original_check(index, arm):
    task, private = development_tasks()[index]
    r = run(task, private, arm, ScriptedCore([plan(task)]))
    assert r["accepted"] and r["model_calls"] == 1 and r["tool_calls"] == 2
    assert r["trace_sha256"] == sha(r["events"])
    assert r["evidence_kind"] == "synthetic_control"
    assert r["resources"]["energy_j"]["value"] is None


def test_original_constraints_cannot_be_removed():
    task, private = development_tasks()[2]
    action = plan(task); action["ir"]["constraints"] = []
    with pytest.raises(ValueError): reduce_original(task, action["ir"])
    assert not verify_original(task, {"A":0,"B":0,"C":0}, private, 1000)


def test_unknown_rule_or_empty_program_tests_cannot_attest_correctness():
    task, private = development_tasks()[2]
    task["public"]["constraints"] = [["unknown","A","B"]]
    with pytest.raises(ValueError): verify_original(task,{"A":0,"B":1,"C":2},private,1000)
    task, _ = development_tasks()[1]
    with pytest.raises(ValueError): verify_original(task,"def solve(items): return 0",{"tests":[]},1000)


def test_ir_rewrite_cannot_change_answer():
    task, _ = development_tasks()[0]
    with pytest.raises(ValueError): reduce_original(task, {"family":"math_logic", "expression":"1"})
    ir = reduce_original(task, plan(task)["ir"])["ir"]
    assert "unused" not in ir["bindings"]


@pytest.mark.parametrize("arm", ["B0", "B1", "B2", "B3"])
def test_baseline_final_wrong_answer_retained(arm):
    task, private = development_tasks()[0]
    r = run(task, private, arm, ScriptedCore([{"action":"final", "answer":"17"}]), Limits(model_calls=1))
    assert not r["accepted"] and r["answer"] == "17" and r["complete_ms"] > 0
    assert any(e["kind"] == "verification" for e in r["events"])


def test_neumann_must_represent_and_b0_may_not_call_tools():
    task, private = development_tasks()[0]
    for arm in ("N", "B0"):
        action = {"action":"final", "answer":"18"} if arm == "N" else plan(task)
        r = run(task, private, arm, ScriptedCore([action]), Limits(model_calls=1))
        assert not r["accepted"]


def test_retry_and_tools_charge_complete_query():
    task, private = development_tasks()[0]
    invalid = plan(task); invalid["ir"]["expression"] = "1"
    r = run(task, private, "N", ScriptedCore([invalid, plan(task)]))
    assert r["accepted"] and r["model_calls"] == 2 and r["tool_calls"] == 3
    assert r["input_tokens"] == 200 and r["output_tokens"] == 20


def test_weight_drift_is_failure():
    task, private = development_tasks()[0]
    core = ScriptedCore([{"action":"final", "answer":"18"}])
    original = core.generate
    def drift(*args):
        r = original(*args); core.identity["revision"] = "changed"; return r
    core.generate = drift
    r = run(task, private, "B0", core)
    assert not r["accepted"] and "drift" in r["error"]


def test_checker_error_is_not_success():
    task, private = development_tasks()[0]
    with patch("neumann1.general_runtime_v106.verify_original", side_effect=ValueError("checker failed")):
        r = run(task, private, "B0", ScriptedCore([{"action":"final", "answer":"18"}]))
    assert not r["accepted"] and r["verification_errors"]


def test_missing_model_receipt_is_explicit_incomplete_accounting():
    task, private = development_tasks()[0]
    core = ScriptedCore([])
    r = run(task, private, "B0", core)
    assert not r["accepted"] and r["token_accounting_complete"] is False
    assert r["model_calls"] == 1 and r["complete_ms"] > 0


def test_nonfinite_json_rejected_with_full_raw_receipt_and_token_cost():
    task, private = development_tasks()[0]
    core = ScriptedCore([])
    core.generate = lambda *args: {"raw":'{"action":"final","answer":NaN}',"input_tokens":100,"output_tokens":10}
    r = run(task,private,"B0",core)
    assert not r["accepted"] and r["token_accounting_complete"]
    assert r["output_tokens"] == 10 and "NaN" in r["events"][1]["receipt"]["raw"]


def test_nested_artifact_identity_drift_is_failure():
    task, private = development_tasks()[0]
    core = ScriptedCore([{"action":"final","answer":"18"}])
    core.identity["files"] = {"weights":"original"}
    original = core.generate
    def drift(*args):
        r = original(*args); core.identity["files"]["weights"] = "changed"; return r
    core.generate = drift
    r = run(task,private,"B0",core)
    assert not r["accepted"] and "drift" in r["error"] and r["output_tokens"] == 10


def test_official_processor_content_used_without_discarding_raw():
    task, private = development_tasks()[0]
    core = ScriptedCore([])
    raw = "retained thinking and token separators"
    core.generate = lambda *args: {"raw":raw,"action_text":'{"action":"final","answer":"18"}',"input_tokens":100,"output_tokens":10}
    r = run(task, private, "B0", core)
    assert r["accepted"] and r["events"][1]["receipt"]["raw"] == raw


@pytest.mark.parametrize("source", ["import os\ndef solve(items): return 1", "def solve(items): return open('x')", "def solve(items): return items.__class__"])
def test_python_subset_rejects_external_access(source):
    with pytest.raises(ValueError): _python(source, [[]], 1000)


def test_python_infinite_loop_is_bounded():
    with pytest.raises((ValueError, TimeoutError)):
        _python("def solve(items):\n while True: pass", [[]], 100)


def test_development_never_overwrites_first_directory(tmp_path):
    from experiments.general_development_v106 import execute
    path = tmp_path / "first"; path.mkdir()
    with pytest.raises(FileExistsError): execute(path, "fixture-head")
