"""Synthetic fault-injection only; no new LP/model/solver/benchmark execution."""
import ast
import copy
import gzip
import importlib
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
registration = importlib.import_module("experiments.q5_register")
replay = importlib.import_module("experiments.q5_replay")
evaluator = importlib.import_module("experiments.q5_evaluate")
ev = registration.evidence_module()
HEAD = "a" * 40


def fixture_records():
    views = {s["id"]: s for s in ev.contract.planned_views()}
    rows = []
    for case_id, route, repeat in ev.schedule():
        s = views[case_id]
        scale = s["rows"] / 32
        direct = 20 * scale ** 3
        if s["width_factor"] == 1:
            direct = 20 * scale
            total = direct + (0.05 if route.startswith("EXPAND4") else 0)
        else:
            total = direct if route == "DIRECT" else (1 if route == "ORACLE" else 2 * scale ** 2 + 0.05)
        proposal = 0.05 if route.startswith("EXPAND4") else 0.0
        rows.append({"case_id": case_id, "route": route, "repeat": repeat,
                     "accepted": True, "accounted": True, "total_ms": total,
                     "proposal_ms": proposal, "post_ms": total - proposal})
    return rows


def fixture_cold():
    return {route: {"cold_start_ms": 1000.0} for route in ev.ROUTES}


def fixture_training():
    return {str(seed): {"fit_ms": 100.0, "feature_setup_ms": 20.0} for seed in ev.contract.SEEDS}


def native_result():
    witness = {"x": [1.0], "y": [1.0]}
    ledger = {"native_run_calls": 1, "set_basis_calls": 0, "certificate_calls": 1}
    return {"accepted": True, "head_kind": "COLD", "fallback_used": False,
            "budget_s": 5.0, "total_ms": 3.5, "status": "VERIFIED", "ledger": ledger,
            "attempts": [{"warm_start": False, "basis": None, "accepted": True,
                "witness": witness, "certificate": {"accepted": True}, "error": None,
                "stages": [{"stage": k, "ms": 1.0} for k in ("model_setup", "native_solve", "original_verification")],
                "ledger": dict(ledger)}]}


class Q5ExecutionTests(unittest.TestCase):
    def test_imports_are_scientific_execution_free(self):
        # Full CI may already have imported torch for unrelated tests. Check a
        # clean interpreter, without changing the application's package init.
        process = subprocess.run([sys.executable, "-c",
            "import sys; import experiments.q5_register, experiments.q5_evaluate, experiments.q5_replay; "
            "assert not any(n in sys.modules for n in ('numpy','scipy','torch','highspy'))"],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_reservation_precedes_preflight_and_blocks_restart(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "first"
            a = ev.Attempt(out, "fixture", HEAD)
            a.finish("failed")
            with self.assertRaises(FileExistsError):
                ev.Attempt(out, "fixture", HEAD)
            self.assertEqual(ev.read_events(out)[1]["status"], "failed")

    def test_invalid_head_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as root:
            for head in ("main", "A" * 40, "x" * 40, True):
                out = Path(root) / "invalid"
                with self.assertRaises(ValueError):
                    ev.Attempt(out, "fixture", head)
                self.assertFalse(out.exists())

    def test_hash_chain_detects_changed_and_truncated_receipts(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "first"
            a = ev.Attempt(out, "fixture", HEAD)
            a.append("partial", {"retained": 1})
            a.finish("failed")
            rows, terminal = ev.read_events(out)
            self.assertEqual(terminal["events"], 2)
            rows[0]["payload"]["retained"] = 2
            with patch.object(Path, "open", return_value=__import__("io").BytesIO(b"\n".join(ev.canonical(r) for r in rows))):
                with self.assertRaises(ValueError):
                    ev.read_events(out)

    def test_per_case_identity_roundtrip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            identity = ev.pack_case(root, "one.json.gz", {"fixture": [1, 2, 3]})
            self.assertEqual(ev.unpack_case(root, identity), {"fixture": [1, 2, 3]})
            with self.assertRaises(FileExistsError):
                ev.pack_case(root, "one.json.gz", {})
            changed = {**identity, "json_sha256": "0" * 64}
            with self.assertRaises(ValueError):
                ev.unpack_case(root, changed)

    def test_decode_limit_is_checked_before_unbounded_expansion(self):
        with tempfile.TemporaryDirectory() as root:
            packed = gzip.compress(b"x" * 1000000, mtime=0)
            ev.exclusive_bytes(Path(root) / "bomb.gz", packed)
            identity = {"file": "bomb.gz", "gzip_bytes": len(packed), "gzip_sha256": ev.digest(packed),
                        "json_bytes": 10, "json_sha256": "0" * 64}
            with self.assertRaises(ValueError):
                ev.unpack_case(root, identity)
            for invalid in (True, -1, ev.MAX_CASE_BYTES + 1):
                with self.assertRaises(ValueError):
                    ev.unpack_case(root, {**identity, "json_bytes": invalid})

    def test_safe_case_paths(self):
        for bad in ("../escape", "/tmp/escape", "..", ".", "", "a\\b", True):
            with self.assertRaises(ValueError):
                ev.safe_name(bad)

    def test_full_schedule_is_serial_and_frozen(self):
        rows = ev.schedule()
        self.assertEqual(len(rows), 1536)
        self.assertEqual(len(set(rows)), 1536)
        self.assertEqual(rows, ev.schedule())
        self.assertEqual([r[2] for r in rows], [-1] * 384 + [0] * 384 + [1] * 384 + [2] * 384)

    def test_summary_full_cost_and_q1_do_not_hide_training_startup(self):
        summary = ev.summarize(fixture_records(), fixture_cold(), fixture_training())
        self.assertEqual(summary["decision"], "Q5_CONSTRUCTED_LP_SCALING_PASS_NOT_CROSS_DOMAIN")
        self.assertFalse(summary["global_q5_closed"])
        self.assertFalse(summary["cross_domain_pass"])
        cost = next(r for r in summary["case_costs"] if r["case_id"] == "q5_m32_w16_r0_base" and r["route"] == "EXPAND4_s100001")
        self.assertAlmostEqual(cost["complete_ms"], 2.05 + 0.1 + 0.012)
        self.assertAlmostEqual(cost["cold_q1_ms"], 1122.05)

    def test_failed_warmup_has_no_capability_ratio_or_dropped_slope(self):
        rows = fixture_records()
        failed = next(r for r in rows if r["route"] == "DIRECT" and r["repeat"] == -1
                      and r["case_id"] == "q5_m256_w32_r0_base")
        failed["accepted"] = False
        summary = ev.summarize(rows, fixture_cold(), fixture_training())
        self.assertEqual(summary["decision"], "Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED")
        cells = [r for r in summary["cells"] if r["rows"] == 256 and r["width_factor"] == 32 and not r["surface"]]
        self.assertTrue(all(r["ratio"] is None for r in cells))
        self.assertEqual(len(summary["slopes"]), 6)

    def test_missing_or_reordered_observation_blocks_summary(self):
        rows = fixture_records()
        for changed in (rows[:-1], list(reversed(rows)), rows + [rows[0]]):
            with self.assertRaises(ValueError):
                ev.summarize(changed, fixture_cold(), fixture_training())

    def test_no_lower_slope_claim_from_equal_exponents(self):
        rows = fixture_records()
        views = {s["id"]: s for s in ev.contract.planned_views()}
        for row in rows:
            if views[row["case_id"]]["width_factor"] != 1 and row["route"].startswith("EXPAND4"):
                row["total_ms"] = 2 * (views[row["case_id"]]["rows"] / 32) ** 3
                row["proposal_ms"] = 0.0
                row["post_ms"] = row["total_ms"]
        cold = {r: {"cold_start_ms": 0.0} for r in ev.ROUTES}
        training = {str(s): {"fit_ms": 0.0, "feature_setup_ms": 0.0} for s in ev.contract.SEEDS}
        summary = ev.summarize(rows, cold, training)
        self.assertEqual(summary["decision"], "Q5_SCALING_COST_PASS_SLOPE_UNRESOLVED")

    def test_one_null_control_failure_cannot_be_pooled_away(self):
        rows = fixture_records()
        for row in rows:
            if row["case_id"] == "q5_m32_w1_r0_base" and row["route"] == "EXPAND4_s100001":
                row["post_ms"] = 1000.0
                row["total_ms"] = 1000.05
        summary = ev.summarize(rows, fixture_cold(), fixture_training())
        self.assertEqual(summary["decision"], "Q5_SCALING_COST_GATE_FAIL")

    def test_native_ledger_missing_stages_and_hidden_work_rejected(self):
        base = native_result()
        with patch.object(replay, "certificate", return_value=True):
            replay.native_checked({}, base)
            for field in ("total_ms", "attempts", "ledger", "head_kind"):
                changed = copy.deepcopy(base)
                if field == "total_ms":
                    changed[field] = 1.0
                elif field == "attempts":
                    changed[field][0]["stages"].pop()
                elif field == "ledger":
                    changed[field]["native_run_calls"] = 0
                else:
                    changed[field] = "BASIS"
                with self.assertRaises(ValueError):
                    replay.native_checked({}, changed)

    def test_external_late_answer_is_retained_but_not_accepted(self):
        result = native_result()
        record = {"route": "DIRECT", "accepted": False, "total_ms": 5001.0, "worker_total_ms": 4.0,
                  "proposal_ms": 0.0, "post_ms": 5001.0, "transport_and_receipt_ms": 4997.0,
                  "execution": result, "ranking": None, "witness": result["attempts"][0]["witness"],
                  "error": None, "peak_rss_kib": 1}
        with patch.object(replay, "certificate", return_value=True):
            self.assertTrue(replay.validate_record({}, {}, record)["accounted"])
            with self.assertRaises(ValueError):
                replay.validate_record({}, {}, {**record, "accepted": True})

    def test_accepted_invalid_original_witness_is_rejected(self):
        with patch.object(replay, "certificate", return_value=False):
            with self.assertRaises(ValueError):
                replay.native_checked({}, native_result())

    def test_retry_after_success_is_not_authorized(self):
        class Matrix:
            shape = (2, 6)
        raw = {"A": Matrix()}
        attempts = [{"support_factor": f, "support_size": min(6, f * 2),
                     "result": {"accepted": True, "witness": {}, "total_ms": 1.0}} for f in (2, 4)]
        with patch.object(replay, "restricted_checked"):
            with self.assertRaises(ValueError):
                replay.expansion_checked(raw, {"attempts": attempts}, list(range(6)))

    def test_failed_attempts_and_fallback_all_charged(self):
        class Matrix:
            shape = (2, 6)
        attempts = [{"support_factor": f, "support_size": min(6, f * 2),
                     "result": {"accepted": False, "witness": None, "total_ms": 1.0}} for f in (2, 4)]
        execution = {"attempts": attempts, "fallback": {"accepted": False, "total_ms": 2.0}, "total_ms": 3.0}
        with patch.object(replay, "restricted_checked"), patch.object(replay, "native_checked"):
            with self.assertRaises(ValueError):
                replay.expansion_checked({"A": Matrix()}, execution, list(range(6)))

    def test_legacy_generator_grid_is_preserved(self):
        tree = ast.parse((ROOT / "neumann1" / "lp_basis_headroom_v082.py").read_text())
        assigned = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                    and n.targets[0].id in ("ROWS", "WIDTH_FACTORS")}
        self.assertEqual(assigned, {"ROWS": (32, 64, 128), "WIDTH_FACTORS": (1, 16)})
        functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(functions["generate_case"].body[0].value.func.id, "_generate_case")
        self.assertEqual(functions["generate_q5_case"].body[-1].value.func.id, "_generate_case")

    def test_failed_seed_audit_retained_before_scientific_import(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "first"
            with self.assertRaises(ValueError):
                registration.register(out, HEAD, collision_check_head="b" * 40)
            terminal = ev.read_events(out)[1]
            self.assertEqual(terminal["completed_views"], 0)
            self.assertEqual(terminal["status"], "registration_failed_no_reseed")

    def test_failed_input_pin_retained_without_observations(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "first"
            with self.assertRaises(FileNotFoundError):
                evaluator.evaluate(Path(root) / "unregistered", out, HEAD, "0" * 64)
            terminal = ev.read_events(out)[1]
            self.assertEqual(terminal["observations"], 0)
            self.assertEqual(terminal["status"], "evaluation_failed_no_replacement")

    def test_complete_fake_executor_retention_and_replay_roundtrip(self):
        # Full orchestration/1536 receipts, but NO actual LPs, workers, models,
        # timing study or numerical witnesses. Capability boundary is mocked.
        rows = fixture_records()
        training = fixture_training()
        environment = {"runtime": ev.RUNTIME, "hardware": {"fixture": True},
                       "threadpools": [{"num_threads": 1}], "openblas_coretype": "HASWELL"}
        cursor = iter(rows)
        class FakeWorker:
            def __init__(self, directory, route, output, shared_authority_ms):
                self.ready = {"ready": True, "route": route, "environment": environment,
                              "training_identity": training if route.startswith("EXPAND4") else None}
                self.cold = {"external_launch_ready_ms": 1000.0,
                             "shared_authority_preflight_ms": shared_authority_ms,
                             "cold_start_ms": 1000.0 + shared_authority_ms,
                             "first_observation": True, "ready": self.ready}
            def observe(self, case_id):
                row = next(cursor)
                if row["case_id"] != case_id:
                    raise AssertionError("fake schedule drift")
                return dict(row)
            def close(self):
                pass
        fake_threadpools = types.ModuleType("threadpoolctl")
        from contextlib import nullcontext
        fake_threadpools.threadpool_limits = lambda _: nullcontext()
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "sources"
            source.mkdir()
            ev.write_json(source / "manifest.json", {"fixture": True})
            source_pin = ev.digest((source / "manifest.json").read_bytes())
            source_identity = {"authority_gzip_sha256": "fixture", "training_identity": training}
            output = Path(root) / "results"
            with patch.dict(sys.modules, {"threadpoolctl": fake_threadpools}), \
                 patch.object(evaluator, "parent_authority", return_value=({"gzip_sha256": "fixture"}, training)), \
                 patch.object(evaluator, "preflight", return_value=environment), \
                 patch.object(evaluator, "load_registered", return_value=source_identity), \
                 patch.object(evaluator, "Worker", FakeWorker), \
                 patch.object(replay, "validate_records", side_effect=lambda directory, records: records):
                report = evaluator.evaluate(source, output, HEAD, source_pin)
            ledger, terminal = ev.read_events(output)
            self.assertEqual(terminal["status"], "completed")
            self.assertEqual(terminal["observations"], 1536)
            self.assertEqual(len(list(output.glob("observation_*.json.gz"))), 1536)
            self.assertFalse(report["global_q5_closed"])
            self.assertEqual(sum(r["kind"] == "query_start" for r in ledger), 1536)
            with patch.object(replay, "parent_authority", return_value=({}, training)), \
                 patch.object(replay, "validate_records", side_effect=lambda directory, records: records):
                retained = replay.replay(source, output)
            self.assertEqual(retained, report)


if __name__ == "__main__":
    unittest.main()
