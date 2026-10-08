from neumann1 import reacomp_policy


def test_no_holdout_feedback_and_no_second_call_when_first_fits(monkeypatch):
    calls = []

    def fake(arm, examples, limit, timeout):
        calls.append(arm)
        return {"accepted": True, "program": [["a", "b"]]}

    monkeypatch.setattr(reacomp_policy, "solve", fake)
    result = reacomp_policy.solve_examples([["a", "b"]])
    assert calls == ["qwen"]
    assert result["status"] == "EXAMPLES_FIT"
    assert result["unseen_function_equivalence"] == "NOT_CERTIFIED"


def test_rejected_first_attempt_is_retained_and_fallback_cannot_promote_failure(monkeypatch):
    monkeypatch.setattr(reacomp_policy, "solve", lambda *args: {"accepted": False, "status": "TIMEOUT"})
    result = reacomp_policy.solve_examples([["a", "b"]])
    assert result["status"] == "ABSTAIN"
    assert [attempt["arm"] for attempt in result["attempts"]] == ["qwen", "cc"]
    assert all(attempt["status"] == "TIMEOUT" for attempt in result["attempts"])
