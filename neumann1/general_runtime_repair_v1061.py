"""Runtime-0.1 repair candidate: native Gemma actions + bounded external reasoning.

This file does not modify or reinterpret Runtime-0 first-run evidence. It is a
separately named opened repair candidate. No training, holdout access or frontier
calls are performed here.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from time import perf_counter_ns

from neumann1.general_runtime_v106 import (
    ARMS, FAMILIES, MODEL_ID, MODEL_REVISION, ToolPool, canonical,
    milliseconds, reduce_original, sha, verify_original,
)

REPAIR_SCHEMA = "neumann.general-runtime-repair.v1061.v1"


@dataclass(frozen=True)
class RepairLimits:
    context_tokens: int = 4096
    output_tokens: int = 512
    per_call_tokens: int = 96
    model_calls: int = 4
    tool_calls: int = 6
    wall_ms: float = 120000.0
    tool_ms: float = 2000.0

    def __post_init__(self):
        for key in ("context_tokens", "output_tokens", "per_call_tokens", "model_calls", "tool_calls"):
            value = getattr(self, key)
            if type(value) is not int or value < 1:
                raise ValueError("positive integer cap required: " + key)
        for key in ("wall_ms", "tool_ms"):
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("positive finite deadline required")
        if self.per_call_tokens > self.output_tokens:
            raise ValueError("per-call cap exceeds complete query output cap")


SYSTEM = (
    "You are a bounded action controller. Do not narrate chain-of-thought. "
    "Take one action per turn. If a tool is useful, call exactly one declared tool. "
    "Otherwise return exactly one JSON object {\"answer\":...}. "
    "After a tool result, either call one next permitted tool or return the final JSON. "
    "Never wrap a tool call in prose. The runtime independently checks the original task."
)

ARM_PROMPTS = {
    "B0": "Answer directly. No tools are available.",
    "B1": "Solve carefully but return only the final JSON. No tools are available.",
    "B2": "You may make at most one tool call, then return the final JSON.",
    "B3": "Use the cheapest useful declared tool steps, then return the final JSON.",
    "N": (
        "Your first action must be the represent tool. Preserve every necessary original field, "
        "drop only irrelevant marked background/unused bindings, and select the cheapest executor. "
        "The runtime certifies the representation, executes it, and checks the original task."
    ),
}


def _fn(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _schemas(arm):
    if arm in ("B0", "B1"):
        return []
    common = [
        _fn(
            "arithmetic",
            "Evaluate a bounded exact rational expression.",
            {
                "expression": {"type": "string", "description": "Original arithmetic expression."},
                "bindings": {"type": "object", "description": "Integer variable bindings."},
            },
            ["expression", "bindings"],
        ),
        _fn(
            "csp",
            "Solve a bounded finite integer constraint problem.",
            {
                "domains": {"type": "object", "description": "Variable to finite integer-list domains."},
                "constraints": {"type": "array", "description": "Original [op,left,right] constraints.", "items": {"type": "array"}},
                "strategy": {"type": "string", "enum": ["mrv", "enumerate"], "description": "Search strategy."},
            },
            ["domains", "constraints", "strategy"],
        ),
        _fn(
            "python",
            "Execute bounded pure Python source defining solve(items).",
            {
                "source": {"type": "string", "description": "Python source defining solve(items)."},
                "inputs": {"type": "array", "description": "Public inputs to execute.", "items": {"type": "array"}},
            },
            ["source", "inputs"],
        ),
    ]
    represent = _fn(
        "represent",
        "Create an exact typed representation and choose its deterministic executor.",
        {
            "family": {"type": "string", "enum": ["math_logic", "coding", "constraint_planning"], "description": "Original task family."},
            "expression": {"type": "string", "description": "Exact original expression for math; empty otherwise."},
            "bindings": {"type": "object", "description": "Original bindings needed by the expression; empty otherwise."},
            "domains": {"type": "object", "description": "Exact original domains for planning; empty otherwise."},
            "constraints": {"type": "array", "description": "Exact original constraints for planning; empty otherwise.", "items": {"type": "array"}},
            "requirement": {"type": "string", "description": "Exact original coding requirement; empty otherwise."},
            "executor": {"type": "string", "enum": ["arithmetic", "csp", "python"], "description": "Deterministic executor."},
            "source": {"type": "string", "description": "Python source when executor is python; empty otherwise."},
        },
        ["family", "executor"],
    )
    return ([represent] + common) if arm in ("N", "B3") else common


def _strip_fence(text):
    text = text.strip()
    for token in ("<turn|>", "<eos>"):
        text = text.replace(token, "")
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    return text


def parse_final(content):
    """Normalize only two pre-registered final envelopes; never infer an answer."""
    value = json.loads(_strip_fence(content))
    canonical(value)
    if type(value) is not dict:
        raise ValueError("final response must be an object")
    if set(value) == {"answer"}:
        return value["answer"]
    if value.get("action") == "final" and set(value).issubset({"action", "answer"}) and "answer" in value:
        return value["answer"]
    raise ValueError("invalid final envelope")


def _tool_call(parsed):
    calls = parsed.get("tool_calls") if type(parsed) is dict else None
    if calls is None or calls == []:
        return None
    if type(calls) is not list or len(calls) != 1:
        raise ValueError("exactly one native tool call per model turn")
    call = calls[0]
    function = call.get("function") if type(call) is dict else None
    if type(function) is not dict or type(function.get("name")) is not str or type(function.get("arguments")) is not dict:
        raise ValueError("malformed native tool call")
    return call


def _representation(task, args):
    if args.get("family") != task["family"]:
        raise ValueError("representation family mismatch")
    public = task["public"]
    family = task["family"]
    if family == "math_logic":
        if args.get("expression") != public["expression"] or type(args.get("bindings")) is not dict:
            raise ValueError("math representation must carry exact original expression and bindings")
        ir = {"family": family, "expression": args["expression"]}
        certified = reduce_original(task, ir)
        required = certified["ir"]["bindings"]
        if any(args["bindings"].get(k) != v for k, v in required.items()):
            raise ValueError("math representation binding mismatch")
        return certified
    elif family == "constraint_planning":
        if args.get("domains") != public["domains"] or args.get("constraints") != public["constraints"]:
            raise ValueError("planning representation must carry exact original domains/constraints")
        ir = {"family": family, "domains": args["domains"], "constraints": args["constraints"]}
    else:
        if args.get("requirement") != public["requirement"]:
            raise ValueError("coding representation must carry exact original requirement")
        ir = {"family": family, "requirement": args["requirement"]}
    certified = reduce_original(task, ir)
    return certified


def _native_to_pool(name, args):
    if name == "arithmetic":
        return name, {"expression": args["expression"], "bindings": args.get("bindings", {})}
    if name == "csp":
        return name, {
            "spec": {"domains": args["domains"], "constraints": args["constraints"]},
            "strategy": args["strategy"],
        }
    if name == "python":
        return name, {"source": args["source"], "inputs": args.get("inputs", [[]])}
    raise ValueError("undeclared native tool")


def _assistant_message(parsed):
    msg = {"role": "assistant", "content": parsed.get("content") or ""}
    if parsed.get("tool_calls"):
        msg["tool_calls"] = parsed["tool_calls"]
    # Thinking is intentionally disabled for this candidate. Do not manufacture it.
    return msg


def run_repair(task, private, arm, core, limits=RepairLimits()):
    """Run the separately named opened repair candidate.

    Core contract:
      count_tokens(messages, tools, thinking=False) -> int
      generate(messages, tools, max_tokens, thinking=False, deadline_ms) -> receipt
    A receipt must contain raw bytes, parsed response, and actual token counts.
    """
    if arm not in ARMS or task["family"] not in FAMILIES:
        raise ValueError("registered strategy/family required")
    identity = json.loads(canonical(core.identity))
    if not identity.get("weights_frozen") or not identity.get("revision") or not identity.get("artifact_sha256"):
        raise ValueError("explicit frozen core identity required")

    start = perf_counter_ns()
    pool = ToolPool(task, private, limits)
    messages = [
        {"role": "system", "content": SYSTEM + " " + ARM_PROMPTS[arm]},
        {"role": "user", "content": canonical(task)},
    ]
    events = []
    model_calls = tool_calls = input_tokens = output_tokens = 0
    answer = None
    verified = False
    error = None
    verification_errors = []
    represented = False
    b2_used_tool = False

    def left():
        return limits.wall_ms - milliseconds(start)

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
            tools = _schemas(arm)
            if arm == "B2" and b2_used_tool:
                tools = []
            if arm == "N" and not represented:
                tools = [t for t in tools if t["function"]["name"] == "represent"]
            if core.count_tokens(messages, tools, False) > limits.context_tokens:
                raise ValueError("context cap; no silent truncation")

            allowance = min(limits.per_call_tokens, limits.output_tokens - output_tokens)
            began = perf_counter_ns()
            model_calls += 1
            events.append({"kind": "model_start", "call": model_calls, "remaining_ms": left(), "thinking": False})
            result = core.generate(messages, tools, allowance, False, left())
            events.append({"kind": "model_result", "call": model_calls, "receipt": result, "ms": milliseconds(began)})

            if type(result.get("input_tokens")) is not int or type(result.get("output_tokens")) is not int:
                raise ValueError("actual token counts required")
            if not 0 <= result["output_tokens"] <= allowance or not 0 <= result["input_tokens"] <= limits.context_tokens:
                raise ValueError("token cap or accounting drift")
            input_tokens += result["input_tokens"]
            output_tokens += result["output_tokens"]
            if core.identity != identity:
                raise ValueError("weights/tokenizer/precision drift")
            if left() <= 0 or result.get("deadline_reached"):
                raise TimeoutError("complete generation deadline; receipt retained")

            parsed = result.get("parsed")
            if type(parsed) is not dict:
                raise ValueError("structured processor response required")
            call = _tool_call(parsed)

            if call is None:
                if arm == "N" and not represented:
                    raise ValueError("NEUMANN must represent before final")
                answer = parse_final(parsed.get("content") or "")
                verified = check(answer)
                if verified or arm in ("B0", "B1", "B2"):
                    break
                messages.append({"role": "assistant", "content": parsed.get("content") or ""})
                messages.append({"role": "user", "content": "Original checker returned false. Take one bounded corrective action."})
                continue

            if arm in ("B0", "B1"):
                raise ValueError("baseline strategy action restriction")
            if arm == "B2" and b2_used_tool:
                raise ValueError("B2 tool-call cap")
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            if arm == "N" and not represented and name != "represent":
                raise ValueError("NEUMANN first action must be represent")
            if tool_calls >= limits.tool_calls:
                raise ValueError("complete tool-call cap")

            messages.append(_assistant_message(parsed))

            if name == "represent":
                tool_calls += 1
                began = perf_counter_ns()
                events.append({"kind": "tool_start", "tool": "reduce", "args": args})
                try:
                    certified = _representation(task, args)
                    events.append({"kind": "tool_result", "tool": "reduce", "result": certified, "ms": milliseconds(began)})
                except Exception as exc:
                    outcome = {"error": type(exc).__name__ + ": " + str(exc)}
                    events.append({"kind": "tool_result", "tool": "reduce", "result": outcome, "ms": milliseconds(began)})
                    messages.append({"role": "tool", "name": "represent", "content": canonical(outcome)})
                    if arm == "N":
                        continue
                    raise

                represented = True
                executor = args.get("executor")
                ir = certified["ir"]
                if executor == "arithmetic" and ir["family"] == "math_logic":
                    execution_args = {"expression": ir["expression"], "bindings": ir["bindings"]}
                elif executor == "csp" and ir["family"] == "constraint_planning":
                    execution_args = {"spec": {"domains": ir["domains"], "constraints": ir["constraints"]}, "strategy": "mrv"}
                elif executor == "python" and ir["family"] == "coding" and type(args.get("source")) is str:
                    execution_args = {"source": args["source"], "inputs": [[]]}
                else:
                    raise ValueError("executor/representation mismatch")
                if tool_calls >= limits.tool_calls:
                    raise ValueError("complete tool-call cap")
                tool_calls += 1
                began = perf_counter_ns()
                events.append({"kind": "tool_start", "tool": executor, "args": execution_args})
                try:
                    executed = pool.call(executor, execution_args, left())
                    events.append({"kind": "tool_result", "tool": executor, "result": executed, "ms": milliseconds(began)})
                    candidate = (
                        executed if executor == "arithmetic"
                        else executed["assignment"] if executor == "csp"
                        else args["source"]
                    )
                    answer = candidate
                    verified = check(candidate)
                    messages.append({
                        "role": "tool",
                        "name": "represent",
                        "content": canonical({"certified": certified, "executor": executor, "result": executed, "original_check": verified}),
                    })
                    if verified:
                        break
                except Exception as exc:
                    outcome = {"error": type(exc).__name__ + ": " + str(exc)}
                    events.append({"kind": "tool_result", "tool": executor, "result": outcome, "ms": milliseconds(began)})
                    messages.append({"role": "tool", "name": "represent", "content": canonical(outcome)})
                continue

            native_name, native_args = _native_to_pool(name, args)
            tool_calls += 1
            if arm == "B2":
                b2_used_tool = True
            began = perf_counter_ns()
            events.append({"kind": "tool_start", "tool": native_name, "args": native_args})
            try:
                outcome = pool.call(native_name, native_args, left())
            except Exception as exc:
                outcome = {"error": type(exc).__name__ + ": " + str(exc)}
            events.append({"kind": "tool_result", "tool": native_name, "result": outcome, "ms": milliseconds(began)})
            messages.append({"role": "tool", "name": name, "content": canonical(outcome)})

        if not verified and error is None:
            error = "CAPABILITY_OR_BUDGET_UNREACHED"
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)

    elapsed = milliseconds(start)
    return {
        "schema": REPAIR_SCHEMA,
        "arm": arm,
        "task_id": task["id"],
        "family": task["family"],
        "task_sha256": sha(task),
        "core": identity,
        "limits": asdict(limits),
        "reasoning_policy": "native_actions_hidden_thinking_disabled",
        "answer": answer,
        "accepted": bool(verified and elapsed <= limits.wall_ms),
        "verification_errors": verification_errors,
        "error": error,
        "model_calls": model_calls,
        "tool_calls": tool_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "token_accounting_complete": sum(e["kind"] == "model_result" for e in events) == model_calls,
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
