"""Read-only post-result diagnostics for retained P1.8 receipts.

This module NEVER performs model inference, generation, execution, verification,
or evidence mutation.  It may compute counterfactual latent choices from a
selector receipt that completed after the frozen wall.  Such values are
POST_HOC_NON_ADMISSIBLE and cannot rescue the historical result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from neumann1.control_plane_v1 import ROUTES, finite
from neumann1.control_plane_p12 import aggregate
from neumann1.control_plane_p18 import _masked_choice

SCHEMA = "neumann.control-plane-p1.8-postmortem.v1"


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def analyze_record(record):
    out = {
        "task_id": record.get("task_id"),
        "stratum": record.get("stratum"),
        "historical_status": record.get("status"),
        "historical_accepted": record.get("accepted"),
        "historical_selected_candidate": record.get("selected_candidate"),
        "eligible_indexes": record.get("eligible_indexes"),
        "model_calls": record.get("model_calls"),
        "neural_forward_calls": record.get("neural_forward_calls"),
        "evaluated_tokens": record.get("evaluated_tokens"),
        "accounting_complete": record.get("accounting_complete"),
        "historical_error": record.get("error"),
        "post_hoc_non_admissible": True,
        "model_inference": False,
        "evidence_mutation": False,
    }
    receipt = record.get("selector_receipt")
    if not isinstance(receipt, dict):
        out["diagnostic_status"] = "NO_SELECTOR_RECEIPT"
        return out

    out["selector_status"] = receipt.get("status")
    out["selector_complete_ms"] = receipt.get("complete_ms")
    passes = receipt.get("passes")
    if (
        receipt.get("status") != "COMPLETE"
        or not isinstance(passes, list)
        or len(passes) != 3
        or any(not isinstance(p, dict) or p.get("status") != "COMPLETE" or not isinstance(p.get("matrix"), list)
               for p in passes)
    ):
        out["diagnostic_status"] = "INCOMPLETE_SELECTOR_RECEIPT"
        return out

    matrices = [p["matrix"] for p in passes]
    summaries = []
    for p, matrix in zip(passes, matrices):
        summary = aggregate(matrix)
        summaries.append({
            "mode": p.get("mode"),
            "complete_ms": p.get("complete_ms"),
            "scores": {k: finite(summary["scores"][k]) for k in ROUTES},
            "winner": summary["winner"],
            "margin_nats": finite(summary["margin_nats"]),
            "all_loo_winners_stable": summary["all_loo_winners_stable"],
            "max_centered_loo_delta_nats": finite(summary["max_centered_loo_delta_nats"]),
            "max_centered_orbit_pair_delta_nats": finite(summary["max_centered_orbit_pair_delta_nats"]),
            "max_centered_per_mapping_range_nats": finite(summary["max_centered_per_mapping_range_nats"]),
        })
    out["pass_summaries"] = summaries

    eligible = record.get("eligible_indexes")
    try:
        out["latent_masked_choice"] = _masked_choice(matrices, eligible)
        out["latent_choice_status"] = "STABLE_UNDER_FROZEN_MASKED_CHOICE"
    except Exception as exc:
        out["latent_masked_choice"] = None
        out["latent_choice_status"] = type(exc).__name__ + ": " + str(exc)

    # This comparison is diagnostic only.  A latent choice from an over-wall
    # receipt is never an admissible historical selection.
    chosen = out["latent_masked_choice"]
    historical = record.get("selected_candidate")
    out["matches_historical_choice"] = (
        chosen == historical if chosen is not None and historical is not None else None
    )
    out["diagnostic_status"] = "COMPLETE_POST_HOC_DIAGNOSTIC"
    return out


def analyze(directory):
    directory = Path(directory)
    tasks = []
    for i in range(8):
        path = directory / ("task_%02d.json" % i)
        if path.is_file():
            tasks.append(analyze_record(_read(path)))
    return {
        "schema": SCHEMA,
        "directory": str(directory),
        "post_hoc_non_admissible": True,
        "historical_result_unchanged": True,
        "model_inference": False,
        "evidence_mutation": False,
        "tasks": tasks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.directory), sort_keys=True, indent=2))
