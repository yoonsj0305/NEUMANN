"""P1.7 opened-development registration, gate and first-run contracts; model-free."""
import unittest

from experiments.control_plane_p17_registration import (
    registration, check_construction, GATE, BOUNDARY,
)
from experiments.control_plane_p17_dev import evaluate, totals
from experiments.control_plane_p17_replay import replay_record
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from neumann1.control_plane_p17 import interpret_and_execute


def records(ambiguous_accept=(True, True, True, True), *, forward_calls=36):
    out = []
    for i in range(8):
        out.append({
            "task_id": "p17d_%02d" % (i + 1),
            "accepted": True,
            "executed": True,
            "selected_route": "ARITHMETIC" if i < 4 else "CSP",
            "accounting_complete": True,
            "model_calls": 0,
            "neural_forward_calls": 0,
            "generated_calls": 0,
            "evaluated_tokens": 0,
            "padded_tokens": 0,
            "tool_calls": 1,
            "verifier_calls": 1,
            "selection": "UNIQUE_COMPLETE_BOUNDED_GRAMMAR",
            "selector_receipt": None,
            "extraction_ms": 1.0,
            "selection_ms": 0.0,
            "compile_ms": 1.0,
            "routing_ms": 1.0,
            "execution_ms": 1.0,
            "verification_ms": 1.0,
            "complete_ms": 5.0,
        })
    for j, accepted in enumerate(ambiguous_accept, start=9):
        out.append({
            "task_id": "p17d_%02d" % j,
            "accepted": accepted,
            "executed": True,
            "selected_route": "CSP",
            "accounting_complete": True,
            "model_calls": 1,
            "neural_forward_calls": forward_calls,
            "generated_calls": 0,
            "evaluated_tokens": 1000,
            "padded_tokens": 1000,
            "tool_calls": 1,
            "verifier_calls": 1,
            "selection": "MASKED_FULL_S4_CANDIDATE",
            "selector_receipt": {"status": "COMPLETE"},
            "extraction_ms": 1.0,
            "selection_ms": 10.0,
            "compile_ms": 1.0,
            "routing_ms": 1.0,
            "execution_ms": 1.0,
            "verification_ms": 1.0,
            "complete_ms": 15.0,
        })
    return out


class DevelopmentRegistrationContracts(unittest.TestCase):
    def test_registration_and_checker_controls_are_model_free(self):
        reg, rows, refs = registration()
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(refs), 12)
        self.assertFalse(reg["scores_seen_at_registration"])
        self.assertTrue(reg["first_only"])
        result = check_construction()
        self.assertTrue(result["registration_valid"])
        self.assertEqual(result["unique_tasks"], 8)
        self.assertEqual(result["ambiguous_tasks"], 4)
        self.assertEqual(result["candidate_counts"], [1] * 8 + [2, 3, 4, 3])
        self.assertEqual(result["deterministic_unique_accepts"], 8)
        self.assertEqual(result["ambiguous_unique_original_valid_controls"], 4)
        self.assertEqual(result["out_of_grammar_stops"], 4)
        self.assertFalse(result["model_inference"])
        self.assertFalse(result["weights_loaded"])

    def test_opened_pass_never_admits_p2(self):
        _, _, refs = registration()
        decision = evaluate(records(), refs, True, True, 1000.0)
        self.assertEqual(decision["verdict"], "PASS")
        self.assertEqual(decision["reason"], "OPENED_SOURCE_BOUND_DIAGNOSTIC_ONLY")
        self.assertEqual(decision["accepted"], 12)
        self.assertEqual(decision["unique_accepted"], 8)
        self.assertEqual(decision["ambiguous_accepted"], 4)
        self.assertFalse(decision["p2_registration_admitted"])
        self.assertFalse(decision["p2_admitted"])
        self.assertFalse(decision["decision3_admitted"])

    def test_ambiguity_floor_is_frozen(self):
        _, _, refs = registration()
        decision = evaluate(records((True, True, False, False)), refs, True, True, 1000.0)
        self.assertEqual(decision["verdict"], "FAIL")
        self.assertEqual(decision["reason"], "SEMANTIC_SELECTION_CAPABILITY_FAILURE")
        self.assertEqual(decision["unique_accepted"], 8)
        self.assertEqual(decision["ambiguous_accepted"], 2)

    def test_zero_neural_and_exact_ambiguous_work_are_gates(self):
        _, _, refs = registration()
        bad = records(forward_calls=35)
        decision = evaluate(bad, refs, True, True, 1000.0)
        self.assertEqual(decision["verdict"], "FAIL")
        self.assertEqual(decision["reason"], "CONTROL_PATH_COST_DRIFT")
        self.assertEqual(decision["path_cost"]["ambiguous_neural_forward_calls"], 140)

        bad = records()
        bad[0]["model_calls"] = 1
        decision = evaluate(bad, refs, True, True, 1000.0)
        self.assertEqual(decision["reason"], "CONTROL_PATH_COST_DRIFT")

    def test_accounting_and_identity_fail_closed(self):
        _, _, refs = registration()
        bad = records()
        bad[9]["accounting_complete"] = False
        self.assertEqual(
            evaluate(bad, refs, True, True, 1000.0)["reason"],
            "CONTROL_WORK_ACCOUNTING_FAILURE",
        )
        self.assertEqual(
            evaluate(records(), refs, False, True, 1000.0)["verdict"],
            "NOT_EVALUATED",
        )
        self.assertEqual(
            evaluate(records()[:-1], refs, True, False, 1000.0)["verdict"],
            "NOT_EVALUATED",
        )

    def test_replay_ignores_execution_timing_identity(self):
        _, rows, refs = registration()
        row, ref = rows[0], refs[0]

        def forbidden():
            raise AssertionError("unique path must not construct selector")

        record = interpret_and_execute(
            row["view"], _executor, _hidden_verifier(ref), forbidden
        )
        record["task_id"] = row["task_id"]
        record["kind"] = ref["kind"]
        record["semantic_path"] = ref["semantic_path"]
        self.assertTrue(record["accepted"])
        self.assertIsNotNone(record["execution"])

        # Replay must verify semantic execution fields, not expect a newly
        # measured local execution timer to be byte-identical.
        record["execution"]["complete_ms"] += 12345.0
        replay_record(row, ref, record)

        corrupted = dict(record)
        corrupted["execution"] = dict(record["execution"])
        corrupted["execution"]["answer"] = "not-the-original-answer"
        with self.assertRaises(ValueError):
            replay_record(row, ref, corrupted)

    def test_gate_and_boundary_values(self):
        self.assertEqual(GATE["unique_model_calls_exact"], 0)
        self.assertEqual(GATE["ambiguous_model_calls_exact"], 4)
        self.assertEqual(GATE["ambiguous_neural_forward_calls_exact"], 144)
        self.assertEqual(GATE["ambiguous_accepted_min"], 3)
        for key in ("p2_registration_admitted", "p2_admitted", "decision3_admitted"):
            self.assertFalse(BOUNDARY[key])

    def test_totals_unknown_propagates(self):
        rows = records()
        self.assertEqual(totals(rows)["neural_forward_calls"], 144)
        rows[8]["evaluated_tokens"] = None
        self.assertIsNone(totals(rows)["evaluated_tokens"])


if __name__ == "__main__":
    unittest.main()
