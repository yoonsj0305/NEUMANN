"""Runtime-0.2 compact pointer-action repair.

Opened interface-repair candidate only. It removes native function schemas and
processor response parsing from the critical path. The frozen model emits one
small JSON action; deterministic tools and the original checker retain authority.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from time import perf_counter_ns

from neumann1.general_runtime_v106 import (
    ARMS, FAMILIES, ToolPool, canonical, milliseconds, reduce_original, sha,
    verify_original,
)

SCHEMA = "neumann.general-runtime-compact.v1062.v1"


@dataclass(frozen=True)
class CompactLimits:
    context_tokens: int = 4096
    admission_tokens: int = 240
    output_tokens: int = 128
    per_call_tokens: int = 64
    model_calls: int = 2
    tool_calls: int = 6
    wall_ms: float = 120000.0
    tool_ms: float = 2000.0
    source_chars: int = 512

    def __post_init__(self):
        for key in (
            "context_tokens", "admission_tokens", "output_tokens", "per_call_tokens",
            "model_calls", "tool_calls", "source_chars"
        ):
            value = getattr(self, key)
            if type(value) is not int or value < 1:
                raise ValueError("positive integer cap required: " + key)
        for key in ("wall_ms", "tool_ms"):
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("positive finite deadline required")
        if self.admission_tokens > self.context_tokens:
            raise ValueError("admission cap exceeds context cap")
        if self.per_call_tokens > self.output_tokens:
            raise ValueError("per-call cap exceeds complete-query output cap")


SYSTEM = (
    'One JSON only; no prose. '
    'f={"a":"f","v":answer}; '
    'c={"a":"c","t":"m|c|p","s":"Python source if p"}; '
    'r={"a":"r","k":["public fields"],"x":"m|c|p","s":"Python source if p"}. '
    'm=math,c=CSP,p=Python solve(items). Code shortest; no comments.'
)

ARM = {
    "B0": 'f only.',
    "B1": 'Solve carefully; f only.',
    "B2": 'Exactly one c; runtime executes/checks.',
    "B3": 'Use c or r; runtime executes/checks.',
    "N": 'r first; select necessary public fields and cheapest x.',
}


def _strip(raw):
    if type(raw) is not str:
        raise ValueError("raw text required")
    text = raw.strip()
    for token in ("<turn|>", "<eos>"):
        text = text.replace(token, "")
    text = text.strip()
    fence = chr(96) * 3
    if text.startswith(fence + "json") and text.endswith(fence):
        text = text[7:-3].strip()
    elif text.startswith(fence) and text.endswith(fence):
        text = text[3:-3].strip()
    return text


def parse_action(raw):
    """Parse only pre-registered complete JSON envelopes; never extract prose."""
    value = json.loads(_strip(raw))
    canonical(value)
    if type(value) is not dict:
        raise ValueError("action must be one object")

    if set(value) == {"answer"}:
        return {"a": "f", "v": value["answer"]}
    if value.get("action") == "final" and "answer" in value and set(value).issubset({"action", "answer"}):
        return {"a": "f", "v": value["answer"]}

    action = value.get("a")
    if action == "f":
        if "v" not in value or not set(value).issubset({"a", "v"}):
            raise ValueError("invalid compact final")
        return value
    if action == "c":
        if value.get("t") not in ("m", "c", "p") or not set(value).issubset({"a", "t", "s"}):
            raise ValueError("invalid compact compute action")
        if value["t"] == "p" and type(value.get("s")) is not str:
            raise ValueError("python compute requires source")
        return value
    if action == "r":
        if type(value.get("k")) is not list or any(type(x) is not str for x in value["k"]):
            raise ValueError("representation requires public-field pointers")
        if len(set(value["k"])) != len(value["k"]) or value.get("x") not in ("m", "c", "p"):
            raise ValueError("invalid compact representation")
        if not set(value).issubset({"a", "k", "x", "s"}):
            raise ValueError("unknown compact representation field")
        if value["x"] == "p" and type(value.get("s")) is not str:
            raise ValueError("python representation requires source")
        return value
    raise ValueError("unknown compact action")


def build_messages(task, arm, state=None):
    if arm not in ARMS:
        raise ValueError("registered arm required")
    payload = {"p": task}
    if state:
        payload["z"] = state
    return [
        {"role": "system", "content": SYSTEM + " " + ARM[arm]},
        {"role": "user", "content": canonical(payload)},
    ]


def _expected_executor(family):
    return {"math_logic": "m", "constraint_planning": "c", "coding": "p"}[family]


def _source(action, limits):
    source = action.get("s")
    if type(source) is not str or not source.strip() or len(source) > limits.source_chars:
        raise ValueError("bounded Python source required")
    return source


def certify_pointer_representation(task, action):
    """Certify model-selected pointers into the original public task.

    The runtime may materialize values only after the model selected their public
    field names. It never reconstructs a hidden answer or rewrites an obligation.
    """
    public = task["public"]
    family = task["family"]
    selected = set(action["k"])
    expected = {
        "math_logic": {"expression", "bindings"},
        "constraint_planning": {"domains", "constraints"},
        "coding": {"requirement"},
    }[family]
    if selected != expected:
        raise ValueError("insufficient or extra public-field pointers")
    if action["x"] != _expected_executor(family):
        raise ValueError("executor/family mismatch")

    if family == "math_logic":
        proposed = {"family": family, "expression": public["expression"]}
    elif family == "constraint_planning":
        proposed = {
            "family": family,
            "domains": public["domains"],
            "constraints": public["constraints"],
        }
    else:
        proposed = {"family": family, "requirement": public["requirement"]}

    certificate = reduce_original(task, proposed)
    certificate = json.loads(canonical(certificate))
    certificate["selected_public_fields"] = sorted(selected)
    certificate["pointer_semantics"] = "model-selected names -> exact original public values"
    return certificate


def _execute(task, action, pool, limits, left_ms, certificate=None):
    family = task["family"]
    code = action["x"] if action["a"] == "r" else action["t"]
    if code != _expected_executor(family):
        raise ValueError("executor/family mismatch")

    if certificate is None:
        public = task["public"]
        if family == "math_logic":
            args = {"expression": public["expression"], "bindings": public["bindings"]}
            result = pool.call("arithmetic", args, left_ms)
            return "arithmetic", args, result, result
        if family == "constraint_planning":
            args = {
                "spec": {"domains": public["domains"], "constraints": public["constraints"]},
                "strategy": "mrv",
            }
            result = pool.call("csp", args, left_ms)
            return "csp", args, result, result["assignment"]
        source = _source(action, limits)
        args = {"source": source, "inputs": [[]]}
        result = pool.call("python", args, left_ms)
        return "python", args, result, source

    ir = certificate["ir"]
    if family == "math_logic":
        args = {"expression": ir["expression"], "bindings": ir["bindings"]}
        result = pool.call("arithmetic", args, left_ms)
        return "arithmetic", args, result, result
    if family == "constraint_planning":
        args = {
            "spec": {"domains": ir["domains"], "constraints": ir["constraints"]},
            "strategy": "mrv",
        }
        result = pool.call("csp", args, left_ms)
        return "csp", args, result, result["assignment"]
    source = _source(action, limits)
    args = {"source": source, "inputs": [[]]}
    result = pool.call("python", args, left_ms)
    return "python", args, result, source


def run_compact(task, private, arm, core, limits=CompactLimits()):
    """Run one opened Runtime-0.2 compact candidate observation."""
    if arm not in ARMS or task["family"] not in FAMILIES:
        raise ValueError("registered strategy/family required")
    identity = json.loads(canonical(core.identity))
    if not identity.get("weights_frozen") or not identity.get("revision") or not identity.get("artifact_sha256"):
        raise ValueError("explicit frozen core identity required")

    started = perf_counter_ns()
    pool = ToolPool(task, private, limits)
    events = []
    model_calls = tool_calls = input_tokens = output_tokens = 0
    max_prompt_tokens = 0
    answer = None
    verified = False
    error = None
    verification_errors = []
    admission_blocked = False
    state = None

    def left():
        return limits.wall_ms - milliseconds(started)

    def check(candidate):
        began = perf_counter_ns()
        try:
            accepted = verify_original(task, candidate, private, min(limits.tool_ms, max(1.0, left())))
            if type(accepted) is not bool:
                raise ValueError("checker did not return Boolean")
            failure = None
        except Exception as exc:
            accepted = False
            failure = type(exc).__name__ + ": " + str(exc)
            verification_errors.append(failure)
        events.append({"kind": "verification", "accepted": accepted, "error": failure, "ms": milliseconds(began)})
        return accepted and left() >= 0

    try:
        while model_calls < limits.model_calls and output_tokens < limits.output_tokens and left() > 0:
            messages = build_messages(task, arm, state)
            prompt_tokens = core.count_tokens(messages, False)
            max_prompt_tokens = max(max_prompt_tokens, prompt_tokens)
            events.append({
                "kind": "prompt_admission",
                "tokens": prompt_tokens,
                "cap": limits.admission_tokens,
                "accepted": prompt_tokens <= limits.admission_tokens,
            })
            if prompt_tokens > limits.admission_tokens:
                admission_blocked = True
                raise ValueError("PROMPT_ADMISSION_BLOCKED:%d>%d" % (prompt_tokens, limits.admission_tokens))

            allowance = min(limits.per_call_tokens, limits.output_tokens - output_tokens)
            began = perf_counter_ns()
            model_calls += 1
            events.append({"kind": "model_start", "call": model_calls, "remaining_ms": left(), "thinking": False})
            result = core.generate(messages, allowance, False, left())
            events.append({"kind": "model_result", "call": model_calls, "receipt": result, "ms": milliseconds(began)})

            if type(result.get("input_tokens")) is not int or type(result.get("output_tokens")) is not int:
                raise ValueError("actual token counts required")
            if result["input_tokens"] != prompt_tokens:
                raise ValueError("prompt token accounting drift")
            if not 0 <= result["output_tokens"] <= allowance:
                raise ValueError("output token cap drift")
            input_tokens += result["input_tokens"]
            output_tokens += result["output_tokens"]
            if core.identity != identity:
                raise ValueError("weights/tokenizer/precision drift")
            if left() <= 0 or result.get("deadline_reached"):
                raise TimeoutError("complete generation deadline; receipt retained")

            try:
                action = parse_action(result["raw"])
            except Exception as exc:
                events.append({"kind": "action_rejected", "error": type(exc).__name__ + ": " + str(exc)})
                if arm in ("B0", "B1", "B2"):
                    error = "invalid one-shot compact response"
                    break
                state = {"e": "invalid_action"}
                continue

            if action["a"] == "f":
                if arm in ("B2", "B3", "N"):
                    raise ValueError("tool/representation action required by repair arm")
                answer = action["v"]
                verified = check(answer)
                if verified or arm in ("B0", "B1"):
                    break
                state = {"e": "original_check_false"}
                continue

            if arm in ("B0", "B1"):
                raise ValueError("direct repair arm may not execute tools")
            if arm == "B2" and action["a"] != "c":
                raise ValueError("B2 requires compact compute")
            if arm == "N" and action["a"] != "r":
                raise ValueError("N requires compact representation")
            if tool_calls >= limits.tool_calls:
                raise ValueError("complete tool-call cap")

            certificate = None
            if action["a"] == "r":
                tool_calls += 1
                began = perf_counter_ns()
                events.append({"kind": "tool_start", "tool": "reduce_pointer", "args": {"k": action["k"], "x": action["x"]}})
                try:
                    certificate = certify_pointer_representation(task, action)
                    events.append({"kind": "tool_result", "tool": "reduce_pointer", "result": certificate, "ms": milliseconds(began)})
                except Exception as exc:
                    outcome = {"error": type(exc).__name__ + ": " + str(exc)}
                    events.append({"kind": "tool_result", "tool": "reduce_pointer", "result": outcome, "ms": milliseconds(began)})
                    if arm in ("B3", "N"):
                        state = {"e": "representation_rejected"}
                        continue
                    raise

            if tool_calls >= limits.tool_calls:
                raise ValueError("complete tool-call cap")
            began = perf_counter_ns()
            try:
                name, args, outcome, candidate = _execute(task, action, pool, limits, left(), certificate)
                tool_calls += 1
                events.append({"kind": "tool_start", "tool": name, "args": args})
                events.append({"kind": "tool_result", "tool": name, "result": outcome, "ms": milliseconds(began)})
            except Exception as exc:
                tool_calls += 1
                events.append({"kind": "tool_start", "tool": "executor", "args": {"code": action.get("t") or action.get("x")}})
                events.append({"kind": "tool_result", "tool": "executor", "error": type(exc).__name__ + ": " + str(exc), "ms": milliseconds(began)})
                if arm == "B2":
                    error = "compact tool execution failed"
                    break
                state = {"e": "tool_failed"}
                continue

            answer = candidate
            verified = check(candidate)
            if verified:
                break
            if arm == "B2":
                break
            state = {"e": "original_check_false"}

        if not verified and error is None:
            error = "CAPABILITY_OR_BUDGET_UNREACHED"
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)

    elapsed = milliseconds(started)
    return {
        "schema": SCHEMA,
        "arm": arm,
        "task_id": task["id"],
        "family": task["family"],
        "task_sha256": sha(task),
        "core": identity,
        "limits": asdict(limits),
        "reasoning_policy": "compact_pointer_actions_hidden_thinking_disabled",
        "answer": answer,
        "accepted": bool(verified and elapsed <= limits.wall_ms),
        "verification_errors": verification_errors,
        "error": error,
        "model_calls": model_calls,
        "tool_calls": tool_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "max_prompt_tokens": max_prompt_tokens,
        "admission_blocked": admission_blocked,
        "token_accounting_complete": sum(event["kind"] == "model_result" for event in events) == model_calls,
        "complete_ms": elapsed,
        "events": events,
        "trace_sha256": sha(events),
        "new_fitting": False,
        "evidence_kind": core.identity.get("evidence_kind", "unattested"),
        "resources": {
            "latency_ms": {"status": "measured", "value": elapsed},
            "compute": {"status": "unavailable", "value": None},
            "energy_j": {"status": "unavailable", "value": None},
            "cost": {"status": "unavailable", "value": None},
        },
    }
