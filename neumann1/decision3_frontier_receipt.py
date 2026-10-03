"""Provider-neutral frontier reference receipt validation for Decision 3."""
from __future__ import annotations

REQUIRED_RESOURCE_AXES = (
    "complete_latency_ms",
    "monetary_cost_usd",
    "energy_j",
    "compute_units",
)


def validate_frontier_receipt(receipt):
    if type(receipt) is not dict:
        raise ValueError("frontier receipt object required")
    for key in (
        "provider",
        "model_id",
        "model_revision",
        "task_id",
        "request_sha256",
        "response_sha256",
        "trace_sha256",
    ):
        if type(receipt.get(key)) is not str or not receipt[key]:
            raise ValueError(key + " required")
    if type(receipt.get("verified_success")) is not bool:
        raise ValueError("verified_success required")
    if type(receipt.get("attempts")) is not int or receipt["attempts"] < 1:
        raise ValueError("attempt count required")
    if receipt.get("selection_role") != "FROZEN_FRONTIER_REFERENCE":
        raise ValueError("frontier role must be frozen before responses")
    resources = receipt.get("resources")
    if type(resources) is not dict:
        raise ValueError("resources required")
    for axis in REQUIRED_RESOURCE_AXES:
        item = resources.get(axis)
        if type(item) is not dict:
            raise ValueError("explicit " + axis + " resource item required")
        status = item.get("status")
        if status not in ("measured", "estimated", "unavailable"):
            raise ValueError("invalid resource status")
        if status == "measured":
            if type(item.get("value")) not in (int, float) or item["value"] < 0:
                raise ValueError("measured value required")
            if type(item.get("unit")) is not str or not item["unit"]:
                raise ValueError("measured unit required")
        elif item.get("value") is not None:
            raise ValueError("unmeasured resource cannot silently become zero")
    return True
