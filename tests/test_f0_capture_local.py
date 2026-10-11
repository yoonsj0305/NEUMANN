"""F0 local-capture tests reuse the existing Hybrid R0 LP engineering fixture.

These are REAL local CPU solver invocations but still ENGINEERING_ONLY,
not authenticated frontier model calls or unseen source-family evidence.
"""
import copy

import pytest

from neumann1.f0_capture_local import capture_opened_locals
from neumann1.f0_opened_bridge import SCHEMA, ROLES, audit_opened, verify_original_answer
from neumann1.hybrid_runtime_r0 import digest, source_problem_payload, validate_task


def opened_lp_manifest():
    # Same published engineering coefficients as test_hybrid_runtime_r0.lp_task.
    cols = 12
    A = [[1.0 if j % 2 == 0 else 0.0 for j in range(cols)],
         [0.0 if j % 2 == 0 else 1.0 for j in range(cols)]]
    task = {
        "domain": "lp.standard_form", "A": A, "b": [1.0, 1.0],
        "c": [0., 0.] + [2. + j / 10 for j in range(2, cols)],
        "budget_s": 8.0,
    }
    return {
        "schema": SCHEMA, "split": "opened_development", "repeats": 1,
        "cases": [{
            "id": "preexisting_r0_lp_regression",
            "family": "r0_original_lp_engineering_only",
            "source_group_id": "preexisting_r0_lp_regression",
            "source": "tests/test_hybrid_runtime_r0.py:lp_task",
            "license": "local_fixture_only_not_fresh",
            "task": task,
            "original_problem_sha256": digest(
                source_problem_payload(task, validate_task(task))),
        }],
        "systems": {
            role: {"id": role + "_opened_local_control",
                   "revision": "r0_opened_local_capture_v1",
                   "tools": ["same_admitted_lp_solver"]}
            for role in ROLES
        },
    }


def test_real_existing_r0_native_and_classical_hybrid_cold_originals():
    m = opened_lp_manifest()
    receipts = capture_opened_locals(m)
    assert len(receipts) == 2
    assert {r["role"] for r in receipts} == {"strong_native", "classical_hybrid"}
    for r in receipts:
        assert r["original_problem_sha256"] == m["cases"][0]["original_problem_sha256"]
        assert r["capture"]["runner_status"] == "VERIFIED", r
        assert r["capture"]["runner_receipt"]["learned_model_inference"] is False
        assert r["capture"]["complete_cost_status"] == "PARTIAL_NO_ENERGY_MONEY_OR_INVESTMENT"
        assert verify_original_answer(m["cases"][0]["task"], r["answer"])
        assert r["resources"]["latency_ms"]["value"] > 0
        assert r["resources"]["cost_usd"] == {"status": "unavailable", "value": None}
    # The bridge must never pretend that absent small/frontier/NEUMANN calls
    # are actual baseline failures.
    with pytest.raises(ValueError, match="missing comparison"):
        audit_opened(m, receipts)


def test_cannot_claim_learned_neumann_without_explicit_frozen_authority():
    m = opened_lp_manifest()
    with pytest.raises(ValueError, match="frozen seed"):
        capture_opened_locals(m, roles=("neumann",))
    with pytest.raises(ValueError, match="frozen seed"):
        capture_opened_locals(m, roles=("neumann",), frozen_seed=123456)


def test_cannot_relabel_exact_solver_as_three_distinct_lp_methods():
    m = opened_lp_manifest()
    case = m["cases"][0]
    case["task"] = {"domain": "exact.linear", "A": [[2]], "b": [1]}
    case["original_problem_sha256"] = digest(
        source_problem_payload(case["task"], validate_task(case["task"])))
    with pytest.raises(ValueError, match="distinct"):
        capture_opened_locals(m)


def test_cannot_repeat_roles_or_relabel_neural_seed_in_native_route():
    m = opened_lp_manifest()
    with pytest.raises(ValueError, match="roles"):
        capture_opened_locals(m, roles=("strong_native", "strong_native"))
    with pytest.raises(ValueError, match="frozen seed"):
        capture_opened_locals(m, roles=("strong_native",), frozen_seed=100001)


def test_local_input_provenance_required():
    m = opened_lp_manifest()
    broken = copy.deepcopy(m)
    broken["cases"][0]["original_problem_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="original problem"):
        capture_opened_locals(broken)


def test_first_frozen_counter_accounting_without_rerunning_checkpoint(monkeypatch, tmp_path):
    """Pure metadata regression; historical frozen original bytes stay immutable."""
    from experiments import f0_run_opened_v102_existing as study
    manifest = opened_lp_manifest()
    second = copy.deepcopy(manifest["cases"][0])
    second["id"] = "opened_second"
    second["source_group_id"] = "opened_second"
    second["task"]["c"][2] = 5.0
    second["original_problem_sha256"] = digest(
        source_problem_payload(second["task"], validate_task(second["task"])))
    manifest["cases"].append(second)

    monkeypatch.setattr(study, "registered_manifest", lambda: manifest)

    def synthetic_receipts(m, roles=("strong_native", "classical_hybrid"), frozen_seed=None):
        assert frozen_seed is None or frozen_seed == 100001
        return [
            {"task_id": case["id"], "role": role,
             "capture": {"runner_status": "VERIFIED"},
             "resources": {"latency_ms": {"value": 4.0 if role == "neumann" else 2.0}}}
            for case in m["cases"] for role in roles
        ]

    monkeypatch.setattr(study, "capture_opened_locals", synthetic_receipts)
    report = study.run_existing(tmp_path / "mock_only", frozen_seed=100001)
    assert report["learned_model_executions"] == 2
    assert report["actual_existing_learned_model_executions"] == 2
    assert report["actual_local_executions"] == 6
    assert report["new_scientific_admission"] is False
    assert report["classification"] == "HISTORICAL_OPENED_ENGINEERING_DIAGNOSTIC_NOT_FRESH"
