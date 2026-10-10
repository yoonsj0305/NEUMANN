"""Model-free F0 opened intake checks: never scientific frontier observations."""
import copy
import unittest
from unittest.mock import patch

from neumann1.f0_opened_bridge import (SCHEMA, ROLES, audit_opened,
                                       OriginalVerificationUnavailable,
                                       validate_manifest, verify_original_answer)
from neumann1.hybrid_runtime_r0 import digest, source_problem_payload, validate_task

# Same invariant engineering fixture used by test_hybrid_sygus_r0, not an
# external source or model result. Faults below are injected verifier outcomes.
SYGUS_SOURCE = """(set-logic LIA)
(synth-inv inv-f ((x Int)))
(declare-primed-var x Int)
(define-fun pre-f ((x Int)) Bool (= x 0))
(define-fun trans-f ((x Int) (x! Int)) Bool (= x! (+ x 1)))
(define-fun post-f ((x Int)) Bool (>= x 0))
(inv-constraint inv-f pre-f trans-f post-f)
(check-synth)
"""
INVARIANT = "(define-fun inv-f ((x Int)) Bool (>= x 0))"


def proof_fixture(statuses, *, accepted=False):
    return {"accepted": accepted, "obligations": [
        {"obligation": name, "smt_result": status, "proved": status == "unsat"}
        for name, status in zip(("init", "inductive", "safe"), statuses)
    ]}


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
                    "neumann": 20.0, "strong_native": 10.0,
                    "classical_hybrid": 12.0}[role]
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
    def test_smt_unknown_and_checker_error_are_not_wrong_model_answers(self):
        task = {"domain": "sygus.invariant", "source": SYGUS_SOURCE}
        for statuses in (("unknown", "unsat", "unsat"),
                         ("unsat", "unknown", "unsat"),
                         ("unsat", "unsat", "unknown"),
                         ("unknown", "unknown", "unknown"),
                         ("unsat", "parser_error:Z3Exception", "unsat")):
            with self.subTest(statuses=statuses), patch(
                    "neumann1.hybrid_sygus_r0.independent_check",
                    return_value=proof_fixture(statuses)):
                with self.assertRaisesRegex(RuntimeError, "not verified"):
                    verify_original_answer(task, {"invariant": INVARIANT})

    def test_unproved_or_incomplete_accepted_flag_has_no_authority(self):
        task = {"domain": "sygus.invariant", "source": SYGUS_SOURCE}
        for statuses in (("unsat", "unknown", "unsat"), ("unsat", "unsat")):
            with self.subTest(statuses=statuses), patch(
                    "neumann1.hybrid_sygus_r0.independent_check",
                    return_value=proof_fixture(statuses, accepted=True)):
                with self.assertRaisesRegex(RuntimeError, "not verified"):
                    verify_original_answer(task, {"invariant": INVARIANT})

    def test_sat_counterexample_remains_a_real_rejection(self):
        task = {"domain": "sygus.invariant", "source": SYGUS_SOURCE}
        with patch("neumann1.hybrid_sygus_r0.independent_check",
                   return_value=proof_fixture(("unsat", "sat", "unknown"))):
            self.assertFalse(verify_original_answer(task, {"invariant": INVARIANT}))

    def test_smt_unknown_cannot_manufacture_frontier_gap_and_is_retained(self):
        m, receipts = fixture()
        case = m["cases"][0]
        case["task"] = {"domain": "sygus.invariant", "source": SYGUS_SOURCE}
        case["original_problem_sha256"] = digest(source_problem_payload(
            case["task"], validate_task(case["task"])))
        for row in receipts:
            if row["task_id"] == case["id"]:
                row["original_problem_sha256"] = case["original_problem_sha256"]
                row["answer"] = {"invariant": INVARIANT}
        unknown = proof_fixture(("unsat", "unknown", "unsat"))
        valid = proof_fixture(("unsat", "unsat", "unsat"), accepted=True)
        with patch("neumann1.hybrid_sygus_r0.independent_check",
                   side_effect=[unknown, valid, valid, valid, valid]):
            out = audit_opened(m, receipts)
        self.assertEqual(out["gap_case_ids"], ["opened_1"])
        self.assertIsNone(out["per_case_verified_rate"]["opened_0"]["small"])
        self.assertEqual(out["incomplete_case_ids"], ["opened_0"])
        self.assertEqual(out["decision"], "INCOMPLETE_ORIGINAL_VERIFICATION")
        self.assertEqual(out["observations"], 10)
        self.assertEqual(len(out["verification_errors"]), 1)
        failure = out["verification_errors"][0]
        self.assertEqual((failure["task_id"], failure["role"]), ("opened_0", "small"))
        self.assertEqual(failure["proof"]["obligations"][1]["smt_result"], "unknown")
        self.assertFalse(out["scientific_success"])
        self.assertEqual(out["global_questions_closed"], [])
        for name, values in out.items():
            if name.endswith("reported_resource_ratio"):
                self.assertEqual(values, {"latency_ms": None, "cost_usd": None})

    def test_unavailable_verification_in_any_arm_or_repeat_is_retained(self):
        for role in ROLES:
            for repeat in (0, 1):
                with self.subTest(role=role, repeat=repeat):
                    m, first = fixture()
                    m["repeats"] = 2
                    receipts = [dict(copy.deepcopy(row), repeat=i)
                                for row in first for i in (0, 1)]
                    target = next(i for i, row in enumerate(receipts)
                                  if row["task_id"] == "opened_0"
                                  and row["role"] == role and row["repeat"] == repeat)
                    calls = iter(range(len(receipts)))

                    def checker(task, answer):
                        if next(calls) == target:
                            raise OriginalVerificationUnavailable(
                                "injected verifier unavailability",
                                {"reason": "DEPENDENCY_UNAVAILABLE"})
                        return verify_original_answer(task, answer)

                    with patch("neumann1.f0_opened_bridge.verify_original_answer",
                               side_effect=checker):
                        out = audit_opened(m, receipts)
                    self.assertEqual(out["observations"], 20)
                    self.assertEqual(out["incomplete_case_ids"], ["opened_0"])
                    self.assertIsNone(out["per_case_verified_rate"]["opened_0"][role])
                    self.assertEqual(out["decision"], "INCOMPLETE_ORIGINAL_VERIFICATION")
                    failure = out["verification_errors"][0]
                    self.assertEqual((failure["role"], failure["repeat"]), (role, repeat))
                    self.assertEqual(failure["resources"], receipts[target]["resources"])
                    self.assertIn("opened_1", out["gap_case_ids"])
                    for name, values in out.items():
                        if name.endswith("reported_resource_ratio"):
                            self.assertEqual(values, {"latency_ms": None, "cost_usd": None})
                    if role in ("strong_native", "classical_hybrid"):
                        self.assertIsNone(out[role + "_gap_verified_rate"])

    def test_real_exact_original_equations_not_declared_acceptance(self):
        m, r = fixture()
        result = audit_opened(m, r)
        self.assertEqual(result["decision"], "BOUNDED_PILOT_CAPABILITY_MATCH")
        self.assertEqual(result["gap_source_groups"], 2)
        self.assertEqual(result["gap_recovery_rate"], 1.)
        self.assertEqual(result["observations"], 10)
        self.assertAlmostEqual(result["neumann_to_frontier_reported_resource_ratio"]["latency_ms"], .2)
        self.assertIsNone(result["neumann_to_frontier_reported_resource_ratio"]["cost_usd"])
        self.assertFalse(result["scientific_success"])
        self.assertEqual(result["capture_attestation"], "UNVERIFIED_EXCEPT_FOR_ORIGINAL_MATH")
        self.assertEqual(result["strong_native_gap_verified_rate"], 1.)
        self.assertEqual(result["classical_hybrid_gap_verified_rate"], 1.)
        self.assertEqual(result["conservative_source_group_recovery_rate"], 1.)
        self.assertAlmostEqual(result["neumann_to_classical_hybrid_reported_resource_ratio"]["latency_ms"], 20/12)
        self.assertAlmostEqual(result["neumann_to_best_classical_reported_resource_ratio"]["latency_ms"], 2.)
        self.assertAlmostEqual(result["neumann_to_strong_native_reported_resource_ratio"]["latency_ms"], 2.)

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



    def test_classical_hybrid_missing_raises_instead_of_disappearing(self):
        m, receipts = fixture()
        receipts = [r for r in receipts if not (r["role"] == "classical_hybrid" and r["task_id"] == "opened_1")]
        with self.assertRaisesRegex(ValueError, "missing comparison"):
            audit_opened(m, receipts)

    def test_classical_hybrid_wrong_answer_disables_its_iso_ratio(self):
        m, receipts = fixture()
        row = next(r for r in receipts if r["role"] == "classical_hybrid" and r["task_id"] == "opened_0")
        row["answer"] = {"solution": {"x0": {"numerator": 0, "denominator": 1}}}
        report = audit_opened(m, receipts)
        self.assertLess(report["classical_hybrid_gap_verified_rate"], 1.)
        self.assertIsNone(report["neumann_to_classical_hybrid_reported_resource_ratio"]["latency_ms"])
        self.assertAlmostEqual(report["neumann_to_best_classical_reported_resource_ratio"]["latency_ms"], 2.)

if __name__ == "__main__":
    unittest.main()
