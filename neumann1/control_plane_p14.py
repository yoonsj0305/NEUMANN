"""P1.4 bounded semantic interpretation for raw obligations.

P1.3 remains the authority for typed admissibility. Raw natural language may
invoke one bounded frozen-model proposal only after deterministic type admission
has established that no specialist representation is already present. The
proposal is untrusted: it must compile into an exact P1.3 public contract, then
the selected specialist executes, and only the original-task verifier may
accept the answer.

This module does not rescue P1.2 or P1.3 evidence and does not admit P2.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL
from neumann1.control_plane_p13 import admissibility, execute_selected, route as contract_route

SCHEMA = "neumann.control-plane-p1.4.v1"
SPECIALISTS = ("ARITHMETIC", "CSP")


@dataclass(frozen=True)
class Budget:
    public_bytes: int = 32768
    semantic_model_calls: int = 1
    semantic_output_tokens: int = 192
    semantic_wall_ms: float = 120000.0
    whole_item_wall_ms: float = 180000.0


def contract():
    return {
        "schema": SCHEMA,
        "parent": "neumann.control-plane-p1.3.v1",
        "raw_entry": "P1.3_NEEDS_SEMANTIC_INTERPRETATION_ONLY",
        "semantic_specialists": list(SPECIALISTS),
        "proposal_mode": "ONE_BOUNDED_GREEDY_FROZEN_MODEL_CALL_THINKING_DISABLED",
        "proposal_is_authority": False,
        "proposal_must_reenter_p13_admissibility": True,
        "execution_requires_unique_specialist_contract": True,
        "acceptance_authority": "ORIGINAL_TASK_BOOLEAN_VERIFIER_ONLY",
        "retry_after_verifier_failure": False,
        "coding_semantic_synthesis": "OUT_OF_SCOPE",
        "mixed_typed_fallback": "UNCHANGED_P1.3_MASKED_FULL_S4",
        "model": dict(MODEL),
        "budget": asdict(Budget()),
        "new_training": False,
        "frontier_calls": 0,
        "sealed_data_opened": False,
        "p12_validation_rescued": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
    }


def _clean_generation(text):
    if type(text) is not str:
        raise ValueError("text generation receipt required")
    value = text.strip()
    if "<|channel>final" in value:
        value = value.rsplit("<|channel>final", 1)[-1].strip()
    if "<channel|>" in value:
        value = value.rsplit("<channel|>", 1)[-1].strip()
    for token in ("<turn|>", "<eos>", "<|end|>"):
        value = value.replace(token, "")
    value = value.strip()
    if value.startswith("\x60\x60\x60json") and value.endswith("\x60\x60\x60"):
        value = value[7:-3].strip()
    elif value.startswith("\x60\x60\x60") and value.endswith("\x60\x60\x60"):
        value = value[3:-3].strip()
    return value


def parse_proposal(raw):
    value = json.loads(_clean_generation(raw))
    if type(value) is not dict or "route" not in value:
        raise ValueError("proposal object with route required")
    route = value["route"]
    if route == "ABSTAIN":
        if set(value) != {"route"}:
            raise ValueError("abstain cannot smuggle typed fields")
        return {"route": "ABSTAIN"}
    if route == "ARITHMETIC":
        if set(value) != {"route", "expression", "bindings"}:
            raise ValueError("exact arithmetic proposal fields required")
        public = {"expression": value["expression"], "bindings": value["bindings"]}
    elif route == "CSP":
        if set(value) != {"route", "domains", "constraints"}:
            raise ValueError("exact CSP proposal fields required")
        public = {"domains": value["domains"], "constraints": value["constraints"]}
    else:
        raise ValueError("unsupported semantic proposal route")
    canonical(public)
    return {"route": route, "public": snapshot(public)}


def semantic_prompt(view):
    admitted = admissibility(view)
    if admitted["interpretation_required"] is not True or admitted["admissible_routes"] != ["DIRECT"]:
        raise ValueError("semantic compiler only accepts raw P1.3 stopped states")
    p = view["public"]
    if set(p) - {"query", "background"} or "query" not in p:
        raise ValueError("raw semantic input must contain query and optional background only")
    return (
        "Compile the original raw problem into exactly one supported specialist representation. "
        "Do not solve the problem and do not add commentary. If the meaning cannot be represented "
        "faithfully as exact scalar arithmetic or a bounded finite constraint problem, abstain.\n"
        "Output exactly one compact JSON object in one of these schemas:\n"
        '{"route":"ARITHMETIC","expression":"...","bindings":{"name":1}}\n'
        '{"route":"CSP","domains":{"A":[0,1]},"constraints":[["lt","A",1]]}\n'
        '{"route":"ABSTAIN"}\n'
        "Arithmetic supports +,-,*,/ and integer bindings. CSP supports lt,le,eq,ne over finite integer domains.\n"
        + canonical({"instruction": view["instruction"], "public": p})
    )


class FrozenSemanticCompiler:
    """One bounded generation call; no model loading occurs in this wrapper."""

    def __init__(self, core):
        self.core = core
        self.identity = snapshot(core.identity)
        if any(self.identity.get(k) != v for k, v in MODEL.items()):
            raise ValueError("exact frozen Gemma identity required")
        audit = core.audit()
        if audit.get("unchanged") is not True:
            raise ValueError("frozen core audit required")

    def propose(self, view, remaining_ms):
        remaining_ms = finite(remaining_ms, True)
        if remaining_ms <= 0:
            raise TimeoutError("no semantic compilation time")
        prompt = semantic_prompt(view)
        messages = [{"role": "user", "content": prompt}]
        began = perf_counter_ns()
        result = self.core.generate(
            messages,
            Budget().semantic_output_tokens,
            False,
            min(remaining_ms, Budget().semantic_wall_ms),
        )
        if self.core.identity != self.identity or self.core.audit().get("unchanged") is not True:
            raise ValueError("semantic compiler model identity drift")
        for key in ("input_tokens", "output_tokens"):
            if type(result.get(key)) is not int or result[key] < 0:
                raise ValueError("complete semantic token receipt required")
        if result["output_tokens"] > Budget().semantic_output_tokens:
            raise ValueError("semantic output budget drift")
        proposal = parse_proposal(result["raw"])
        return {
            "proposal": proposal,
            "raw_sha256": digest(result["raw"]),
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "generation_ms": finite(result.get("generation_ms"), True),
            "deadline_reached": bool(result.get("deadline_reached")),
            "peak_accelerator_memory_bytes": result.get("peak_accelerator_memory_bytes"),
            "core_sha256": result.get("core_sha256"),
            "complete_ms": (perf_counter_ns() - began) / 1e6,
        }


def _routing_from_proposal(original, proposal):
    if proposal["route"] == "ABSTAIN":
        return None, None
    typed = {"instruction": original["instruction"], "public": snapshot(proposal["public"])}
    admitted = admissibility(typed)
    if admitted["interpretation_required"] is not False:
        raise ValueError("typed proposal still requires interpretation")
    if admitted["admissible_routes"] != [proposal["route"]]:
        raise ValueError("proposal must compile to one exact specialist contract")
    routed = contract_route(typed)
    if routed["status"] != "SELECTED" or routed["selected_route"] != proposal["route"]:
        raise ValueError("deterministic P1.3 re-entry did not select proposal route")
    if routed["neural_forward_calls"] != 0 or routed["fallback_calls"] != 0 or routed["generated_calls"] != 0:
        raise ValueError("typed re-entry must remain zero-neural")
    return typed, routed


def interpret_and_execute(view, compiler, executor, original_verifier):
    """Compile once, execute at most once, and verify only against original task."""

    began = perf_counter_ns()
    result = {
        "schema": SCHEMA,
        "status": "INCOMPLETE",
        "accepted": False,
        "executed": False,
        "selected_route": None,
        "proposal": None,
        "typed_view_sha256": None,
        "original_view_sha256": digest(view),
        "model_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "tool_calls": 0,
        "error": None,
        "accounting_complete": False,
    }
    try:
        admitted = admissibility(view)
        if admitted["interpretation_required"] is not True or admitted["admissible_routes"] != ["DIRECT"]:
            raise ValueError("raw semantic stopped state required")
        if len(canonical(view).encode()) > Budget().public_bytes:
            raise ValueError("raw public byte cap")

        remaining = lambda: Budget().whole_item_wall_ms - (perf_counter_ns() - began) / 1e6
        result["model_calls"] = 1
        receipt = compiler.propose(snapshot(view), remaining())
        result["semantic_receipt"] = snapshot(receipt)
        result["input_tokens"] = receipt["input_tokens"]
        result["output_tokens"] = receipt["output_tokens"]
        proposal = receipt["proposal"]
        result["proposal"] = snapshot(proposal)

        if proposal["route"] == "ABSTAIN":
            result["status"] = "ABSTAINED"
            result["accounting_complete"] = True
        else:
            typed, routed = _routing_from_proposal(view, proposal)
            result["selected_route"] = routed["selected_route"]
            result["typed_view_sha256"] = digest(typed)
            if remaining() <= 0:
                raise TimeoutError("semantic item wall before execution")
            result["tool_calls"] = 1
            execution = execute_selected(
                typed,
                routed,
                executor,
                lambda _typed, answer: original_verifier(snapshot(view), answer),
            )
            result["execution"] = snapshot(execution)
            result["executed"] = execution["executed"]
            result["accepted"] = execution["accepted"]
            result["status"] = "ACCEPTED" if execution["accepted"] else "REJECTED_BY_ORIGINAL_VERIFIER"
            result["accounting_complete"] = True
        if remaining() <= 0:
            raise TimeoutError("semantic item complete wall exceeded")
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        if result["status"] == "INCOMPLETE":
            result["status"] = "FAILED"
    result["complete_ms"] = (perf_counter_ns() - began) / 1e6
    return result


def run_mixed_and_execute(view, fallback_factory, executor, original_verifier):
    """Exercise the unchanged P1.3 masked full-S4 fallback and original verifier."""

    began = perf_counter_ns()
    result = {
        "schema": SCHEMA,
        "status": "INCOMPLETE",
        "accepted": False,
        "executed": False,
        "selected_route": None,
        "routing": None,
        "error": None,
    }
    try:
        routed = contract_route(view, fallback_factory=fallback_factory)
        result["routing"] = snapshot(routed)
        result["selected_route"] = routed["selected_route"]
        if routed["status"] != "SELECTED":
            raise ValueError("mixed semantic fallback did not select")
        execution = execute_selected(view, routed, executor, original_verifier)
        result["execution"] = snapshot(execution)
        result["executed"] = execution["executed"]
        result["accepted"] = execution["accepted"]
        result["status"] = "ACCEPTED" if execution["accepted"] else "REJECTED_BY_ORIGINAL_VERIFIER"
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = type(exc).__name__ + ": " + str(exc)
    result["complete_ms"] = (perf_counter_ns() - began) / 1e6
    return result
