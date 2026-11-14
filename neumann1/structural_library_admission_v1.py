"""Structural library preflight: do not attempt impossible cross-DSL macro reuse.

This is only a public-metadata admission interface. Operator-name overlap is a
necessary condition, not semantic equivalence, proof or learned Q3 invention.
No benchmark bodies/model weights are loaded.
"""
from __future__ import annotations

import re

SCHEMA = "neumann.north-star.structure-library-admission.v1"


def _sha(value):
    return type(value) is str and bool(re.fullmatch(r"[a-f0-9]{64}", value))


def _name(value):
    return type(value) is str and 1 <= len(value) <= 128 and bool(value.strip())


def _signature(value):
    if type(value) is not dict or set(value) != {"inputs", "output"}:
        raise ValueError("exact typed interface required")
    if (type(value["inputs"]) is not list or len(value["inputs"]) > 32
            or not all(_name(v) for v in value["inputs"])
            or not _name(value["output"])):
        raise ValueError("valid typed interface required")
    return (tuple(value["inputs"]), value["output"])


def qualify(macro, target):
    """Return an admission/abstention receipt, never a success proof.

    Do NOT call this after peeking at prospective original target source
    contents for first-use evaluation. A target signature needs provenance
    in its frozen source metadata before the source body is read.
    """
    if type(macro) is not dict or set(macro) != {
        "dsl_id", "signature", "required_operators", "macro_sha256"
    }:
        raise ValueError("exact frozen macro contract required")
    if type(target) is not dict or set(target) != {
        "dsl_id", "signature", "supported_operators", "source_metadata_sha256"
    }:
        raise ValueError("exact target source metadata contract required")
    if not _name(macro["dsl_id"]) or not _name(target["dsl_id"]):
        raise ValueError("explicit DSL IDs required")
    a, b = _signature(macro["signature"]), _signature(target["signature"])
    for value, key in ((macro["required_operators"], "required"),
                       (target["supported_operators"], "supported")):
        if (type(value) is not list or not value
                or len(value) > 512 or not all(_name(x) for x in value)
                or len(set(value)) != len(value)):
            raise ValueError("complete, unique named "+key+" operators required")
    if not _sha(macro["macro_sha256"]) or not _sha(target["source_metadata_sha256"]):
        raise ValueError("source and learned-macro hashes required")
    missing = sorted(set(macro["required_operators"]) - set(target["supported_operators"]))
    reasons = []
    if macro["dsl_id"] != target["dsl_id"]:
        reasons.append("CROSS_DSL_WITHOUT_VERIFIED_TRANSLATOR")
    if a != b:
        reasons.append("TYPE_SIGNATURE_MISMATCH")
    if missing:
        reasons.append("MISSING_REQUIRED_OPERATORS")
    status = "ADMITTED_REQUIRES_INDEPENDENT_PROOF" if not reasons else "ABSTAIN_INCOMPATIBLE_INTERFACE"
    return {
        "schema": SCHEMA, "status": status, "admissible": not reasons,
        "reasons": reasons, "missing_operator_heads": missing,
        "required_operator_heads": len(macro["required_operators"]),
        "declared_target_operator_heads": len(target["supported_operators"]),
        "target_original_source_bodies_read": 0,
        "macro_sha256": macro["macro_sha256"],
        "target_source_metadata_sha256": target["source_metadata_sha256"],
        "cross_dsl_translation_implicitly_allowed": False,
        "original_problem_verified": False,
        "generated_new_semantics": False, "Q3": "OPEN", "Q6": "OPEN"
    }
