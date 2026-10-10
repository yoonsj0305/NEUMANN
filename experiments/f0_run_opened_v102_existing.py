"""Reuse v102 first-archive original LPs as OPENED engineering cost controls.

No new corpus, fitting, frontier model or oracle use. The original 2026 v102
holdout became OPENED after first use; NEVER report this as fresh evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import geometric_mean

from experiments.lp_expand4_holdout_register_v102 import load_registered
from neumann1 import lp_portfolio_v084 as storage
from neumann1.f0_capture_local import capture_opened_locals
from neumann1.f0_opened_bridge import SCHEMA, ROLES, validate_manifest
from neumann1.hybrid_runtime_r0 import (MAX_INPUT_BYTES, canonical, digest,
                                        source_problem_payload, validate_task)

REGISTRY = "docs/experiments/results/v102_fresh_sources.manifest.json"
CLASSIFICATION = "HISTORICAL_OPENED_ENGINEERING_DIAGNOSTIC_NOT_FRESH"


def registered_manifest() -> dict:
    _, archive = load_registered(REGISTRY)  # Existing SHA-pinned gzip + JSON verification.
    originals = sorted((s for s in archive["sources"]
                        if s["rows"] == 64 and s["id"].endswith("_base")),
                       key=lambda s: s["id"])
    chosen = originals[:2]  # Freeze BEFORE execution. Never choose based on results.
    if len(chosen) != 2 or len({s["pair_id"] for s in chosen}) != 2:
        raise RuntimeError("registered original-pair authority missing")
    cases = []
    for s in chosen:
        m, n = s["rows"], s["cols"]
        raw = {k: storage.decode_array(s["arrays"][k], shape).tolist()
               for k, shape in (("A", (m, n)), ("b", (m,)), ("c", (n,)))}
        task = {"domain": "lp.standard_form", **raw, "budget_s": 15.0}
        if len(canonical({**task, "policy": "native"}).encode()) > MAX_INPUT_BYTES:
            raise RuntimeError("original too large for R0 CLI")
        cases.append({
            "id": s["id"], "family": "historical_v102_q34_m64_constructed_lp",
            "source_group_id": s["pair_id"],
            "source": REGISTRY + "#" + s["id"] + "@" + s["sha256"],
            "license": "repo_opened_internal_research_only_rights_unassessed",
            "task": task,
            "original_problem_sha256": digest(source_problem_payload(task, validate_task(task))),
        })
    mfest = {
        "schema": SCHEMA, "split": "opened_development", "repeats": 1,
        "cases": cases,
        "systems": {role: {"id": role + "_opened_v102_control",
                           "revision": "R0_original_existing_engineering_v1",
                           "tools": ["equal_eligible_original_lp_solver"]}
                    for role in ROLES},
    }
    validate_manifest(mfest)
    return mfest


def run_existing(outdir: Path) -> dict:
    if outdir.exists() and any(outdir.iterdir()):
        raise FileExistsError("refuse to replace an existing or first-run capture")
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = registered_manifest()
    (outdir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2))
    rows = capture_opened_locals(manifest)
    if len(rows) != 4 or len({r["task_id"] for r in rows}) != 2:
        raise RuntimeError("expected two registered originals x two real local routes")
    if not all(r["capture"]["runner_status"] == "VERIFIED" for r in rows):
        raise RuntimeError("one original LP failed independent certification")
    raw = "".join(canonical(row) + "\n" for row in rows).encode()
    (outdir / "local_controls.jsonl").write_bytes(raw)
    by_source = {}
    for r in rows:
        by_source.setdefault(r["task_id"], {})[r["role"]] = r["resources"]["latency_ms"]["value"]
    ratio = {key: data["strong_native"] / data["classical_hybrid"]
             for key, data in by_source.items()}
    summary = {
        "schema": "neumann.f0-opened-v102-local-control.v1",
        "classification": CLASSIFICATION,
        "independent_originals": len(by_source),
        "actual_local_executions": len(rows),
        "frontier_executions": 0, "small_baseline_executions": 0,
        "learned_model_executions": 0,
        "observed_cold_wall_ms_by_original": by_source,
        "native_over_classical_cold_wall_ratio_by_original": ratio,
        "native_over_classical_cold_wall_geomean": geometric_mean(ratio.values()),
        "capture_sha256": hashlib.sha256(raw).hexdigest(),
        "complete_end_to_end_economics": "UNKNOWN",
        "new_scientific_admission": False,
        "global_questions_closed": [],
    }
    (outdir / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description="Previously registered, already OPENED v102 local controls")
    p.add_argument("--outdir", type=Path, required=True)
    args = p.parse_args()
    result = run_existing(args.outdir)
    print("F0_ACTUAL_OPENED_LOCAL_CONTROLS_NO_FRONTIER", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
