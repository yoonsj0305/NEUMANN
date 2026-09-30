"""v0.0.82 pre-audit structural and accounting contracts."""
import unittest

import numpy as np

from neumann1.lp_basis_headroom_v082 import (
    DIRECT_POLICIES,
    MAX_RATIO,
    MIN_WIN_CASES,
    POLICIES,
    REPEATS,
    generate,
    observe,
    specifications,
)


class LPBasisHeadroomV082Tests(unittest.TestCase):
    def test_frozen_case_registry_is_unique_and_bounded(self):
        specs = specifications()
        self.assertEqual(len(specs), 12)
        self.assertEqual(len({s["id"] for s in specs}), 12)
        self.assertEqual({s["rows"] for s in specs}, {16, 32, 64})
        self.assertEqual(max(s["cols"] for s in specs), 4096)
        self.assertEqual(REPEATS, 5)
        self.assertEqual(MAX_RATIO, 0.80)
        self.assertEqual(MIN_WIN_CASES, 9)
        self.assertEqual(POLICIES, DIRECT_POLICIES + ("oracle_basis",))

    def test_generator_is_reproducible_and_certificate_valid(self):
        spec = specifications()[0]
        left, right = generate(spec), generate(spec)
        for key in ("A", "b", "c", "basis", "planted_x", "planted_y"):
            self.assertTrue(np.array_equal(left[key], right[key]), key)
        self.assertEqual(left["basis"].size, spec["rows"])
        self.assertEqual(np.unique(left["basis"]).size, spec["rows"])
        self.assertTrue(np.all(left["planted_x"][left["basis"]] > 0))

    def test_all_declared_paths_verify_on_micro_case(self):
        case = generate(specifications()[0])
        for policy in POLICIES:
            result = observe(case, policy)
            self.assertTrue(result["accepted"], result)
            self.assertIsNone(result["error"])
            self.assertGreaterEqual(result["total_ms"], result["verify_ms"])
            self.assertTrue(result["certificate"]["accepted"])


if __name__ == "__main__":
    unittest.main()
