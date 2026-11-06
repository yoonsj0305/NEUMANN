"""Opened original interface diagnostic; NEVER claim Decision-2 rescue or Q3."""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p1_contract import PUBLIC_SHA256, TASK_IDS
from neumann1.finite_action_boundary_v1 import ACTIONS, run

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "docs/experiments/control_plane_p1_opened_public.json"
ARITH = {
    "instruction": "Return the exact rational value.",
    "public": {"expression": "(a+b)/c", "bindings": {"a": 3, "b": 5, "c": 2}},
}
CODE = {
    "instruction": "Return code.",
    "public": {"requirement": "sum integers", "examples": [{"input": [1, 2], "output": 3}]},
}


def candidate(value, provenance="SYNTHETIC_TEST_CALLBACK"):
    return {"answer": value, "provenance": provenance,
            "model_calls": 0, "tool_calls": 1, "generated_tokens": 0}


class FiniteActionBridgeTests(unittest.TestCase):
    def test_opened_12_original_views_from_frozen_p1_enter_control_safely(self):
        data = json.loads(PUBLIC.read_text(encoding="utf-8"))
        rows = data["rows"]
        self.assertEqual(tuple(r["task_id"] for r in rows), TASK_IDS)
        self.assertEqual(digest([r["view"] for r in rows]), PUBLIC_SHA256)
        seen = []

        def native(route, view):
            seen.append((route, view))
            return candidate("unverified opaque answer")

        results = [
            run(r["view"], classical=native, verify_original=lambda view, answer: False)
            for r in rows
        ]
        # Diagnostics only: arithmetic/CSP interfaces reach real callback boundary,
        # coding has no source generator and explicitly abstains.
        self.assertEqual(len(results), 12)
        self.assertEqual([x["action"] for x in results].count("CLASSICAL"), 8)
        self.assertEqual([x["action"] for x in results].count("ABSTAIN"), 4)
        self.assertEqual(len(seen), 8)
        self.assertEqual(sum(x["verifier_calls"] for x in results), 8)
        self.assertEqual(sum(x["accepted"] for x in results), 0)
        self.assertTrue(all(x["status"] == "UNKNOWN" for x in results))
        self.assertTrue(all(x["cost_accounting_complete"] for x in results))
        self.assertTrue(all(x["Q3"] == "OPEN" and x["Q6"] == "OPEN" for x in results))

    def test_verified_native_requires_independent_boolean(self):
        r = run(ARITH, classical=lambda route, v: candidate(4),
                verify_original=lambda view, ans: ans == 4)
        self.assertEqual(r["status"], "VERIFIED")
        self.assertTrue(r["accepted"])
        self.assertEqual(r["trace"], ["CLASSICAL", "VERIFY"])
        self.assertEqual(r["executor_calls"], 1)
        self.assertEqual(r["verifier_calls"], 1)
        self.assertEqual(r["model_calls"], 0)

    def test_no_verifier_remains_unknown(self):
        r = run(ARITH, classical=lambda *args: candidate(4))
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertEqual(r["error"], "NO_INDEPENDENT_VERIFIER")
        self.assertFalse(r["accepted"])

    def test_bad_classifier_never_executes(self):
        for fake in (
            lambda view, labels: {k: math.nan for k in labels},
            lambda view, labels: {"CLASSICAL": 1.0},
            lambda view, labels: {k: 1.0 for k in labels},
            lambda view, labels: (_ for _ in ()).throw(RuntimeError("inference failure")),
        ):
            called = []
            r = run(ARITH, classical=lambda *args: called.append(1),
                    verify_original=lambda *args: True, action_scorer=fake)
            self.assertEqual(called, [])
            self.assertEqual(r["action"], "ABSTAIN")
            self.assertFalse(r["accepted"])
            self.assertEqual(r["selector_calls"], 1)

    def test_inadmissible_hidden_or_missing_data_fails_closed(self):
        for view in (
            dict(ARITH, expected_answer=4),
            {"instruction": "x", "public": {"expression": "1+2"}},
            {"instruction": "x", "public": {"query": "", "other": 1}},
        ):
            r = run(view, classical=lambda *args: candidate(1),
                    verify_original=lambda *args: True)
            self.assertEqual(r["executor_calls"], 0)
            self.assertFalse(r["accepted"])
            self.assertIsNotNone(r["error"])

    def test_frozen_action_set_and_deterministic_verify_only(self):
        self.assertEqual(ACTIONS, ("CLASSICAL", "GENERATE", "VERIFY", "ESCALATE", "ABSTAIN"))
        scores = lambda view, labels: {k: (10 if k == "GENERATE" else 0) for k in labels}
        r = run(CODE, generator=lambda view: candidate("def solve(xs): return sum(xs)", "OWN_WEIGHT_TEST_MOCK"),
                action_scorer=scores, verify_original=lambda view, answer: True)
        self.assertTrue(r["accepted"])
        self.assertEqual(r["trace"], ["GENERATE", "VERIFY"])
        self.assertEqual(r["candidate_provenance"], "OWN_WEIGHT_TEST_MOCK")
        self.assertEqual(r["Q3"], "OPEN")

    def test_external_escalation_origin_never_promotes_q3(self):
        scores = lambda view, labels: {k: (2 if k == "ESCALATE" else 0) for k in labels}
        r = run(CODE, escalator=lambda view: candidate("x", "EXTERNAL_TEACHER_MOCK"),
                action_scorer=scores, verify_original=lambda view, answer: True)
        self.assertTrue(r["accepted"])
        self.assertEqual(r["candidate_provenance"], "EXTERNAL_TEACHER_MOCK")
        self.assertEqual(r["Q3"], "OPEN")

    def test_verifier_wrong_type_cannot_pass(self):
        r = run(ARITH, classical=lambda *args: candidate(4),
                verify_original=lambda *args: {"ok": True})
        self.assertFalse(r["accepted"])
        self.assertEqual(r["status"], "UNKNOWN")
        self.assertIn("exact bool", r["error"])
        self.assertFalse(r["cost_accounting_complete"])

    def test_incomplete_candidate_is_never_accepted(self):
        r = run(ARITH, classical=lambda *args: {"answer": 4},
                verify_original=lambda *args: True)
        self.assertFalse(r["accepted"])
        self.assertFalse(r["cost_accounting_complete"])
        self.assertEqual(r["verifier_calls"], 0)

    def test_missing_specialist_is_abstain_not_guess(self):
        r = run(CODE, classical=lambda *args: candidate("fake"), verify_original=lambda *args: True)
        self.assertEqual(r["action"], "ABSTAIN")
        self.assertEqual(r["executor_calls"], 0)
        self.assertFalse(r["accepted"])


if __name__ == "__main__":
    unittest.main()
