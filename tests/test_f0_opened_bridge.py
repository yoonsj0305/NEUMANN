"""Model-free F0 opened intake checks: never scientific frontier observations."""
import copy
import unittest

from neumann1.f0_opened_bridge import (SCHEMA, ROLES, audit_opened,
                                       validate_manifest, verify_original_answer)
from neumann1.hybrid_runtime_r0 import digest, source_problem_payload, validate_task


def fixture():
    tasks = [
        {"domain": "exact.linear", "A": [[2]], "b": [1]},
        {"domain": "exact.linear", "A": [[3]], "b": [1]},
    ]
    cases = []
    for i, task in enumerate(tasks):
        cases.append({
            "id": "opened_" + str(i),
            "family": "exact_rational_family_" + str(i),
            "source_group_id": "original_fixture_" + str(i),
            "source": "synthetic_test_only",
            "license": "synthetic_test_only",
            "task": task,
            "original_problem_sha256": digest(source_problem_payload(task, validate_task(task))),
        })
    systems = {r: {"id": r + "_test", "revision": "frozen_test_1",
                   "tools": ["equal_eligible_exact_solver"]} for r in ROLES}
    manifest = {"schema": SCHEMA, "split": "opened_development",
                "repeats": 1, "cases": cases, "systems": systems}
    receipts = []
    for case in cases:
        for role in ROLES:
            denom = case["task"]["A"][0][0]
            candidate = {"solution": {"x0": {"numerator": 1, "denominator": denom}}}
            if role == "small":
                candidate = {"solution": {"x0": {"numerator": 0, "denominator": 1}}}
            cost = {"frontier": 100.0, "small": 50.0,
                    "neumann": 20.0, "strong_native": 10.0}[role]
            receipts.append({
                "task_id": case["id"], "role": role, "repeat": 0,
                "original_problem_sha256": case["original_problem_sha256"],
                "system_id": systems[role]["id"],
                "system_revision": systems[role]["revision"],
                "execution_complete": True, "capture": {"source": "unit_fixture_not_provider"},
                "answer": candidate,
                "resources": {"latency_ms": {"status": "measured", "value": cost},
                              "cost_usd": {"status": "unavailable", "value": None}},
            })
    return manifest, receipts


class F0OpenedTests(unittest.TestCase):
    def test_real_exact_original_equations_not_declared_acceptance(self):
        m, r = fixture()
        result = audit_opened(m, r)
        self.assertEqual(result["decision"], "BOUNDED_PILOT_CAPABILITY_MATCH")
        self.assertEqual(result["gap_source_groups"], 2)
        self.assertEqual(result["gap_recovery_rate"], 1.)
        self.assertEqual(result["observations"], 8)
        self.assertAlmostEqual(result["neumann_to_frontier_reported_resource_ratio"]["latency_ms"], .2)
        self.assertIsNone(result["neumann_to_frontier_reported_resource_ratio"]["cost_usd"])
        self.assertFalse(result["scientific_success"])
        self.assertEqual(result["capture_attestation"], "UNVERIFIED_EXCEPT_FOR_ORIGINAL_MATH")
        self.assertEqual(result["strong_native_gap_verified_rate"], 1.)

    def test_wrong_neumann_answer_never_counts_as_recovery(self):
        m, r = fixture()
        row = next(x for x in r if x["role"] == "neumann")
        row["answer"] = {"solution": {"x0": {"numerator": 0, "denominator": 1}}}
        row["accepted"] = True  # Adversarial self-report has no authority.
        out = audit_opened(m, r)
        self.assertEqual(out["decision"], "BOUNDED_PILOT_CAPABILITY_UNREACHED")
        self.assertEqual(out["gap_recovery_rate"], 0.5)
        self.assertIsNone(out["neumann_to_frontier_reported_resource_ratio"]["latency_ms"])

    def test_missing_receipt_is_not_counted_as_small_failure(self):
        m, r = fixture()
        r = [row for row in r if not (row["role"] == "small" and row["task_id"] == "opened_0")]
        with self.assertRaisesRegex(ValueError, "missing comparison"):
            audit_opened(m, r)

    def test_duplication_and_provider_revision_swap_fail(self):
        m, r = fixture()
        with self.assertRaises(ValueError):
            audit_opened(m, r + [copy.deepcopy(r[0])])
        m, r = fixture()
        r[0]["system_revision"] = "swapped_after_task"
        with self.assertRaisesRegex(ValueError, "unbound"):
            audit_opened(m, r)

    def test_tools_and_sealed_split_rejected(self):
        m, r = fixture()
        m["systems"]["frontier"]["tools"] = []
        with self.assertRaisesRegex(ValueError, "identical tool"):
            validate_manifest(m)
        m, r = fixture()
        m["split"] = "fresh_evaluation"
        with self.assertRaisesRegex(ValueError, "opened development"):
            audit_opened(m, r)

    def test_unknown_is_not_zero(self):
        m, r = fixture()
        r[0]["resources"]["cost_usd"]["value"] = 0
        with self.assertRaisesRegex(ValueError, "not zero"):
            audit_opened(m, r)

    def test_true_boolean_and_float_as_exact_rational_denied(self):
        task = {"domain": "exact.linear", "A": [[2]], "b": [1]}
        for n in (True, 0.5, 0):
            candidate = {"solution": {"x0": {"numerator": n, "denominator": 1}}}
            self.assertFalse(verify_original_answer(task, candidate))

    def test_original_lp_primal_dual_certificate(self):
        task = {"domain": "lp.standard_form", "A": [[1, 0], [0, 1]],
                "b": [1, 1], "c": [0, 0]}
        self.assertTrue(verify_original_answer(task, {"primal": [1, 1], "dual": [0, 0]}))
        self.assertFalse(verify_original_answer(task, {"primal": [1, 1], "dual": [1, 0]}))


if __name__ == "__main__":
    unittest.main()
