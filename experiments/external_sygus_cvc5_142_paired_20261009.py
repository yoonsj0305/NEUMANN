"""Paired source-pinned external SyGuS native CPU reference experiment.

No new NEUMANN proposer/model, no fresh holdout, no changes to original goals.
A prior technical failure and corrected native-first run remain separate.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from experiments.external_sygus_native_g0_20261009 import (
    convert_legacy_sygus, independent_check, sha_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "research/development/external_sygus_cvc5_142_paired_20261009"
REGISTERED = ROOT / "docs/experiments/external_sygus_cvc5_142_paired_20261009.preregister.json"
FIRST = ROOT / "docs/experiments/external_sygus_native_g0_20261009.preregister.json"


def version(binary):
    p = subprocess.run([binary, "--version"], text=True, capture_output=True, timeout=6)
    if p.returncode:
        raise RuntimeError("version command failed: " + str(binary))
    m = re.search(r"This is cvc5 version ([0-9]+\.[0-9]+\.[0-9]+)", p.stdout)
    if m is None:
        raise RuntimeError("unparseable cvc5 version: " + p.stdout[:200])
    return m.group(1)


def runner():
    frozen_bytes = REGISTERED.read_bytes()
    contract = json.loads(frozen_bytes)
    first = json.loads(FIRST.read_text())
    if contract["schema"] != "neumann.external-sygus-cvc5-142-paired.v1":
        raise RuntimeError("invalid frozen schema")
    if contract["source_commit"] != first["upstream"]["sha"]:
        raise RuntimeError("external source SHA drift")
    if contract["execution"]["task_timeout_seconds"] != 15 or contract["execution"]["repeats"] != 3:
        raise RuntimeError("research protocol changed")

    upstream = ROOT / "third_party/sygus_benchmarks"
    head = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
    if head != contract["source_commit"]:
        raise RuntimeError("external repo commit drift")

    bin_paths = {"APT_OLD": "/usr/bin/cvc5", "RELEASE_142": "/tmp/cvc5_142"}
    binaries = {spec["id"]: {"binary": bin_paths[spec["id"]],
                              "declared_version": spec["version"],
                              "actual_version": version(bin_paths[spec["id"]])}
                for spec in contract["solvers"]}
    for entry in binaries.values():
        if entry["declared_version"] != entry["actual_version"]:
            raise RuntimeError("binary version drift")

    prepared = {}
    translation_work_ns = 0
    for path in first["selected_sources"]:
        src = upstream / path
        begin = time.perf_counter_ns()
        original = src.read_bytes()
        converted, ndecl = convert_legacy_sygus(original.decode())
        translation_work_ns += time.perf_counter_ns() - begin
        prepared[path] = {
            "original_sha256": sha_bytes(original),
            "original_bytes": len(original),
            "converted_sha256": sha_bytes(converted.encode()),
            "legacy_primed_declarations": ndecl,
            "converted": converted,
        }
    DEST.mkdir(parents=True, exist_ok=True)
    input_dir = DEST / "converted_inputs"
    input_dir.mkdir(exist_ok=True)
    file_map = {}
    for i, (path, entry) in enumerate(prepared.items()):
        dst = input_dir / f"{i:02d}.sygus"
        dst.write_text(entry["converted"])
        file_map[path] = dst

    import z3
    records = []
    orders = []
    for repeat in range(contract["execution"]["repeats"]):
        order = [(path, solver["id"]) for path in prepared for solver in contract["solvers"]]
        random.Random(contract["execution"]["shuffle_seed"] + repeat).shuffle(order)
        orders.append([{"source": p, "solver": b} for p, b in order])
        for path, solver in order:
            binary = bin_paths[solver]
            stamp = time.perf_counter_ns()
            timed_out = False
            ret = None
            stdout = ""
            stderr = ""
            try:
                proc = subprocess.run([binary, "--sygus", "--lang=sygus2", str(file_map[path])],
                                      text=True, capture_output=True,
                                      timeout=contract["execution"]["task_timeout_seconds"])
                ret, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                stdout = ((exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes)
                          else (exc.stdout or ""))
                stderr = ((exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes)
                          else (exc.stderr or ""))
            solver_wall_ms = (time.perf_counter_ns() - stamp) / 1e6

            check_begin = time.perf_counter_ns()
            if timed_out:
                check = {"status": "TIMEOUT", "obligations": []}
            elif ret != 0:
                check = {"status": "SOLVER_ERROR", "obligations": []}
            else:
                try:
                    check = independent_check(prepared[path]["converted"], stdout)
                except Exception as exc:
                    check = {"status": "VERIFIER_ERROR", "obligations": [],
                             "error": f"{type(exc).__name__}: {exc}"[:500]}
            verification_ms = (time.perf_counter_ns() - check_begin) / 1e6
            receipt = {
                "source": path, "solver": solver, "repeat": repeat,
                "source_sha256": prepared[path]["original_sha256"],
                "converted_sha256": prepared[path]["converted_sha256"],
                "solver_exit_code": ret, "solver_timeout": timed_out,
                "solver_wall_ms": solver_wall_ms,
                "independent_verification_ms": verification_ms,
                "solver_plus_verifier_ms": solver_wall_ms + verification_ms,
                "result": check,
                "stdout_sha256": sha_bytes(stdout.encode()),
                "stdout": stdout[:40000], "stderr": stderr[:10000],
            }
            records.append(receipt)
            print("CASE=" + json.dumps({"source": path, "solver": solver, "repeat": repeat,
                  "solver_ms": round(solver_wall_ms, 2), "outcome": check["status"]}), flush=True)

    summary = {}
    all_routes = [s["id"] for s in contract["solvers"]]
    for solver in all_routes:
        selection = [r for r in records if r["solver"] == solver]
        grouped = defaultdict(list)
        for r in selection:
            grouped[r["source"]].append(r)
        medians = {}
        for name, sample in grouped.items():
            if len(sample) != contract["execution"]["repeats"]:
                raise RuntimeError(f"missing repeats: {solver} {name}")
            medians[name] = {
                "solver_ms": median(x["solver_wall_ms"] for x in sample),
                "solver_plus_verifier_ms": median(x["solver_plus_verifier_ms"] for x in sample),
                "accepted_repeats": sum(x["result"]["status"] == "VERIFIED_ALL_THREE" for x in sample),
                "outcomes": dict(Counter(x["result"]["status"] for x in sample)),
            }
        summary[solver] = {
            "repeat_outcomes": dict(Counter(x["result"]["status"] for x in selection)),
            "verified_all_repeats_sources": sum(x["accepted_repeats"] == contract["execution"]["repeats"] for x in medians.values()),
            "case_medians": medians,
        }

    pair = {}
    for path in first["selected_sources"]:
        older = summary["APT_OLD"]["case_medians"][path]
        newer = summary["RELEASE_142"]["case_medians"][path]
        full = older["accepted_repeats"] == 3 and newer["accepted_repeats"] == 3
        pair[path] = {
            "both_verified_3_of_3": full,
            "old_solver_median_ms": older["solver_ms"],
            "new_solver_median_ms": newer["solver_ms"],
            "old_verifier_included_ms": older["solver_plus_verifier_ms"],
            "new_verifier_included_ms": newer["solver_plus_verifier_ms"],
            "old_over_new_solver_ratio_if_both_verified": (
                older["solver_ms"]/newer["solver_ms"] if full else None),
            "old_over_new_paid_ratio_if_both_verified": (
                older["solver_plus_verifier_ms"]/newer["solver_plus_verifier_ms"] if full else None),
        }

    info = {
        "status": "COMPLETED_OPENED_NATIVE_PAIRED",
        "contract_sha256": sha_bytes(frozen_bytes),
        "source_sha": head,
        "independent_source_files": len(prepared),
        "scientific_records": len(records),
        "binaries": binaries,
        "translation_preparation_ms": translation_work_ns/1e6,
        "native": summary, "pairwise": pair,
        "repeats": contract["execution"]["repeats"],
        "technical_attempt_reference": contract["historical_first_technical"],
        "earlier_first_evaluable_reference": contract["historical_first_actual"],
        "unknowns": ["memory","energy","money","training","external independent reproduction"],
        "decision": "HOLD_LEARNING; STRONG_NATIVE_REFERENCE_ONLY; NO_NEUMANN_HEADROOM_CLAIM",
    }
    (DEST / "summary.json").write_text(json.dumps(info, indent=2, sort_keys=True)+"\n")
    (DEST / "first_paired_receipts.json").write_text(json.dumps(
        {"summary": info, "records": records, "orders": orders}, indent=2, sort_keys=True)+"\n")
    print("PAIRED_NATIVE_SUMMARY="+json.dumps({
        "status": info["status"], "counts": {s: summary[s]["repeat_outcomes"] for s in all_routes},
        "verified_sources": {s: summary[s]["verified_all_repeats_sources"] for s in all_routes},
        "pairwise": pair}, sort_keys=True), flush=True)
    return info


if __name__ == "__main__":
    try:
        runner()
    except Exception as exc:
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / "fatal.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        raise
