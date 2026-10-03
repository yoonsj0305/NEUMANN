"""Frozen P1 real controller diagnostic, not a capability experiment."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from neumann1.control_plane_v1 import ROUTES, digest, finite

SCHEMA = "neumann.control-plane-p1.v1"
MODEL = {
    "model_id": "google/gemma-4-E2B-it",
    "model_revision": "3e22461f65e89153144f8adb70e3b8c2cc9845a7",
    "artifact_sha256": "bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66",
    "tokenizer_sha256": "8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207",
    "precision": "bfloat16", "weights_frozen": True,
}
PUBLIC_SHA256 = "c883a44136817bf2501549a42c268b29577b8f153b3ca95b807e7ab245fdd2f0"
TASK_SHA256 = "ad32fd947e4c63fc1b67f849254bb16bd62fad6067bd719d5ad3da6c1f11e99f"
TASK_IDS = tuple("am_%s_%02d" % (group, i) for group in ("math", "code", "plan") for i in range(1, 5))


@dataclass(frozen=True)
class P1Budget:
    context_tokens: int = 4096
    label_tokens: int = 16
    task_wall_ms: float = 120000.0
    study_wall_ms: float = 1800000.0
    evaluated_tokens: int = 196608
    padded_tokens: int = 196608
    forward_calls: int = 72
    score_rows: int = 144


CRITERIA = {
    "score_abs_tolerance_nats": 0.05,
    "minimum_distinct_winners": 2,
    "maximum_dominant_winner_count": 10,
    "minimum_centered_score_range_nats": 0.001,
    "strict_winner_margin_nats": 0.1,
}


def manifest():
    return {"schema": SCHEMA, "model": dict(MODEL), "public_sha256": PUBLIC_SHA256,
            "original_task_sha256": TASK_SHA256, "task_count": 12, "routes": list(ROUTES),
            "modes": ["batch4", "unbatched1", "reverse_batch4"], "cost_weight": 0.0,
            "budget": asdict(P1Budget()), "criteria": dict(CRITERIA),
            "runtime": {"torch": "2.11.0+cu128", "torchvision": "0.26.0+cu128", "transformers": "5.16.1"},
            "allowed_device_name": "Tesla T4", "generated_tokens": 0, "tool_calls": 0,
            "new_training": False, "frontier_calls": 0, "sealed": False,
            "split": "existing_opened_author_constructed_12", "favorable_rerun_allowed": False}


def validate_identity(identity):
    if any(identity.get(key) != expected for key, expected in MODEL.items()):
        raise ValueError("exact frozen model/tokenizer/revision/BF16 identity required")
    if identity.get("device_type") != "cuda" or identity.get("device_name") != "Tesla T4":
        raise ValueError("registered Kaggle Tesla T4 accelerator required")
    if identity.get("evidence_kind") != "actual_frozen_model":
        raise ValueError("actual frozen model evidence required")
    if identity.get("framework") != "torch-2.11.0+cu128/transformers-5.16.1":
        raise ValueError("registered scoring runtime required")
    if identity.get("torchvision") != "0.26.0+cu128":
        raise ValueError("registered torchvision required")


def route_statistics(scores):
    if len(scores) != len(ROUTES):
        raise ValueError("four route scores required")
    scores = [finite(v) for v in scores]
    ranking = sorted(range(4), key=lambda i: (-scores[i], i))
    return {"winner": ROUTES[ranking[0]], "margin_nats": scores[ranking[0]] - scores[ranking[1]],
            "scores": dict(zip(ROUTES, scores))}


def evaluate(records, audit, generated_calls, total_ms, accounting_complete):
    """Pure diagnostic verdict. No task-family or answer labels are consumed."""
    if generated_calls != 0:
        return {"verdict": "FAIL", "reason": "GENERATION_FORBIDDEN", "p2_admitted": False}
    if len(records) != 12 or not accounting_complete or audit.get("unchanged") is not True:
        return {"verdict": "NOT_EVALUATED", "reason": "INCOMPLETE_OR_IDENTITY_DRIFT", "p2_admitted": False}
    if tuple(record.get("task_id") for record in records) != TASK_IDS:
        return {"verdict": "NOT_EVALUATED", "reason": "TASK_COVERAGE_DRIFT", "p2_admitted": False}
    if finite(total_ms, True) > P1Budget().study_wall_ms:
        return {"verdict": "FAIL", "reason": "STUDY_WALL_CAP", "p2_admitted": False}
    winners = []
    centered = []
    for record in records:
        if record.get("status") != "COMPLETE" or finite(record["complete_ms"], True) > P1Budget().task_wall_ms:
            return {"verdict": "FAIL", "reason": "TASK_INCOMPLETE_OR_WALL_CAP", "p2_admitted": False}
        stats = route_statistics(record["canonical_scores"])
        winners.append(stats["winner"])
        row = record["canonical_scores"]
        mean = math.fsum(row) / 4
        centered.append([v - mean for v in row])
        if finite(record["max_batch_delta_nats"], True) > CRITERIA["score_abs_tolerance_nats"] or finite(record["max_order_delta_nats"], True) > CRITERIA["score_abs_tolerance_nats"]:
            return {"verdict": "FAIL", "reason": "NUMERICAL_OR_ORDER_INCONSISTENCY", "p2_admitted": False}
        if record["stable_large_margin_winner"] is not True:
            return {"verdict": "FAIL", "reason": "LARGE_MARGIN_WINNER_DRIFT", "p2_admitted": False}
    dominant = max(winners.count(route) for route in ROUTES)
    spread = max(max(row[i] for row in centered) - min(row[i] for row in centered) for i in range(4))
    nondegenerate = (len(set(winners)) >= CRITERIA["minimum_distinct_winners"]
                     and dominant <= CRITERIA["maximum_dominant_winner_count"]
                     and spread >= CRITERIA["minimum_centered_score_range_nats"])
    return {"verdict": "PASS" if nondegenerate else "FAIL", "reason": "CONTROLLER_DIAGNOSTIC_ONLY" if nondegenerate else "DEGENERATE_ROUTE_SELECTION",
            "p2_admitted": nondegenerate, "winner_counts": {r: winners.count(r) for r in ROUTES},
            "centered_score_range_nats": spread, "general_capability_gate": "NOT_EVALUATED",
            "decision3_admitted": False, "global_questions_closed": []}
