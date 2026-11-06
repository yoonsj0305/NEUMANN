"""Runtime-0 finite-action bridge over the existing P1.3 typed admission.

This is a bounded execution-interface *diagnostic*, not learned structural
invention and not a rerun/rescue of the frozen Decision 2 FAIL.
Model scorers are injected and may return ONLY finite scores for allowed actions.
VERIFY is a deterministic runtime state; it is never generated as free text.
"""
from __future__ import annotations

import math
from time import perf_counter_ns

from neumann1.control_plane_p13 import admissibility
from neumann1.control_plane_v1 import digest, snapshot

SCHEMA = "neumann.north-star.finite-action-bridge.v1"
ACTIONS = ("CLASSICAL", "GENERATE", "VERIFY", "ESCALATE", "ABSTAIN")
SELECTABLE = ("CLASSICAL", "GENERATE", "ESCALATE", "ABSTAIN")
NATIVE_ROUTES = ("ARITHMETIC", "CSP")


def _candidate(receipt):
    """No naked answer, unchecked executable code, or unmetered work."""
    if type(receipt) is not dict or set(receipt) != {
        "answer", "provenance", "model_calls", "tool_calls", "generated_tokens"
    }:
        raise ValueError("exact candidate receipt required")
    if type(receipt["provenance"]) is not str or not receipt["provenance"].strip():
        raise ValueError("candidate origin required")
    for k in ("model_calls", "tool_calls", "generated_tokens"):
        if type(receipt[k]) is not int or receipt[k] < 0:
            raise ValueError("nonnegative complete execution counters required")
    return snapshot(receipt)


def _select(view, allowed, scorer):
    if scorer is None:
        # Safest classical-first control, explicitly NOT a learned result.
        return "CLASSICAL" if "CLASSICAL" in allowed else "ABSTAIN"
    scores = scorer(snapshot(view), tuple(allowed))
    if type(scores) is not dict or set(scores) != set(allowed):
        raise ValueError("one score per permitted action required")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in scores.values()):
        raise ValueError("finite action scores required")
    ordered = sorted(allowed, key=lambda a: (-scores[a], SELECTABLE.index(a)))
    if len(ordered) > 1 and scores[ordered[0]] == scores[ordered[1]]:
        raise ValueError("unresolved action score tie")
    return ordered[0]


def run(view, *, classical=None, generator=None, escalator=None,
        verify_original=None, action_scorer=None):
    """Single bounded action + at most one independent proof, no retries.

    Classical executor receives (typed_route, public_view).
    Generator and escalator receive public_view only. All return exact candidate
    receipts. Verifier receives (public_view, answer) and returns an exact bool.
    Unknown is the default. No hidden reference/answer is ever passed to scorer.
    """
    started = perf_counter_ns()
    wall = lambda: (perf_counter_ns() - started) / 1e6
    out = {
        "schema": SCHEMA, "scientific_scope": "OPENED_INTERFACE_DIAGNOSTIC_ONLY",
        "status": "UNKNOWN", "accepted": False, "action": "ABSTAIN",
        "selected_route": None, "trace": [], "selector_calls": 0,
        "executor_calls": 0, "verifier_calls": 0, "model_calls": 0,
        "tool_calls": 0, "generated_tokens": 0, "cost_accounting_complete": True,
        "error": None, "view_sha256": None, "Q3": "OPEN", "Q4": "OPEN",
        "Q5": "OPEN", "Q6": "OPEN", "Q7": "OPEN"
    }
    try:
        admitted = admissibility(view)
        out["view_sha256"] = admitted["view_sha256"]
        routes = admitted["admissible_routes"]
        typed = [r for r in routes if r in NATIVE_ROUTES]
        native = (classical is not None and not admitted["interpretation_required"]
                  and len(routes) == 1 and len(typed) == 1)
        generative = generator is not None and len(routes) == 1 and routes[0] == "PYTHON"
        allowed = [a for a, yes in (
            ("CLASSICAL", native), ("GENERATE", generative),
            ("ESCALATE", escalator is not None), ("ABSTAIN", True)
        ) if yes]
        out["allowed_actions"] = allowed
        if action_scorer is not None:
            out["selector_calls"] = 1
            # A callback may have made partial neural forwards. Without a
            # complete scorer receipt, its cost is UNKNOWN, never free.
            out["cost_accounting_complete"] = False
        try:
            choice = _select(view, allowed, action_scorer)
        except Exception as exc:
            # An untrusted scorer error is an abstention, not authority to execute.
            out["error"] = type(exc).__name__ + ": " + str(exc)
            choice = "ABSTAIN"
        out["action"] = choice
        out["trace"].append(choice)
        if choice == "ABSTAIN":
            return out
        if choice == "CLASSICAL":
            out["selected_route"] = typed[0]
            callback = lambda: classical(typed[0], snapshot(view))
        elif choice == "GENERATE":
            callback = lambda: generator(snapshot(view))
        else:
            callback = lambda: escalator(snapshot(view))
        out["executor_calls"] += 1
        out["cost_accounting_complete"] = False
        candidate = _candidate(callback())
        for k in ("model_calls", "tool_calls", "generated_tokens"):
            out[k] += candidate[k]
        out["candidate_provenance"] = candidate["provenance"]
        if verify_original is None:
            out["error"] = "NO_INDEPENDENT_VERIFIER"
            out["cost_accounting_complete"] = action_scorer is None
            return out
        out["trace"].append("VERIFY")
        out["verifier_calls"] += 1
        ok = verify_original(snapshot(view), snapshot(candidate["answer"]))
        if type(ok) is not bool:
            raise ValueError("original verifier must return exact bool")
        out["accepted"] = ok
        out["status"] = "VERIFIED" if ok else "UNKNOWN"
        out["cost_accounting_complete"] = action_scorer is None
        return out
    except Exception as exc:
        out["error"] = type(exc).__name__ + ": " + str(exc)
        return out
    finally:
        out["complete_wall_ms"] = round(wall(), 3)
        out["energy_j"] = None
        out["flops"] = None
        out["total_monetary_cost"] = None
