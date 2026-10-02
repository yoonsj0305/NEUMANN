"""General Runtime-0: frozen-core orchestration, never a fitted model.

Every strategy receives the same original task, eligible tools and hard caps.
Synthetic adapters test control flow only; they are never model evidence.
"""
from __future__ import annotations

import ast
import hashlib
import itertools
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from fractions import Fraction
from time import perf_counter_ns

ARMS = ("B0", "B1", "B2", "B3", "N")
FAMILIES = ("math_logic", "coding", "constraint_planning")
TOOLS = ("arithmetic", "csp", "python", "reduce", "verify")
MODEL_ID = "google/gemma-4-E2B-it"
MODEL_REVISION = "3e22461f65e89153144f8adb70e3b8c2cc9845a7"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def milliseconds(start):
    return (perf_counter_ns() - start) / 1e6


@dataclass(frozen=True)
class Limits:
    context_tokens: int = 4096
    output_tokens: int = 512
    per_call_tokens: int = 192
    model_calls: int = 6
    tool_calls: int = 6
    wall_ms: float = 120000.
    tool_ms: float = 2000.

    def __post_init__(self):
        for key in ("context_tokens", "output_tokens", "per_call_tokens", "model_calls", "tool_calls"):
            if type(getattr(self, key)) is not int or getattr(self, key) < 1:
                raise ValueError("positive integer cap required: " + key)
        for key in ("wall_ms", "tool_ms"):
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("positive finite deadline required")
        if self.per_call_tokens > self.output_tokens:
            raise ValueError("per-call cap exceeds complete query output cap")


def _rational(expression, bindings):
    """Bounded arithmetic tool. AST evaluation, no eval/exec or file access."""
    if type(expression) is not str or len(expression) > 2000:
        raise ValueError("bounded arithmetic expression required")
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 256:
        raise ValueError("expression too large")
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            if abs(node.value) > 10**12:
                raise ValueError("integer bound")
            return Fraction(node.value)
        if isinstance(node, ast.Name):
            v = bindings[node.id]
            if type(v) is not int or abs(v) > 10**12:
                raise ValueError("integer binding required")
            return Fraction(v)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = visit(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError("unsupported arithmetic grammar")
    value = visit(tree.body)
    return str(value)


def _satisfies(assignment, constraints):
    for item in constraints:
        op, left, right = item
        if left not in assignment or (type(right) is str and right not in assignment):
            continue
        a = assignment[left]
        b = assignment[right] if type(right) is str else right
        if not {"lt": a < b, "le": a <= b, "ne": a != b, "eq": a == b}[op]:
            return False
    return True


def _csp(spec, strategy):
    domains, constraints = spec["domains"], spec["constraints"]
    if strategy not in ("enumerate", "mrv") or not 1 <= len(domains) <= 9:
        raise ValueError("bounded finite CSP required")
    if any(type(k) is not str or type(v) is not list or not 1 <= len(v) <= 8
           or any(type(x) is not int for x in v) for k, v in domains.items()):
        raise ValueError("finite integer domains required")
    if any(type(c) is not list or len(c) != 3 or c[0] not in ("lt", "le", "ne", "eq")
           or c[1] not in domains or (type(c[2]) is str and c[2] not in domains)
           or type(c[2]) not in (str, int) for c in constraints):
        raise ValueError("invalid original constraint")
    if math.prod(len(v) for v in domains.values()) > 200000:
        raise ValueError("CSP operation cap")
    nodes = 0
    if strategy == "enumerate":
        names = sorted(domains)
        for values in itertools.product(*(domains[n] for n in names)):
            nodes += 1
            assignment = dict(zip(names, values))
            if _satisfies(assignment, constraints):
                return {"assignment": assignment, "nodes": nodes}
    else:
        def search(assignment):
            nonlocal nodes
            if len(assignment) == len(domains):
                return dict(assignment)
            pending = []
            for name in sorted(set(domains) - set(assignment)):
                allowed = [v for v in domains[name] if _satisfies({**assignment, name: v}, constraints)]
                pending.append((len(allowed), name, allowed))
            _, name, allowed = min(pending)
            for value in allowed:
                nodes += 1
                found = search({**assignment, name: value})
                if found is not None:
                    return found
            return None
        found = search({})
        if found is not None:
            return {"assignment": found, "nodes": nodes}
    return {"assignment": None, "nodes": nodes}


def reduce_original(task, proposed_ir):
    """Cheap certified field elimination. A learned proposal cannot drop facts.

    Runtime-0 supports exact expressions/specification fields, not a general
    semantic equivalence theorem. Irrelevant background is author-marked data.
    All baselines can invoke this identical tool.
    """
    if type(proposed_ir) is not dict or proposed_ir.get("family") != task["family"]:
        raise ValueError("typed representation required")
    family, public = task["family"], task["public"]
    if family == "math_logic":
        if proposed_ir.get("expression") != public["expression"]:
            raise ValueError("unproved expression rewrite")
        names = {n.id for n in ast.walk(ast.parse(public["expression"], mode="eval")) if isinstance(n, ast.Name)}
        result = {"family": family, "expression": public["expression"],
                  "bindings": {n: public["bindings"][n] for n in sorted(names)}}
    elif family == "constraint_planning":
        if proposed_ir.get("domains") != public["domains"] or proposed_ir.get("constraints") != public["constraints"]:
            raise ValueError("unproved variable/constraint deletion")
        result = {"family": family, "domains": public["domains"], "constraints": public["constraints"]}
    else:
        if proposed_ir.get("requirement") != public["requirement"]:
            raise ValueError("unproved programming requirement change")
        result = {"family": family, "requirement": public["requirement"], "signature": "solve(items)"}
    return {"ir": result, "original_task_sha256": sha(task),
            "eliminated_background": "background" in public,
            "certificate_scope": "exact task fields / unused arithmetic bindings only"}


def _python(source, arguments, deadline_ms):
    """Bounded Python subset in an isolated resource-capped child."""
    payload = canonical({"source": source, "arguments": arguments})
    worker = str(__import__("pathlib").Path(__file__).with_name("general_python_worker_v106.py"))
    try:
        p = subprocess.run([sys.executable, "-I", worker], input=payload, text=True,
                           capture_output=True, timeout=deadline_ms / 1000)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Python tool deadline; attempted work charged") from exc
    if p.returncode != 0:
        raise ValueError("Python subset rejected or process limit reached")
    value = json.loads(p.stdout)
    if value.get("ok") is not True:
        raise ValueError(value.get("error", "Python subset failed"))
    return value["outputs"]


def verify_original(task, candidate, private, deadline_ms):
    """Independent original-task checker; no model judge or IR authority.

    Coding means original-spec finite-test validity, NOT proof for all inputs.
    Math reference is retained independently in the task construction record.
    Constraint validity is checked directly on all original domains/rules.
    """
    family = task["family"]
    if family == "math_logic":
        return Fraction(str(candidate)) == Fraction(private["exact"])
    if family == "coding":
        if type(candidate) is not str:
            return False
        if not private.get("tests"):
            raise ValueError("original-spec test vectors required")
        outputs = _python(candidate, [case["input"] for case in private["tests"]], deadline_ms)
        return len(outputs) == len(private["tests"]) and all(
            canonical(a) == canonical(b["output"]) for a, b in zip(outputs, private["tests"]))
    if type(candidate) is not dict or set(candidate) != set(task["public"]["domains"]):
        return False
    if any(type(candidate[k]) is not int or candidate[k] not in values for k, values in task["public"]["domains"].items()):
        return False
    # Separate complete-rule check, not the solver's partial consistency helper.
    for op, name, other in task["public"]["constraints"]:
        if op not in ("lt", "le", "eq", "ne"):
            raise ValueError("unknown original constraint; checker cannot attest")
        a = candidate[name]
        b = candidate[other] if type(other) is str else other
        if op == "lt" and not a < b: return False
        if op == "le" and not a <= b: return False
        if op == "eq" and not a == b: return False
        if op == "ne" and not a != b: return False
    return True


class ToolPool:
    def __init__(self, task, private, limits):
        self.task, self.private, self.limits = task, private, limits

    def call(self, name, args, left_ms):
        if name not in TOOLS or type(args) is not dict:
            raise ValueError("unknown tool or argument type")
        cap = min(left_ms, self.limits.tool_ms)
        if cap <= 0:
            raise TimeoutError("complete query deadline")
        if name == "arithmetic":
            return _rational(args["expression"], args.get("bindings", {}))
        if name == "csp":
            return _csp(args["spec"], args["strategy"])
        if name == "python":
            return _python(args["source"], args["inputs"], cap)
        if name == "reduce":
            return reduce_original(self.task, args["ir"])
        return {"accepted": verify_original(self.task, args["candidate"], self.private, cap),
                "feedback": "original check pass/fail only; no hidden tests or solution"}


WIRE = ('Return one JSON object only. Actions: {"action":"final","answer":...}; '
        '{"action":"call","tool":"arithmetic|csp|python|reduce|verify","args":{...}}; '
        '{"action":"represent","ir":{...}}. '
        'arithmetic args expression,bindings; csp args spec with domains,constraints and strategy mrv|enumerate; '
        'python args source defining solve(items),inputs list of test inputs; reduce args ir; verify args candidate. '
        'Python supports bounded pure list/integer functions, no imports, attributes, files, network or eval. '
        'Use the original task; do not claim success without a final answer.')
PROMPTS = {
    "B0": "Answer directly; use no intermediate tool or representation actions.",
    "B1": "Reason carefully, then give the final answer. Do not invoke tools.",
    "B2": "Use at most one tool invocation, then give the final answer.",
    "B3": ("Iteratively solve with any eligible tools, original verification and correction. Choose economical steps. "
           "You may also use represent with executor arithmetic|csp|python (plus source for python) "
           "to execute and check a certified plan without another narration call."),
    "N": ("First produce a typed representation of the necessary original fields via represent. "
          "Its cheap reduction certificate must preserve the original obligations. "
          "In the same represent object select executor arithmetic|csp|python; for python add source. "
          "The runtime executes this plan and verifies on the original task without another narration call. "
          "On failure revise the representation using original fields, and increase compute only as needed. "
          "If uncertain or reduction is invalid, retain the original problem and use the same tools; never bypass checking.")
}


def parse_action(raw):
    text = raw.strip()
    # Thinking is retained/billed in raw generation; only the response is parsed.
    if "<channel|>" in text:
        text = text.rsplit("<channel|>", 1)[-1].strip()
    if "<|channel>final" in text:
        text = text.rsplit("<|channel>final", 1)[-1].strip()
    for token in ("<turn|>", "<eos>"):
        text = text.replace(token, "")
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    value = json.loads(text)
    canonical(value)  # Reject NaN/Infinity before any parsed value enters a receipt.
    if type(value) is not dict or value.get("action") not in ("final", "call", "represent"):
        raise ValueError("invalid action envelope")
    return value


def run(task, private, arm, core, limits=Limits()):
    """core.generate(messages, max_tokens, thinking, deadline_ms) -> real receipt.

    Core identity includes weight revision/precision/tokenizer hash. It is checked
    after EVERY generation. Only the external adapter can attest actual inference.
    """
    if arm not in ARMS or task["family"] not in FAMILIES:
        raise ValueError("registered strategy/family required")
    identity = json.loads(canonical(core.identity))
    if not identity.get("weights_frozen") or not identity.get("revision") or not identity.get("artifact_sha256"):
        raise ValueError("explicit frozen core identity required")
    start = perf_counter_ns()
    pool = ToolPool(task, private, limits)
    events, history = [], []
    calls = output_tokens = input_tokens = tool_calls = 0
    answer = None
    error = None
    verified = False
    ir = None
    verification_errors = []
    def left():
        return limits.wall_ms - milliseconds(start)
    def check(candidate):
        began = perf_counter_ns()
        try:
            accepted = verify_original(task, candidate, private, min(limits.tool_ms, max(1, left())))
            if type(accepted) is not bool:
                raise ValueError("checker did not return Boolean")
            e = None
        except Exception as exc:
            accepted = False
            e = type(exc).__name__ + ": " + str(exc)
            verification_errors.append(e)
        events.append({"kind": "verification", "accepted": accepted, "error": e,
                       "ms": milliseconds(began)})
        return accepted and left() >= 0
    try:
        while calls < limits.model_calls and left() > 0 and output_tokens < limits.output_tokens:
            state = {"original": task} if ir is None else {"certified_representation": ir}
            messages = [{"role": "system", "content": WIRE + " " + PROMPTS[arm]},
                        {"role": "user", "content": canonical({"problem": state, "history": history})}]
            if core.count_tokens(messages, arm != "B0") > limits.context_tokens:
                raise ValueError("context cap; no silent truncation")
            allowance = min(limits.per_call_tokens, limits.output_tokens - output_tokens)
            began = perf_counter_ns()
            calls += 1
            events.append({"kind": "model_start", "call": calls, "remaining_ms": left()})
            result = core.generate(messages, allowance, arm != "B0", left())
            events.append({"kind": "model_result", "call": calls, "receipt": result, "ms": milliseconds(began)})
            if type(result["input_tokens"]) is not int or type(result["output_tokens"]) is not int:
                raise ValueError("actual token counts required")
            if not 0 <= result["output_tokens"] <= allowance or not 0 <= result["input_tokens"] <= limits.context_tokens:
                raise ValueError("token cap or accounting drift")
            input_tokens += result["input_tokens"]; output_tokens += result["output_tokens"]
            if core.identity != identity:
                raise ValueError("weights/tokenizer/precision drift")
            if left() <= 0:
                raise TimeoutError("complete generation deadline; receipt retained")
            try:
                action = parse_action(result.get("action_text") or result["raw"])
                if action["action"] == "final":
                    if arm == "N" and ir is None:
                        raise ValueError("NEUMANN has not established a sufficient representation")
                    answer = action["answer"]
                    verified = check(answer)
                    if verified or arm in ("B0", "B1", "B2"):
                        break
                    history.append({"feedback": "original verification failed; revise representation or computation"})
                    if arm == "N": ir = None
                    continue
                if arm in ("B0", "B1") or (arm == "B2" and tool_calls >= 1):
                    raise ValueError("baseline strategy action restriction")
                if tool_calls >= limits.tool_calls:
                    raise ValueError("complete tool-call cap")
                if action["action"] == "represent":
                    name, args = "reduce", {"ir": action["ir"]}
                else:
                    name, args = action["tool"], action["args"]
                if arm == "N" and ir is None and name != "reduce":
                    raise ValueError("establish sufficient representation first")
                tool_calls += 1
                began = perf_counter_ns()
                events.append({"kind": "tool_start", "tool": name, "args": args})
                try:
                    outcome = pool.call(name, args, left())
                except Exception as exc:
                    outcome = {"error": type(exc).__name__ + ": " + str(exc)}
                events.append({"kind": "tool_result", "tool": name, "result": outcome, "ms": milliseconds(began)})
                if name == "reduce" and "ir" in outcome:
                    ir = outcome["ir"]
                    # All arms may compact context through the same certified tool.
                    history = [{"reduction": outcome}]
                    if arm in ("N", "B3") and "executor" in action:
                        executor = action["executor"]
                        if executor == "arithmetic" and ir["family"] == "math_logic":
                            execution_args = {"expression": ir["expression"], "bindings": ir["bindings"]}
                        elif executor == "csp" and ir["family"] == "constraint_planning":
                            execution_args = {"spec": {k: ir[k] for k in ("domains", "constraints")}, "strategy": "mrv"}
                        elif executor == "python" and ir["family"] == "coding":
                            execution_args = {"source": action["source"], "inputs": [[]]}
                        else:
                            raise ValueError("executor/representation mismatch")
                        if tool_calls >= limits.tool_calls:
                            raise ValueError("complete tool-call cap")
                        tool_calls += 1
                        began = perf_counter_ns()
                        events.append({"kind": "tool_start", "tool": executor, "args": execution_args})
                        try:
                            executed = pool.call(executor, execution_args, left())
                            candidate = (executed if executor == "arithmetic" else
                                         executed["assignment"] if executor == "csp" else action["source"])
                            events.append({"kind": "tool_result", "tool": executor, "result": executed, "ms": milliseconds(began)})
                            answer = candidate
                            verified = check(candidate)
                            if verified: break
                            history.append({"feedback": "original verification failed; revise representation/plan"})
                            ir = None
                        except Exception as exc:
                            events.append({"kind": "tool_result", "tool": executor, "error": str(exc), "ms": milliseconds(began)})
                            history.append({"feedback": str(exc)})
                            ir = None
                else:
                    history.append({"tool": name, "result": outcome})
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                events.append({"kind": "action_rejected", "error": str(exc)})
                if arm in ("B0", "B1"):
                    error = "invalid one-shot response"; break
                history.append({"feedback": str(exc)})
        if not verified and error is None:
            error = "CAPABILITY_OR_BUDGET_UNREACHED"
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    elapsed = milliseconds(start)
    return {"schema": "neumann.general-runtime.v106.v1", "arm": arm,
            "task_id": task["id"], "family": task["family"], "task_sha256": sha(task),
            "core": identity, "limits": asdict(limits), "answer": answer,
            "accepted": bool(verified and elapsed <= limits.wall_ms),
            "verification_errors": verification_errors, "error": error,
            "model_calls": calls, "tool_calls": tool_calls,
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "token_accounting_complete": sum(e["kind"] == "model_result" for e in events) == calls,
            "complete_ms": elapsed, "events": events, "trace_sha256": sha(events),
            "new_fitting": False, "evidence_kind": core.identity.get("evidence_kind", "unattested"),
            "resources": {"latency_ms": {"status": "measured", "value": elapsed},
                          "compute": {"status": "unavailable", "value": None},
                          "energy_j": {"status": "unavailable", "value": None},
                          "cost": {"status": "unavailable", "value": None}}}


def development_tasks():
    """Opened author-constructed diagnostics, NEVER a sealed v107 holdout."""
    return [
        ({"id": "runtime0_dev_math", "family": "math_logic",
          "public": {"expression": "(a*b-c)/(d+e)", "bindings": {"a": 17, "b": 13, "c": 5, "d": 4, "e": 8, "unused": 999},
                     "background": "The notebook cover is blue."},
          "instruction": "Return the exact rational value."}, {"exact": "18"}),
        ({"id": "runtime0_dev_code", "family": "coding",
          "public": {"requirement": "Return the sum of distinct even integers in items, a list of integers.",
                     "background": "The caller likes astronomy."},
          "instruction": "Return Python source defining solve(items)."},
         {"tests": [{"input": [], "output": 0}, {"input": [2,2,3,4,-2], "output": 4},
                    {"input": [1,3,5], "output": 0}, {"input": [0,6,6,8], "output": 14}]}),
        ({"id": "runtime0_dev_plan", "family": "constraint_planning",
          "public": {"domains": {"A": [0,1,2], "B": [0,1,2], "C": [0,1,2]},
                     "constraints": [["lt","A","B"], ["lt","B","C"]],
                     "background": "A room has five chairs."},
          "instruction": "Return a complete assignment meeting every original constraint."}, {})
    ]
