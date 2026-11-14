"""REAL opened-only original arithmetic/CSP tool + independent verification gate.

Not Decision-2 rerun; no Gemma, student, frozen test, or answer corpus exposure
to controller. Unavailable coding generator deliberately abstains.
"""
from __future__ import annotations

import json
from pathlib import Path

from experiments.general_multiplier_tasks import multiplier_tasks
from neumann1.control_plane_p1_contract import PUBLIC_SHA256, TASK_IDS
from neumann1.control_plane_v1 import digest
from neumann1.finite_action_boundary_v1 import run
from neumann1.general_runtime_v106 import Limits, ToolPool, verify_original

ROOT = Path(__file__).resolve().parents[1]


def execute_opened():
    source = json.loads((ROOT / "docs/experiments/control_plane_p1_opened_public.json").read_text())
    tasks = multiplier_tasks()
    views = [{"instruction": t["instruction"], "public": t["public"]} for t, _ in tasks]
    if len(views) != 12 or digest(views) != PUBLIC_SHA256:
        raise ValueError("frozen original twelve public input views drift")
    if tuple(t["id"] for t, _ in tasks) != TASK_IDS:
        raise ValueError("frozen opened task IDs drift")

    rows = []
    for (task, private), view in zip(tasks, views):
        # Checker-only private information is intentionally not passed into pool.
        pool = ToolPool(task, {}, Limits())

        def classic(route, public_view):
            public = public_view["public"]
            if route == "ARITHMETIC":
                answer = pool.call("arithmetic", {
                    "expression": public["expression"], "bindings": public["bindings"]
                }, 2000)
            elif route == "CSP":
                solved = pool.call("csp", {
                    "spec": {"domains": public["domains"],
                             "constraints": public["constraints"]},
                    "strategy": "mrv"
                }, 2000)
                answer = solved["assignment"]
            else:
                raise ValueError("unsupported classical route")
            return {
                "answer": answer, "provenance": "EXISTING_GENERAL_RUNTIME_V106_TOOLPOOL",
                "model_calls": 0, "tool_calls": 1, "generated_tokens": 0
            }

        def independent(public_view, candidate):
            # Private exact reference/test information is visible ONLY here.
            return verify_original(task, candidate, private, 2000)

        result = run(view, classical=classic, verify_original=independent)
        rows.append({
            "task_id": task["id"], "family": task["family"],
            "action": result["action"], "route": result["selected_route"],
            "verified": result["accepted"], "status": result["status"],
            "tool_calls": result["tool_calls"],
            "verifier_calls": result["verifier_calls"],
            "model_calls": result["model_calls"],
            "complete_wall_ms": result["complete_wall_ms"],
            "accounting_complete": result["cost_accounting_complete"],
            "error": result["error"],
            "original_public_view_SHA256": result["view_sha256"]
        })
    report = {
        "schema": "neumann.north-star.opened-12-actual-native.v1",
        "scientific_scope": "EXISTING_OPENED_DEV_TASKS_ONLY_CLASSICAL_TOOL",
        "frozen_original_public_SHA256": PUBLIC_SHA256,
        "total": len(rows),
        "valid_actions": sum(x["action"] in ("CLASSICAL", "ABSTAIN") and x["error"] is None for x in rows),
        "actual_native_tool_entry": sum(x["tool_calls"] == 1 for x in rows),
        "independently_verified_originals": sum(x["verified"] for x in rows),
        "coding_no_generator_abstained": sum(x["family"] == "coding" and x["action"] == "ABSTAIN" for x in rows),
        "model_inference": False, "new_learning": False,
        "Decision2_verdict_replaced": False,
        "Q3": "OPEN", "Q4": "OPEN", "Q5": "OPEN", "Q6": "OPEN", "Q7": "OPEN",
        "energy_j": None, "flops": None, "usd": None,
        "rows": rows
    }
    if not (
        report["valid_actions"] == 12
        and report["actual_native_tool_entry"] == 8
        and report["independently_verified_originals"] == 8
        and report["coding_no_generator_abstained"] == 4
        and all(x["accounting_complete"] for x in rows)
    ):
        raise RuntimeError("opened actual native gate failed: " + json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    print(json.dumps(execute_opened(), indent=2, sort_keys=True))
