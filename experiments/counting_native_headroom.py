"""Bounded opened-input diagnostic using upstream D4/CPOG and exact Ganak.

No learned policy, new compiler, formal-checker replacement or G1 admission.
The process-group timeout pattern reuses the existing Synduce runner design.
"""
from fractions import Fraction
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import re
import signal
import statistics
import subprocess
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact_count(text, kind):
    patterns = {
        "ganak": r"^c s exact arb int\s+(\S+)\s*$",
        "d4": r"^s\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$",
        "cpog": r"Regular model count =\s*(\S+)",
    }
    if kind == "cpog" and "FULL-PROOF SUCCESS" not in text:
        return None
    values = re.findall(patterns[kind], text, re.MULTILINE)
    try:
        parsed = [Fraction(value) for value in values]
    except (ValueError, ZeroDivisionError):
        return None
    if not parsed or len(set(parsed)) != 1:
        return None
    answer = parsed[0]
    return answer if answer >= 0 and answer.denominator == 1 else None


def decision_summary(contract, rows):
    verified = [row for row in rows if row["status"] == "VERIFIED"]
    speeds = [row["native_over_free"] for row in verified]
    complete = len(verified) == len(contract["cases"])
    geometric = math.exp(statistics.mean(map(math.log, speeds))) if speeds else None
    fraction = sum(value >= 10 for value in speeds) / len(rows) if rows else 0
    bins = {}
    for label in ["variables_le_200", "variables_gt_200"]:
        selected = [row for row in rows if row["complexity_bin"] == label]
        valid = [row for row in selected if row["status"] == "VERIFIED"]
        bins[label] = {"registered": len(selected), "verified": len(valid),
                       "10x": sum(row["native_over_free"] >= 10 for row in valid)}
    headroom = complete and geometric >= 10 and fraction >= .8 and all(
        item["registered"] and item["10x"] / item["registered"] >= .8
        for item in bins.values())
    return {"status": "INCOMPLETE" if not complete else
            "PERFORMANCE_HEADROOM_DIAGNOSTIC_ONLY" if headroom else
            "NO_MEANINGFUL_HEADROOM_FOR_REGISTERED_FREE_CIRCUITS",
            "geomean_native_over_free_verified_subset": geometric,
            "geomean_is_complete_sample": complete,
            "10x_fraction_all_registered": fraction, "bins": bins,
            "headroom_screen_met": headroom,
            "G0_admission": "HOLD_FORMAL_CHECKER_AND_FULL_REUSE_CONTRACT",
            "G1_admitted": False, "learning_performed": False,
            "formal_checker": "INCOMPLETE_NO_FORMAL_CERTIFICATION",
            "same_circuit_reuse": "Native may use identical upstream circuit and counter; no extra warm advantage established",
            "warm_resident_cost": "UNKNOWN", "energy": "UNKNOWN",
            "peak_memory": "UNKNOWN", "FLOPs": "UNKNOWN",
            "complete_system_cost_advantage": "UNKNOWN",
            "fresh_evaluation_cases": 0}


def run(root, output, registration):
    contract_bytes = registration.read_bytes()
    contract = json.loads(contract_bytes)
    assert contract["kind"] == "G0_OPENED_NATIVE_COST_DIAGNOSTIC"
    assert contract["G1_automatic_admission"] is False
    assert contract["repeats"] == 3 and len(contract["cases"]) == 17
    assert digest(__file__) == contract["runner_sha256"], "Registered runner mismatch"
    assert os.name == "posix", "Linux-only upstream-tool harness"
    assert not output.exists(), "First result directory must not exist"
    source = root / "cpog"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == contract["cpog_commit"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root / "d4", text=True).strip() == contract["d4_commit"]
    for case in contract["cases"]:
        assert Path(case["file"]).name == case["file"]
        assert digest(source / "benchmarks" / case["file"]) == case["sha256"]
    ganak = root / "ganak-release" / "ganak"
    assert digest(ganak) == contract["ganak_binary_sha256"]
    binaries = {name: digest(path) for name, path in {
        "ganak": ganak, "d4": root / "d4" / "d4",
        "generator": source / "src" / "cpog-gen",
        "checker": source / "src" / "cpog-check"}.items()}
    output.mkdir(parents=True)
    (output / "preregister.json").write_bytes(contract_bytes)
    (output / "runtime-first.json").write_text(json.dumps({
        "binaries": binaries, "CPU": Path("/proc/cpuinfo").read_text(),
        "accelerator": "None", "learning": False}, indent=2))
    started = time.perf_counter()
    events = []
    rows = []

    def execute(label, command, cwd):
        remaining = contract["total_wall_budget_seconds"] - (time.perf_counter() - started)
        if remaining <= 0:
            event = {"label": label, "status": "NOT_RUN_TOTAL_BUDGET", "seconds": None, "value": None}
        else:
            timeout = min(remaining, contract["per_process_wall_seconds"])
            before = time.perf_counter()
            with (output / (label + ".log")).open("xb") as log:
                child = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                expired = False
                try:
                    child.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    expired = True
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
            seconds = time.perf_counter() - before
            text = (output / (label + ".log")).read_text(errors="replace")
            kind = "ganak" if label.startswith("ganak") else "d4" if label.startswith("direct") else "cpog" if label.startswith("free") else None
            value = exact_count(text, kind) if kind and not expired and child.returncode == 0 else None
            event = {"label": label, "command": command, "seconds": seconds,
                     "exit_code": child.returncode, "status": "TIMEOUT" if expired else "EXECUTED" if child.returncode == 0 else "EXECUTION_ERROR",
                     "value": str(value) if value is not None else None,
                     "log_sha256": digest(output / (label + ".log"))}
        events.append(event)
        (output / "events.json").write_text(json.dumps(events, indent=2))
        return event

    for index, case in enumerate(contract["cases"]):
        case_dir = output / f"case-{index:02}"
        case_dir.mkdir()
        cnf = source / "benchmarks" / case["file"]
        nnf = case_dir / "representation.nnf"
        proof = case_dir / "representation.cpog"
        compile_event = execute(f"compile-{index:02}", [str(root / "d4" / "d4"), "-dDNNF", str(cnf), "-out=" + str(nnf)], case_dir)
        generate_event = execute(f"generate-{index:02}", [str(source / "src" / "cpog-gen"), "-L", str(case_dir / "generator-internal.log"), str(cnf), str(nnf), str(proof)], case_dir) if compile_event["status"] == "EXECUTED" and nnf.is_file() else None
        receipts = {"ganak": [], "d4": [], "free": []}
        # Rotate direct/free order across repeats; no faster-result case selection.
        for repeat in range(3):
            order = ["ganak", "d4", "free"] if repeat % 2 == 0 else ["free", "d4", "ganak"]
            for method in order:
                if method == "free" and not (generate_event and generate_event["status"] == "EXECUTED" and proof.is_file()):
                    continue
                command = ([str(ganak), "--prob", "0", "--fast", "--mode", "0", str(cnf)] if method == "ganak" else
                           [str(root / "d4" / "d4"), "-mc", str(cnf)] if method == "d4" else
                           [str(source / "src" / "cpog-check"), str(cnf), str(proof)])
                receipt = execute(f"{method if method != 'd4' else 'direct'}-{index:02}-{repeat}", command, case_dir)
                receipts[method].append(receipt)
        values = [event["value"] for items in receipts.values() for event in items]
        valid = all(len(items) == 3 for items in receipts.values()) and all(value is not None for value in values) and len(set(values)) == 1
        medians = {name: statistics.median(event["seconds"] for event in items) if len(items) == 3 and all(event["value"] is not None for event in items) else None for name, items in receipts.items()}
        row = {**case, "status": "VERIFIED" if valid else "INCOMPLETE",
               "medians_seconds": medians, "exact_value": values[0] if valid else None,
               "generation_seconds": generate_event["seconds"] if generate_event else None,
               "compilation_seconds": compile_event["seconds"],
               "native_over_free": min(medians["ganak"], medians["d4"]) / medians["free"] if valid else None,
               "nnf_sha256": digest(nnf) if nnf.is_file() else None,
               "certificate_sha256": digest(proof) if proof.is_file() else None}
        rows.append(row)
        (output / "cases-first.json").write_text(json.dumps(rows, indent=2))
        print(json.dumps({key: row[key] for key in ["file", "status", "medians_seconds", "native_over_free"]}), flush=True)
    report = {**decision_summary(contract, rows), "cases": rows,
              "whole_diagnostic_seconds": time.perf_counter() - started,
              "registration_sha256": hashlib.sha256(contract_bytes).hexdigest(),
              "all_attempt_cost_seconds": sum(event["seconds"] or 0 for event in events),
              "process_events": len(events)}
    (output / "report-first.json").write_text(json.dumps(report, indent=2))
    manifest = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob("*")) if path.is_file()}
    (output / "manifest-first.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registration", type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.output.resolve(), args.registration.resolve())
