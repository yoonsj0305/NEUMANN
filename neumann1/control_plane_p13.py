"""P1.3 contract-first routing. Interface validity is not solved capability.

Typed admissibility uses public bytes only. A lazy full-S4 adapter is advisory
on mixed valid interfaces; invalid routes are never executable candidates.
Untyped interpretation and coding source synthesis remain separate obligations.
"""
from __future__ import annotations

import ast
import math
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, canonical, digest, finite, snapshot
from neumann1.control_plane_p12 import (Budget as P12Budget, CRITERIA, CODE_TOKEN_IDS,
    CodePlan, NextCodeBackend, aggregate, plan_cost, score_development)
from neumann1.control_plane_p1_contract import MODEL

SCHEMA = "neumann.control-plane-p1.3.v1"
GROUPS = {"ARITHMETIC": ("expression", "bindings"),
          "CSP": ("domains", "constraints"), "PYTHON": ("requirement", "examples")}
FIELDS = frozenset(k for group in GROUPS.values() for k in group) | {"background", "query"}


@dataclass(frozen=True)
class Budget:
    public_bytes: int = 32768
    wall_ms: float = 120000.0
    fallback_calls: int = 1


def contract():
    return {"schema": SCHEMA, "public_fields": sorted(FIELDS), "typed_groups": snapshot(GROUPS),
            "selected_route_in_admissible_routes": True, "single_typed_neural_forwards": 0,
            "malformed_typed_input": "REJECT_ENTIRE_INPUT", "unknown_fields": "REJECT",
            "mixed_typed_input": "LAZY_FULL_S4_MASKED_SELECTION_OR_ABSTAIN",
            "raw_query": "NEEDS_SEMANTIC_INTERPRETATION_NO_AUTOMATIC_EXECUTION",
            "cost_estimates": "optional nonnegative milliseconds with provenance; no measured-cheapest claim",
            "fallback_model": dict(MODEL), "fallback_codes": list(CODE_TOKEN_IDS),
            "fallback_geometry": dict(CRITERIA), "fallback_budget": asdict(P12Budget()),
            "budget": asdict(Budget()), "generation_in_controller": False,
            "references_visible_to_controller": False, "p12_validation_rescued": False,
            "p2_registration_admitted": False, "p2_admitted": False, "decision3_admitted": False,
            "global_questions_closed": []}


def _int(value):
    return type(value) is int and abs(value) <= 10**12


def _json_value(value, depth=0):
    if depth > 8:
        raise ValueError("bounded example depth")
    if value is None or type(value) is bool or _int(value) or (type(value) is str and len(value) <= 4096):
        return
    if type(value) is list and len(value) <= 128:
        for item in value: _json_value(item, depth+1)
        return
    if type(value) is dict and len(value) <= 128 and all(type(k) is str for k in value):
        for item in value.values(): _json_value(item, depth+1)
        return
    raise ValueError("bounded JSON examples required")


def _arithmetic(p):
    expression, bindings = p["expression"], p["bindings"]
    if type(expression) is not str or not 1 <= len(expression) <= 2000:
        raise ValueError("bounded expression required")
    if type(bindings) is not dict or len(bindings) > 64 or any(
            type(k) is not str or not k.isidentifier() or not _int(v) for k, v in bindings.items()):
        raise ValueError("bounded integer bindings required")
    tree = ast.parse(expression, mode="eval")
    nodes = list(ast.walk(tree))
    if len(nodes) > 256: raise ValueError("arithmetic AST cap")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Constant,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub, ast.Load)
    for n in nodes:
        if not isinstance(n, allowed): raise ValueError("unsupported arithmetic grammar")
        if isinstance(n, ast.Constant) and not _int(n.value): raise ValueError("integer literal required")
        if isinstance(n, ast.Name) and n.id not in bindings: raise ValueError("missing arithmetic binding")
    # No expression evaluation during type admission; division by zero is an
    # execution failure, never permission to silently choose another interface.


def _constraints(p):
    domains, constraints = p["domains"], p["constraints"]
    if type(domains) is not dict or not 1 <= len(domains) <= 9:
        raise ValueError("bounded finite CSP domains required")
    for name, values in domains.items():
        if type(name) is not str or not name.isidentifier() or type(values) is not list or not 1 <= len(values) <= 8:
            raise ValueError("finite named domains required")
        if any(not _int(v) for v in values) or len(set(values)) != len(values):
            raise ValueError("distinct integer domain values required")
    if math.prod(len(v) for v in domains.values()) > 200000:
        raise ValueError("CSP operation admission cap")
    if type(constraints) is not list or len(constraints) > 128:
        raise ValueError("bounded constraint list required")
    for c in constraints:
        if type(c) is not list or len(c) != 3: raise ValueError("three-field constraint required")
        op, left, right = c
        if type(op) is not str or op not in ("lt", "le", "ne", "eq") or type(left) is not str or left not in domains:
            raise ValueError("supported original constraint required")
        if not ((type(right) is str and right in domains) or _int(right)):
            raise ValueError("known variable or integer constant required")


def _coding(p):
    if type(p["requirement"]) is not str or not 1 <= len(p["requirement"].strip()) <= 4096:
        raise ValueError("bounded coding requirement required")
    examples = p["examples"]
    if type(examples) is not list or not 1 <= len(examples) <= 16:
        raise ValueError("bounded public examples required")
    for case in examples:
        if type(case) is not dict or set(case) != {"input", "output"}:
            raise ValueError("exact public example fields required")
        _json_value(case["input"]); _json_value(case["output"])


def admissibility(view):
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("only original instruction/public may enter routing")
    if type(view["instruction"]) is not str or not view["instruction"].strip() or type(view["public"]) is not dict:
        raise ValueError("public original problem required")
    if len(canonical(view).encode()) > Budget().public_bytes: raise ValueError("public byte admission cap")
    p = view["public"]
    if not p or set(p)-FIELDS: raise ValueError("unknown public fields; metadata is not authority")
    if "background" in p and type(p["background"]) is not str: raise ValueError("text background required")
    if "query" in p and (type(p["query"]) is not str or not p["query"].strip()):
        raise ValueError("nonempty raw query required")
    valid = []
    for route, fields in GROUPS.items():
        present = [f in p for f in fields]
        if any(present):
            if not all(present): raise ValueError("incomplete typed group: "+route)
            {"ARITHMETIC": _arithmetic, "CSP": _constraints, "PYTHON": _coding}[route](p)
            valid.append(route)
    if "query" in p: valid.append("DIRECT")
    if not valid: raise ValueError("no admissible public interface")
    routes = [r for r in ROUTES if r in valid]
    return {"view_sha256": digest(view), "admissible_routes": routes,
            "interpretation_required": "query" in p,
            "projects": {r: {k: snapshot(p[k]) for k in GROUPS[r]} for r in routes if r in GROUPS}}


def _masked_choice(matrix, eligible, costs, cost_weight):
    a = aggregate(matrix)
    indexes = [ROUTES.index(r) for r in eligible]
    def ordered(row):
        values = [finite(finite(row[i])-cost_weight*costs[ROUTES[i]]) for i in indexes]
        order = sorted(range(len(indexes)), key=lambda j: (-values[j], indexes[j]))
        return ROUTES[indexes[order[0]]], values[order[0]]-values[order[1]]
    winner, margin = ordered([a["scores"][r] for r in ROUTES])
    if margin <= CRITERIA["minimum_full_margin_nats"] or any(ordered(row)[0] != winner for row in a["loo_scores"]):
        raise ValueError("masked full-S4 choice ambiguous or LOO-unstable")
    if a["max_centered_loo_delta_nats"] > CRITERIA["loo_centered_tolerance_nats"]:
        raise ValueError("full-S4 LOO geometry failure")
    return winner, margin


class FrozenFullS4Fallback:
    """Attach an already frozen core lazily; this class never loads a model."""
    def __init__(self, core):
        from neumann1.control_plane_scoring_v1 import attach_frozen_gemma
        from neumann1.control_plane_p11 import audit_codes
        from experiments.control_plane_p1_first import forbid_generation
        self.core = core
        self.identity = snapshot(core.identity)
        if any(self.identity.get(k) != v for k, v in MODEL.items()): raise ValueError("exact frozen Gemma required")
        self.generation_counter = forbid_generation(core)
        self.scorer = attach_frozen_gemma(core)
        audit = audit_codes(core.processor.tokenizer)
        if tuple(audit["token_ids"]) != CODE_TOKEN_IDS: raise ValueError("original audited codes required")
        self.backend = NextCodeBackend(core.model, core.processor.tokenizer.pad_token_id, core.device)

    def score(self, view, remaining_ms):
        ledger = {k: 0 for k in ("input_rows", "score_rows", "scored_tokens", "evaluated_tokens", "padded_tokens", "forward_calls")}
        result = score_development(view, self.scorer.encode_prefix, CODE_TOKEN_IDS, self.backend, ledger, remaining_ms)
        result.update(identity=snapshot(self.core.identity), ledger=ledger, generated_calls=self.generation_counter["calls"],
                      audit=self.core.audit())
        return result


def route(view, fallback_factory=None, cost_estimates=None, cost_weight=0.0):
    """Select once. No executor, answer generation or verifier is invoked here.

    An unsupported semantic obligation is a stopped state, not an answer.
    Callback startup/scoring time lies inside complete route wall accounting.
    """
    began = perf_counter_ns(); elapsed = lambda: (perf_counter_ns()-began)/1e6
    result = {"schema": SCHEMA, "status": "REJECTED", "selected_route": None,
              "admissible_routes": [], "neural_forward_calls": 0, "fallback_calls": 0,
              "generated_calls": 0, "tool_calls": 0, "accounting_complete": True,
              "project": None, "fallback_receipt": None, "error": None}
    try:
        admitted = admissibility(view); result.update(admitted)
        eligible = admitted["admissible_routes"]
        if admitted["interpretation_required"]:
            result["status"] = "NEEDS_SEMANTIC_INTERPRETATION"
        elif len(eligible) == 1:
            result.update(status="SELECTED", selected_route=eligible[0], selection="UNIQUE_PUBLIC_CONTRACT")
        elif fallback_factory is None:
            result["status"] = "NEEDS_SEMANTIC_FALLBACK"
        else:
            finite(cost_weight, True)
            costs = {r: 0.0 for r in eligible}
            if cost_estimates is not None:
                if set(cost_estimates) != set(eligible): raise ValueError("exact eligible cost-estimate coverage required")
                for r, e in cost_estimates.items():
                    if set(e) != {"ms", "provenance"} or type(e["provenance"]) is not str or not e["provenance"].strip():
                        raise ValueError("estimate provenance required")
                    costs[r] = finite(e["ms"], True)
            elif cost_weight != 0: raise ValueError("nonzero weight requires explicit estimates")
            result["fallback_calls"] = 1
            result["accounting_complete"] = False
            result["neural_forward_calls"] = None
            result["generated_calls"] = None
            adapter = fallback_factory()
            remaining = lambda: Budget().wall_ms-elapsed()
            if remaining() <= 0: raise TimeoutError("lazy fallback startup deadline")
            receipt = adapter.score(snapshot(view), remaining)
            result["fallback_receipt"] = snapshot(receipt)
            result["generated_calls"] = receipt["generated_calls"]
            ledger = receipt["ledger"]
            if set(ledger) != {"input_rows", "score_rows", "scored_tokens", "evaluated_tokens", "padded_tokens", "forward_calls"}:
                raise ValueError("exact fallback ledger fields required")
            result["neural_forward_calls"] = ledger["forward_calls"]
            for key in ("input_rows", "score_rows", "scored_tokens", "evaluated_tokens", "padded_tokens", "forward_calls"):
                value = ledger[key]
                if type(value) is not int or value < 0 or value > getattr(P12Budget(), key):
                    raise ValueError("bounded complete fallback cost receipt required")
            if receipt["status"] != "COMPLETE" or len(receipt["passes"]) != 3:
                raise ValueError("partial fallback; stop without execution")
            totals = {k: 0 for k in ledger}
            for p, (mode, size, order) in zip(receipt["passes"], (
                    ("batch4", 4, list(range(24))), ("unbatched1", 1, list(range(24))),
                    ("reverse_batch4", 4, list(reversed(range(24)))))):
                if p["status"] != "COMPLETE" or p["mode"] != mode or p["batch_size"] != size or p["order"] != order:
                    raise ValueError("complete original execution modes required")
                if tuple(p["code_ids"]) != CODE_TOKEN_IDS or len(p["prefixes"]) != 24:
                    raise ValueError("original code/prefix coverage required")
                if any(not q or len(q)+1 > P12Budget().context_tokens or any(type(t) is not int or t < 0 for t in q) for q in p["prefixes"]):
                    raise ValueError("exact bounded token prefixes required")
                costs_actual = plan_cost(CodePlan(tuple(tuple(q) for q in p["prefixes"]), CODE_TOKEN_IDS), size)
                if p["planned"] != costs_actual or p["actual"] != costs_actual:
                    raise ValueError("fallback token/forward accounting mismatch")
                if type(p["peak_accelerator_memory_bytes"]) is not int or p["peak_accelerator_memory_bytes"] <= 0:
                    raise ValueError("fallback VRAM receipt required")
                for k, v in costs_actual.items(): totals[k] += v
            if totals != ledger: raise ValueError("fallback complete ledger mismatch")
            if receipt["passes"][1]["prefixes"] != receipt["passes"][0]["prefixes"] or receipt["passes"][2]["prefixes"] != list(reversed(receipt["passes"][0]["prefixes"])):
                raise ValueError("identical original prefixes across execution modes required")
            if any(receipt["identity"].get(k) != v for k,v in MODEL.items()) or receipt["audit"].get("unchanged") is not True:
                raise ValueError("fallback identity drift")
            if type(receipt["generated_calls"]) is not int or receipt["generated_calls"] != 0:
                raise ValueError("control generation forbidden")
            matrices = [p["matrix"] for p in receipt["passes"]]
            choices = [_masked_choice(m, eligible, costs, cost_weight) for m in matrices]
            numeric = max(abs(matrices[0][i][j]-m[i][j]) for m in matrices[1:] for i in range(24) for j in range(4))
            if numeric > CRITERIA["numeric_tolerance_nats"] or len({c[0] for c in choices}) != 1:
                raise ValueError("fallback numeric/order disagreement")
            if remaining() <= 0: raise TimeoutError("complete route deadline")
            result.update(status="SELECTED", selected_route=choices[0][0], selection="MASKED_FULL_S4",
                          masked_margin_nats=choices[0][1], numeric_delta_nats=numeric,
                          cost_estimates=snapshot(cost_estimates), cost_weight=cost_weight, accounting_complete=True)
        if result["status"] == "SELECTED":
            if result["selected_route"] not in eligible: raise ValueError("selected route outside admissibility")
            result["project"] = admitted["projects"][result["selected_route"]]
    except Exception as exc:
        result.update(status="REJECTED", selected_route=None, project=None,
                      error=type(exc).__name__+": "+str(exc))
    result.pop("projects", None)
    result["complete_ms"] = elapsed()
    return result


def execute_selected(view, routing, executor, original_verifier):
    """One gated attempt. Caller supplies reasoning/tools and original checker.

    No reference/witness is ever passed to routing or executor. Verification
    returns only original-obligation boolean; failure cannot promote a route.
    """
    began = perf_counter_ns()
    result = {"accepted": False, "executed": False, "error": None}
    try:
        admitted = admissibility(view); selected = routing["selected_route"]
        if routing["status"] != "SELECTED" or selected not in admitted["admissible_routes"] or routing.get("view_sha256") != digest(view):
            raise ValueError("execution requires matching admitted original view")
        if admitted["interpretation_required"] or routing.get("accounting_complete") is not True:
            raise ValueError("interpretation/accounting obligation unresolved")
        if routing.get("project") != admitted["projects"].get(selected): raise ValueError("unproved projected input")
        result["executed"] = True
        answer = executor(selected, snapshot(routing["project"]))
        result["answer"] = snapshot(answer)
        accepted = original_verifier(snapshot(view), answer)
        if type(accepted) is not bool: raise ValueError("original verifier must return bool")
        result["accepted"] = accepted
    except Exception as exc:
        result["error"] = type(exc).__name__+": "+str(exc)
    result["complete_ms"] = (perf_counter_ns()-began)/1e6
    return result
