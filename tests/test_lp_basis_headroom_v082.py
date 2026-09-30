"""v0.0.82 protocol and route contracts; no full timing audit rerun."""
from copy import deepcopy
import unittest

import numpy as np

from neumann1.lp_basis_headroom_v082 import (
    DIRECT_ROUTES,
    ROUTES,
    generate_case,
    observe,
    source_identity,
    specifications,
    summarize,
)


class LPBasisHeadroomV082Tests(unittest.TestCase):
    def test_frozen_specification_has_twelve_fresh_cells(self):
        specs = specifications()
        self.assertEqual(len(specs), 12)
        self.assertEqual([s["seed"] for s in specs], list(range(8201, 8213)))
        self.assertEqual({s["rows"] for s in specs}, {16, 32, 64, 128})
        self.assertEqual({s["ratio"] for s in specs}, {4, 16, 64})
        self.assertTrue(all(s["cols"] == s["rows"] * s["ratio"] for s in specs))

    def test_generator_is_reproducible_and_certificate_valid(self):
        spec = specifications()[0]
        first = generate_case(spec)
        second = generate_case(spec)
        self.assertEqual(source_identity(first), source_identity(second))
        self.assertTrue(first["planted_certificate"]["accepted"])
        self.assertEqual(first["A"].shape, (16, 64))
        self.assertEqual(first["basis"].shape, (16,))
        self.assertEqual(len(np.unique(first["basis"])), 16)

    def test_unknown_generator_cell_is_rejected(self):
        bad = dict(specifications()[0])
        bad["seed"] += 1
        with self.assertRaises(ValueError):
            generate_case(bad)

    def test_all_routes_share_original_certificate_on_smallest_cell(self):
        spec = specifications()[0]
        case = generate_case(spec)
        for route in ROUTES:
            record = observe(case, spec, route)
            self.assertTrue(record["accepted"], record)
            self.assertTrue(record["certificate"]["accepted"], record)

    def test_summary_uses_posthoc_fastest_direct_and_frozen_gate(self):
        rows, warmups = [], []
        for spec in specifications():
            for route in ROUTES:
                warmups.append(
                    {
                        "case_id": spec["id"],
                        "route": route,
                        "accepted": True,
                    }
                )
                base = {
                    "direct_highs": 10.0,
                    "direct_highs_ds": 9.0,
                    "direct_highs_ipm": 11.0,
                    "oracle_basis": 6.0,
                }[route]
                for repeat in range(3):
                    rows.append(
                        {
                            "case_id": spec["id"],
                            "route": route,
                            "repeat": repeat,
                            "accepted": True,
                            "total_ms": base,
                        }
                    )
        summary = summarize(rows, warmups)
        self.assertEqual(
            summary["decision"], "CONSTRUCTED_ORACLE_BASIS_HEADROOM_PRESENT"
        )
        self.assertEqual(summary["twenty_percent_win_cases"], 12)
        self.assertTrue(
            all(
                cell["posthoc_fastest_direct_route"] == "direct_highs_ds"
                for cell in summary["cells"]
            )
        )

        broken = deepcopy(rows)
        broken.pop()
        with self.assertRaises(ValueError):
            summarize(broken, warmups)

    def test_capability_failure_blocks_cost_claim(self):
        rows, warmups = [], []
        for spec in specifications():
            for route in ROUTES:
                warmups.append(
                    {"case_id": spec["id"], "route": route, "accepted": True}
                )
                for repeat in range(3):
                    rows.append(
                        {
                            "case_id": spec["id"],
                            "route": route,
                            "repeat": repeat,
                            "accepted": True,
                            "total_ms": 1.0,
                        }
                    )
        rows[0]["accepted"] = False
        summary = summarize(rows, warmups)
        self.assertEqual(summary["decision"], "CAPABILITY_UNREACHED")
        self.assertEqual(summary["q3"], "OPEN")
        self.assertEqual(summary["q4"], "OPEN")


if __name__ == "__main__":
    unittest.main()
