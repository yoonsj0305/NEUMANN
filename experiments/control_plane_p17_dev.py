"""Exclusive first P1.7 opened source-bound development study.

Eight unique obligations exercise the zero-neural path. Four prospectively
registered pronoun-binding obligations exercise the frozen non-generative
full-S4 selector. This diagnostic never admits P2.
"""
import argparse
import hashlib
from importlib.metadata import version
from pathlib import Path
import re
import subprocess
from time import perf_counter_ns
import traceback

from neumann1.control_plane_v1 import canonical, finite, snapshot, digest
from neumann1.control_plane_p1_contract import manifest as p1_manifest, validate_identity
from neumann1.control_plane_p17 import (
    FrozenEvidenceSelector, interpret_and_execute,
)
from experiments.control_plane_p1_first import write_new
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p17_registration import registration, GATE, BOUNDARY, ROOT

IDS = tuple("p17d_%02d" % i for i in range(1, 13))
UNIQUE_IDS = IDS[:8]
AMBIGUOUS_IDS = IDS[8:]


def totals(records):
    keys = (
        "model_calls", "neural_forward_calls", "generated_calls",
        "evaluated_tokens", "padded_tokens", "tool_calls", "verifier_calls",
    )
    out = {}
    for key in keys:
        values = [r.get(key) for r in records]
        out[key] = sum(values) if all(type(v) is int and v >= 0 for v in values) else None
    return out


def _sum_known(records, key):
    values = [r.get(key) for r in records]
    return sum(values) if all(type(v) is int and v >= 0 for v in values) else None


def evaluate(records, references, core_unchanged, complete, whole_ms):
    def verdict(value, reason, **extra):
        return {**BOUNDARY, "verdict": value, "reason": reason, **extra}

    if complete is not True or tuple(r.get("task_id") for r in records) != IDS:
        return verdict("NOT_EVALUATED", "INCOMPLETE_OR_COVERAGE_DRIFT")
    if tuple(r.get("task_id") for r in references) != IDS or core_unchanged is not True:
        return verdict("NOT_EVALUATED", "REFERENCE_OR_CORE_IDENTITY_DRIFT")
    if finite(whole_ms, True) > GATE["whole_study_wall_ms"]:
        return verdict("FAIL", "COMPLETE_COST_WALL_CAP")
    if any(finite(r.get("complete_ms"), True) > GATE["per_item_wall_ms"] for r in records):
        return verdict("FAIL", "TASK_WALL_CAP")

    unique = records[:8]
    ambiguous = records[8:]
    try:
        for record, ref in zip(records, references):
            if record.get("accounting_complete") is not True:
                raise ValueError("incomplete item accounting")
            if type(record.get("accepted")) is not bool:
                raise ValueError("boolean acceptance required")
            for key in (
                "model_calls", "neural_forward_calls", "generated_calls",
                "evaluated_tokens", "padded_tokens", "tool_calls", "verifier_calls",
            ):
                if type(record.get(key)) is not int or record[key] < 0:
                    raise ValueError("complete nonnegative cost ledger required")
            for key in (
                "extraction_ms", "selection_ms", "compile_ms", "routing_ms",
                "execution_ms", "verification_ms", "complete_ms",
            ):
                finite(record.get(key), True)
            if record.get("selected_route") != ref["expected_route"] and record.get("executed"):
                raise ValueError("executed route drift")
    except Exception:
        return verdict("FAIL", "CONTROL_WORK_ACCOUNTING_FAILURE")

    path = {
        "unique_model_calls": _sum_known(unique, "model_calls"),
        "ambiguous_model_calls": _sum_known(ambiguous, "model_calls"),
        "unique_neural_forward_calls": _sum_known(unique, "neural_forward_calls"),
        "ambiguous_neural_forward_calls": _sum_known(ambiguous, "neural_forward_calls"),
        "generated_calls": _sum_known(records, "generated_calls"),
    }
    if (
        path["unique_model_calls"] != GATE["unique_model_calls_exact"]
        or path["ambiguous_model_calls"] != GATE["ambiguous_model_calls_exact"]
        or path["unique_neural_forward_calls"] != GATE["unique_neural_forward_calls_exact"]
        or path["ambiguous_neural_forward_calls"] != GATE["ambiguous_neural_forward_calls_exact"]
        or path["generated_calls"] != GATE["generated_calls_exact"]
    ):
        return verdict("FAIL", "CONTROL_PATH_COST_DRIFT", path_cost=path, cost_totals=totals(records))

    for record in unique:
        if record.get("selection") != "UNIQUE_COMPLETE_BOUNDED_GRAMMAR":
            return verdict("FAIL", "UNIQUE_ZERO_NEURAL_PATH_DRIFT", path_cost=path, cost_totals=totals(records))
        if record.get("selector_receipt") is not None:
            return verdict("FAIL", "UNIQUE_SELECTOR_CONSTRUCTION_DRIFT", path_cost=path, cost_totals=totals(records))
    for record in ambiguous:
        if record.get("selection") != "MASKED_FULL_S4_CANDIDATE":
            return verdict("FAIL", "AMBIGUOUS_SELECTION_PATH_DRIFT", path_cost=path, cost_totals=totals(records))
        receipt = record.get("selector_receipt")
        if type(receipt) is not dict or receipt.get("status") != "COMPLETE":
            return verdict("FAIL", "AMBIGUOUS_SELECTOR_RECEIPT_INCOMPLETE", path_cost=path, cost_totals=totals(records))

    counts = {
        "accepted": sum(r["accepted"] for r in records),
        "unique_accepted": sum(r["accepted"] for r in unique),
        "ambiguous_accepted": sum(r["accepted"] for r in ambiguous),
        "path_cost": path,
        "cost_totals": totals(records),
    }
    capability = (
        counts["accepted"] >= GATE["overall_accepted_min"]
        and counts["unique_accepted"] == GATE["unique_accepted_exact"]
        and counts["ambiguous_accepted"] >= GATE["ambiguous_accepted_min"]
    )
    return verdict(
        "PASS" if capability else "FAIL",
        "OPENED_SOURCE_BOUND_DIAGNOSTIC_ONLY" if capability else "SEMANTIC_SELECTION_CAPABILITY_FAILURE",
        **counts,
        next=(
            "FREEZE_P17_THEN_REGISTER_NEW_FRESH_SEMANTIC_VALIDATION"
            if capability else "RETAIN_FIRST_P17_FAILURE_AND_DIAGNOSE"
        ),
    )


class LazyFrozenSelector:
    """Construct the frozen core once, only when the first ambiguous item asks."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.attempted = False
        self.core = None
        self.selector = None
        self.error = None
        self.identity = None

    def get(self):
        if self.attempted:
            if self.error is not None:
                raise RuntimeError("frozen selector startup previously failed; no retry") from self.error
            return self.selector
        self.attempted = True
        try:
            from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
            self.core = FrozenAcceleratorCore()
            validate_identity(self.core.identity)
            self.identity = snapshot(self.core.identity)
            write_new(self.directory / "core.json", self.identity)
            self.selector = FrozenEvidenceSelector(self.core)
            return self.selector
        except Exception as exc:
            self.error = exc
            raise


def run(directory, frozen_head):
    if not re.fullmatch(r"[0-9a-f]{40}", frozen_head):
        raise ValueError("exact frozen P1.7 source required")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns()
    elapsed = lambda: (perf_counter_ns() - began) / 1e6

    records = []
    refs = []
    reg = None
    error = None
    audit = {}
    lazy = LazyFrozenSelector(directory)

    write_new(directory / "study_started.json", {
        "schema": "neumann.control-plane-p1.7-development.v1",
        "frozen_head": frozen_head,
        "first_only": True,
        **BOUNDARY,
    })

    try:
        reg, rows, refs = registration()
        write_new(directory / "manifest.json", {
            "registration": reg,
            "public_rows": rows,
            "frozen_head": frozen_head,
        })
        if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != frozen_head:
            raise ValueError("exact frozen P1.7 source commit required")
        subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=ROOT, check=True, capture_output=True)
        for package, expected in p1_manifest()["runtime"].items():
            if version(package) != expected:
                raise ValueError("original runtime mismatch: " + package)

        for i, (row, ref) in enumerate(zip(rows, refs)):
            write_new(directory / ("task_%02d_started.json" % i), {
                "task_id": row["task_id"],
                "view_sha256": digest(row["view"]),
            })
            record = interpret_and_execute(
                row["view"],
                _executor,
                _hidden_verifier(ref),
                lazy.get,
            )
            record.update(
                task_id=row["task_id"],
                kind=ref["kind"],
                semantic_path=ref["semantic_path"],
            )
            records.append(record)
            write_new(directory / ("task_%02d.json" % i), record)
            print(canonical({
                k: record.get(k)
                for k in (
                    "task_id", "semantic_path", "status", "accepted",
                    "selected_candidate", "selected_route", "model_calls",
                    "neural_forward_calls", "accounting_complete",
                )
            }), flush=True)
            if elapsed() > GATE["whole_study_wall_ms"]:
                raise TimeoutError("P1.7 study wall deadline")

        if lazy.core is None:
            raise ValueError("registered ambiguous stratum did not construct frozen selector")
        audit = lazy.core.audit()
        if lazy.core.identity != lazy.identity:
            audit["unchanged"] = False
    except Exception as exc:
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }

    if lazy.core is not None and not audit:
        try:
            audit = lazy.core.audit()
            if lazy.identity is not None and lazy.core.identity != lazy.identity:
                audit["unchanged"] = False
        except Exception as exc:
            audit = {"unchanged": False, "error": str(exc)}

    complete = error is None and len(records) == len(IDS)
    whole = elapsed()
    decision = evaluate(records, refs, audit.get("unchanged"), complete, whole)
    report = {
        "schema": "neumann.control-plane-p1.7-development.v1",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "decision": decision,
        "source_head": frozen_head,
        "observations": len(records),
        "whole_study_ms": whole,
        "startup_ms": getattr(lazy.core, "startup_ms", None),
        "selector_startup_attempted": lazy.attempted,
        "core_audit": audit,
        "accounting_complete": complete and all(r.get("accounting_complete") is True for r in records),
        "cost_totals": totals(records),
        "fallback_calls": 0,
        "frontier_calls": 0,
        "new_training": False,
        "sealed_data_opened": False,
        "historical_score_reuse": False,
        **BOUNDARY,
        "error": error,
        "energy_j": None,
        "flops": None,
        "cost_money": None,
        "timing_scope": (
            "study includes registration/source/runtime checks, all deterministic unique items, "
            "lazy core startup, ambiguous scoring, specialists, original verification and final audit; "
            "excludes Python imports/bootstrap/setup/final serialization/packaging/replay"
        ),
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
        **BOUNDARY,
    })
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    result = run(args.directory, args.frozen_head)
    print(canonical(result))
    raise SystemExit(0 if result["decision"]["verdict"] == "PASS" else 2)
