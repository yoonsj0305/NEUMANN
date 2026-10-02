"""Three-arm opened Architecture Multiplier runtime.

DIRECT, TOOL and NEUMANN share the same frozen core, model-visible task, budgets
and original checker. TOOL may route to deterministic executors. NEUMANN must
first emit a certified pointer representation and executor choice.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict
from time import perf_counter_ns

from neumann1.general_multiplier_contract import ARMS, MultiplierBudget
from neumann1.general_runtime_v106 import (
    ToolPool,
    canonical,
    milliseconds,
    reduce_original,
    sha,
    verify_original,
)

SCHEMA = "neumann.architecture-multiplier-runtime.v1"

SYSTEM = (
    'Return one JSON object only in the final response. '
    'f={"a":"f","v":answer}; '
    't={"a":"t","t":"m|c|p","s":"Python source if p"}; '
    'r={"a":"r","k":["public field names"],"x":"m|c|p","s":"Python source if p"}. '
    'm=exact arithmetic, c=finite CSP, p=Python solve(items). '
    'No imports/files/network/eval in Python.'
)
ARM_PROMPTS = {
    "DIRECT": "Use f only. Solve the visible problem yourself.",
    "TOOL": "Use f or t. Choose tools only when useful.",
    "NEUMANN": (
        "First use r. Select only necessary public fields, choose the cheapest "
        "executor, and include source when x=p."
    ),
}


def model_messages(model_view, arm, state=None):
    if arm not in ARMS:
        raise ValueError("registered arm required")
    payload = {"problem": model_view}
    if state is not None:
        payload["state"] = state
    return [
        {"role": "system", "content": SYSTEM + " " + ARM_PROMPTS[arm]},
        {"role": "user", "content": canonical(payload)},
    ]


def parse_action(raw):
    if type(raw) is not str:
        raise ValueError("raw model text required")
    text = raw.strip()
    # Gemma thinking stays billed in the receipt. Parse only the final channel.
    if "<|channel>final" in text:
        text = text.rsplit("<|channel>final", 1)[-1].strip()
    elif "<channel|>" in text:
        text = text.rsplit("<channel|>", 1)[-1].strip()
    for token in ("<turn|>", "<eos>", "<|end|>"):
        text = text.replace(token, "")
    text = text.strip()
    fence = chr(96) * 3
    if text.startswith(fence + "json") and text.endswith(fence):
        text = text[7:-3].strip()
    elif text.startswith(fence) and text.endswith(fence):
        text = text[3:-3].strip()
    value = json.loads(text)
    canonical(value)
    if type(value) is not dict:
        raise ValueError("one action object required")
    a = value.get("a")
    if a == "f":
        if "v" not in value or not set(value).issubset({"a", "v"}):
            raise ValueError("invalid final action")
        return value
    if a == "t":
        if value.get("t") not in ("m", "c", "p") or not set(value).issubset({"a", "t", "s"}):
            raise ValueError("invalid tool action")
        if value["t"] == "p" and type(value.get("s")) is not str:
            raise ValueError("Python tool requires source")
        return value
    if a == "r":
        if type(value.get("k")) is not list or any(type(item) is not str for item in value["k"]):
            raise ValueError("representation pointers required")
        if len(set(value["k"])) != len(value["k"]):
            raise ValueError("duplicate representation pointer")
        if value.get("x") not in ("m", "c", "p") or not set(value).issubset({"a", "k", "x", "s"}):
            raise ValueError("invalid representation action")
        if value["x"] == "p" and type(value.get("s")) is not str:
            raise ValueError("Python representation requires source")
        return value
    raise ValueError("unknown action")


def _executor_code(family):
    return {
        "math_logic": "m",
        "constraint_planning": "c",
        "coding": "p",
    }[family]


def certify_representation(task, action):
    public = task["public"]
    expected = {
        "math_logic": {"expression", "bindings"},
        "constraint_planning": {"domains", "constraints"},
        "coding": {"requirement"},
    }[task["family"]]
    selected = set(action["k"])
    if selected != expected:
        raise ValueError("representation must select exactly the necessary public fields")
    if action["x"] != _executor_code(task["family"]):
        raise ValueError("representation executor/family mismatch")

    if task["family"] == "math_logic":
        proposed = {"family": task["family"], "expression": public["expression"]}
    elif task["family"] == "constraint_planning":
        proposed = {
            "family": task["family"],
            "domains": public["domains"],
            "constraints": public["constraints"],
        }
    else:
        proposed = {"family": task["family"], "requirement": public["requirement"]}

    certificate = json.loads(canonical(reduce_original(task, proposed)))
    certificate["selected_public_fields"] = sorted(selected)
    certificate["pointer_semantics"] = "model-selected public names -> exact original values"
    return certificate


def _execute(task, action, pool, budget, left_ms, certificate=None):
    code = action["x"] if action["a"] == "r" else action["t"]
    if code != _executor_code(task["family"]):
        raise ValueError("executor/family mismatch")

    public = task["public"]
    if certificate is not None:
        source = certificate["ir"]
    else:
        source = public

    if code == "m":
        args = {
            "expression": source["expression"],
            "bindings": source["bindings"],
        }
        result = pool.call("arithmetic", args, left_ms)
        return "arithmetic", args, result, result

    if code == "c":
        args = {
            "spec": {
                "domains": source["domains"],
                "constraints": source["constraints"],
            },
            "strategy": "mrv",
        }
        result = pool.call("csp", args, left_ms)
        return "csp", args, result, result["assignment"]

    python_source = action.get("s")
    if type(python_source) is not str or not python_source.strip() or len(python_source) > 2048:
        raise ValueError("bounded Python source required")
    # Public examples may be used for tool feedback; hidden tests remain checker-only.
    examples = public.get("examples", [])
    inputs = [example["input"] for example in examples] or [[]]
    args = {"source": python_source, "inputs": inputs}
    result = pool.call("python", args, left_ms)
    return "python", args, result, python_source


def run_observation(task, private, model_view, arm, core, budget=MultiplierBudget()):
    if arm not in ARMS:
        raise ValueError("registered arm required")
    identity = json.loads(canonical(core.identity))
    if not identity.get("weights_frozen") or not identity.get("accelerator_class"):
        raise ValueError("frozen accelerator core required")

    # ToolPool only needs the shared numerical/time fields.
    pool = ToolPool(task, private, budget)
    started = perf_counter_ns()
    events = []
    state = None
    model_calls = tool_calls = input_tokens = output_tokens = 0
    answer = None
    accepted = False
    error = None

    def left():
        return budget.wall_ms - milliseconds(started)

    def check(candidate):
        began = perf_counter_ns()
        try:
            ok = verify_original(task, candidate, private, min(budget.tool_ms, max(1.0, left())))
            failure = None
        except Exception as exc:
            ok = False
            failure = type(exc).__name__ + ": " + str(exc)
        events.append({
            "kind": "verification",
            "accepted": bool(ok),
            "error": failure,
            "ms": milliseconds(began),
        })
        return bool(ok) and left() >= 0

    try:
        while (
            model_calls < budget.model_calls
            and output_tokens < budget.output_tokens
            and left() > 0
        ):
            messages = model_messages(model_view, arm, state)
            prompt_tokens = core.count_tokens(messages, True)
            if prompt_tokens > budget.context_tokens:
                raise ValueError("context cap; no silent truncation")
            allowance = min(budget.per_call_tokens, budget.output_tokens - output_tokens)

            began = perf_counter_ns()
            model_calls += 1
            receipt = core.generate(messages, allowance, True, left())
            events.append({
                "kind": "model_result",
                "call": model_calls,
                "receipt": receipt,
                "ms": milliseconds(began),
            })
            if type(receipt.get("input_tokens")) is not int or type(receipt.get("output_tokens")) is not int:
                raise ValueError("actual token accounting required")
            if receipt["input_tokens"] != prompt_tokens:
                raise ValueError("prompt token accounting drift")
            if not 0 <= receipt["output_tokens"] <= allowance:
                raise ValueError("output token cap drift")
            input_tokens += receipt["input_tokens"]
            output_tokens += receipt["output_tokens"]
            if core.identity != identity:
                raise ValueError("frozen core identity drift")
            if receipt.get("deadline_reached") or left() <= 0:
                raise TimeoutError("query generation deadline")

            try:
                action = parse_action(receipt["raw"])
            except Exception as exc:
                events.append({"kind": "action_rejected", "error": type(exc).__name__ + ": " + str(exc)})
                state = {"error": "invalid_action"}
                continue

            if action["a"] == "f":
                if arm == "NEUMANN":
                    state = {"error": "representation_required"}
                    continue
                answer = action["v"]
                accepted = check(answer)
                break

            if arm == "DIRECT":
                raise ValueError("DIRECT may not use external tools")
            if arm == "NEUMANN" and action["a"] != "r":
                state = {"error": "representation_required"}
                continue
            if tool_calls >= budget.tool_calls:
                raise ValueError("tool-call cap")

            certificate = None
            if action["a"] == "r":
                began = perf_counter_ns()
                tool_calls += 1
                events.append({"kind": "tool_start", "tool": "reduce_pointer", "args": {"k":action["k"],"x":action["x"]}})
                try:
                    certificate = certify_representation(task, action)
                    events.append({"kind": "tool_result", "tool": "reduce_pointer", "result": certificate, "ms": milliseconds(began)})
                except Exception as exc:
                    events.append({"kind": "tool_result", "tool": "reduce_pointer", "error": type(exc).__name__ + ": " + str(exc), "ms": milliseconds(began)})
                    state = {"error": "representation_rejected"}
                    continue

            if tool_calls >= budget.tool_calls:
                raise ValueError("tool-call cap")
            began = perf_counter_ns()
            try:
                name, args, result, candidate = _execute(task, action, pool, budget, left(), certificate)
                tool_calls += 1
                events.append({"kind": "tool_start", "tool": name, "args": args})
                events.append({"kind": "tool_result", "tool": name, "result": result, "ms": milliseconds(began)})
                answer = candidate
                accepted = check(candidate)
                break
            except Exception as exc:
                tool_calls += 1
                events.append({"kind": "tool_start", "tool": "executor", "args": {"code": action.get("t") or action.get("x")}})
                events.append({"kind": "tool_result", "tool": "executor", "error": type(exc).__name__ + ": " + str(exc), "ms": milliseconds(began)})
                state = {"error": "tool_failed"}
                continue

        if not accepted and error is None:
            error = "CAPABILITY_OR_BUDGET_UNREACHED"
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)

    elapsed = milliseconds(started)
    peak = max(
        [
            event["receipt"].get("peak_accelerator_memory_bytes", 0)
            for event in events
            if event.get("kind") == "model_result" and type(event.get("receipt")) is dict
        ]
        or [0]
    )
    return {
        "schema": SCHEMA,
        "arm": arm,
        "task_id": task["id"],
        "family": task["family"],
        "task_sha256": sha(task),
        "model_view_sha256": sha(model_view),
        "core_sha256": sha(identity),
        "answer": answer,
        "accepted": bool(accepted and elapsed <= budget.wall_ms),
        "error": error,
        "model_calls": model_calls,
        "tool_calls": tool_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "token_accounting_complete": sum(event.get("kind") == "model_result" for event in events) == model_calls,
        "complete_ms": elapsed,
        "peak_accelerator_memory_bytes": int(peak),
        "events": events,
        "trace_sha256": sha(events),
        "new_training": False,
    }
