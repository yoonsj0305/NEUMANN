"""Synthetic contract fixtures only: no model, LP generation, or timing."""
import copy
import importlib.util
import math
import unittest
from pathlib import Path

# The package's legacy __init__ eagerly imports scientific/model dependencies.
# Load this standalone pure-stdlib analysis module without executing that init.
_spec = importlib.util.spec_from_file_location(
    "q5_scaling_contract", Path(__file__).resolve().parents[1] / "neumann1" / "q5_scaling_contract.py"
)
q5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q5)


class Q5ScalingContractTests(unittest.TestCase):
    def test_metadata_factorial_and_pairing(self):
        views = q5.planned_views()
        q5.validate_source_metadata(views)
        self.assertEqual(len(views), 96)
        self.assertEqual(len({v["seed"] for v in views}), 48)
        self.assertEqual({v["condition"] for v in views}, {1, 1000})
        self.assertGreater(min(v["seed"] for v in views), 102223)
        for i in range(0, len(views), 2):
            self.assertEqual(views[i]["pair_id"], views[i+1]["pair_id"])
            self.assertFalse(views[i]["surface"])
            self.assertTrue(views[i+1]["surface"])
        for changed in (views[:-1], list(reversed(views)), views + [views[0]]):
            with self.assertRaises(ValueError):
                q5.validate_source_metadata(changed)

    def test_protocol_is_unopened_and_immutable_to_callers(self):
        original = q5.protocol()
        changed = q5.protocol()
        changed["support_factors"].append(8)
        self.assertEqual(q5.protocol(), original)
        self.assertFalse(original["new_fitting"])
        self.assertEqual(original["cache"], "disabled")
        self.assertFalse(original["cross_domain_pass"])

    def test_pinned_authority_and_integer_key_roundtrip(self):
        manifest = {
            "format": "neumann.q34-expand4-fresh-eval-v102.archive.v1",
            "frozen_head": "46af13c3d7d9b1a87f0a0db8511f5972511beb16",
            "rerun": False, "advance_q5": True,
            "decision": "Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5",
            "gzip_sha256": q5.EXPECTED_RESULT_GZIP,
            "json_sha256": q5.EXPECTED_RESULT_JSON,
        }
        training = {int(s): {"weights_sha256": h} for s, h in q5.EXPECTED_WEIGHTS.items()}
        q5.validate_authority(manifest, training)
        for field in ("decision", "advance_q5", "gzip_sha256", "rerun", "frozen_head"):
            changed = dict(manifest)
            changed[field] = None
            with self.assertRaises(ValueError):
                q5.validate_authority(changed, training)
        changed = copy.deepcopy(training)
        changed[100001]["weights_sha256"] = "different checkpoint"
        with self.assertRaises(ValueError):
            q5.validate_authority(manifest, changed)
        changed = dict(training)
        changed["100001"] = training[100001]
        with self.assertRaises(ValueError):
            q5.validate_authority(manifest, changed)

    def test_full_cost_charges_training_and_cold_start(self):
        cost = q5.charged_cost(proposal_ms=2, post_ms=5, fit_setup_ms=10000, cold_start_ms=20000)
        self.assertEqual(cost["complete_ms"], 10)
        self.assertEqual(cost["discovery_ms"], 5)
        for queries in (1, 1000, True):
            with self.assertRaises(ValueError):
                q5.charged_cost(proposal_ms=2, post_ms=5, fit_setup_ms=0, cold_start_ms=0, queries=queries)
        for value in (-1, math.nan, math.inf, True):
            with self.assertRaises(ValueError):
                q5.charged_cost(proposal_ms=value, post_ms=5, fit_setup_ms=0, cold_start_ms=0)

    def test_no_speed_ratio_for_failed_capability_or_uncharged_fallback(self):
        args = dict(direct_ms=100, oracle_ms=10, discovery_ms=2, post_ms=20,
                    direct_verified=True, oracle_verified=True, candidate_verified=True,
                    all_attempt_costs_charged=True, width_factor=16)
        good = q5.cell_gate(**args)
        self.assertTrue(good["passed"])
        for field in ("direct_verified", "oracle_verified", "candidate_verified", "all_attempt_costs_charged"):
            bad = q5.cell_gate(**{**args, field: False})
            self.assertIsNone(bad["ratio"])
            self.assertFalse(bad["passed"])
        bad = q5.cell_gate(**{**args, "post_ms": 101})
        self.assertIsNone(bad["utility"])
        self.assertFalse(bad["passed"])

    def test_wide_utility_floor_and_null_control_are_separate(self):
        args = dict(direct_ms=100, oracle_ms=10, discovery_ms=5, post_ms=40,
                    direct_verified=True, oracle_verified=True, candidate_verified=True,
                    all_attempt_costs_charged=True)
        self.assertFalse(q5.cell_gate(**args, width_factor=16)["passed"])
        self.assertTrue(q5.cell_gate(**args, width_factor=1)["passed"])
        self.assertFalse(q5.cell_gate(**{**args, "post_ms": 116}, width_factor=1)["passed"])

    def test_slope_checks_complete_cost_not_solver_dimension(self):
        self.assertAlmostEqual(q5.log_slope({m: m*m for m in q5.ROWS}), 2)
        pairs = {m: [(m*m*(i+1), m*(i+1)) for i in range(4)] for m in q5.ROWS}
        evidence = q5.slope_evidence(pairs)
        self.assertAlmostEqual(evidence["slope_difference"], -1)
        self.assertTrue(evidence["lower_empirical_slope"])
        equal = {m: [(m*m, m*m)]*4 for m in q5.ROWS}
        self.assertFalse(q5.slope_evidence(equal)["lower_empirical_slope"])
        with self.assertRaises(ValueError):
            q5.slope_evidence({m: pairs[m] for m in (32, 64, 128)})
        with self.assertRaises(ValueError):
            q5.slope_evidence({m: pairs[m][:2] for m in q5.ROWS})
        self.assertFalse(evidence["global_q5_closed"])

    def test_final_conjunction_cannot_pool_away_failure_or_claim_transfer(self):
        args = dict(direct_ms=100, oracle_ms=10, discovery_ms=2, post_ms=20,
                    direct_verified=True, oracle_verified=True, candidate_verified=True,
                    all_attempt_costs_charged=True)
        cells = {(seed, m, width, surface): q5.cell_gate(**args, width_factor=width)
                 for seed in q5.SEEDS for m in q5.ROWS for width in q5.WIDTHS
                 for surface in (False, True)}
        evidence = q5.slope_evidence({m: [(m*m, m)]*4 for m in q5.ROWS})
        slopes = {(seed, width, surface): evidence for seed in q5.SEEDS
                  for width in (16, 32) for surface in (False, True)}
        result = q5.summarize_scaling(cells, slopes)
        self.assertEqual(result["decision"], "Q5_CONSTRUCTED_LP_SCALING_PASS_NOT_CROSS_DOMAIN")
        self.assertFalse(result["cross_domain_pass"])
        self.assertFalse(result["global_q5_closed"])
        key = (100002, 256, 32, True)
        weak = copy.deepcopy(cells)
        weak[key]["passed"] = False
        self.assertEqual(q5.summarize_scaling(weak, {})["decision"], "Q5_SCALING_COST_GATE_FAIL")
        weak[key] = q5.cell_gate(**{**args, "direct_verified": False}, width_factor=32)
        self.assertEqual(q5.summarize_scaling(weak, {})["decision"],
                         "Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED")
        weak = copy.deepcopy(cells)
        weak[key]["ratio"] = 0.81
        self.assertEqual(q5.summarize_scaling(weak, {})["decision"], "Q5_SCALING_COST_GATE_FAIL")
        equal = q5.slope_evidence({m: [(m*m, m*m)]*4 for m in q5.ROWS})
        uncertain = dict(slopes)
        uncertain[(100002, 32, True)] = equal
        self.assertEqual(q5.summarize_scaling(cells, uncertain)["decision"],
                         "Q5_SCALING_COST_PASS_SLOPE_UNRESOLVED")
        with self.assertRaises(ValueError):
            q5.summarize_scaling(cells, {})
        with self.assertRaises(ValueError):
            q5.summarize_scaling({}, slopes)


if __name__ == "__main__":
    unittest.main()
