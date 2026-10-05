"""P1.9 P0: candidate-local semantic proposition scoring.

Post-P1.8 architecture candidate.  This module does not change or rescue the
historical P1.8 result.  Candidate identity lives only in the prompt; response
semantics are fixed across candidates:

    A = FAITHFUL
    B = NOT_FAITHFUL

C/D remain audited one-token codes in the backend interface but are never used
for selection.  No route/candidate code permutation is performed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL, validate_identity
from neumann1.control_plane_p11 import (
    CODES, CodePlan, CodedFailure, NextCodeBackend, audit_codes, plan_cost,
)
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, Budget as ScoreBudget
from neumann1.control_plane_p17 import LEDGER_KEYS
from neumann1.control_plane_p18_semantic import build_semantic_bundle, parser_view

SCHEMA = "neumann.control-plane-p1.9.proposition-selector.p0.v1"
A_INDEX = 0
B_INDEX = 1


@dataclass(frozen=True)
class Criteria:
    max_mode_log_odds_delta_nats: float = 0.05
    minimum_faithful_log_odds_nats: float = 0.0
    minimum_candidate_margin_nats: float = 0.5


def contract():
    return {
        "schema": SCHEMA,
        "stage": "P0_SYNTHETIC_CONTRACT_ONLY",
        "model": dict(MODEL),
        "response_semantics": {
            CODES[A_INDEX]: "FAITHFUL",
            CODES[B_INDEX]: "NOT_FAITHFUL",
        },
        "candidate_identity_in_output_code": False,
        "candidate_code_permutations": 0,
        "modes": ["batch_all", "unbatched1", "reverse_batch_all"],
        "forward_calls_per_item": "k+2 for k eligible candidates",
        "criteria": asdict(Criteria()),
        "generation": False,
        "retry": False,
        "hidden_reference_access": False,
        "numeric_regeneration": False,
        "p18_result_rescued": False,
        "actual_gemma_run": "NOT_RUN",
        "development_registration": "NOT_REGISTERED",
        "fresh_validation_registered": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
    }


def proposition_prompt(view, parsed, bundle, candidate_index):
    if parsed != parser_view(view) or bundle != build_semantic_bundle(view)[1]:
        raise ValueError("P1.9 semantic candidate/source drift")
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
    payload = {
        "original": view,
        "query_parser_view": parsed,
        "evidence": evidence,
        "candidate_interpretation": candidate,
    }
    return (
        "Judge only whether the candidate interpretation is faithful to the original public "
        "instruction and obligation. References copy source evidence; never invent numbers or "
        "entities. Return one code only: A means FAITHFUL; B means NOT_FAITHFUL. "
        "C and D are invalid responses.\n" + canonical(payload)
    )


def planned_cost(prefixes):
    if type(prefixes) is not tuple or not 2 <= len(prefixes) <= 4:
        raise ValueError("2..4 eligible candidate prefixes required")
    k = len(prefixes)
    total = dict.fromkeys(LEDGER_KEYS, 0)
    for size, order in (
        (k, list(range(k))),
        (1, list(range(k))),
        (k, list(reversed(range(k)))),
    ):
        plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
        cost = plan_cost(plan, size)
        for key, value in cost.items():
            total[key] += value
    return total


class FrozenPropositionSelector:
    """Frozen Gemma scorer with fixed A/B semantics across candidate prompts."""

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
            if (
                type(eligible) is not list
                or not 2 <= len(eligible) <= 4
                or eligible != sorted(set(eligible))
                or any(type(i) is not int or not 0 <= i < len(bundle["candidates"]) for i in eligible)
            ):
                raise ValueError("2..4 distinct eligible candidate indexes required")

            prompts = [proposition_prompt(view, parsed, bundle, i) for i in eligible]
            receipt["prompt_sha256"] = [digest(p) for p in prompts]
            prefixes = tuple(tuple(self.encoder(prompt)) for prompt in prompts)
            k = len(prefixes)

            for mode, size, order in (
                ("batch_all", k, list(range(k))),
                ("unbatched1", 1, list(range(k))),
                ("reverse_batch_all", k, list(reversed(range(k)))),
            ):
                plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
                cost = plan_cost(plan, size)
                if any(receipt["ledger"][key] + value > getattr(ScoreBudget(), key) for key, value in cost.items()):
                    raise ValueError("P1.9 scorer pre-forward cost cap")
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
                    raise TimeoutError("P1.9 scoring deadline")
                try:
                    output = self.backend.evaluate(plan, size, left)
                except CodedFailure as exc:
                    row["known_partial_cost"] = snapshot(exc.known_cost)
                    for key, value in exc.known_cost.items():
                        receipt["ledger"][key] += value
                    raise
                for key, value in output["cost"].items():
                    receipt["ledger"][key] += value
                matrix = [None] * k
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


def _log_odds(row):
    if type(row) is not list or len(row) != 4:
        raise ValueError("four audited code scores required")
    values = [finite(v) for v in row]
    if any(v > 0 for v in values):
        raise ValueError("nonpositive log probabilities required")
    return values[A_INDEX] - values[B_INDEX]


def validate_selection(view, parsed, bundle, eligible, receipt, criteria=Criteria()):
    if parsed != parser_view(view) or bundle != build_semantic_bundle(view)[1]:
        raise ValueError("P1.9 semantic candidate/source drift")
    if (
        type(eligible) is not list
        or not 2 <= len(eligible) <= 4
        or eligible != sorted(set(eligible))
        or any(type(i) is not int or not 0 <= i < len(bundle["candidates"]) for i in eligible)
    ):
        raise ValueError("2..4 distinct eligible candidate indexes required")
    if receipt.get("status") != "COMPLETE":
        raise ValueError("complete P1.9 selector receipt required")
    if receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("P1.9 bundle identity drift")
    if receipt.get("original_view_sha256") != digest(view) or receipt.get("parser_view_sha256") != digest(parsed):
        raise ValueError("P1.9 view identity drift")
    if receipt.get("eligible_indexes") != eligible:
        raise ValueError("P1.9 eligible-index drift")
    expected_prompts = [digest(proposition_prompt(view, parsed, bundle, i)) for i in eligible]
    if receipt.get("prompt_sha256") != expected_prompts:
        raise ValueError("P1.9 prompt identity drift")
    if any(receipt.get("identity", {}).get(k) != v for k, v in MODEL.items()) or receipt.get("unchanged") is not True:
        raise ValueError("frozen core identity required")
    validate_identity(receipt["identity"])
    if receipt.get("generated_calls") != 0:
        raise ValueError("control generation forbidden")

    passes = receipt.get("passes", [])
    k = len(eligible)
    expected_modes = (
        ("batch_all", k, list(range(k))),
        ("unbatched1", 1, list(range(k))),
        ("reverse_batch_all", k, list(reversed(range(k)))),
    )
    if len(passes) != 3:
        raise ValueError("three P1.9 execution modes required")

    totals = dict.fromkeys(LEDGER_KEYS, 0)
    odds_by_mode = []
    base_prefixes = None
    for row, (mode, size, order) in zip(passes, expected_modes):
        if (
            row.get("mode") != mode
            or row.get("batch_size") != size
            or row.get("order") != order
            or row.get("status") != "COMPLETE"
            or row.get("code_ids") != list(CODE_TOKEN_IDS)
        ):
            raise ValueError("exact P1.9 execution mode required")
        plan = CodePlan(tuple(tuple(p) for p in row["prefixes"]), CODE_TOKEN_IDS)
        cost = plan_cost(plan, size)
        if row.get("planned") != cost or row.get("actual") != cost:
            raise ValueError("P1.9 exact cost coverage required")
        if type(row.get("peak_accelerator_memory_bytes")) is not int or row["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("P1.9 accelerator memory receipt required")
        for key, value in cost.items():
            totals[key] += value
        matrix = row.get("matrix")
        if type(matrix) is not list or len(matrix) != k:
            raise ValueError("P1.9 candidate matrix coverage required")
        odds_by_mode.append([_log_odds(scores) for scores in matrix])

        if mode == "batch_all":
            base_prefixes = row["prefixes"]
        elif mode == "unbatched1" and row["prefixes"] != base_prefixes:
            raise ValueError("P1.9 tokenized prefix identity drift")
        elif mode == "reverse_batch_all" and row["prefixes"] != list(reversed(base_prefixes)):
            raise ValueError("P1.9 reverse prefix identity drift")

    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(), key) for key, v in totals.items()):
        raise ValueError("P1.9 scoring ledger mismatch or cap")

    max_delta = max(
        abs(odds_by_mode[0][i] - odds_by_mode[m][i])
        for m in (1, 2)
        for i in range(k)
    )
    if max_delta > criteria.max_mode_log_odds_delta_nats:
        raise ValueError("P1.9 batch/order numerical drift")

    means = [
        sum(odds_by_mode[m][i] for m in range(3)) / 3.0
        for i in range(k)
    ]
    ranked = sorted(range(k), key=lambda i: (-means[i], eligible[i]))
    best, second = ranked[0], ranked[1]
    if means[best] < criteria.minimum_faithful_log_odds_nats:
        raise ValueError("P1.9 no positively faithful candidate")
    if means[best] - means[second] <= criteria.minimum_candidate_margin_nats:
        raise ValueError("P1.9 candidate margin failure")

    per_mode_winners = [
        max(range(k), key=lambda i: (odds[i], -eligible[i]))
        for odds in odds_by_mode
    ]
    if any(w != best for w in per_mode_winners):
        raise ValueError("P1.9 batch/order winner disagreement")

    return {
        "selected_candidate": eligible[best],
        "candidate_log_odds_nats": {str(eligible[i]): means[i] for i in range(k)},
        "margin_nats": means[best] - means[second],
        "max_mode_log_odds_delta_nats": max_delta,
        "forward_calls": totals["forward_calls"],
        "evaluated_tokens": totals["evaluated_tokens"],
    }
