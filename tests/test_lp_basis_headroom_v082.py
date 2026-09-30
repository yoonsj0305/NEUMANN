"""v0.0.82 contracts: zero-discovery basis headroom screen."""
from copy import deepcopy
import json
import unittest

from neumann1.lp_basis_headroom_v082 import (
    CONDITION_NUMBERS,
    DECISION_ADMIT,
    DECISION_REJECT,
    DIRECT_METHODS,
    REPEATS,
    WIDTH_FACTORS,
    generate_case,
    oracle_basis_once,
    protocol,
    specifications,
    summarize,
)


class LPBasisHeadroomV082Tests(unittest.TestCase):
    def test_grid_and_pairing_are_frozen_and_deterministic(self):
        specs = specifications()
        self.assertEqual(len(specs), 24)
        self.assertEqual({s["width_factor"] for s in specs}, set(WIDTH_FACTORS))
        self.assertEqual({s["condition_number"] for s in specs}, set(CONDITION_NUMBERS))
        self.assertEqual(len({s["id"] for s in specs}), 24)

        by_pair = {}
        for spec in specs:
            by_pair.setdefault(spec["pair_id"], []).append(spec)
        self.assertEqual(len(by_pair), 12)
        self.assertTrue(all({s["width_factor"] for s in pair} == {1, 16}
                            for pair in by_pair.values()))

        control = generate_case(specs[0])
        again = generate_case(specs[0])
        self.assertEqual(control["raw_observable_sha256"], again["raw_observable_sha256"])
        self.assertEqual(control["oracle_basis_sha256"], again["oracle_basis_sha256"])
        self.assertEqual(control["latent_pair_sha256"], again["latent_pair_sha256"])

        pair_spec = next(
            s for s in specs
            if s["pair_id"] == specs[0]["pair_id"] and s["width_factor"] == 16
        )
        expanded = generate_case(pair_spec)
        self.assertEqual(control["latent_pair_sha256"], expanded["latent_pair_sha256"])
        self.assertNotEqual(control["raw_observable_sha256"],
                            expanded["raw_observable_sha256"])

    def test_protocol_is_json_roundtrip_stable(self):
        frozen = protocol()
        self.assertEqual(json.loads(json.dumps(frozen)), frozen)

    def test_oracle_basis_reconstructs_verified_original_certificate(self):
        spec = next(s for s in specifications()
                    if s["rows"] == 32
                    and s["condition_number"] == 1000
                    and s["width_factor"] == 16
                    and s["replicate"] == 0)
        case = generate_case(spec)
        result = oracle_basis_once(case, case["oracle_basis"])
        self.assertTrue(result["accepted"], result)
        self.assertTrue(result["certificate"]["accepted"], result)

    def test_invalid_oracle_basis_fails_closed(self):
        spec = next(s for s in specifications() if s["width_factor"] == 16)
        case = generate_case(spec)
        duplicated = case["oracle_basis"].copy()
        duplicated[-1] = duplicated[0]
        result = oracle_basis_once(case, duplicated)
        self.assertFalse(result["accepted"])
        self.assertIsNotNone(result["error"])

        short = case["oracle_basis"][:-1]
        result = oracle_basis_once(case, short)
        self.assertFalse(result["accepted"])

    def _fake_archive(self, wide_oracle_ms=3.0):
        records = []
        warmups = []
        for spec in specifications():
            for route in (*DIRECT_METHODS, "oracle_basis"):
                warmups.append({
                    "case_id": spec["id"],
                    "route_id": route,
                    "accepted": True,
                })
                for repeat in range(REPEATS):
                    if route == "oracle_basis":
                        total = 2.0 if spec["width_factor"] == 1 else wide_oracle_ms
                    else:
                        direct_rank = DIRECT_METHODS.index(route)
                        base = 10.0 + direct_rank * 2.0
                        total = base if spec["width_factor"] == 1 else base * 10.0
                    records.append({
                        "case_id": spec["id"],
                        "route_id": route,
                        "repeat": repeat,
                        "accepted": True,
                        "total_ms": total,
                    })
        return records, warmups

    def test_summary_requires_structural_scaling_not_only_generic_solver_gap(self):
        records, warmups = self._fake_archive(wide_oracle_ms=3.0)
        summary = summarize(records, warmups)
        self.assertEqual(summary["decision"], DECISION_ADMIT)
        self.assertEqual(summary["expanded_twenty_percent_win_cases"], 12)
        self.assertEqual(summary["scaling_pairs_ge_2x"], 12)

        weak, weak_warmups = self._fake_archive(wide_oracle_ms=90.0)
        rejected = summarize(weak, weak_warmups)
        self.assertEqual(rejected["decision"], DECISION_REJECT)

    def test_summary_rejects_duplicate_or_missing_evidence(self):
        records, warmups = self._fake_archive()
        duplicate = deepcopy(records)
        duplicate.append(deepcopy(duplicate[0]))
        with self.assertRaises(ValueError):
            summarize(duplicate, warmups)

        missing_warmup = warmups[:-1]
        with self.assertRaises(ValueError):
            summarize(records, missing_warmup)


if __name__ == "__main__":
    unittest.main()
