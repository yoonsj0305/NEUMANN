import json
import subprocess

import pytest

from neumann1.reacomp_adapter import exact_check, normalize, solve, verify_vendor


def test_real_vendor_bytes_match_manifest():
    assert verify_vendor()["revision"] == "2b24f50b9e55cfb6bc6fd40510c35bceaf0eda06"


def test_published_solvers_different_formats_are_equivalent():
    strings = ["replace('ab', 'x')", "replace('x', '')"]
    pairs = [["ab", "x"], ["x", ""]]
    assert normalize(strings, 5) == normalize(pairs, 5)
    assert exact_check(pairs, [["abc", "c"], ["abab", ""]])["all_correct"]


@pytest.mark.parametrize("program", [
    ["replace('a','b') or True"], ["replace('a','b'); print('extra')"],
    ["something.replace('a','b')"], ["replace('a','b', count=1)"],
    ["replace('', 'b')"], ["replace('abcd','b')"], [["a", True]],
    [["a", "long"]], "replace('a','b')", ["replace(__import__('os'),'b')"],
])
def test_partial_parsing_and_non_dsl_programs_are_rejected(program):
    with pytest.raises((ValueError, SyntaxError)):
        normalize(program, 5)


def test_original_inputs_still_reject_a_plausible_program():
    assert not exact_check(normalize(["replace('a','b')"], 5), [["aa", "bc"]])["all_correct"]


def test_cascade_bound_is_enforced_independently_of_solver_claim():
    with pytest.raises(ValueError):
        normalize([["a", "b"]] * 6, 5)


def test_empty_program_identity_is_distinct_from_published_reward():
    assert exact_check(normalize([], 5), [["a", "a"]])["all_correct"]
    assert not exact_check([], [["a", "b"]])["all_correct"]


def test_worker_payload_contains_only_permitted_examples_and_limits(monkeypatch):
    observed = {}

    class FakeProcess:
        returncode = 0

        def communicate(self, payload, timeout):
            observed.update(json.loads(payload))
            return json.dumps({"result": {"program": [["a", "b"]], "success": True},
                               "upstream_reward": 1, "solver_internal_seconds": 0.01}), ""

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    assert solve("qwen", [["a", "b"]], 5, 8)["accepted"]
    assert observed == {"arm": "qwen", "examples": [["a", "b"]], "max_programs": 5}


@pytest.mark.parametrize("program,reward", [([["a", "x"]], 1), ([["a", "b"]], 0)])
def test_acceptance_requires_both_independent_check_and_published_reward(monkeypatch, program, reward):
    class FakeProcess:
        returncode = 0

        def communicate(self, payload, timeout):
            return json.dumps({"result": {"program": program, "success": True},
                               "upstream_reward": reward, "solver_internal_seconds": 0.01}), ""

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    assert not solve("cc", [["a", "b"]], 5, 8)["accepted"]


def test_timeout_kills_child_and_retains_failure_cost(monkeypatch):
    killed = []

    class FakeProcess:
        returncode = -1

        def communicate(self, *args, **kwargs):
            if kwargs:
                raise subprocess.TimeoutExpired("synthetic child", kwargs["timeout"])
            return "", ""

        def kill(self):
            killed.append(True)

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    result = solve("cc", [["a", "b"]], 5, 8)
    assert result["status"] == "TIMEOUT" and not result["accepted"]
    assert result["elapsed_seconds"] > 0 and killed == [True]
