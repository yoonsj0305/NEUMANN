"""P1.8 opened-development semantic selector.

This module is prospective and separate from the already-published P1.8 P0.
It preserves the P1.7 source-bound query grammar, but permits a small frozen set
of public semantic instructions used only to disambiguate multiple feasible
candidate bindings. Query evidence and candidate IR remain deterministic.

No free generation, retry, hidden reference access, or numeric regeneration.
"""
from __future__ import annotations

from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL, validate_identity
from neumann1.control_plane_p11 import CODES, CodePlan, CodedFailure, NextCodeBackend, audit_codes, plan_cost
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, PERMUTATIONS, aggregate, Budget as ScoreBudget
from neumann1.control_plane_p17 import (
    build_candidates as p17_build_candidates,
    INSTRUCTIONS as P17_INSTRUCTIONS,
    LEDGER_KEYS,
)
from neumann1.control_plane_p18 import _masked_choice

SCHEMA = "neumann.control-plane-p1.8.semantic-selector.v1"
SELECTOR_WALL_MS = 180000.0

SEMANTIC_INSTRUCTIONS = (
    "X is the primary channel and Y is the spare channel. Resolve 'It' to the backup channel, then return a complete assignment.",
    "A is the input stage, B is the buffer stage, and C is the output stage. Resolve 'It' to the intermediate storage stage, then return a complete assignment.",
    "P is intake, Q is processing, R is holding, and S is output. Resolve 'It' to the temporary storage role, then return a complete assignment.",
    "M is the leader, N is the deputy, and O is the observer. Resolve 'It' to the second-in-command, then return a complete assignment.",
)


def parser_view(view):
    """Map a P1.8 semantic instruction to the unchanged P1.7 query parser.

    The original query bytes are unchanged. Only the instruction string is
    normalized for deterministic candidate construction. The original semantic
    instruction remains visible to the selector and original verifier.
    """
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("exact P1.8 semantic view required")
    if type(view.get("public")) is not dict or set(view["public"]) != {"query"}:
        raise ValueError("exact query-only public payload required")
    instruction = view.get("instruction")
    if instruction in P17_INSTRUCTIONS:
        return snapshot(view)
    if instruction not in SEMANTIC_INSTRUCTIONS:
        raise ValueError("unregistered P1.8 semantic instruction")
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


def selector_prompt(view, parsed, bundle, permutation):
    if tuple(permutation) not in PERMUTATIONS:
        raise ValueError("fixed candidate legend required")
    if parsed != parser_view(view) or bundle != p17_build_candidates(parsed):
        raise ValueError("semantic candidate/source drift")
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
    legend = []
    for i in range(4):
        if i < len(bundle["candidates"]):
            original = bundle["candidates"][i]
            candidate = {
                "route": original["route"],
                "atoms": [[a[0], *[aliases[ref] for ref in a[1:]]] for a in original["atoms"]],
            }
        else:
            candidate = {"unavailable": True}
        legend.append({"code": CODES[permutation[i]], "interpretation": candidate})
    payload = {
        "original": view,
        "query_parser_view": parsed,
        "evidence": evidence,
        "legend": legend,
    }
    return (
        "Select the interpretation faithful to the original public instruction and obligation. "
        "Return one code only. Unavailable slots cannot be chosen. "
        "References copy source evidence; never generate numbers.\n"
        + canonical(payload)
    )


class FrozenSemanticSelector:
    """Frozen Gemma teacher-forced selector for genuine residual P1.8 ambiguity."""

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

    def score(self, view, parsed, bundle, remaining_ms):
        began = perf_counter_ns()
        elapsed = lambda: (perf_counter_ns() - began) / 1e6
        receipt = {
            "schema": SCHEMA,
            "status": "FAILED",
            "bundle_sha256": bundle["bundle_sha256"],
            "original_view_sha256": digest(view),
            "parser_view_sha256": digest(parsed),
            "passes": [],
            "ledger": dict.fromkeys(LEDGER_KEYS, 0),
        }
        try:
            prompts = [selector_prompt(view, parsed, bundle, p) for p in PERMUTATIONS]
            receipt["prompt_sha256"] = [digest(prompt) for prompt in prompts]
            prefixes = [tuple(self.encoder(prompt)) for prompt in prompts]
            for mode, size, order in (
                ("batch4", 4, list(range(24))),
                ("unbatched1", 1, list(range(24))),
                ("reverse_batch4", 4, list(reversed(range(24)))),
            ):
                plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
                cost = plan_cost(plan, size)
                if any(receipt["ledger"][k] + v > getattr(ScoreBudget(), k) for k, v in cost.items()):
                    raise ValueError("selector pre-forward cost cap")
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
                left = min(
                    finite(remaining_ms, True) - elapsed(),
                    SELECTOR_WALL_MS - elapsed(),
                )
                if left <= 0:
                    raise TimeoutError("semantic selector preparation deadline")
                try:
                    output = self.backend.evaluate(plan, size, left)
                except CodedFailure as exc:
                    row["known_partial_cost"] = snapshot(exc.known_cost)
                    for key, value in exc.known_cost.items():
                        receipt["ledger"][key] += value
                    raise
                for key, value in output["cost"].items():
                    receipt["ledger"][key] += value
                matrix = [None] * 24
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


def validate_selection(view, parsed, bundle, eligible, receipt):
    if parsed != parser_view(view) or bundle != p17_build_candidates(parsed):
        raise ValueError("semantic candidate/source drift")
    if (
        type(eligible) is not list
        or len(eligible) < 2
        or eligible != sorted(set(eligible))
        or any(type(i) is not int or not 0 <= i < len(bundle["candidates"]) for i in eligible)
    ):
        raise ValueError("distinct original eligible indexes required")
    if receipt.get("status") != "COMPLETE" or receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("partial or wrong semantic selector receipt")
    if receipt.get("original_view_sha256") != digest(view) or receipt.get("parser_view_sha256") != digest(parsed):
        raise ValueError("semantic selector view identity drift")
    expected_prompts = [digest(selector_prompt(view, parsed, bundle, p)) for p in PERMUTATIONS]
    if receipt.get("prompt_sha256") != expected_prompts:
        raise ValueError("semantic scored prompt identity drift")
    if any(receipt.get("identity", {}).get(k) != v for k, v in MODEL.items()) or receipt.get("unchanged") is not True:
        raise ValueError("frozen core identity required")
    validate_identity(receipt["identity"])
    if type(receipt.get("generated_calls")) is not int or receipt["generated_calls"] != 0:
        raise ValueError("control generation forbidden")

    passes = receipt.get("passes", [])
    if len(passes) != 3:
        raise ValueError("complete batch/order passes required")
    totals = dict.fromkeys(LEDGER_KEYS, 0)
    matrices = []
    for row, (mode, size, order) in zip(
        passes,
        (
            ("batch4", 4, list(range(24))),
            ("unbatched1", 1, list(range(24))),
            ("reverse_batch4", 4, list(reversed(range(24)))),
        ),
    ):
        if row.get("mode") != mode or row.get("batch_size") != size or row.get("order") != order or row.get("status") != "COMPLETE":
            raise ValueError("exact scoring mode required")
        if row.get("code_ids") != list(CODE_TOKEN_IDS):
            raise ValueError("tokenizer code drift")
        plan = CodePlan(tuple(tuple(p) for p in row["prefixes"]), CODE_TOKEN_IDS)
        if any(len(p) > ScoreBudget().context_tokens for p in plan.prefixes):
            raise ValueError("selector context cap; no truncation")
        cost = plan_cost(plan, size)
        if len(plan.prefixes) != 24 or row.get("actual") != cost or row.get("planned") != cost:
            raise ValueError("complete prefix/cost coverage required")
        if type(row.get("peak_accelerator_memory_bytes")) is not int or row["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("accelerator memory receipt required")
        for key, value in cost.items():
            totals[key] += value
        matrices.append(row["matrix"])

    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(), k) for k, v in totals.items()):
        raise ValueError("semantic scoring ledger mismatch or cap")
    if passes[1]["prefixes"] != passes[0]["prefixes"] or passes[2]["prefixes"] != list(reversed(passes[0]["prefixes"])):
        raise ValueError("tokenized prefix identity drift")
    if finite(receipt.get("complete_ms"), True) > SELECTOR_WALL_MS:
        raise ValueError("semantic selector wall cap")
    return _masked_choice(matrices, eligible)


def contract():
    return {
        "schema": SCHEMA,
        "model": dict(MODEL),
        "query_candidate_parser": "UNCHANGED_P1.7_VIA_INSTRUCTION_ONLY_PARSER_VIEW",
        "semantic_instructions": list(SEMANTIC_INSTRUCTIONS),
        "selector_wall_ms": SELECTOR_WALL_MS,
        "generation": False,
        "retry": False,
        "all_24_code_mappings": True,
        "three_batch_order_modes": True,
        "private_reference_visible_to_selector": False,
        "p17_result_rescued": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
    }
