"""Prospective P1.9 opened-development semantic surface.

This module instantiates the merged P1.9 P0.1 complementary-polarity mechanism
on a NEW semantic-development vocabulary.  P1.8 opened semantic tasks are
regression history only and are never rescored here.

No model work occurs at import time.
"""
from __future__ import annotations

from time import perf_counter_ns

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL, validate_identity
from neumann1.control_plane_p11 import (
    CODES, CodePlan, CodedFailure, NextCodeBackend, audit_codes, plan_cost,
)
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, Budget as ScoreBudget
from neumann1.control_plane_p17 import (
    build_candidates as p17_build_candidates,
    INSTRUCTIONS as P17_INSTRUCTIONS,
    LEDGER_KEYS,
)
from neumann1.control_plane_p19_balanced import (
    CLAIMS, MAX_BATCH, Criteria, _balanced_scores,
)

SCHEMA = "neumann.control-plane-p1.9.opened-semantic.v1"

SEMANTIC_INSTRUCTIONS = (
    "X is the inbound channel and Y is the outbound channel. Resolve 'It' to the channel carrying traffic away from the system, then return a complete assignment.",
    "A is the left port, B is the center port, and C is the right port. Resolve 'It' to the middle port, then return a complete assignment.",
    "P is the first stage, Q is the second stage, R is the third stage, and S is the fourth stage. Resolve 'It' to the stage immediately after Q, then return a complete assignment.",
    "M is the active unit, N is the standby unit, and O is the retired unit. Resolve 'It' to the unit that would take over if the active unit failed, then return a complete assignment.",
)


def parser_view(view):
    """Normalize only the registered instruction; query bytes stay identical."""
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("exact P1.9 semantic view required")
    if type(view.get("public")) is not dict or set(view["public"]) != {"query"}:
        raise ValueError("exact query-only public payload required")
    instruction = view.get("instruction")
    if instruction in P17_INSTRUCTIONS:
        return snapshot(view)
    if instruction not in SEMANTIC_INSTRUCTIONS:
        raise ValueError("unregistered P1.9 semantic instruction")
    if type(view["public"]["query"]) is not str or not view["public"]["query"]:
        raise ValueError("nonempty query required")
    return {
        "instruction": "Return a complete assignment.",
        "public": {"query": view["public"]["query"]},
    }


def build_semantic_bundle(view):
    parsed = parser_view(view)
    bundle = p17_build_candidates(parsed)
    return parsed, bundle


def _candidate_payload(view, parsed, bundle, candidate_index):
    if parsed != parser_view(view) or bundle != p17_build_candidates(parsed):
        raise ValueError("P1.9 registered candidate/source drift")
    if type(candidate_index) is not int or not 0 <= candidate_index < len(bundle["candidates"]):
        raise ValueError("valid candidate index required")

    aliases = {token["id"]: "e%d" % i for i, token in enumerate(bundle["evidence"]["tokens"])}
    evidence = [
        {
            "ref": aliases[t["id"]],
            "kind": t["kind"],
            "span": t["span"],
            "surface": t["surface"],
            "value": t["value"],
        }
        for t in bundle["evidence"]["tokens"]
    ]
    original = bundle["candidates"][candidate_index]
    candidate = {
        "route": original["route"],
        "atoms": [[a[0], *[aliases[ref] for ref in a[1:]]] for a in original["atoms"]],
    }
    return {
        "original": view,
        "query_parser_view": parsed,
        "evidence": evidence,
        "candidate_interpretation": candidate,
    }


def polarity_prompt(view, parsed, bundle, candidate_index, claim):
    if claim not in CLAIMS:
        raise ValueError("registered polarity claim required")
    payload = {
        **_candidate_payload(view, parsed, bundle, candidate_index),
        "claim": (
            "The candidate interpretation is faithful to the original public instruction and obligation."
            if claim == "FAITHFUL"
            else "The candidate interpretation is not faithful to the original public instruction and obligation."
        ),
    }
    return (
        "Judge whether the claim is correct. References copy source evidence; never invent numbers "
        "or entities. Return one code only: A means YES; B means NO. C and D are invalid responses.\n"
        + canonical(payload)
    )


def prompt_rows(view, parsed, bundle, eligible):
    if (
        type(eligible) is not list
        or not 2 <= len(eligible) <= 4
        or eligible != sorted(set(eligible))
        or any(type(i) is not int or not 0 <= i < len(bundle["candidates"]) for i in eligible)
    ):
        raise ValueError("2..4 distinct eligible candidate indexes required")
    rows = []
    for candidate_index in eligible:
        for claim in CLAIMS:
            rows.append({
                "candidate_index": candidate_index,
                "claim": claim,
                "prompt": polarity_prompt(view, parsed, bundle, candidate_index, claim),
            })
    return rows


class FrozenRegisteredBalancedSelector:
    """Frozen Gemma P0.1 selector on the registered fresh semantic surface."""

    def __init__(self, core):
        from neumann1.control_plane_scoring_v1 import attach_frozen_gemma
        from experiments.control_plane_p1_first import forbid_generation

        self.core = core
        self.identity = snapshot(core.identity)
        if any(self.identity.get(k) != v for k, v in MODEL.items()) or core.audit().get("unchanged") is not True:
            raise ValueError("original frozen core required")
        validate_identity(self.identity)
        self.counter = forbid_generation(core)
        self.encoder = attach_frozen_gemma(core).encode_prefix
        if tuple(audit_codes(core.processor.tokenizer)["token_ids"]) != CODE_TOKEN_IDS:
            raise ValueError("tokenizer code drift")
        self.backend = NextCodeBackend(core.model, core.processor.tokenizer.pad_token_id, core.device)

    def score(self, view, parsed, bundle, eligible, remaining_ms):
        began = perf_counter_ns()
        elapsed = lambda: (perf_counter_ns() - began) / 1e6
        receipt = {
            "schema": SCHEMA,
            "status": "FAILED",
            "bundle_sha256": bundle["bundle_sha256"],
            "original_view_sha256": digest(view),
            "parser_view_sha256": digest(parsed),
            "eligible_indexes": snapshot(eligible),
            "passes": [],
            "ledger": dict.fromkeys(LEDGER_KEYS, 0),
        }
        try:
            rows = prompt_rows(view, parsed, bundle, eligible)
            receipt["row_keys"] = [[r["candidate_index"], r["claim"]] for r in rows]
            receipt["prompt_sha256"] = [digest(r["prompt"]) for r in rows]
            prefixes = tuple(tuple(self.encoder(r["prompt"])) for r in rows)
            n = len(prefixes)

            for mode, size, order in (
                ("batch4", MAX_BATCH, list(range(n))),
                ("unbatched1", 1, list(range(n))),
                ("reverse_batch4", MAX_BATCH, list(reversed(range(n)))),
            ):
                plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
                cost = plan_cost(plan, size)
                if any(receipt["ledger"][key] + value > getattr(ScoreBudget(), key) for key, value in cost.items()):
                    raise ValueError("P1.9 registered scorer pre-forward cost cap")
                row = {
                    "mode": mode,
                    "batch_size": size,
                    "order": order,
                    "prefixes": snapshot(plan.prefixes),
                    "code_ids": list(CODE_TOKEN_IDS),
                    "planned": cost,
                    "status": "STARTED",
                }
                receipt["passes"].append(row)
                left = finite(remaining_ms, True) - elapsed()
                if left <= 0:
                    raise TimeoutError("P1.9 registered scoring deadline")
                try:
                    output = self.backend.evaluate(plan, size, left)
                except CodedFailure as exc:
                    row["known_partial_cost"] = snapshot(exc.known_cost)
                    for key, value in exc.known_cost.items():
                        receipt["ledger"][key] += value
                    raise
                for key, value in output["cost"].items():
                    receipt["ledger"][key] += value
                matrix = [None] * n
                for i, scores in zip(order, output["scores"]):
                    matrix[i] = snapshot(scores)
                row.update(
                    status="COMPLETE",
                    actual=output["cost"],
                    matrix=matrix,
                    peak_accelerator_memory_bytes=output["peak_accelerator_memory_bytes"],
                )
            receipt["status"] = "COMPLETE"
        except Exception as exc:
            receipt["error"] = type(exc).__name__ + ": " + str(exc)

        receipt.update(
            identity=snapshot(self.core.identity),
            unchanged=self.core.identity == self.identity and self.core.audit().get("unchanged") is True,
            generated_calls=self.counter["calls"],
            complete_ms=elapsed(),
        )
        return receipt


def validate_selection(view, parsed, bundle, eligible, receipt, criteria=Criteria()):
    rows = prompt_rows(view, parsed, bundle, eligible)
    if receipt.get("status") != "COMPLETE":
        raise ValueError("complete P1.9 registered selector receipt required")
    if receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("P1.9 registered bundle identity drift")
    if receipt.get("original_view_sha256") != digest(view) or receipt.get("parser_view_sha256") != digest(parsed):
        raise ValueError("P1.9 registered view identity drift")
    if receipt.get("eligible_indexes") != eligible:
        raise ValueError("P1.9 registered eligible-index drift")
    if receipt.get("row_keys") != [[r["candidate_index"], r["claim"]] for r in rows]:
        raise ValueError("P1.9 registered polarity-row drift")
    if receipt.get("prompt_sha256") != [digest(r["prompt"]) for r in rows]:
        raise ValueError("P1.9 registered prompt identity drift")
    if any(receipt.get("identity", {}).get(k) != v for k, v in MODEL.items()) or receipt.get("unchanged") is not True:
        raise ValueError("frozen core identity required")
    validate_identity(receipt["identity"])
    if receipt.get("generated_calls") != 0:
        raise ValueError("control generation forbidden")

    passes = receipt.get("passes", [])
    n = len(rows)
    expected_modes = (
        ("batch4", MAX_BATCH, list(range(n))),
        ("unbatched1", 1, list(range(n))),
        ("reverse_batch4", MAX_BATCH, list(reversed(range(n)))),
    )
    if len(passes) != 3:
        raise ValueError("three registered P1.9 execution modes required")

    totals = dict.fromkeys(LEDGER_KEYS, 0)
    scores_by_mode = []
    priors_by_mode = []
    base_prefixes = None
    for row, (mode, size, order) in zip(passes, expected_modes):
        if (
            row.get("mode") != mode
            or row.get("batch_size") != size
            or row.get("order") != order
            or row.get("status") != "COMPLETE"
            or row.get("code_ids") != list(CODE_TOKEN_IDS)
        ):
            raise ValueError("exact registered P1.9 execution mode required")
        plan = CodePlan(tuple(tuple(p) for p in row["prefixes"]), CODE_TOKEN_IDS)
        cost = plan_cost(plan, size)
        if row.get("planned") != cost or row.get("actual") != cost:
            raise ValueError("P1.9 registered exact cost coverage required")
        if type(row.get("peak_accelerator_memory_bytes")) is not int or row["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("P1.9 registered accelerator memory receipt required")
        for key, value in cost.items():
            totals[key] += value

        scores, priors = _balanced_scores(row.get("matrix"), eligible)
        scores_by_mode.append(scores)
        priors_by_mode.append(priors)

        if mode == "batch4":
            base_prefixes = row["prefixes"]
        elif mode == "unbatched1" and row["prefixes"] != base_prefixes:
            raise ValueError("P1.9 registered tokenized prefix identity drift")
        elif mode == "reverse_batch4" and row["prefixes"] != list(reversed(base_prefixes)):
            raise ValueError("P1.9 registered reverse prefix identity drift")

    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(), key) for key, v in totals.items()):
        raise ValueError("P1.9 registered scoring ledger mismatch or cap")

    k = len(eligible)
    max_delta = max(
        abs(scores_by_mode[0][i] - scores_by_mode[m][i])
        for m in (1, 2)
        for i in range(k)
    )
    if max_delta > criteria.max_mode_balanced_score_delta_nats:
        raise ValueError("P1.9 registered batch/order numerical drift")

    means = [sum(scores_by_mode[m][i] for m in range(3)) / 3.0 for i in range(k)]
    prior_means = [sum(priors_by_mode[m][i] for m in range(3)) / 3.0 for i in range(k)]
    ranked = sorted(range(k), key=lambda i: (-means[i], eligible[i]))
    best, second = ranked[0], ranked[1]
    if means[best] < criteria.minimum_balanced_score_nats:
        raise ValueError("P1.9 registered no positively balanced candidate")
    if means[best] - means[second] <= criteria.minimum_candidate_margin_nats:
        raise ValueError("P1.9 registered candidate margin failure")

    per_mode_winners = [
        max(range(k), key=lambda i: (scores[i], -eligible[i]))
        for scores in scores_by_mode
    ]
    if any(w != best for w in per_mode_winners):
        raise ValueError("P1.9 registered batch/order winner disagreement")

    return {
        "selected_candidate": eligible[best],
        "candidate_balanced_score_nats": {str(eligible[i]): means[i] for i in range(k)},
        "candidate_label_prior_trace_nats": {str(eligible[i]): prior_means[i] for i in range(k)},
        "margin_nats": means[best] - means[second],
        "max_mode_balanced_score_delta_nats": max_delta,
        "forward_calls": totals["forward_calls"],
        "evaluated_tokens": totals["evaluated_tokens"],
    }


def contract():
    return {
        "schema": SCHEMA,
        "parent": "neumann.control-plane-p1.9.p0.1.balanced-proposition.v1",
        "semantic_instructions": list(SEMANTIC_INSTRUCTIONS),
        "query_candidate_parser": "P1.7_BOUNDED_QUERY_GRAMMAR_WITH_REGISTERED_INSTRUCTION_NORMALIZATION",
        "response_semantics": {CODES[0]: "YES", CODES[1]: "NO"},
        "candidate_code_permutations": 0,
        "generation": False,
        "retry": False,
        "hidden_reference_access": False,
        "p18_opened_tasks_model_score_reuse": False,
        "actual_gemma_run": "NOT_RUN",
    }
