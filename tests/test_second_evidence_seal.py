"""SECOND verdicts and evidence are immutable: any byte change to a sealed file fails this test."""
import hashlib, json, pathlib


def test_second_evidence_is_unchanged():
    seal = json.loads(pathlib.Path("docs/experiments/second_evidence_seal.json").read_text())
    for f, want in seal["sha256"].items():
        assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() == want, f
    res = json.loads(pathlib.Path("docs/experiments/results/invention_second_result.json").read_text())
    assert res["verdict"] == seal["verdict_fixed"]
    assert res["verdict"]["P2_rule"] == res["verdict"]["P2_dc"] == res["verdict"]["P2_oeis"] == "FAIL"
    assert res["verdict"]["issue_745_gate"] == "FAIL" and res["verdict"]["Q3_scoped"] == "FAIL"


def test_fresh_reserve_is_unopened():
    """No freeze, rows or result for plan `fresh` may exist: the reserve stays closed."""
    for p in ("docs/experiments/invention_fresh_freeze.json", "docs/experiments/results/invention_fresh_rows.jsonl",
              "docs/experiments/results/invention_fresh_result.json"):
        assert not pathlib.Path(p).exists(), p
