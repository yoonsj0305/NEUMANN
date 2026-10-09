"""Reuse Hybrid R0 to capture actual cold-process local F0 opened control arms.

This adapter DOES NOT invoke a frontier/small model, access sealed tasks, or
claim scientific cost evidence. It writes partial 5-arm receipts only; the
existing f0_opened_bridge audits after independently captured remaining arms
are combined. No new solvers, dataset generators or learned policies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns

from .f0_opened_bridge import validate_manifest, verify_original_answer
from .hybrid_runtime_r0 import SCHEMA as R0_SCHEMA
from .hybrid_runtime_r0 import canonical, digest

LOCAL_POLICIES = {
    "strong_native": "native",
    "classical_hybrid": "residual_fixed4m",
    "neumann": "frozen_q34",
}


def _run_once(task: dict, *, python: str) -> tuple[dict, bytes, float]:
    """New interpreter per case and arm; includes launch and final original proof."""
    started = perf_counter_ns()
    budget = float(task.get("budget_s", 5.0))
    proc = subprocess.run(
        [python, "-m", "neumann1.hybrid_runtime_r0"],
        input=canonical(task), text=True, capture_output=True,
        timeout=budget + 15.0, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("R0 child failed: no certified capture")
    raw = proc.stdout.encode("utf-8")
    if len(raw) > 2_000_000:
        raise RuntimeError("oversized R0 output")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("R0 emitted no parseable receipt") from exc
    if result.get("schema") != R0_SCHEMA or result.get("execution_request_sha256") != digest(task):
        raise RuntimeError("R0 output not bound to requested run")
    return result, raw, (perf_counter_ns() - started) / 1e6


def capture_opened_locals(manifest: dict, *,
                          roles: tuple[str, ...] = ("strong_native", "classical_hybrid"),
                          frozen_seed: int | None = None,
                          python: str = sys.executable) -> list[dict]:
    """Capture only real local executions; any infrastructure error aborts.

    A separate approved provider capture must supply the small/frontier arms.
    The entire output remains an OPENED developer diagnostic.
    """
    cases = validate_manifest(manifest)
    if (not roles or len(roles) != len(set(roles))
            or any(role not in LOCAL_POLICIES for role in roles)):
        raise ValueError("only distinct admitted local roles may run")
    if "neumann" in roles and frozen_seed not in (100001, 100002):
        raise ValueError("neumann role requires explicitly pinned historical frozen seed")
    if "neumann" not in roles and frozen_seed is not None:
        raise ValueError("frozen seed cannot affect a classical-only capture")
    if any(case["task"]["domain"] != "lp.standard_form" for case in cases.values()):
        raise ValueError("existing R0's distinct Native/4m/frozen LP policies only; no fake different arms")
    rows = []
    for case in cases.values():
        for repeat in range(manifest["repeats"]):
            for role in roles:
                task = dict(case["task"])
                task.pop("ranking", None)
                task.pop("seed", None)
                task["policy"] = LOCAL_POLICIES[role]
                if role == "neumann":
                    task["seed"] = frozen_seed
                result, raw, subprocess_ms = _run_once(task, python=python)
                if result.get("original_problem_sha256") != case["original_problem_sha256"]:
                    raise RuntimeError("original problem changed between F0 and Hybrid R0")
                if result.get("domain") != "lp.standard_form":
                    raise RuntimeError("wrong domain")
                if (result.get("status") == "ERROR"
                        or (result.get("reason") and "OPTIONAL_DEPENDENCY_MISSING"
                            in result["reason"])):
                    raise RuntimeError("R0 infrastructure failure; not a model capability failure")
                events = result.get("events", [])
                if not isinstance(events, list):
                    raise RuntimeError("R0 events invalid")
                learned = any(event.get("kind") == "frozen_q34_learned_proposal"
                              for event in events)
                if learned != (role == "neumann"):
                    raise RuntimeError("R0 route identity mismatch or frozen checkpoint unavailable")
                # Additional, separate parent-process original-problem verification
                # is not inferred from the child 'VERIFIED' label.
                proof_started = perf_counter_ns()
                answer = result.get("answer") if result["status"] == "VERIFIED" else None
                parent_verified = verify_original_answer(case["task"], answer)
                proof_ms = (perf_counter_ns() - proof_started) / 1e6
                if result["status"] == "VERIFIED" and not parent_verified:
                    raise RuntimeError("R0 claimed VERIFIED but independent F0 verifier rejected")
                wall = subprocess_ms + proof_ms
                rows.append({
                    "task_id": case["id"], "role": role, "repeat": repeat,
                    "original_problem_sha256": case["original_problem_sha256"],
                    "system_id": manifest["systems"][role]["id"],
                    "system_revision": manifest["systems"][role]["revision"],
                    "execution_complete": True,
                    "capture": {
                        "source": "actual_local_cold_subprocess_hybrid_r0",
                        "mode": "cold_new_python_per_case_role",
                        "policy": LOCAL_POLICIES[role],
                        "frozen_seed": frozen_seed if role == "neumann" else None,
                        "runner_status": result["status"],
                        "runner_output_sha256": hashlib.sha256(raw).hexdigest(),
                        "runner_receipt": result,
                        "subprocess_wall_ms": subprocess_ms,
                        "independent_parent_verification_ms": proof_ms,
                        "complete_cost_status": "PARTIAL_NO_ENERGY_MONEY_OR_INVESTMENT",
                    },
                    "answer": answer,
                    "resources": {
                        "latency_ms": {"status": "measured", "value": wall},
                        "cost_usd": {"status": "unavailable", "value": None},
                    },
                })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="F0 opened cold R0 local-arm capture only")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roles", default="strong_native,classical_hybrid")
    parser.add_argument("--frozen-seed", type=int)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = capture_opened_locals(
        manifest,
        roles=tuple(args.roles.split(",")),
        frozen_seed=args.frozen_seed,
    )
    if args.output.exists():
        raise FileExistsError("refuse to overwrite any first-run capture artifact")
    with args.output.open("x", encoding="utf-8") as out:
        for row in rows:
            out.write(canonical(row) + "\n")
    print("F0_OPENED_PARTIAL_LOCAL_CAPTURE_ONLY", len(rows),
          "provider_small_frontier_NOT_RUN", "global_Q1_Q7_OPEN")


if __name__ == "__main__":
    main()
