"""Finite exact bag semantics and archive integrity, never a final timing rerun."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sqlite3
import unittest

from neumann1.relational_headroom_v080 import (
    POLICIES, build, grouped_sql, observe, original_sql, relations,
    specifications, validate_archive,
)

ROWS = {"a": [(0, 1), (0, 1), (1, 99)],
        "b": [(0, 2, 3), (0, 2, 3), (1, 4, 8)],
        "c": [(2, 2), (2, 2), (2, 2), (4, 99)]}


def brute(rows, threshold):
    weights = [b[2] for a in rows["a"] for b in rows["b"] for c in rows["c"]
               if a[0] == b[0] and b[1] == c[0] and a[1] < threshold and c[1] < threshold]
    return (len(weights), sum(weights))


def sqlite_fixture(rows):
    db = sqlite3.connect(":memory:")
    for name, schema in (("a", "k INTEGER,flag INTEGER"),
                         ("b", "k INTEGER,j INTEGER,w INTEGER"),
                         ("c", "j INTEGER,flag INTEGER")):
        db.execute(f"CREATE TABLE {name}({schema})")
        db.executemany(f"INSERT INTO {name} VALUES ({','.join('?' for _ in rows[name][0])})",
                       rows[name])
    return db


class RelationalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((Path(__file__).parents[1] /
            "docs/experiments/results/v080_first_audit.json").read_text())

    def test_bag_multiplicity_rewrite_matches_independent_brute_force(self):
        for rows in (ROWS, {**ROWS, "a": [(0, 99), (1, 99)]}):
            with sqlite_fixture(rows) as db:
                expected = brute(rows, 25)
                self.assertEqual(db.execute(original_sql(25)).fetchone(), expected)
                self.assertEqual(db.execute(grouped_sql(25)).fetchone(), expected)
        self.assertEqual(brute(ROWS, 25), (12, 36))

    def test_typed_query_rejects_unregistered_or_injected_forms(self):
        for t in (True, 25.0, -1, "25; DROP TABLE a"):
            with self.assertRaises(ValueError): original_sql(t)
        with self.assertRaises(ValueError): original_sql(25, ("a", "c", "b"))

    def test_generator_is_bounded_and_reproducible(self):
        specs = specifications()
        self.assertEqual(len({s["id"] for s in specs}), 12)
        rows = relations(specs[0])
        self.assertEqual(rows, relations(specs[0]))
        self.assertEqual({len(v) for v in rows.values()}, {2000})
        self.assertTrue(all(0 <= r[0] < 512 and 0 <= r[1] < 100 for r in rows["a"]))
        self.assertTrue(all(0 <= r[0] < 512 and 0 <= r[1] < 512 and 1 <= r[2] <= 9
                            for r in rows["b"]))

    def test_first_archive_is_complete_and_keeps_negative_decision(self):
        validate_archive(self.archive)
        self.assertEqual(len(self.archive["rows"]), 216)
        self.assertEqual(self.archive["summary"]["decision"],
                         "REJECT_BOUNDED_RELATIONAL_PLANNER_TRAINING")
        self.assertEqual(self.archive["summary"]["q4"], "OPEN")

    def test_archive_rejects_deleted_cost_duplicate_and_changed_source(self):
        for mutation in (lambda r: r["rows"].append(r["rows"][0]),
                         lambda r: r["rows"].pop(),
                         lambda r: r["rows"][0].update(total_ms=0),
                         lambda r: r["setup"][0]["table_sha256"].update(a="0" * 64),
                         lambda r: r["rows"][0].update(accepted_exact=False),
                         lambda r: r["summary"].update(decision="PASS")):
            archive = deepcopy(self.archive)
            mutation(archive)
            with self.assertRaises(ValueError): validate_archive(archive)

    @unittest.skipUnless(importlib.util.find_spec("duckdb"), "optional pinned DuckDB experiment")
    def test_shared_engines_verify_all_micro_fixture_policies_and_restore_state(self):
        db, checker = build(ROWS)
        try:
            for policy in POLICIES:
                result = observe(db, checker, {"id": "fixture", "threshold": 25}, policy)
                self.assertTrue(result["accepted_exact"], result)
                self.assertEqual(result["answer"], brute(ROWS, 25))
                self.assertEqual(db.execute("SELECT current_setting('disabled_optimizers')").fetchone(), ("",))
        finally:
            db.close(); checker.close()


if __name__ == "__main__":
    unittest.main()
