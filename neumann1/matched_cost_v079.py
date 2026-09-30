"""Serial, shared-authority measurements; reports are not Q3/Q4 certificates."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from math import isfinite
from random import Random
from statistics import mean
from time import perf_counter_ns
from typing import Callable


ROLES = ("direct_deterministic", "direct_answer", "direct_program",
         "neumann", "no_compression")
DIRECT_ROLES = ROLES[:3]


class Scope(str, Enum):
    ORIGINAL = "VERIFIED_ORIGINAL_TASK"
    LABEL = "DATASET_LABEL_MATCH"
    EXPRESSION = "EXPRESSION_ONLY"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Verification:
    scope: Scope
    evidence_ref: str


@dataclass(frozen=True)
class Case:
    case_id: str
    text: str


@dataclass(frozen=True)
class Path:
    role: str
    model_ref: str
    training_data_ref: str
    budget_ref: str
    representation_ref: str
    training_examples: int
    training_ms: float
    teacher_ms: float
    cold_load_ms: float
    propose: Callable[[str], object]


@dataclass(frozen=True)
class Protocol:
    protocol_ref: str
    hardware_ref: str
    runtime_ref: str
    verifier_ref: str
    warmup_policy: str
    case_ids: tuple[str, ...]
    repeats: int = 3
    order_seed: int = 7901


def _nonnegative(value: object) -> bool:
    return type(value) in (int, float) and isfinite(value) and value >= 0


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _declarations(paths: tuple[Path, ...]) -> dict:
    names = ("model_ref", "training_data_ref", "budget_ref", "representation_ref",
             "training_examples", "training_ms", "teacher_ms", "cold_load_ms")
    return {p.role: {name: getattr(p, name) for name in names} for p in paths}


def validate_design(protocol: Protocol, paths: tuple[Path, ...]) -> None:
    if (len(paths) != len(ROLES) or {p.role for p in paths} != set(ROLES)
            or len({p.role for p in paths}) != len(paths)):
        raise ValueError("all five distinct comparator roles required")
    if (not protocol.case_ids or any(not _text(x) for x in protocol.case_ids)
            or len(set(protocol.case_ids)) != len(protocol.case_ids)
            or type(protocol.repeats) is not int or protocol.repeats < 1
            or type(protocol.order_seed) is not int):
        raise ValueError("unique case IDs and positive repeat count required")
    if not all(_text(getattr(protocol, name)) for name in (
            "protocol_ref", "hardware_ref", "runtime_ref", "verifier_ref",
            "warmup_policy")):
        raise ValueError("explicit shared measurement contract required")
    for path in paths:
        if not all(_text(getattr(path, name)) for name in (
                "model_ref", "training_data_ref", "budget_ref", "representation_ref")):
            raise ValueError("actual path and budget references required")
        if (type(path.training_examples) is not int or path.training_examples < 0
                or not all(_nonnegative(getattr(path, name)) for name in (
                    "training_ms", "teacher_ms", "cold_load_ms"))
                or not callable(path.propose)):
            raise ValueError("invalid path cost/learner declaration")
    learned = [p for p in paths if p.role != "direct_deterministic"]
    if any(p.training_examples <= 0 for p in learned):
        raise ValueError("learned routes need declared training examples")
    if len({(p.training_data_ref, p.budget_ref, p.training_examples)
            for p in learned}) != 1:
        raise ValueError("learned training data/example/cap budgets must match")
    by_role = {p.role: p for p in paths}
    if by_role["neumann"].representation_ref != by_role["no_compression"].representation_ref:
        raise ValueError("ablation must preserve the representation contract")


def _attempt(text: str, path: Path, execute: Callable, verify: Callable) -> dict:
    stages = []
    scope, evidence, error = Scope.UNKNOWN, "", None

    def charge(name, function, *args):
        started = perf_counter_ns()
        try:
            return function(*args)
        finally:
            stages.append({"stage": name, "ms": (perf_counter_ns() - started) / 1e6})

    try:
        # No Case, gold answer, teacher equation, or evaluation ID enters a proposer.
        proposal = charge("proposal", path.propose, text)
        answer = charge("shared_execution", execute, text, proposal)
        result = charge("shared_verification", verify, text, answer)
        if (not isinstance(result, Verification) or not isinstance(result.scope, Scope)
                or not _text(result.evidence_ref)):
            raise ValueError("verifier must declare scope and evidence reference")
        scope, evidence = result.scope, result.evidence_ref
    except Exception as exc:
        # KeyboardInterrupt and SystemExit propagate. No rejected work is erased.
        error = f"{type(exc).__name__}: {exc}"
    return {"path_role": path.role, "stages": stages, "scope": scope.value,
            "evidence_ref": evidence, "error": error}


def measure(protocol: Protocol, cases: tuple[Case, ...], paths: tuple[Path, ...],
            *, execute: Callable, verify: Callable, fallback: bool = True) -> dict:
    """Use one executor/verifier instance across all routes, in shuffled serial order.

    Proposal includes every path-specific parse/model/reduction operation. Callers
    must run all work synchronously; background work is outside this contract.
    Shared callbacks are trusted inputs, not audited for semantic independence.
    """
    validate_design(protocol, paths)
    if (len(cases) != len(protocol.case_ids)
            or {c.case_id for c in cases} != set(protocol.case_ids)
            or any(not _text(c.text) for c in cases)):
        raise ValueError("exact observable corpus required")
    if not callable(execute) or not callable(verify) or type(fallback) is not bool:
        raise ValueError("shared synchronous callbacks and explicit fallback policy required")
    by_case, by_role = {c.case_id: c for c in cases}, {p.role: p for p in paths}
    schedule = [(c, r, repeat) for repeat in range(protocol.repeats)
                for c in protocol.case_ids for r in ROLES]
    Random(protocol.order_seed).shuffle(schedule)
    rows = []
    for case_id, role, repeat in schedule:
        case, path = by_case[case_id], by_role[role]
        start = perf_counter_ns()
        attempts = [_attempt(case.text, path, execute, verify)]
        if (fallback and role != "direct_deterministic"
                and attempts[0]["scope"] != Scope.ORIGINAL.value):
            attempts.append(_attempt(case.text, by_role["direct_deterministic"], execute, verify))
        elapsed = (perf_counter_ns() - start) / 1e6
        rows.append({"case_id": case_id, "role": role, "repeat": repeat,
                     "observable_sha256": sha256(case.text.encode()).hexdigest(),
                     "total_ms": elapsed, "attempts": attempts})
    return {"protocol_ref": protocol.protocol_ref, "hardware_ref": protocol.hardware_ref,
            "runtime_ref": protocol.runtime_ref, "verifier_ref": protocol.verifier_ref,
            "warmup_policy": protocol.warmup_policy, "fallback": fallback,
            "order_seed": protocol.order_seed, "repeats": protocol.repeats,
            "case_ids": list(protocol.case_ids),
            "path_costs": _declarations(paths), "rows": rows}


def summarize(protocol: Protocol, paths: tuple[Path, ...], report: dict) -> dict:
    """Audit completeness before emitting any iso-capability latency ratio.

    Descriptive arithmetic means, no confidence bound or generalization claim.
    Caller-supplied references/scope cannot certify data sealing or independence.
    """
    validate_design(protocol, paths)
    if report.get("path_costs") != _declarations(paths):
        raise ValueError("model/investment declaration drift")
    for key in ("protocol_ref", "hardware_ref", "runtime_ref", "verifier_ref", "warmup_policy"):
        if report.get(key) != getattr(protocol, key):
            raise ValueError("measurement contract drift")
    if type(report.get("fallback")) is not bool:
        raise ValueError("fallback policy missing")
    if (report.get("order_seed") != protocol.order_seed
            or report.get("repeats") != protocol.repeats
            or report.get("case_ids") != list(protocol.case_ids)):
        raise ValueError("schedule/corpus contract drift")
    expected = {(c, r, i) for c in protocol.case_ids for r in ROLES
                for i in range(protocol.repeats)}
    seen, hashes, totals = set(), {}, {r: [] for r in ROLES}
    verified, rescued = {r: 0 for r in ROLES}, {r: 0 for r in ROLES}
    for row in report["rows"]:
        if type(row.get("repeat")) is not int:
            raise ValueError("noninteger repeat")
        key = (row["case_id"], row["role"], row["repeat"])
        if key not in expected or key in seen:
            raise ValueError("duplicate or unexpected observation")
        seen.add(key)
        digest = row.get("observable_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("invalid observable digest")
        if hashes.setdefault(row["case_id"], digest) != digest:
            raise ValueError("unequal observable inputs")
        attempts = row["attempts"]
        allow_fallback = report["fallback"] and row["role"] != "direct_deterministic"
        if not (1 <= len(attempts) <= (2 if allow_fallback else 1)):
            raise ValueError("invalid attempt/fallback count")
        if attempts[0]["path_role"] != row["role"]:
            raise ValueError("primary path drift")
        primary_ok = attempts[0]["scope"] == Scope.ORIGINAL.value
        if len(attempts) != (2 if allow_fallback and not primary_ok else 1):
            raise ValueError("fallback omitted or run after success")
        if len(attempts) == 2 and attempts[1]["path_role"] != "direct_deterministic":
            raise ValueError("fallback authority drift")
        component_ms = 0.0
        for attempt in attempts:
            if attempt["scope"] not in {s.value for s in Scope}:
                raise ValueError("unknown verification scope")
            if attempt["scope"] != Scope.UNKNOWN.value and not _text(attempt["evidence_ref"]):
                raise ValueError("verification evidence missing")
            if attempt["error"] is not None and attempt["scope"] != Scope.UNKNOWN.value:
                raise ValueError("exception cannot establish capability")
            names = [stage["stage"] for stage in attempt["stages"]]
            if names not in (["proposal"], ["proposal", "shared_execution"],
                             ["proposal", "shared_execution", "shared_verification"]):
                raise ValueError("invalid serial stage sequence")
            if attempt["error"] is None and len(names) != 3:
                raise ValueError("completed attempt omitted execution/verification")
            for stage in attempt["stages"]:
                if not _nonnegative(stage["ms"]):
                    raise ValueError("invalid component time")
                component_ms += stage["ms"]
        if not _nonnegative(row["total_ms"]) or row["total_ms"] < component_ms:
            raise ValueError("total omitted attempted work")
        role = row["role"]
        totals[role].append(row["total_ms"])
        ok = attempts[-1]["scope"] == Scope.ORIGINAL.value
        verified[role] += ok
        rescued[role] += ok and len(attempts) == 2
    if seen != expected:
        raise ValueError("incomplete paired measurements")
    means = {r: mean(values) for r, values in totals.items()}
    count = len(protocol.case_ids) * protocol.repeats
    complete = all(v == count for v in verified.values())
    strongest = min(DIRECT_ROLES, key=lambda r: means[r]) if complete else None
    ratio = (means["neumann"] / means[strongest]
             if complete and means[strongest] > 0 else None)
    ablation_ratio = (means["neumann"] / means["no_compression"]
                      if complete and means["no_compression"] > 0 else None)
    # Incremental deployment investment: training + teacher cost. Cold loading
    # remains separate; no subtraction between different hardware is attempted.
    break_even = None
    if complete:
        costs = report["path_costs"]
        investment = lambda r: costs[r]["training_ms"] + costs[r]["teacher_ms"]
        saving = means[strongest] - means["neumann"]
        if saving > 0:
            break_even = max(0.0, investment("neumann") - investment(strongest)) / saving
    return {"status": "DESCRIPTIVE_COMPLETE" if complete else "CAPABILITY_UNREACHED",
            "verified_original_counts": verified, "rescued_counts": rescued,
            "observations_per_role": count, "mean_total_ms": means,
            "strongest_measured_direct": strongest, "neumann_direct_ratio": ratio,
            "neumann_ablation_ratio": ablation_ratio,
            "incremental_training_break_even_queries": break_even,
            "q3": "OPEN", "q4": "OPEN",
            "boundary": "Caller-declared semantics; no statistical or model-efficiency certificate."}
