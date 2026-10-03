"""Metadata-only deterministic selection for a future sealed Decision-3 set.

No dataset access occurs here. Callers provide metadata rows only after Decision
2 has admitted unsealing. Question text, answer, rationale and model outputs are
forbidden selection inputs.
"""
from __future__ import annotations

import hashlib

SEED = "NEUMANN-D3-SEALED-V1-2026-10-03"
FORBIDDEN_KEYS = {"question", "answer", "rationale", "choices", "solution", "response"}


def _hash(source_id, task_id):
    raw = (SEED + "|" + source_id + "|" + task_id).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def select_metadata(rows, *, source_id, target_count=18):
    if type(rows) is not list:
        raise ValueError("metadata rows list required")
    candidates = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("metadata row object required")
        if FORBIDDEN_KEYS.intersection(row):
            raise ValueError("content/answer fields forbidden during sealed selection")
        task_id = row.get("id")
        family = row.get("family")
        raw_subject = row.get("raw_subject") or "UNKNOWN"
        category = row.get("category") or "UNKNOWN"
        if type(task_id) is not str or not task_id:
            raise ValueError("stable id required")
        if type(family) is not str or not family:
            raise ValueError("family label required")
        if row.get("eligible") is not True:
            continue
        candidates.append({
            "id": task_id,
            "family": family,
            "raw_subject": str(raw_subject),
            "category": str(category),
            "new_family": bool(row.get("new_family")),
            "selection_hash": _hash(source_id, task_id),
        })

    candidates.sort(key=lambda row: (row["selection_hash"], row["id"]))
    selected = []
    subject_counts = {}
    category_counts = {}
    for row in candidates:
        if subject_counts.get(row["raw_subject"], 0) >= 2:
            continue
        if category_counts.get(row["category"], 0) >= 6:
            continue
        selected.append(row)
        subject_counts[row["raw_subject"]] = subject_counts.get(row["raw_subject"], 0) + 1
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1
        if len(selected) == target_count:
            break

    if len(selected) != target_count:
        raise ValueError("insufficient eligible metadata diversity for frozen target count")
    return selected
