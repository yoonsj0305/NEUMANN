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
        self.assertEqual(report["schema"], CERTIFICATE_SCHEMA)
        self.assertEqual(report["rows"], 6)
        self.assertEqual(report["cols"], 30)

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
        self.assertGreater(report["equality_abs"], report["equality_tol"])

        nonnegative_bad = x.copy()
        zero_index = int(np.flatnonzero(x == 0)[0])
        nonnegative_bad[zero_index] = -1e-3
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], nonnegative_bad, y
        )
        self.assertFalse(report["accepted"])
        self.assertGreater(report["nonnegative_abs"], report["nonnegative_tol"])

        dual_bad = y.copy()
        dual_bad[0] += 10.0
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], x, dual_bad
        )
        self.assertFalse(report["accepted"])
        self.assertTrue(
            report["dual_feasibility_abs"] > report["dual_feasibility_tol"]
            or report["objective_gap_abs"] > report["objective_gap_tol"]
        )

        feasible_but_nonoptimal_x = np.zeros_like(x)
        report = verify_standard_form_certificate(
            self.case["A"], self.case["b"], self.case["c"], feasible_but_nonoptimal_x, y
        )
        self.assertFalse(report["accepted"])

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
        with self.assertRaises(ValueError):
            verify_standard_form_certificate(
                self.case["A"], self.case["b"], self.case["c"],
                self.case["known_x"], self.case["known_y"], atol=-1.0
            )


if __name__ == "__main__":
    unittest.main()
