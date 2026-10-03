"""P0 non-generative control: scoring is advisory; original verification decides.

No model loading, generation, fitting, benchmark labels or hidden answers here.
Scorers/executors are injected; synthetic contract tests are not model evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from time import perf_counter_ns

ROUTES = ("DIRECT", "ARITHMETIC", "CSP", "PYTHON")
SCHEMA = "neumann.control-plane-pivot.v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def snapshot(value):
    return json.loads(canonical(value))


def finite(value, nonnegative=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError("finite numeric value required")
    return float(value)


@dataclass(frozen=True)
class EncodedChoice:
    prompt_ids: tuple[int, ...]
    label_ids: tuple[int, ...]

    def validate(self):
        if not self.prompt_ids or not self.label_ids:
            raise ValueError("nonempty prompt and forced label required")
        if any(type(i) is not int or i < 0 for i in self.prompt_ids + self.label_ids):
            raise ValueError("nonnegative integer token IDs required")


@dataclass(frozen=True)
class ScorePlan:
    rows: tuple[EncodedChoice, ...]
    prompt_count: int
    labels: tuple[str, ...]

    def validate(self):
        if type(self.prompt_count) is not int or self.prompt_count < 1:
            raise ValueError("prompt count required")
        if not self.labels or len(set(self.labels)) != len(self.labels):
            raise ValueError("unique fixed labels required")
        if len(self.rows) != self.prompt_count * len(self.labels):
            raise ValueError("prompt-major row coverage required")
        for row in self.rows:
            row.validate()

    @property
    def evaluated_tokens(self):
        return sum(len(r.prompt_ids) + len(r.label_ids) for r in self.rows)

    @property
    def scored_tokens(self):
        return sum(len(r.label_ids) for r in self.rows)


@dataclass(frozen=True)
class ScoreResult:
    scores: tuple[tuple[float, ...], ...]
    forward_calls: int
    padded_tokens: int
    peak_accelerator_memory_bytes: int | None = None


class ScoreFailure(RuntimeError):
    """Partial tensor work survives a timeout or backend failure."""
    def __init__(self, reason, forward_calls, padded_tokens, complete_ms):
        super().__init__(reason)
        self.forward_calls = forward_calls
        self.padded_tokens = padded_tokens
        self.complete_ms = complete_ms


@dataclass(frozen=True)
class ExecutionResult:
    answer: object
    generated_tokens: int = 0
    model_calls: int = 0
    tool_calls: int = 1


@dataclass(frozen=True)
class ControlBudget:
    context_tokens: int = 4096
    evaluated_tokens: int = 32768
    forward_calls: int = 32
    score_rows: int = 256
    evidence_atoms: int = 32
    attempts: int = 32
    generated_tokens: int = 512
    model_calls: int = 4
    tool_calls: int = 16
    wall_ms: float = 120000.0

    def validate(self):
        for key, value in vars(self).items():
            if key == "wall_ms":
                if finite(value, True) <= 0:
                    raise ValueError("positive wall budget required")
            elif type(value) is not int or value < 1:
                raise ValueError("positive integer budgets required")


@dataclass(frozen=True)
class CostEstimate:
    ms: float
    provenance: str

    def validate(self):
        finite(self.ms, True)
        if type(self.provenance) is not str or not self.provenance.strip():
            raise ValueError("cost-estimate provenance required")


def public_view(view):
    # Model visibility is an explicit allowlist, not a filter of the task record.
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("only instruction/public may enter the controller")
    if type(view["instruction"]) is not str or type(view["public"]) is not dict:
        raise ValueError("public problem required")
    if not view["public"] or any(type(k) is not str or not k for k in view["public"]):
        raise ValueError("nonempty named evidence atoms required")
    return snapshot(view)


def route_prompt(instruction, evidence):
    return "Select one executor label.\n" + canonical({"instruction": instruction, "public": evidence})


def relevance_prompt(view, key):
    return "Score whether the named public field is necessary for solving the original problem.\n" + canonical({"problem": view, "field": key})


def route_order(scores, costs, cost_weight):
    if len(scores) != len(ROUTES) or set(costs) != set(ROUTES):
        raise ValueError("all fixed routes and cost estimates required")
    finite(cost_weight, True)
    for estimate in costs.values():
        estimate.validate()
    adjusted = [finite(score) - cost_weight * costs[route].ms for route, score in zip(ROUTES, scores)]
    # Exact ties use frozen candidate order, never task/family labels.
    return tuple(ROUTES[i] for i in sorted(range(len(ROUTES)), key=lambda i: (-adjusted[i], i)))


def run_control(view, arm, scorer, execute, verify_original, costs, cost_weight=0.0,
                budget=ControlBudget()):
    """Bounded P0 wiring. Callbacks must enforce the supplied remaining deadline.

    DIRECT submits a normal typed answer via execute, never a control JSON.
    TOOL scores full public input. NEUMANN ranks KEEP-DROP, then grows prefixes
    one atom at a time. Route failures try remaining routes before adding evidence.
    Only a boolean from the original verifier is used; no solution feedback.
    """
    original = public_view(view)
    budget.validate()
    if arm not in ("DIRECT", "TOOL", "NEUMANN"):
        raise ValueError("registered arm required")
    if len(original["public"]) > budget.evidence_atoms:
        raise ValueError("evidence atom admission cap")
    route_order((0.0,) * len(ROUTES), costs, cost_weight)
    identity = snapshot(scorer.identity)
    if identity.get("weights_frozen") is not True:
        raise ValueError("frozen scorer identity required")
    started = perf_counter_ns()
    counts = dict(evaluated_tokens=0, scored_tokens=0, forward_calls=0, score_rows=0,
                  padded_tokens=0, generated_tokens=0, model_calls=0, tool_calls=0, attempts=0)
    events = []
    accepted = False
    answer = None
    error = None

    def remaining():
        return budget.wall_ms - (perf_counter_ns() - started) / 1e6

    def check_deadline():
        if remaining() <= 0:
            raise TimeoutError("complete controller deadline")
        if scorer.identity != identity:
            raise ValueError("frozen scorer identity drift")

    def score(prompts, labels):
        check_deadline()
        began = perf_counter_ns()
        plan = scorer.prepare(tuple(prompts), tuple(labels))
        plan.validate()
        if plan.prompt_count != len(prompts) or plan.labels != tuple(labels):
            raise ValueError("scoring request/plan mismatch")
        if max(len(r.prompt_ids) + len(r.label_ids) for r in plan.rows) > budget.context_tokens:
            raise ValueError("context admission; silent truncation forbidden")
        if counts["evaluated_tokens"] + plan.evaluated_tokens > budget.evaluated_tokens:
            raise ValueError("evaluated token admission")
        if counts["score_rows"] + len(plan.rows) > budget.score_rows:
            raise ValueError("scoring row admission")
        upper = scorer.forward_bound(plan)
        if type(upper) is not int or upper < 1 or counts["forward_calls"] + upper > budget.forward_calls:
            raise ValueError("forward admission")
        event = {"kind": "score", "request_sha256": digest([prompts, labels]),
                 "plan_sha256": digest([vars(r) for r in plan.rows]), "status": "STARTED",
                 "plan_rows": [vars(r) for r in plan.rows], "labels": list(labels),
                 "evaluated_tokens": plan.evaluated_tokens, "scored_tokens": plan.scored_tokens,
                 "score_rows": len(plan.rows), "generated_tokens": 0}
        events.append(event)
        counts["evaluated_tokens"] += plan.evaluated_tokens
        counts["scored_tokens"] += plan.scored_tokens
        counts["score_rows"] += len(plan.rows)
        try:
            result = scorer.evaluate(plan, remaining())
        except ScoreFailure as exc:
            counts["forward_calls"] += exc.forward_calls
            counts["padded_tokens"] += exc.padded_tokens
            event.update(forward_calls=exc.forward_calls, padded_tokens=exc.padded_tokens,
                         complete_ms=exc.complete_ms, error=str(exc), accounting_complete=False)
            raise
        # A failed forward remains STARTED/unknown; never invent completed counts.
        if type(result.forward_calls) is not int or not 1 <= result.forward_calls <= upper:
            raise ValueError("forward accounting mismatch")
        counts["forward_calls"] += result.forward_calls
        if type(result.padded_tokens) is not int or result.padded_tokens < plan.evaluated_tokens:
            raise ValueError("padding accounting mismatch")
        counts["padded_tokens"] += result.padded_tokens
        if len(result.scores) != len(prompts) or any(len(r) != len(labels) for r in result.scores):
            raise ValueError("score matrix mismatch")
        values = tuple(tuple(finite(v) for v in row) for row in result.scores)
        event.update(status="COMPLETE", scores=values, forward_calls=result.forward_calls,
                     padded_tokens=result.padded_tokens,
                     peak_accelerator_memory_bytes=result.peak_accelerator_memory_bytes,
                     complete_ms=(perf_counter_ns() - began) / 1e6)
        check_deadline()
        return values

    try:
        keys = sorted(original["public"])
        if arm == "NEUMANN":
            values = score([relevance_prompt(original, key) for key in keys], ("KEEP", "DROP"))
            priority = {key: row[0] - row[1] for key, row in zip(keys, values)}
            keys.sort(key=lambda key: (-priority[key], key))
            events.append({"kind": "evidence_order", "keys": keys, "scores": priority})
            sizes = range(1, len(keys) + 1)
        else:
            sizes = (len(keys),)
        for size in sizes:
            evidence = {key: original["public"][key] for key in keys[:size]}
            routes = ("DIRECT",) if arm == "DIRECT" else route_order(
                score([route_prompt(original["instruction"], evidence)], ROUTES)[0],
                costs, cost_weight if arm == "NEUMANN" else 0.0)
            for route in routes:
                check_deadline()
                if counts["attempts"] >= budget.attempts:
                    raise ValueError("attempt cap")
                if counts["model_calls"] >= budget.model_calls or counts["tool_calls"] >= budget.tool_calls:
                    raise ValueError("execution resource cap")
                if counts["generated_tokens"] >= budget.generated_tokens:
                    raise ValueError("answer generation cap")
                counts["attempts"] += 1
                event = {"kind": "execution", "route": route, "keys": list(evidence), "status": "STARTED"}
                events.append(event)
                began = perf_counter_ns()
                allowances = {key: getattr(budget, key) - counts[key]
                              for key in ("generated_tokens", "model_calls", "tool_calls")}
                result = execute(route, snapshot({"instruction": original["instruction"], "public": evidence}),
                                 remaining(), allowances)
                if not isinstance(result, ExecutionResult):
                    raise ValueError("execution receipt required, including failed routes")
                for key in allowances:
                    value = getattr(result, key)
                    if type(value) is not int or not 0 <= value <= allowances[key]:
                        raise ValueError("execution receipt budget mismatch")
                    counts[key] += value
                answer = snapshot(result.answer)
                event.update(status="COMPLETE", answer=answer, complete_ms=(perf_counter_ns() - began) / 1e6,
                             **{key: getattr(result, key) for key in allowances})
                check_deadline()
                began = perf_counter_ns()
                verification = {"kind": "original_verification", "status": "STARTED"}
                events.append(verification)
                ok = verify_original(snapshot(answer), remaining())
                if type(ok) is not bool:
                    raise ValueError("original verifier must return boolean only")
                verification.update(status="COMPLETE", accepted=ok,
                                    complete_ms=(perf_counter_ns() - began) / 1e6)
                check_deadline()
                if ok:
                    accepted = True
                    break
            if accepted:
                break
        if not accepted:
            error = "EXHAUSTED_EVIDENCE_OR_ROUTES"
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    complete_ms = (perf_counter_ns() - started) / 1e6
    return {"schema": SCHEMA, "arm": arm, "accepted": accepted, "answer": answer, "error": error,
            "counts": counts, "complete_ms": complete_ms, "events": events,
            "budget": vars(budget), "cost_estimates": {route: vars(costs[route]) for route in ROUTES},
            "cost_weight_nats_per_ms": cost_weight if arm == "NEUMANN" else 0.0,
            "original_sha256": digest(original), "core_sha256": digest(identity),
            "trace_sha256": digest(events), "accounting_complete": all(e.get("status") != "STARTED" for e in events),
            "general_capability_gate": "NOT_EVALUATED", "global_questions_closed": [],
            "energy_j": None, "flops": None, "cost_money": None}
