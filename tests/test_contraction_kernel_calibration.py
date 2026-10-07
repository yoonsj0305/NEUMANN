import unittest
import numpy as np
from experiments.contraction_kernel_calibration import agreement


class CalibrationTests(unittest.TestCase):
    def test_relative_positive_agreement(self):
        self.assertTrue(agreement(np.array([1., 2.]) * (1 + 1e-12), np.array([1., 2.])))
        self.assertFalse(agreement(np.array([1., 2.01]), np.array([1., 2.])))

    def test_shape_zero_and_nonfinite_rejected(self):
        expected = np.array([1., 2.])
        for actual in [np.zeros(2), expected.reshape(1, 2), np.array([1., np.nan]), np.array([1., np.inf])]:
            self.assertFalse(agreement(actual, expected))

    def test_underflow_reference_rejected(self):
        self.assertFalse(agreement(np.array([0.]), np.array([0.])))


if __name__ == "__main__":
    unittest.main()
