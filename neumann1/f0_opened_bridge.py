"""F0 OPENED-development original-task verifier and paired response intake.

NO hosted model invocation, credential access, sealed data, code execution, or
scientific F1 admission. A captured response is NOT a provider attestation.
This module only checks whether supplied candidate answers solve the ORIGINAL
LP / exact-linear / SyGuS tasks through existing independent certificates.
"""
from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path

from .hybrid_runtime_r0 import (canonical, digest, source_problem_payload,
                                validate_task)

SCHEMA = "neumann.f0-opened-paired.v1"
ROLES = ("small", "frontier", "neumann", "strong_native", "classical_hybrid")
RESOURCE_KEYS = ("latency_ms", "cost_usd")


def _nonnegative(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def verify_original_answer(task: dict, answer: object) -> bool:
    """Source-level verification; never trust submitted 'correct' claims."""
    try:
        spec = validate_task(task)
        if not isinstance(answer, dict):
            return False
        if spec["domain"] == "exact.linear":
            values = answer.get("solution")
            if not isinstance(values, dict) or set(values) != set(spec["variables"]):
                return False
            xs = []
            for name in spec["variables"]:
                cell = values[name]
                if (not isinstance(cell, dict)
                        or set(cell) != {"numerator", "denominator"}
                        or type(cell["numerator"]) is not int
                        or type(cell["denominator"]) is not int
                        or cell["denominator"] <= 0
                        or max(abs(cell["numerator"]), cell["denominator"]) > 10 ** 60):
                    return False
                xs.append(Fraction(cell["numerator"], cell["denominator"]))
            return all(sum(Fraction(a) * x for a, x in zip(row, xs)) == rhs
                       for row, rhs in zip(spec["A"], spec["b"]))
        if spec["domain"] == "lp.standard_form":
            from .lp_certificate_v081 import verify_standard_form_certificate
            if "primal" not in answer or "dual" not in answer:
                return False
            proof = verify_standard_form_certificate(
                spec["A"], spec["b"], spec["c"],
                answer["primal"], answer["dual"])
            return proof["accepted"] is True
        if spec["domain"] == "sygus.invariant":
            from .hybrid_sygus_r0 import prepare, independent_check
            invariant = answer.get("invariant")
            if not isinstance(invariant, str) or not 0 < len(invariant) <= 40000:
                return False
            _, arguments, original_defs = prepare(spec["source"])
            proof = independent_check(arguments, original_defs, invariant, timeout_ms=2500)
            return proof["accepted"] is True
    except ImportError as exc:
        # Infrastructure failure cannot be silently counted as a small-model FAIL.
        raise RuntimeError("independent verifier dependency unavailable") from exc
    except (ValueError, TypeError, KeyError, OverflowError):
        return False
    return False


def validate_manifest(m: dict) -> dict:
    if not isinstance(m, dict) or m.get("schema") != SCHEMA:
        raise ValueError("F0 schema required")
    if m.get("split") != "opened_development":
        raise ValueError("F0 input must be expressly opened development; sealed data forbidden")
    if type(m.get("repeats")) is not int or not 1 <= m["repeats"] <= 3:
        raise ValueError("repeats must be registered in [1,3]")
    if not isinstance(m.get("cases"), list) or not m["cases"]:
        raise ValueError("nonempty original cases required")
    if set(m.get("systems", {})) != set(ROLES):
        raise ValueError("four frozen roles including strong native required")
    toolsets = []
    for role in ROLES:
        system = m["systems"][role]
        if (not isinstance(system, dict)
                or any(not isinstance(system.get(key), str) or not system[key].strip()
                       for key in ("id", "revision"))
                or not isinstance(system.get("tools"), list)
                or any(type(t) is not str or not t for t in system["tools"])
                or len(system["tools"]) != len(set(system["tools"]))):
            raise ValueError("frozen system identities and tools required")
        toolsets.append(sorted(system["tools"]))
    if any(t != toolsets[0] for t in toolsets[1:]):
        raise ValueError("all systems must be eligible for identical tool authority")
    ids, hashes = set(), set()
    for case in m["cases"]:
        if (not isinstance(case, dict) or not isinstance(case.get("id"), str)
                or not case["id"] or case["id"] in ids
                or not isinstance(case.get("family"), str) or not case["family"]
                or not isinstance(case.get("source_group_id"), str)
                or not case["source_group_id"]
                or not isinstance(case.get("source"), str) or not case["source"]
                or not isinstance(case.get("license"), str) or not case["license"]):
            raise ValueError("distinct case, independent-family, provenance required")
        ids.add(case["id"])
        spec = validate_task(case["task"])
        h = digest(source_problem_payload(case["task"], spec))
        if case.get("original_problem_sha256") != h or h in hashes:
            raise ValueError("duplicate or incorrectly bound original problem")
        hashes.add(h)
    return {c["id"]: c for c in m["cases"]}


def audit_opened(manifest: dict, receipts: list[dict]) -> dict:
    """Diagnostic results ONLY; never promote response metadata to attestation."""
    tasks = validate_manifest(manifest)
    expected = {(t, r, i) for t in tasks for r in ROLES
                for i in range(manifest["repeats"])}
    observations, seen = [], set()
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise ValueError("receipt object required")
        k = (receipt.get("task_id"), receipt.get("role"), receipt.get("repeat"))
        if k not in expected or k in seen:
            raise ValueError("duplicate or unregistered response")
        seen.add(k)
        task = tasks[k[0]]
        sys = manifest["systems"][k[1]]
        if (receipt.get("original_problem_sha256") != task["original_problem_sha256"]
                or receipt.get("system_id") != sys["id"]
                or receipt.get("system_revision") != sys["revision"]
                or receipt.get("execution_complete") is not True):
            raise ValueError("unbound or incomplete captured execution")
        evidence = receipt.get("capture")
        if (not isinstance(evidence, dict)
                or not isinstance(evidence.get("source"), str)
                or not evidence["source"]):
            raise ValueError("explicit external capture provenance required")
        costs = receipt.get("resources")
        if not isinstance(costs, dict) or set(costs) != set(RESOURCE_KEYS):
            raise ValueError("both resource measurements must be declared")
        for metric in RESOURCE_KEYS:
            item = costs[metric]
            if not isinstance(item, dict) or item.get("status") not in ("measured", "unavailable"):
                raise ValueError("cost provenance must be measured or unavailable")
            if item["status"] == "unavailable" and item.get("value") is not None:
                raise ValueError("missing resource is not zero")
            if item["status"] == "measured" and not _nonnegative(item.get("value")):
                raise ValueError("invalid measured resource")
        accepted = verify_original_answer(task["task"], receipt.get("answer"))
        observations.append({"task_id": k[0], "role": k[1], "repeat": k[2],
                             "source_group_id": task["source_group_id"],
                             "family": task["family"], "verified": accepted,
                             "resources": costs})
    if seen != expected:
        raise ValueError("missing comparison arm; absence is not a model failure")
    per_case = {}
    for task_id in tasks:
        per_case[task_id] = {
            r: sum(x["verified"] for x in observations
                   if x["task_id"] == task_id and x["role"] == r)
            / manifest["repeats"] for r in ROLES
        }
    # Gap membership depends ONLY on the small and frontier results.
    # For this first strict pilot, require all repetitions to agree.
    gap = [task_id for task_id, q in per_case.items()
           if q["small"] == 0 and q["frontier"] == 1]
    recovered = [task_id for task_id in gap if per_case[task_id]["neumann"] == 1]
    independent_gap_groups = {tasks[t]["source_group_id"] for t in gap}
    recovered_groups = {g for g in independent_gap_groups
                        if all(t in recovered for t in gap
                               if tasks[t]["source_group_id"] == g)}
    frontier_matching = bool(gap and len(recovered) == len(gap))
    # Do not claim an economic frontier gain while the best native already wins.
    # Compare matched-capability totals against BOTH frontier and specialist.
    ratio, native_ratio, classical_ratio = {}, {}, {}
    native_matching = bool(gap and all(per_case[t]["strong_native"] == 1 for t in gap))
    classical_matching = bool(gap and all(per_case[t]["classical_hybrid"] == 1 for t in gap))
    for metric in RESOURCE_KEYS:
        n = [x["resources"][metric] for x in observations
             if x["task_id"] in gap and x["role"] == "neumann"]
        for comparator, eligible, sink in (
            ("frontier", frontier_matching, ratio),
            ("strong_native", frontier_matching and native_matching, native_ratio),
            ("classical_hybrid", frontier_matching and classical_matching, classical_ratio),
        ):
            ref = [x["resources"][metric] for x in observations
                   if x["task_id"] in gap and x["role"] == comparator]
            if (eligible and ref and n
                    and all(x["status"] == "measured" for x in ref + n)
                    and sum(x["value"] for x in ref) > 0):
                sink[metric] = sum(x["value"] for x in n) / sum(x["value"] for x in ref)
            else:
                sink[metric] = None
    return {
        "schema": SCHEMA,
        "scope": "OPENED_DEVELOPMENT_DIAGNOSTIC_NOT_FRESH_OR_SEALED",
        "capture_attestation": "UNVERIFIED_EXCEPT_FOR_ORIGINAL_MATH",
        "decision": ("NO_OBSERVED_GAP" if not gap else
                     "BOUNDED_PILOT_CAPABILITY_MATCH" if frontier_matching else
                     "BOUNDED_PILOT_CAPABILITY_UNREACHED"),
        "cases": len(tasks), "observations": len(observations),
        "gap_case_ids": gap,
        "gap_source_groups": len(independent_gap_groups),
        "recovered_source_groups": len(recovered_groups),
        "conservative_source_group_recovery_rate":
            len(recovered_groups) / len(independent_gap_groups) if gap else None,
        "recovered_case_ids": recovered,
        "gap_recovery_rate": len(recovered) / len(gap) if gap else None,
        "per_case_verified_rate": per_case,
        "neumann_to_frontier_reported_resource_ratio": ratio,
        "neumann_to_strong_native_reported_resource_ratio": native_ratio,
        "neumann_to_classical_hybrid_reported_resource_ratio": classical_ratio,
        "neumann_to_best_classical_reported_resource_ratio": {
            k: (max(eligible) if eligible else None)
            for k in RESOURCE_KEYS
            for eligible in [[r for r in (native_ratio[k], classical_ratio[k])
                              if r is not None]]
        },
        "strong_native_gap_verified_rate":
            sum(per_case[t]["strong_native"] for t in gap) / len(gap) if gap else None,
        "classical_hybrid_gap_verified_rate":
            sum(per_case[t]["classical_hybrid"] for t in gap) / len(gap) if gap else None,
        "scientific_success": False,
        "global_questions_closed": [],
        "limitations": [
            "External model identity/provider requests/usage are supplied, not attested.",
            "Equal declared tool eligibility does not prove equal actual access.",
            "Only original mathematical answers are independently verified.",
            "No complete compute/energy/RAM/VRAM/investment or provider invoices audited.",
            "Reported resources must charge all tool attempts, proof and retries; intake does not attest this.",
            "Holdout, generalization and F1 require separate gates."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="F0 opened paired original-certification diagnostic")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    receipts = [json.loads(line) for line in args.receipts.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    report = audit_opened(manifest, receipts)
    text = canonical(report) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
