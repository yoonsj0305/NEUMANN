"""P0 synthetic contracts. No Gemma inference, training or sealed content."""
import math
import unittest
from dataclasses import replace

from neumann1.control_plane_v1 import (
    ROUTES, ControlBudget, CostEstimate, ExecutionResult, ScoreResult,
    ScoreFailure, public_view, route_order, run_control,
)
from neumann1.control_plane_scoring_v1 import ChoiceScorer, label_mean_logprob


VIEW = {"instruction": "solve", "public": {"a": 3, "b": 7, "noise": 99}}
COSTS = {r: CostEstimate(1.0, "synthetic estimate, not measured") for r in ROUTES}


class FixtureBackend:
    def __init__(self, scores=None):
        self.calls = 0
        self.scores = scores

    def forward_bound(self, plan):
        return 1

    def evaluate(self, plan, remaining_ms):
        self.calls += 1
        # Alphabetical atom a,b,noise; not an actual model.
        rows = ((-1.0, -2.0), (-1.0, -3.0), (-4.0, -1.0)) if plan.labels == ("KEEP", "DROP") else ((-4.0, -1.0, -3.0, -2.0),)
        rows = self.scores if self.scores is not None else rows
        return ScoreResult(rows, 1, plan.evaluated_tokens)


def fixture(backend=None):
    return ChoiceScorer(lambda text: [1, 2], lambda text: [3], backend or FixtureBackend(),
                        {"weights_frozen": True, "evidence_kind": "synthetic_contract_fixture"})


class ControllerTests(unittest.TestCase):
    def test_cost_changes_route_without_generating(self):
        costs = dict(COSTS, ARITHMETIC=CostEstimate(1000, "synthetic"))
        self.assertEqual(route_order((-4, -1, -3, -2), costs, 0)[0], "ARITHMETIC")
        self.assertEqual(route_order((-4, -1, -3, -2), costs, .01)[0], "PYTHON")
        self.assertEqual(route_order((0, 0, 0, 0), COSTS, 0), ROUTES)

    def test_invalid_costs_and_nonfinite_scores_fail(self):
        for scores in [(math.nan, 0, 0, 0), (math.inf, 0, 0, 0), (0, 0)]:
            with self.assertRaises(ValueError):
                route_order(scores, COSTS, 0)
        with self.assertRaises(ValueError):
            route_order((0, 0, 0, 0), dict(COSTS, DIRECT=CostEstimate(-1, "test")), 0)
        with self.assertRaises(ValueError):
            route_order((0, 0, 0, 0), dict(COSTS, DIRECT=CostEstimate(1, "")), 0)

    def test_private_task_labels_never_enter_model_view(self):
        for key in ("family", "id", "private", "exact"):
            with self.assertRaises(ValueError):
                public_view(dict(VIEW, **{key: "hidden"}))

    def test_evidence_expands_monotonically_and_stops_at_original_pass(self):
        calls = []
        def execute(route, view, remaining, allowances):
            calls.append((route, dict(view["public"])))
            public = view["public"]
            return ExecutionResult(public.get("a", 0) + public.get("b", 0))
        result = run_control(VIEW, "NEUMANN", fixture(), execute, lambda answer, ms: answer == 10, COSTS)
        self.assertTrue(result["accepted"])
        self.assertEqual(len(calls), 5)  # Four failed routes on b, first route on b+a.
        self.assertEqual(calls[-1], ("ARITHMETIC", {"b": 7, "a": 3}))
        self.assertTrue(all("noise" not in evidence for _, evidence in calls))
        self.assertEqual(result["counts"]["generated_tokens"], 0)
        self.assertEqual(result["counts"]["forward_calls"], 3)
        self.assertTrue(result["accounting_complete"])
        self.assertEqual(result["general_capability_gate"], "NOT_EVALUATED")

    def test_tool_uses_full_input_same_routes_and_checks(self):
        seen = []
        def execute(route, view, ms, allowances):
            seen.append(view)
            return ExecutionResult(10)
        result = run_control(VIEW, "TOOL", fixture(), execute, lambda a, ms: a == 10, COSTS)
        self.assertTrue(result["accepted"])
        self.assertEqual(seen[0], VIEW)
        self.assertEqual(result["counts"]["forward_calls"], 1)

    def test_direct_normal_answer_has_no_route_or_json_scoring(self):
        scorer = fixture()
        result = run_control(VIEW, "DIRECT", scorer,
                             lambda r, v, ms, caps: ExecutionResult("10", 2, 1, 0),
                             lambda a, ms: a == "10", COSTS)
        self.assertTrue(result["accepted"])
        self.assertEqual(scorer.backend.calls, 0)
        self.assertEqual(result["counts"]["generated_tokens"], 2)

    def test_false_verifier_never_accepts_even_full_evidence(self):
        result = run_control(VIEW, "NEUMANN", fixture(),
                             lambda *args: ExecutionResult(10), lambda *args: False, COSTS)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["counts"]["attempts"], 12)
        self.assertEqual(result["error"], "EXHAUSTED_EVIDENCE_OR_ROUTES")

    def test_verifier_cannot_supply_answer_feedback(self):
        result = run_control(VIEW, "TOOL", fixture(), lambda *args: ExecutionResult(10),
                             lambda *args: {"accepted": True, "gold": 10}, COSTS)
        self.assertFalse(result["accepted"])
        self.assertIn("boolean only", result["error"])

    def test_admission_rejects_before_forward(self):
        for budget in [replace(ControlBudget(), context_tokens=2), replace(ControlBudget(), evaluated_tokens=1),
                       replace(ControlBudget(), score_rows=1)]:
            scorer = fixture()
            result = run_control(VIEW, "TOOL", scorer, lambda *a: ExecutionResult(10), lambda *a: True, COSTS, budget=budget)
            self.assertFalse(result["accepted"])
            self.assertEqual(scorer.backend.calls, 0)

    def test_nonfinite_model_score_rejected(self):
        result = run_control(VIEW, "TOOL", fixture(FixtureBackend(((0, math.nan, 0, 0),))),
                             lambda *a: ExecutionResult(10), lambda *a: True, COSTS)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["accounting_complete"])

    def test_failed_forward_keeps_incomplete_receipt(self):
        class Failed(FixtureBackend):
            def evaluate(self, *args):
                raise TimeoutError("synthetic forward timeout")
        result = run_control(VIEW, "TOOL", fixture(Failed()), lambda *a: ExecutionResult(10), lambda *a: True, COSTS)
        self.assertFalse(result["accounting_complete"])
        self.assertEqual(result["events"][0]["status"], "STARTED")
        self.assertEqual(result["counts"]["forward_calls"], 0)  # Completed count; not unknown actual work.

    def test_known_partial_forward_is_charged_but_never_accepted(self):
        class Partial(FixtureBackend):
            def evaluate(self, *args):
                raise ScoreFailure("synthetic partial timeout", 1, 12, 100)
        result = run_control(VIEW, "TOOL", fixture(Partial()), lambda *a: ExecutionResult(10), lambda *a: True, COSTS)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["accounting_complete"])
        self.assertEqual(result["counts"]["forward_calls"], 1)
        self.assertEqual(result["counts"]["padded_tokens"], 12)

    def test_attempt_cap_and_verifier_exception_preserved(self):
        result = run_control(VIEW, "TOOL", fixture(), lambda *a: ExecutionResult(10), lambda *a: False,
                             COSTS, budget=replace(ControlBudget(), attempts=1))
        self.assertEqual(result["counts"]["attempts"], 1)
        self.assertIn("attempt cap", result["error"])
        def fail(*args):
            raise RuntimeError("original verifier failure")
        result = run_control(VIEW, "DIRECT", fixture(), lambda *a: ExecutionResult(10), fail, COSTS)
        self.assertFalse(result["accounting_complete"])
        self.assertEqual(result["events"][-1]["kind"], "original_verification")

    def test_mutating_executor_receives_copy_and_cannot_edit_original(self):
        seen = []
        def execute(route, view, ms, caps):
            seen.append(dict(view["public"]))
            view["public"].clear()
            return ExecutionResult(0)
        result = run_control(VIEW, "TOOL", fixture(), execute, lambda *a: False, COSTS)
        self.assertEqual(len(seen), 4)
        self.assertTrue(all(x == VIEW["public"] for x in seen))
        self.assertFalse(result["accepted"])

    def test_execution_budgets_are_charged_and_capped(self):
        result = run_control(VIEW, "DIRECT", fixture(),
                             lambda *args: ExecutionResult(10, 513, 1, 0), lambda *args: True, COSTS)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["accounting_complete"])
        self.assertIn("budget mismatch", result["error"])

    def test_identity_drift_blocks_acceptance(self):
        scorer = fixture()
        def execute(*args):
            scorer.identity["changed"] = True
            return ExecutionResult(10)
        result = run_control(VIEW, "DIRECT", scorer, execute, lambda *a: True, COSTS)
        self.assertFalse(result["accepted"])
        self.assertIn("identity drift", result["error"])

    def test_reference_causal_shift_and_length_normalization(self):
        logits = [[1000, 999], [0, 2], [2, 0], [-100, 100]]
        actual = label_mean_logprob(logits, 2, [1, 0])
        self.assertAlmostEqual(actual, -math.log1p(math.exp(-2)))
        self.assertAlmostEqual(label_mean_logprob(logits, 2, [1]), actual)
        with self.assertRaises(ValueError):
            label_mean_logprob(logits, 0, [1])


if __name__ == "__main__":
    unittest.main()
