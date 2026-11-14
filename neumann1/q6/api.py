"""Safe integration facade; Q3 supplies evidence authority and fallback.

This facade was added after the v1 study. It does not alter its frozen matcher
or retrospectively create capability evidence for unsupported representations.
"""
from __future__ import annotations
import time

from .contracts import Artifact, digest, result
from .transport import extract, transport


def structural_transport(artifacts, observations, *, source_authority, cap_s=3, q3_fallback=None):
    started = time.process_time()
    if observations.get("test"):
        visible_digest = digest({k: v for k, v in observations.items() if k != "test"})
        return result(visible_digest, reason="receiver_TEST_not_authorized_for_inference")
    d = digest(observations)
    if observations.get("out_type") not in ("I", "B", "L") or any(
            t not in ("I", "B", "L") for t in observations.get("in_types", [])):
        return result(d, reason="unsupported_observation_representation")
    admitted, rejected = [], []
    for payload in artifacts:
        try:
            a = Artifact.admit(payload, source_authority)
            data = a.data
            m = data["executable_method"]
            if data["discovered_representation"].get("kind") != "typed-ast.v1" or m.get("kind") not in ("ast", "zmap", "zfilter"):
                raise ValueError("unsupported_source_representation")
            if any(t not in ("I", "B", "L") for t in m.get("state_types", [])):
                raise ValueError("unsupported_source_state_type")
            admitted.append(a)
        except (ValueError, KeyError, TypeError) as e:
            rejected.append(str(e))
    if not admitted:
        return result(d, reason="no_independently_admitted_source_artifact", counterexamples=rejected,
                      cost={"admission_cpu_seconds": time.process_time() - started})
    try:
        inventory = extract(admitted)
    except (ValueError, KeyError, TypeError) as e:
        return result(d, reason="unsupported_or_invalid_typed_source", counterexamples=[str(e)])
    admission = time.process_time() - started
    if admission >= cap_s:
        return result(d, reason="source_admission_exhausted_budget", cost={"admission_cpu_seconds": admission})
    r = transport(observations, inventory, cap_s=cap_s - admission, fallback=q3_fallback)
    r["measured_cost"]["admission_and_extraction_cpu_seconds"] = admission
    r["measured_cost"]["total_cpu_seconds"] = time.process_time() - started
    r["rejected_source_artifact_reasons"] = rejected
    return r
