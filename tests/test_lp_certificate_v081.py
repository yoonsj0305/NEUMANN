"""v0.0.81 contract tests: certificate authority without re-solving."""
import unittest
from unittest.mock import patch

import numpy as np

from neumann1.lp_certificate_v081 import (
    CERTIFICATE_SCHEMA,
    contract_fixture,
    highs_candidate,
    verify_standard_form_certificate,
)


class LPCertificateV081Tests(unittest.TestCase):
    def setUp(self):
        self.case = contract_fixture()

    def test_known_primal_dual_certificate_is_accepted(self):
        report = verify_standard_form_certificate(
            self.case["A"],
            self.case["b"],
            self.case["c"],
            self.case["known_x"],
            self.case["known_y"],
        )
        self.assertTrue(report["accepted"], report)
        self.assertTrue(report["numerical_finite"])
        self.assertEqual(report["schema"], CERTIFICATE_SCHEMA)
        self.assertEqual(report["rows"], 6)
        self.assertEqual(report["cols"], 30)
        self.assertTrue(report["complementarity_diagnostic_only"])

    def test_highs_output_is_not_trusted_without_independent_certificate(self):
        candidate = highs_candidate(self.case["A"], self.case["b"], self.case["c"])
        self.assertTrue(candidate["solver_success"], candidate)
        self.assertTrue(candidate["certificate"]["accepted"], candidate)

    def test_verifier_never_calls_optimizer(self):
        with patch("scipy.optimize.linprog", side_effect=AssertionError("solver called")):
            report = verify_standard_form_certificate(
                self.case["A"],
                self.case["b"],
                self.case["c"],
                self.case["known_x"],
                self.case["known_y"],
            )
        self.assertTrue(report["accepted"])

    def test_primal_dual_and_objective_faults_fail_closed(self):
        x = self.case["known_x"].copy()
        y = self.case["known_y"].copy()

        primal_bad = x.copy()
        primal_bad[self.case["known_basis"][0]] += 1e-3
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], primal_bad, y
        )
        self.assertFalse(report["accepted"])
        self.assertGreater(report["equality_ratio"], 1.0)

        nonnegative_bad = x.copy()
        zero_index = int(np.flatnonzero(x == 0)[0])
        nonnegative_bad[zero_index] = -1e-3
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], nonnegative_bad, y
        )
        self.assertFalse(report["accepted"])
        self.assertGreater(report["nonnegative_ratio"], 1.0)

        dual_bad = y.copy()
        dual_bad[0] += 10.0
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], x, dual_bad
        )
        self.assertFalse(report["accepted"])
        self.assertTrue(
            report["dual_feasibility_ratio"] > 1.0
            or report["objective_gap_ratio"] > 1.0
        )

        infeasible_x = np.zeros_like(x)
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], infeasible_x, y
        )
        self.assertFalse(report["accepted"])

    def test_backward_error_scaling_handles_large_cancelling_terms(self):
        # The first equality has O(1e8) terms whose exact result is O(1).
        # A 1e-14 relative perturbation produces an O(1e-6) absolute row
        # residual. It should be judged relative to the original dot-product
        # magnitude rather than only to the small right-hand side.
        A = np.array([[1e8, -1e8], [1.0, 0.0]], dtype=float)
        x = np.array([1.0, 1.0 - 1e-8], dtype=float)
        b = A @ x
        y = np.zeros(2)
        c = np.zeros(2)
        perturbed = x.copy()
        perturbed[1] += 1e-14
        report = verify_standard_form_certificate(A, b, c, perturbed, y)
        self.assertTrue(report["accepted"], report)
        self.assertLessEqual(report["equality_ratio"], 1.0)

    def test_shape_nonfinite_and_tolerance_errors_are_rejected(self):
        with self.assertRaises(ValueError):
            verify_standard_form_certificate(
                self.case["A"], self.case["b"][:-1], self.case["c"],
                self.case["known_x"], self.case["known_y"]
            )
        corrupt = self.case["known_x"].copy()
        corrupt[0] = np.nan
        with self.assertRaises(ValueError):
            verify_standard_form_certificate(
                self.case["A"], self.case["b"], self.case["c"], corrupt,
                self.case["known_y"]
            )
        for bad in (-1.0, True, float("inf"), "1e-8"):
            with self.assertRaises(ValueError):
                verify_standard_form_certificate(
                    self.case["A"], self.case["b"], self.case["c"],
                    self.case["known_x"], self.case["known_y"], atol=bad
                )
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"],
            self.case["known_x"], self.case["known_y"], atol=np.float64(1e-8)
        )
        self.assertTrue(report["accepted"])


if __name__ == "__main__":
    unittest.main()
