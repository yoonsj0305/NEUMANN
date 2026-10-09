"""2026-10-09 Hybrid R0 clean-install and edge-budget release candidate acceptance.

Engineering-only: previously OPENED/public source, no new model, no G0/G1/G2.
The test source and outcomes are frozen before this script runs. No retries.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from statistics import median

import psutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/development/hybrid_r0_release_gate_20261009"
CLI = [sys.executable, "-m", "neumann1.hybrid_runtime_r0"]
R0_EDGE_RAM_BUDGET_BYTES = 4 * 1024**3
SUBPROCESS_TIMEOUT_S = 35.0
EXPECTED = {
    "lp_native": "VERIFIED",
    "lp_residual": "VERIFIED",
    "lp_external_reject_fallback": "VERIFIED",
    "exact_fraction": "VERIFIED",
    "exact_integer": "VERIFIED",
    "exact_singular": "UNKNOWN",
    "invalid_domain": "ERROR",
    "sygus_original": "VERIFIED",
    "sygus_bad_source": "ERROR",
}
ALLOWED_DOMAINS = ("lp.standard_form", "exact.linear", "sygus.invariant")


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def task_suite(sygus_source):
    A = [[1 if j % 2 == 0 else 0 for j in range(12)],
         [0 if j % 2 == 0 else 1 for j in range(12)]]
    base = {"domain": "lp.standard_form", "A": A, "b": [1, 1],
            "c": [0, 0] + [2 + j / 10 for j in range(2, 12)], "budget_s": 10}
    cases = {
        "lp_native": dict(base, policy="native"),
        "lp_residual": dict(base, policy="residual_fixed4m"),
        "lp_external_reject_fallback": dict(base, policy="external_ranking",
            ranking=[2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 10, 11]),
        "exact_fraction": {"domain": "exact.linear", "A": [[2, 0], [0, 3]],
                           "b": [1, 1]},
        "exact_integer": {"domain": "exact.linear", "A": [[1, 1], [1, -1]],
                          "b": [3, 1]},
        "exact_singular": {"domain": "exact.linear", "A": [[1, 1], [2, 2]],
                           "b": [3, 6]},
        "invalid_domain": {"domain": "unsupported.neural", "input": "test"},
        "sygus_original": {"domain": "sygus.invariant", "source": sygus_source,
                           "budget_s": 15},
        "sygus_bad_source": {"domain": "sygus.invariant",
                             "source": "(set-option :produce-models true)\n" + sygus_source,
                             "budget_s": 15}
    }
    assert set(cases) == set(EXPECTED)
    return cases


def sampled_process_tree_call(payload: str, *, jsonl: bool = False):
    args = CLI + (["--jsonl"] if jsonl else [])
    t0 = time.perf_counter_ns()
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, cwd=ROOT)
    root = psutil.Process(proc.pid)
    sampled_peak = 0
    sampled_count = 0
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(proc.communicate, payload)
        deadline = time.monotonic() + SUBPROCESS_TIMEOUT_S
        try:
            while not future.done():
                if time.monotonic() >= deadline:
                    proc.kill()
                    future.result(timeout=4)
                    raise RuntimeError("process tree timeout")
                try:
                    processes = [root] + root.children(recursive=True)
                    total = 0
                    for p in processes:
                        try:
                            total += p.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    sampled_peak = max(sampled_peak, total)
                    sampled_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                time.sleep(0.004)
            stdout, stderr = future.result()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            raise
    wall_ms = (time.perf_counter_ns() - t0) / 1e6
    if proc.returncode != 0:
        raise RuntimeError(f"CLI exit {proc.returncode}: {stderr[-1200:]}")
    if stderr.strip():
        raise RuntimeError(f"unexpected CLI stderr: {stderr[-1200:]}")
    lines = stdout.splitlines()
    expected_lines = len(payload.splitlines()) if jsonl else 1
    if len(lines) != expected_lines:
        raise RuntimeError(f"missing JSONL receipts: {len(lines)} vs {expected_lines}")
    parsed = [json.loads(x) for x in lines]
    return {"receipts": parsed, "outer_process_wall_ms": wall_ms,
            "sampled_process_tree_peak_rss_bytes": sampled_peak,
            "sample_count": sampled_count,
            "rss_sampling_note": "4 ms sampled maximum, lower bound, not exact all-time peak"}


def check_receipt(name, task, receipt):
    if receipt["status"] != EXPECTED[name]:
        raise AssertionError(f"{name}: unexpected {receipt['status']} expected {EXPECTED[name]}")
    if receipt["original_task_sha256"] != sha(task):
        raise AssertionError("original identity changed")
    if receipt["domain"] not in ALLOWED_DOMAINS and name != "invalid_domain":
        raise AssertionError("wrong domain")
    if receipt["learned_model_inference"] or receipt["cost"]["model_calls"] != 0:
        raise AssertionError("model-free engineering contract violated")
    if receipt["cost"]["frontier_calls"] != 0:
        raise AssertionError("unexpected remote reference model")
    if receipt["north_star_global_questions_closed"] != []:
        raise AssertionError("global question altered")
    if receipt["cost"]["observed_wall_ms"] <= 0:
        raise AssertionError("missing core wall receipt")
    stage_sum = sum(receipt["cost"]["stages_ms"].values())
    if abs(stage_sum - receipt["cost"]["observed_wall_ms"]) > .75:
        raise AssertionError("stage cost not closed to total wall")
    if name in ("lp_native", "lp_residual", "lp_external_reject_fallback"):
        if not any(x.get("kind") == "independent_original_lp_certificate"
                   and x.get("passed") for x in receipt["events"]):
            raise AssertionError("LP original cert not proved")
    if name.startswith("exact_") and receipt["status"] == "VERIFIED":
        if not any(x.get("kind") == "independent_exact_original_certificate"
                   and x.get("passed") for x in receipt["events"]):
            raise AssertionError("exact original full-system cert not proved")
    if name == "lp_external_reject_fallback":
        if not any(x.get("kind") == "certified_restricted_then_native"
                   and x.get("fallback") for x in receipt["events"]):
            raise AssertionError("no actual fallback path witnessed")
        if receipt["cost"]["external_structure_proposal_ms"] != "UNKNOWN":
            raise AssertionError("unpaid ranking improperly called free")
    if name == "sygus_original":
        proof = [x for x in receipt["events"]
                 if x.get("kind") == "independent_original_sygus_certificate"]
        if len(proof) != 1 or not proof[0]["passed"] or len(proof[0]["obligations"]) != 3:
            raise AssertionError("independent original-program certificate missing")
        if not all(x["smt_result"] == "unsat" for x in proof[0]["obligations"]):
            raise AssertionError("unproven SyGuS obligation")
    if receipt["status"] != "VERIFIED" and receipt["answer"] is not None:
        raise AssertionError("unverified answer escaped")


def run(source_path):
    raw_source = Path(source_path).read_bytes()
    source = raw_source.decode("utf-8")
    if "(inv-constraint inv-f pre-f trans-f post-f)" not in source:
        raise ValueError("expected exact official inv-constraint")
    cases = task_suite(source)
    original_source_sha256 = hashlib.sha256(raw_source).hexdigest()
    if len(cases) != 9:
        raise RuntimeError("frozen fixture count drift")
    observations = []
    for name, task in cases.items():
        attempt = sampled_process_tree_call(json.dumps(task, ensure_ascii=False))
        receipt = attempt["receipts"][0]
        check_receipt(name, task, receipt)
        observations.append({"name": name, "task_sha256": sha(task),
            "isolated_launch": {k: v for k, v in attempt.items() if k != "receipts"},
            "receipt": receipt})
        print(f"COLD {name}: {receipt['status']} {attempt['outer_process_wall_ms']:.3f}ms", flush=True)

    order = list(cases)
    session_payload = "\n".join(json.dumps(cases[x], ensure_ascii=False) for x in order) + "\n"
    persistent = sampled_process_tree_call(session_payload, jsonl=True)
    for name, receipt in zip(order, persistent["receipts"]):
        check_receipt(name, cases[name], receipt)
    all_observed_memory = [o["isolated_launch"]["sampled_process_tree_peak_rss_bytes"] for o in observations]
    all_observed_memory.append(persistent["sampled_process_tree_peak_rss_bytes"])
    measured_peak = max(all_observed_memory)
    # A 4GB sampled peak threshold is necessary for a provisional Edge CPU smoke,
    # but it is NOT an energy/thermal or strict peak guarantee.
    if not measured_peak or measured_peak >= R0_EDGE_RAM_BUDGET_BYTES:
        raise AssertionError(f"edge sampled RAM budget exceeded/unknown: {measured_peak}")
    if not all(x["receipt"]["status"] == EXPECTED[x["name"]] for x in observations):
        raise AssertionError("cold sample incomplete")
    summary = {
        "status": "HYBRID_R0_CLEAN_INSTALL_ENGINEERING_GATE_PASS",
        "classification": "ENGINEERING_OPENED_FIXTURES_ONLY",
        "source": "SyGuS-Org/benchmarks 2019 Inv_Track From2018/ex1.sl",
        "source_file_sha256": original_source_sha256,
        "sources_independent": 1, "engineering_tasks": 9, "cold_processes": 9,
        "persistent_processes": 1, "persistent_independent_task_receipts": 9,
        "domains": list(ALLOWED_DOMAINS), "fail_closed_count": 3,
        "full_original_certificates": 2*6,  # 3 LP + 2 exact + 1 SyGuS, cold and persistent
        "observed_max_sampled_process_tree_rss_mib": measured_peak / 1024**2,
        "edge_cpu_provisional_ram_limit_mib": R0_EDGE_RAM_BUDGET_BYTES / 1024**2,
        "energy_j": "UNKNOWN", "thermal": "UNKNOWN",
        "cloud_transport": "NOT_MEASURED",
        "frozen_model_checked_in_this_gate": False,
        "frozen_model_cold_warm_separate_archives": [
            "37897312107", "37897620753"],
        "full_r0_release_admitted": False,
        "scientific_g1_admitted": False, "new_model_training": False,
        "decision": "ENGINEERING_GATE_PASS_ONLY; R0 final still requires matched complete cost and release packaging",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "isolated_receipts": observations,
               "persistent_receipts": {k: v for k, v in persistent.items()}}
    (OUT / "first_run_receipts.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")
    print("HYBRID_R0_RELEASE_GATE=" + json.dumps(summary, sort_keys=True), flush=True)
    return summary


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: python -m experiments.hybrid_r0_release_gate_20261009 PATH_TO_FROZEN_ORIGINAL")
        run(sys.argv[1])
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "fatal.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        raise
