import json
from pathlib import Path

from experiments.decision3_readiness import check


def test_readiness_waits_without_decision2_and_opens_nothing():
    r=check(None)
    assert r["status"]=="WAIT_DECISION2_EVIDENCE"
    assert r["sealed_rows_opened"] is False
    assert r["model_inference_performed"] is False
    assert r["frontier_calls"]==0


def test_valid_decision2_pass_still_blocks_current_task_specific_interface(tmp_path):
    replay=tmp_path/"replay.json"
    replay.write_text(json.dumps({
        "valid":True,
        "recomputed_decision_2":{"verdict":"PASS"},
    }),encoding="utf-8")
    r=check(replay)
    assert r["decision2_valid"] is True
    assert r["decision2_verdict"]=="PASS"
    assert r["status"]=="BLOCKED_TASK_SPECIFIC_INTERFACE"
    assert r["sealed_rows_opened"] is False


def test_invalid_replay_cannot_arm(tmp_path):
    replay=tmp_path/"replay.json"
    replay.write_text(json.dumps({
        "valid":False,
        "recomputed_decision_2":{"verdict":"PASS"},
    }),encoding="utf-8")
    r=check(replay)
    assert r["status"]=="BLOCKED_INVALID_DECISION2_REPLAY"


def test_negative_decision2_never_opens_decision3(tmp_path):
    replay=tmp_path/"replay.json"
    replay.write_text(json.dumps({
        "valid":True,
        "recomputed_decision_2":{"verdict":"FAIL"},
    }),encoding="utf-8")
    r=check(replay)
    assert r["status"]=="BLOCKED_DECISION2_NOT_PASS"
    assert r["sealed_rows_opened"] is False
