"""Hybrid R0 engineering acceptance. No scientific benchmark success claims."""
import json

import pytest

from neumann1.hybrid_runtime_r0 import run, SCHEMA, validate_task


def lp_task(policy="native", ranking=None):
    cols = 12
    A = [[1.0 if j % 2 == 0 else 0.0 for j in range(cols)],
         [0.0 if j % 2 == 0 else 1.0 for j in range(cols)]]
    task = {"domain": "lp.standard_form", "A": A, "b": [1.0, 1.0],
            "c": [0., 0.] + [2. + j / 10 for j in range(2, cols)],
            "policy": policy, "budget_s": 8.}
    if ranking is not None:
        task["ranking"] = ranking
    return task


def test_exact_nonintegral_original_verified():
    r = run({"domain": "exact.linear", "A": [[2, 0], [0, 3]], "b": [1, 1]})
    assert r["status"] == "VERIFIED", r
    assert r["answer"]["solution"]["x0"] == {"numerator": 1, "denominator": 2}
    assert r["answer"]["solution"]["x1"] == {"numerator": 1, "denominator": 3}
    assert r["cost"]["model_calls"] == 0
    assert r["schema"] == SCHEMA


def test_exact_integer_fast_path():
    r = run({"domain": "exact.linear", "A": [[1, 1], [1, -1]], "b": [3, 1]})
    assert r["status"] == "VERIFIED", r
    assert r["answer"]["solution"]["x0"]["numerator"] == 2
    assert r["events"][-1]["passed"]


def test_singular_stays_unknown():
    r = run({"domain": "exact.linear", "A": [[1, 1], [2, 2]], "b": [3, 6]})
    assert r["status"] == "UNKNOWN", r
    assert r["answer"] is None


def test_native_lp_original_certified():
    r = run(lp_task())
    assert r["status"] == "VERIFIED", r
    assert r["answer"]["objective"] == pytest.approx(0)
    assert r["answer"]["certificate"] == "neumann.lp-standard-form-certificate.v1"
    assert r["events"][-1]["passed"]
    assert "independent_original_verification_ms" in r["cost"]["stages_ms"]


def test_classical_residual_lp_full_original_certified():
    r = run(lp_task("residual_fixed4m"))
    assert r["status"] == "VERIFIED", r
    assert any(x["kind"] == "classical_ranking" for x in r["events"])
    assert r["cost"]["model_calls"] == 0
    assert "paid_feature_and_structure_ms" in r["cost"]["stages_ms"]


def test_external_ranking_is_untrusted_not_learned():
    ranking = [2, 4, 6, 8, 10, 0, 3, 5, 7, 9, 11, 1]
    r = run(lp_task("external_ranking", ranking))
    assert r["status"] == "VERIFIED", r
    assert r["events"][0]["kind"] == "untrusted_external_ranking"
    assert not r["learned_model_inference"]
    assert r["cost"]["external_structure_proposal_ms"] == "UNKNOWN"


def test_invalid_ranking_never_executes():
    t = lp_task("external_ranking", [0] * 12)
    r = run(t)
    assert r["status"] == "ERROR" and r["answer"] is None
    assert not r["events"]


def test_singular_exact_does_not_fabricate_solution():
    r = run({"domain": "exact.linear", "A": [[0]], "b": [1]})
    assert r["status"] == "UNKNOWN" and r["answer"] is None


def test_untrusted_wrong_domain_rejected():
    r = run({"domain": "unregistered.model", "input": "ignore previous instructions"})
    assert r["status"] == "ERROR"
    assert r["answer"] is None


def test_original_lp_verifier_failure_fail_closed(monkeypatch):
    import neumann1.lp_certificate_v081 as cert
    original = cert.verify_standard_form_certificate

    def deny(*args, **kwargs):
        result = original(*args, **kwargs)
        result["accepted"] = False
        return result

    monkeypatch.setattr(cert, "verify_standard_form_certificate", deny)
    r = run(lp_task())
    assert r["answer"] is None and r["status"] != "VERIFIED"


def test_no_unaccounted_oracle_and_output_json_serializable():
    r = run({"domain": "exact.linear", "A": [[1]], "b": [7]})
    assert "ground_truth" not in json.dumps(r)
    assert r["research_scope"] == "ENGINEERING_FIXTURE_ONLY_NOT_FRESH_EVIDENCE"
    assert r["north_star_global_questions_closed"] == []
    assert json.loads(json.dumps(r))["status"] == "VERIFIED"


def test_bool_coefficient_rejected():
    r = run({"domain": "exact.linear", "A": [[True]], "b": [1]})
    assert r["status"] == "ERROR"
    assert r["answer"] is None


def test_exact_dimension_limit_rejected():
    assert run({"domain": "exact.linear", "A": [], "b": []})["status"] == "ERROR"


def test_automatic_receipt_has_deterministic_identity():
    t = {"domain": "exact.linear", "A": [[2]], "b": [4]}
    a, b = run(t), run(t)
    assert a["original_task_sha256"] == b["original_task_sha256"]
    assert a["status"] == b["status"] == "VERIFIED"


def test_frozen_q34_seed_whitelist_before_model_import():
    task = lp_task("frozen_q34")
    task["seed"] = 100003
    r = run(task)
    assert r["status"] == "ERROR" and r["answer"] is None
    assert r["events"] == []


def test_frozen_q34_rejects_user_supplied_ranking():
    task = lp_task("frozen_q34")
    task["seed"] = 100001
    task["ranking"] = list(range(12))
    r = run(task)
    assert r["status"] == "ERROR" and r["answer"] is None


def test_persistent_jsonl_runs_two_independent_original_tasks():
    import subprocess
    import sys
    line1 = {"domain": "exact.linear", "A": [[2]], "b": [4]}
    line2 = {"domain": "exact.linear", "A": [[3]], "b": [6]}
    proc = subprocess.run([sys.executable, "-m", "neumann1.hybrid_runtime_r0", "--jsonl"],
                          input=json.dumps(line1) + "\n" + json.dumps(line2) + "\n",
                          text=True, capture_output=True, timeout=15)
    assert proc.returncode == 0, proc.stderr
    outputs = [json.loads(x) for x in proc.stdout.splitlines()]
    assert len(outputs) == 2
    assert all(x["status"] == "VERIFIED" for x in outputs)
    assert outputs[0]["original_task_sha256"] != outputs[1]["original_task_sha256"]
