"""Fault-injection fixtures only. No fixture is a model efficiency result."""
from copy import deepcopy
from dataclasses import replace
import unittest

from neumann1.matched_cost_v079 import (
    Case, Path, Protocol, ROLES, Scope, Verification, measure, summarize,
    validate_design,
)


def propose(text):
    assert type(text) is str
    return text


def execute(text, proposal):
    return proposal


def verify(text, answer):
    return Verification(Scope.ORIGINAL if text == answer else Scope.REJECTED,
                        "fixture-original-check")


class MatchedCostTests(unittest.TestCase):
    def setUp(self):
        self.cases = (Case("a", "observable A"), Case("b", "observable B"))
        self.protocol = Protocol("fixture-only", "fixture-cpu", "shared-runtime",
                                 "fixture-original-check", "no warmup; fixture only",
                                 ("a", "b"), repeats=2)
        self.paths = tuple(Path(r, "fixture:" + r, "fixture-train", "fixture-cap",
                                "fixture-representation", 0 if i == 0 else 10,
                                0 if i == 0 else 100, 0, 0, propose)
                           for i, r in enumerate(ROLES))

    def report(self, **kwargs):
        return measure(self.protocol, self.cases, self.paths,
                       execute=execute, verify=verify, **kwargs)

    def summary(self, report):
        return summarize(self.protocol, self.paths, report)

    def test_all_comparators_share_observable_only_authority(self):
        received = []
        def observable_only(text):
            received.append(text)
            return text
        paths = tuple(replace(p, propose=observable_only) for p in self.paths)
        result = measure(self.protocol, self.cases, paths, execute=execute, verify=verify)
        self.assertEqual(set(received), {c.text for c in self.cases})
        self.assertEqual(len(received), 20)
        summary = summarize(self.protocol, paths, result)
        self.assertEqual(summary["verified_original_counts"], dict.fromkeys(ROLES, 4))
        self.assertEqual((summary["q3"], summary["q4"]), ("OPEN", "OPEN"))

    def test_missing_or_duplicate_rows_cannot_manufacture_quality(self):
        result = self.report()
        for rows in (result["rows"][:-1], result["rows"] + [result["rows"][0]]):
            with self.assertRaises(ValueError):
                self.summary({**result, "rows": rows})

    def test_equal_inputs_and_repeat_identity_are_checked(self):
        result = self.report()
        result["rows"][0]["observable_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.summary(result)
        result = self.report()
        result["rows"][0]["repeat"] = True
        with self.assertRaises(ValueError):
            self.summary(result)

    def test_label_or_expression_agreement_is_not_original_verification(self):
        for scope in (Scope.LABEL, Scope.EXPRESSION):
            result = measure(self.protocol, self.cases, self.paths,
                             execute=execute, verify=lambda *_: Verification(scope, "fixture"))
            summary = self.summary(result)
            self.assertEqual(summary["status"], "CAPABILITY_UNREACHED")
            self.assertIsNone(summary["neumann_direct_ratio"])
            self.assertIsNone(summary["incremental_training_break_even_queries"])

    def test_proposal_failure_is_charged_before_successful_fallback(self):
        def fail(_):
            raise TimeoutError("fixture model timeout")
        paths = tuple(replace(p, propose=fail) if p.role == "neumann" else p
                      for p in self.paths)
        result = measure(self.protocol, self.cases, paths, execute=execute, verify=verify)
        for row in result["rows"]:
            if row["role"] == "neumann":
                self.assertEqual(len(row["attempts"]), 2)
                self.assertIn("TimeoutError", row["attempts"][0]["error"])
                self.assertEqual(row["attempts"][0]["stages"][0]["stage"], "proposal")
                self.assertGreaterEqual(row["total_ms"], sum(
                    s["ms"] for a in row["attempts"] for s in a["stages"]))
        summary = summarize(self.protocol, paths, result)
        self.assertEqual(summary["rescued_counts"]["neumann"], 4)

    def test_executor_and_verifier_failures_cannot_establish_capability(self):
        def fail(*_):
            raise TimeoutError("fixture shared callback timeout")
        for executor, checker in ((fail, verify), (execute, fail)):
            result = measure(self.protocol, self.cases, self.paths,
                             execute=executor, verify=checker)
            self.assertEqual(self.summary(result)["status"], "CAPABILITY_UNREACHED")
            self.assertTrue(all(r["attempts"][-1]["error"] for r in result["rows"]))

    def test_fallback_work_cannot_be_deleted(self):
        result = measure(self.protocol, self.cases, self.paths, execute=execute,
                         verify=lambda *_: Verification(Scope.UNKNOWN, "fixture"))
        row = next(r for r in result["rows"] if r["role"] == "neumann")
        row["attempts"] = row["attempts"][:1]
        with self.assertRaises(ValueError):
            self.summary(result)
        result = self.report()
        result["rows"][0]["total_ms"] = 0
        with self.assertRaises(ValueError):
            self.summary(result)

    def test_strongest_direct_is_a_whole_workload_route_not_per_case_oracle(self):
        result = self.report(fallback=False)
        for row in result["rows"]:
            role, case = row["role"], row["case_id"]
            # Synthetic times test arithmetic only; never archived as measurements.
            totals = {"direct_deterministic": 10, "direct_answer": 20,
                      "direct_program": 1 if case == "a" else 21,
                      "neumann": 5, "no_compression": 8}
            row["total_ms"] = totals[role]
            for attempt in row["attempts"]:
                for stage in attempt["stages"]:
                    stage["ms"] = 0
        summary = self.summary(result)
        self.assertEqual(summary["strongest_measured_direct"], "direct_deterministic")
        self.assertEqual(summary["neumann_direct_ratio"], 0.5)
        self.assertEqual(summary["neumann_ablation_ratio"], 0.625)
        self.assertEqual(summary["incremental_training_break_even_queries"], 20)
        slower = deepcopy(result)
        for row in slower["rows"]:
            if row["role"] == "neumann":
                row["total_ms"] = 30
        self.assertIsNone(self.summary(slower)["incremental_training_break_even_queries"])

    def test_verifier_must_name_scope_and_evidence(self):
        for invalid in (True, Verification("VERIFIED_ORIGINAL_TASK", "fixture"),
                        Verification(Scope.ORIGINAL, "")):
            result = measure(self.protocol, self.cases, self.paths, execute=execute,
                             verify=lambda *_: invalid, fallback=False)
            self.assertEqual(self.summary(result)["status"], "CAPABILITY_UNREACHED")

    def test_matching_training_and_ablation_cannot_drift(self):
        for changed in (replace(self.paths[2], training_examples=11),
                        replace(self.paths[2], training_data_ref="other"),
                        replace(self.paths[2], budget_ref="larger"),
                        replace(self.paths[4], representation_ref="other")):
            paths = tuple(changed if p.role == changed.role else p for p in self.paths)
            with self.assertRaises(ValueError):
                validate_design(self.protocol, paths)
        with self.assertRaises(ValueError):
            validate_design(self.protocol, self.paths[:-1])

    def test_invalid_costs_and_contract_drift_are_rejected(self):
        for value in (-1, float("nan"), float("inf"), True):
            paths = (replace(self.paths[0], training_ms=value),) + self.paths[1:]
            with self.assertRaises(ValueError):
                validate_design(self.protocol, paths)
        result = self.report()
        result["path_costs"]["neumann"]["teacher_ms"] = 500
        with self.assertRaises(ValueError):
            self.summary(result)
        result = self.report()
        result["runtime_ref"] = "structural-only-tool"
        with self.assertRaises(ValueError):
            self.summary(result)

    def test_incomplete_corpus_and_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            measure(self.protocol, self.cases[:1], self.paths, execute=execute, verify=verify)
        with self.assertRaises(ValueError):
            validate_design(replace(self.protocol, case_ids=("a", "a")), self.paths)


if __name__ == "__main__":
    unittest.main()
