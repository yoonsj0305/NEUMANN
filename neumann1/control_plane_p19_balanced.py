"""P1.9 P0.1: candidate-local complementary-polarity proposition scoring.

This is prospective synthetic-contract work only. P1.8 remains immutable FAIL
and P1.9 P0 remains the parent mechanism.

For every eligible candidate, score two complementary propositions with fixed
response-code semantics:

    A = YES
    B = NO

Claims:
    + candidate is FAITHFUL
    - candidate is NOT_FAITHFUL

The balanced semantic score is:

    0.5 * [(log P(A)-log P(B))_faithful
           - (log P(A)-log P(B))_not_faithful]

A fixed additive A/B code prior cancels algebraically. Candidate identity never
moves into an output code and no candidate/code permutations are used.
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

SCHEMA = "neumann.control-plane-p1.9.p0.1.balanced-proposition.v1"
A_INDEX = 0
B_INDEX = 1
CLAIMS = ("FAITHFUL", "NOT_FAITHFUL")
MAX_BATCH = 4


@dataclass(frozen=True)
class Criteria:
    max_mode_balanced_score_delta_nats: float = 0.05
    minimum_balanced_score_nats: float = 0.0
    minimum_candidate_margin_nats: float = 0.5


def contract():
    return {
        "schema": SCHEMA,
        "stage": "P0_1_SYNTHETIC_CONTRACT_ONLY",
        "model": dict(MODEL),
        "response_semantics": {
            CODES[A_INDEX]: "YES",
            CODES[B_INDEX]: "NO",
        },
        "claims": list(CLAIMS),
        "balanced_score": "0.5*((A-B)_FAITHFUL-(A-B)_NOT_FAITHFUL)",
        "fixed_additive_ab_prior_cancels": True,
        "candidate_identity_in_output_code": False,
        "candidate_code_permutations": 0,
        "modes": ["batch4", "unbatched1", "reverse_batch4"],
        "max_batch": MAX_BATCH,
        "forward_calls_per_item": "2*k + 2*ceil((2*k)/4)",
        "p18_shape_planned_forward_calls": 38,
        "criteria": asdict(Criteria()),
        "generation": False,
        "retry": False,
        "hidden_reference_access": False,
        "numeric_regeneration": False,
        "p18_result_rescued": False,
        "p18_opened_tasks_model_score_reuse": False,
        "future_actual_requires_new_registered_tasks": True,
        "actual_gemma_run": "NOT_RUN",
        "development_registration": "NOT_REGISTERED",
        "fresh_validation_registered": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
    }


def _candidate_payload(view, parsed, bundle, candidate_index):
    if parsed != parser_view(view) or bundle != build_semantic_bundle(view)[1]:
        raise ValueError("P1.9 P0.1 semantic candidate/source drift")
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


def planned_cost(prefixes):
    if type(prefixes) is not tuple or len(prefixes) not in (4, 6, 8):
        raise ValueError("exact 2*k polarity prefixes required for k=2..4")
    n = len(prefixes)
    total = dict.fromkeys(LEDGER_KEYS, 0)
    for size, order in (
        (MAX_BATCH, list(range(n))),
        (1, list(range(n))),
        (MAX_BATCH, list(reversed(range(n)))),
    ):
        plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
        cost = plan_cost(plan, size)
        for key, value in cost.items():
            total[key] += value
    return total


class FrozenBalancedPropositionSelector:
    """Frozen Gemma scorer with complementary polarity and fixed YES/NO codes."""

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
            receipt["row_keys"] = [
                [row["candidate_index"], row["claim"]]
                for row in rows
            ]
            receipt["prompt_sha256"] = [digest(row["prompt"]) for row in rows]
            prefixes = tuple(tuple(self.encoder(row["prompt"])) for row in rows)
            n = len(prefixes)

            for mode, size, order in (
                ("batch4", MAX_BATCH, list(range(n))),
                ("unbatched1", 1, list(range(n))),
                ("reverse_batch4", MAX_BATCH, list(reversed(range(n)))),
            ):
                plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
                cost = plan_cost(plan, size)
                if any(receipt["ledger"][key] + value > getattr(ScoreBudget(), key) for key, value in cost.items()):
                    raise ValueError("P1.9 P0.1 scorer pre-forward cost cap")
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
                    raise TimeoutError("P1.9 P0.1 scoring deadline")
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


def _yes_no_log_odds(row):
    if type(row) is not list or len(row) != 4:
        raise ValueError("four audited code scores required")
    values = [finite(v) for v in row]
    if any(v > 0 for v in values):
        raise ValueError("nonpositive log probabilities required")
    return values[A_INDEX] - values[B_INDEX]


def _balanced_scores(matrix, eligible):
    if type(matrix) is not list or len(matrix) != 2 * len(eligible):
        raise ValueError("complete polarity matrix required")
    scores = []
    priors = []
    for i in range(len(eligible)):
        faithful = _yes_no_log_odds(matrix[2 * i])
        not_faithful = _yes_no_log_odds(matrix[2 * i + 1])
        scores.append(0.5 * (faithful - not_faithful))
        priors.append(0.5 * (faithful + not_faithful))
    return scores, priors


def validate_selection(view, parsed, bundle, eligible, receipt, criteria=Criteria()):
    rows = prompt_rows(view, parsed, bundle, eligible)
    if receipt.get("status") != "COMPLETE":
        raise ValueError("complete P1.9 P0.1 selector receipt required")
    if receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("P1.9 P0.1 bundle identity drift")
    if receipt.get("original_view_sha256") != digest(view) or receipt.get("parser_view_sha256") != digest(parsed):
        raise ValueError("P1.9 P0.1 view identity drift")
    if receipt.get("eligible_indexes") != eligible:
        raise ValueError("P1.9 P0.1 eligible-index drift")
    expected_keys = [[row["candidate_index"], row["claim"]] for row in rows]
    if receipt.get("row_keys") != expected_keys:
        raise ValueError("P1.9 P0.1 polarity-row drift")
    if receipt.get("prompt_sha256") != [digest(row["prompt"]) for row in rows]:
        raise ValueError("P1.9 P0.1 prompt identity drift")
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
        raise ValueError("three P1.9 P0.1 execution modes required")

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
            raise ValueError("exact P1.9 P0.1 execution mode required")
        plan = CodePlan(tuple(tuple(p) for p in row["prefixes"]), CODE_TOKEN_IDS)
        cost = plan_cost(plan, size)
        if row.get("planned") != cost or row.get("actual") != cost:
            raise ValueError("P1.9 P0.1 exact cost coverage required")
        if type(row.get("peak_accelerator_memory_bytes")) is not int or row["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("P1.9 P0.1 accelerator memory receipt required")
        for key, value in cost.items():
            totals[key] += value

        matrix = row.get("matrix")
        scores, priors = _balanced_scores(matrix, eligible)
        scores_by_mode.append(scores)
        priors_by_mode.append(priors)

        if mode == "batch4":
            base_prefixes = row["prefixes"]
        elif mode == "unbatched1" and row["prefixes"] != base_prefixes:
            raise ValueError("P1.9 P0.1 tokenized prefix identity drift")
        elif mode == "reverse_batch4" and row["prefixes"] != list(reversed(base_prefixes)):
            raise ValueError("P1.9 P0.1 reverse prefix identity drift")

    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(), key) for key, v in totals.items()):
        raise ValueError("P1.9 P0.1 scoring ledger mismatch or cap")

    k = len(eligible)
    max_delta = max(
        abs(scores_by_mode[0][i] - scores_by_mode[m][i])
        for m in (1, 2)
        for i in range(k)
    )
    if max_delta > criteria.max_mode_balanced_score_delta_nats:
        raise ValueError("P1.9 P0.1 batch/order numerical drift")

    means = [
        sum(scores_by_mode[m][i] for m in range(3)) / 3.0
        for i in range(k)
    ]
    prior_means = [
        sum(priors_by_mode[m][i] for m in range(3)) / 3.0
        for i in range(k)
    ]
    ranked = sorted(range(k), key=lambda i: (-means[i], eligible[i]))
    best, second = ranked[0], ranked[1]
    if means[best] < criteria.minimum_balanced_score_nats:
        raise ValueError("P1.9 P0.1 no positively balanced candidate")
    if means[best] - means[second] <= criteria.minimum_candidate_margin_nats:
        raise ValueError("P1.9 P0.1 candidate margin failure")

    per_mode_winners = [
        max(range(k), key=lambda i: (scores[i], -eligible[i]))
        for scores in scores_by_mode
    ]
    if any(w != best for w in per_mode_winners):
        raise ValueError("P1.9 P0.1 batch/order winner disagreement")

    return {
        "selected_candidate": eligible[best],
        "candidate_balanced_score_nats": {str(eligible[i]): means[i] for i in range(k)},
        "candidate_label_prior_trace_nats": {str(eligible[i]): prior_means[i] for i in range(k)},
        "margin_nats": means[best] - means[second],
        "max_mode_balanced_score_delta_nats": max_delta,
        "forward_calls": totals["forward_calls"],
        "evaluated_tokens": totals["evaluated_tokens"],
    }
