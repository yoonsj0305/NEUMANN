"""First actual opened P1.4 semantic-development study on the frozen T4 core."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
import re
import subprocess
from time import perf_counter_ns
import traceback

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import manifest as p1_manifest, validate_identity
from neumann1.control_plane_p13 import FrozenFullS4Fallback
from neumann1.control_plane_p14 import (
    Budget, FrozenSemanticCompiler, contract, interpret_and_execute, run_mixed_and_execute,
)
from neumann1.general_runtime_v106 import _csp, _rational, verify_original
from experiments.control_plane_p1_first import write_new
from experiments.control_plane_p14_registration import registration

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "docs/experiments/control_plane_p14_references.json"
IDS = tuple("p14d_%02d" % i for i in range(1, 13))
GATE = {
    "raw_semantic_accepted_min": 6,
    "raw_math_accepted_min": 3,
    "raw_csp_accepted_min": 3,
    "mixed_fallback_accepted_min": 3,
    "raw_model_calls_exact": 8,
    "mixed_fallback_calls_exact": 4,
    "semantic_retries": 0,
    "per_item_wall_ms": 180000.0,
    "whole_study_wall_ms": 1800000.0,
}


def _hidden_verifier(ref):
    if ref["family"] == "math_logic":
        exact = Fraction(ref["private"]["exact"])
        return lambda _original, answer: _fraction_equal(answer, exact)
    private = ref["private"]
    task = {
        "id": ref["task_id"],
        "family": "constraint_planning",
        "instruction": "hidden original checker",
        "public": {
            "domains": private["domains"],
            "constraints": private["constraints"],
        },
    }
    return lambda _original, answer: verify_original(task, answer, {}, 2000)


def _fraction_equal(answer, exact):
    try:
        return Fraction(str(answer)) == exact
    except Exception:
        return False


def _executor(route, project):
    if route == "ARITHMETIC":
        return _rational(project["expression"], project["bindings"])
    if route == "CSP":
        result = _csp({"domains": project["domains"], "constraints": project["constraints"]}, "mrv")
        if result.get("assignment") is None:
            raise ValueError("CSP specialist found no assignment")
        return result["assignment"]
    raise ValueError("P1.4 specialist executor outside registered scope")


def evaluate(records, references, core_unchanged, complete, whole_ms):
    boundary = {
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
        "development_only": True,
        "fresh_validation_registered": False,
    }
    if complete is not True or tuple(r.get("task_id") for r in records) != IDS:
        return {**boundary, "verdict": "NOT_EVALUATED", "reason": "INCOMPLETE_OR_COVERAGE_DRIFT"}
    if tuple(r.get("task_id") for r in references) != IDS or core_unchanged is not True:
        return {**boundary, "verdict": "NOT_EVALUATED", "reason": "REFERENCE_OR_CORE_IDENTITY_DRIFT"}
    if finite(whole_ms, True) > GATE["whole_study_wall_ms"]:
        return {**boundary, "verdict": "FAIL", "reason": "COMPLETE_COST_WALL_CAP"}

    raw = records[:8]
    mixed = records[8:]
    if any(finite(r["complete_ms"], True) > GATE["per_item_wall_ms"] for r in records):
        return {**boundary, "verdict": "FAIL", "reason": "TASK_WALL_CAP"}
    if any(r.get("accounting_complete") is not True for r in raw):
        return {**boundary, "verdict": "FAIL", "reason": "RAW_ACCOUNTING_INCOMPLETE"}

    raw_model_calls = sum(r.get("model_calls", 0) for r in raw)
    fallback_calls = sum((r.get("routing") or {}).get("fallback_calls", 0) for r in mixed)
    if raw_model_calls != GATE["raw_model_calls_exact"] or fallback_calls != GATE["mixed_fallback_calls_exact"]:
        return {**boundary, "verdict": "FAIL", "reason": "SEMANTIC_WORK_ACCOUNTING_DRIFT"}

    raw_accept = sum(bool(r["accepted"]) for r in raw)
    raw_math = sum(bool(r["accepted"]) for r in raw[:4])
    raw_csp = sum(bool(r["accepted"]) for r in raw[4:8])
    mixed_accept = sum(bool(r["accepted"]) for r in mixed)
    mixed_route_match = sum(r.get("selected_route") == ref["expected_route"]
                            for r, ref in zip(mixed, references[8:]))

    diagnostics = {
        "raw_semantic_accepted": raw_accept,
        "raw_math_accepted": raw_math,
        "raw_csp_accepted": raw_csp,
        "mixed_fallback_accepted": mixed_accept,
        "mixed_expected_route_matches": mixed_route_match,
        "raw_model_calls": raw_model_calls,
        "mixed_fallback_calls": fallback_calls,
    }
    okay = (
        raw_accept >= GATE["raw_semantic_accepted_min"]
        and raw_math >= GATE["raw_math_accepted_min"]
        and raw_csp >= GATE["raw_csp_accepted_min"]
        and mixed_accept >= GATE["mixed_fallback_accepted_min"]
    )
    return {
        **boundary,
        **diagnostics,
        "verdict": "PASS" if okay else "FAIL",
        "reason": "OPENED_SEMANTIC_PATH_DIAGNOSTIC_ONLY" if okay else "SEMANTIC_PATH_CAPABILITY_FAILURE",
        "next": "FREEZE_P14_THEN_REGISTER_NEW_FRESH_SEMANTIC_VALIDATION"
                if okay else "PRESERVE_FIRST_P14_FAILURE_AND_DIAGNOSE",
    }


def run(directory, frozen_head):
    if not re.fullmatch(r"[0-9a-f]{40}", frozen_head):
        raise ValueError("exact P1.4 frozen source head required")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns()
    elapsed = lambda: (perf_counter_ns() - began) / 1e6
    records = []
    core = None
    audit = {}
    error = None
    write_new(directory / "study_started.json", {
        "schema": contract()["schema"],
        "frozen_head": frozen_head,
        "first_only": True,
        "development_only": True,
    })
    try:
        reg, rows, refs = registration()
        if tuple(r["task_id"] for r in rows) != IDS or tuple(r["task_id"] for r in refs) != IDS:
            raise ValueError("exact P1.4 opened coverage required")
        write_new(directory / "manifest.json", {
            "registration": reg,
            "public_rows": rows,
            "frozen_head": frozen_head,
        })
        if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != frozen_head:
            raise ValueError("exact frozen P1.4 source commit required")
        subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=ROOT, check=True, capture_output=True)
        for package, expected in p1_manifest()["runtime"].items():
            if version(package) != expected:
                raise ValueError("original runtime mismatch: " + package)

        from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
        core = FrozenAcceleratorCore()
        validate_identity(core.identity)
        identity = snapshot(core.identity)
        write_new(directory / "core.json", identity)

        compiler = FrozenSemanticCompiler(core)
        for i, (row, ref) in enumerate(zip(rows[:8], refs[:8])):
            write_new(directory / ("task_%02d_started.json" % i), {
                "task_id": row["task_id"],
                "view_sha256": digest(row["view"]),
            })
            record = interpret_and_execute(
                row["view"], compiler, _executor, _hidden_verifier(ref)
            )
            record["task_id"] = row["task_id"]
            record["kind"] = ref["kind"]
            records.append(record)
            write_new(directory / ("task_%02d.json" % i), record)
            print(canonical({
                "task_id": row["task_id"],
                "status": record["status"],
                "accepted": record["accepted"],
                "route": record.get("selected_route"),
            }), flush=True)
            if elapsed() > GATE["whole_study_wall_ms"]:
                raise TimeoutError("P1.4 complete study deadline")

        # Generation is no longer needed after all raw items. The P1.3 fallback
        # now forbids generation and reuses the same audited frozen core.
        fallback = FrozenFullS4Fallback(core)
        for i, (row, ref) in enumerate(zip(rows[8:], refs[8:]), start=8):
            write_new(directory / ("task_%02d_started.json" % i), {
                "task_id": row["task_id"],
                "view_sha256": digest(row["view"]),
            })
            record = run_mixed_and_execute(
                row["view"], lambda: fallback, _executor, _hidden_verifier(ref)
            )
            record["task_id"] = row["task_id"]
            record["kind"] = ref["kind"]
            records.append(record)
            write_new(directory / ("task_%02d.json" % i), record)
            print(canonical({
                "task_id": row["task_id"],
                "status": record["status"],
                "accepted": record["accepted"],
                "route": record.get("selected_route"),
            }), flush=True)
            if elapsed() > GATE["whole_study_wall_ms"]:
                raise TimeoutError("P1.4 complete study deadline")
        audit = core.audit()
        if core.identity != identity:
            audit["unchanged"] = False
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}

    if core is not None and not audit:
        try:
            audit = core.audit()
        except Exception as exc:
            audit = {"unchanged": False, "error": str(exc)}

    reg, rows, refs = registration()
    complete = error is None and len(records) == 12
    whole = elapsed()
    decision = evaluate(records, refs if complete else [], audit.get("unchanged"), complete, whole)
    report = {
        "schema": contract()["schema"],
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "decision": decision,
        "source_head": frozen_head,
        "observations": len(records),
        "whole_study_ms": whole,
        "startup_ms": getattr(core, "startup_ms", None) if core is not None else None,
        "core_audit": audit,
        "accounting_complete": complete,
        "generated_calls": sum(r.get("model_calls", 0) for r in records[:8]),
        "tool_calls": sum(r.get("tool_calls", 0) for r in records[:8])
                      + sum(int(bool(r.get("executed"))) for r in records[8:]),
        "fallback_calls": sum((r.get("routing") or {}).get("fallback_calls", 0) for r in records[8:]),
        "frontier_calls": 0,
        "new_training": False,
        "sealed_data_opened": False,
        "development_only": True,
        "historical_score_reuse": False,
        "error": error,
        "energy_j": None,
        "flops": None,
        "cost_money": None,
    }
    write_new(directory / "report.json", report)
    pins = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.glob("*.json"))
    }
    write_new(directory / "terminal.json", {
        "files": pins,
        "complete": complete,
        "no_replacement": True,
        "decision": decision["verdict"],
        "development_only": True,
    })
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory")
    parser.add_argument("--frozen-head")
    args = parser.parse_args()
    if not args.directory or not args.frozen_head:
        parser.error("first P1.4 run requires directory and frozen-head")
    result = run(args.directory, args.frozen_head)
    print(canonical(result))
    raise SystemExit(0 if result["decision"]["verdict"] == "PASS" else 2)
