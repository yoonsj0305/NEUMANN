"""Versioned JSON boundary; no Q3 private policy/state dependency."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re

REQUIRED = ("artifact_id", "producer_commit", "source_task_digest", "observation_schema",
            "discovered_representation", "executable_method", "source_verification",
            "provenance", "resource_cost")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def seal_artifact(payload):
    data = json.loads(json.dumps(payload, allow_nan=False))
    data.pop("artifact_id", None)
    data["artifact_id"] = digest(data)
    return data


@dataclass(frozen=True)
class Artifact:
    canonical_json: str

    @property
    def data(self):
        return json.loads(self.canonical_json)

    @property
    def identity(self):
        return self.data["artifact_id"]

    @classmethod
    def admit(cls, data, source_authority):
        if not all(k in data for k in REQUIRED):
            raise ValueError("missing discovery artifact field")
        payload = {k: v for k, v in data.items() if k != "artifact_id"}
        if digest(payload) != data["artifact_id"]:
            raise ValueError("artifact digest mismatch")
        if not re.fullmatch(r"[0-9a-f]{40}", data["producer_commit"]):
            raise ValueError("unidentified producer commit")
        if not re.fullmatch(r"[0-9a-f]{64}", data["source_task_digest"]):
            raise ValueError("unidentified source task")
        e = data["source_verification"]
        if e.get("method_digest") != digest(data["executable_method"]):
            raise ValueError("source proof is bound to a different method")
        if e.get("status") != "EXACT_OBSERVED_SOURCE" or not e.get("checker"):
            raise ValueError("missing finite original-source verification")
        if not source_authority(data):
            raise ValueError("independent source authority rejected artifact")
        return cls(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False))


def result(target_digest, *, status="UNKNOWN", source=None, correspondence=None,
           representation=None, method=None, obligations=None, counterexamples=None,
           cost=None, reason=None):
    return {"source_artifact_id": source, "target_observation_digest": target_digest,
            "candidate_correspondence": correspondence,
            "transported_representation": representation,
            "transformed_executable_method": method,
            "verification_obligations": obligations or ["original independent TEST not yet checked"],
            "verification_status": status, "counterexamples": counterexamples or [],
            "measured_cost": cost or {}, "failure_reason": reason}
