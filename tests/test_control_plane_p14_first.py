"""P1.4 first-run gate and frozen semantic wrapper contracts; model-free."""
import unittest

from neumann1.control_plane_p1_contract import MODEL
from neumann1.control_plane_p14 import FrozenSemanticCompiler
from experiments.control_plane_p14_dev import evaluate
from experiments.control_plane_p14_registration import registration, check_construction


class FakeCore:
    def __init__(self, raw='{"route":"ARITHMETIC","expression":"a+b","bindings":{"a":2,"b":3}}',
                 deadline=False, peak=1234):
        self.identity = dict(MODEL)
        self.raw = raw
        self.deadline = deadline
        self.peak = peak
        self.calls = 0

    def audit(self):
        return {"unchanged": True}

    def generate(self, messages, max_tokens, thinking, deadline_ms):
        self.calls += 1
        if thinking is not False:
            raise AssertionError("P1.4 semantic compiler must disable thinking")
        return {
            "raw": self.raw,
            "input_tokens": 40,
            "output_tokens": 20,
            "generation_ms": 5.0,
            "deadline_reached": self.deadline,
            "peak_accelerator_memory_bytes": self.peak,
            "core_sha256": "synthetic-core",
        }


def records(raw_accept=(True, True, True, True, True, True, True, True),
            mixed_accept=(True, True, True, True), model_calls=1):
    out = []
    for i, accepted in enumerate(raw_accept):
        out.append({
            "task_id": "p14d_%02d" % (i+1),
            "accepted": accepted,
            "accounting_complete": True,
            "model_calls": model_calls,
            "complete_ms": 10.0,
        })
    for j, accepted in enumerate(mixed_accept, start=9):
        out.append({
            "task_id": "p14d_%02d" % j,
            "accepted": accepted,
            "routing": {"fallback_calls": 1},
            "selected_route": "ARITHMETIC" if j < 11 else "CSP",
            "complete_ms": 10.0,
        })
    return out


class FirstRunContracts(unittest.TestCase):
    def test_registration_and_construction_controls_are_model_free(self):
        reg, rows, refs = registration()
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(refs), 12)
        self.assertFalse(reg["scores_seen_at_registration"])
        receipt = check_construction()
        self.assertTrue(receipt["registration_valid"])
        self.assertEqual(receipt["positive_checker_controls"], 12)
        self.assertEqual(receipt["negative_checker_controls"], 12)
        self.assertFalse(receipt["model_inference"])

    def test_semantic_wrapper_is_one_greedy_thinking_disabled_call(self):
        core = FakeCore()
        compiler = FrozenSemanticCompiler(core)
        view = {"instruction":"Return exact.","public":{"query":"Add 2 and 3."}}
        receipt = compiler.propose(view, 1000.0)
        self.assertEqual(receipt["proposal"]["route"], "ARITHMETIC")
        self.assertEqual(core.calls, 1)
        self.assertEqual(receipt["output_tokens"], 20)

    def test_semantic_deadline_or_missing_vram_fails_closed(self):
        view = {"instruction":"Return exact.","public":{"query":"Add 2 and 3."}}
        with self.assertRaises(TimeoutError):
            FrozenSemanticCompiler(FakeCore(deadline=True)).propose(view, 1000.0)
        with self.assertRaises(ValueError):
            FrozenSemanticCompiler(FakeCore(peak=None)).propose(view, 1000.0)

    def test_opened_gate_pass_never_admits_p2(self):
        _, _, refs = registration()
        decision = evaluate(records(), refs, True, True, 1000.0)
        self.assertEqual(decision["verdict"], "PASS")
        self.assertEqual(decision["raw_semantic_accepted"], 8)
        self.assertEqual(decision["mixed_fallback_accepted"], 4)
        self.assertFalse(decision["p2_registration_admitted"])
        self.assertFalse(decision["p2_admitted"])
        self.assertFalse(decision["decision3_admitted"])

    def test_domain_floor_and_work_accounting_fail(self):
        _, _, refs = registration()
        # Overall 6/8, but arithmetic only 2/4.
        d = evaluate(records(raw_accept=(True, True, False, False, True, True, True, True)),
                     refs, True, True, 1000.0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertEqual(d["reason"], "SEMANTIC_PATH_CAPABILITY_FAILURE")
        d = evaluate(records(model_calls=2), refs, True, True, 1000.0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertEqual(d["reason"], "SEMANTIC_WORK_ACCOUNTING_DRIFT")

    def test_incomplete_or_identity_drift_is_not_evaluated(self):
        _, _, refs = registration()
        d = evaluate(records()[:-1], refs, True, False, 1000.0)
        self.assertEqual(d["verdict"], "NOT_EVALUATED")
        d = evaluate(records(), refs, False, True, 1000.0)
        self.assertEqual(d["verdict"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
