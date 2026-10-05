"""P1.10 P0: minimal semantic contrast + symmetric pairwise scoring.

Prospective architecture after the retained P1.9 semantic-capability FAIL.

The deterministic front half has already extracted source evidence, enumerated
bounded candidates and performed feasibility pruning.  P1.10 therefore removes
solver-irrelevant structure from the neural prompt and exposes only the
irreducible semantic contrast: which source-bound entity the single ambiguous
mention denotes under the public semantic instruction.

Pairwise outputs use fixed semantics:
    A = LEFT binding is more faithful
    B = RIGHT binding is more faithful

Both pair orientations are scored.  The antisymmetric preference

    D(i,j) = (L(i,j) - L(j,i)) / 2

cancels a global A/B token bias and first-order left/right presentation bias.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import re
from time import perf_counter_ns

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL, validate_identity
from neumann1.control_plane_p11 import (
    CODES, CodePlan, CodedFailure, NextCodeBackend, audit_codes, plan_cost,
)
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, Budget as ScoreBudget
from neumann1.control_plane_p17 import LEDGER_KEYS, build_candidates as p17_build_candidates

SCHEMA = "neumann.control-plane-p1.10.minimal-pairwise.p0.v1"
A_INDEX = 0
B_INDEX = 1


@dataclass(frozen=True)
class Criteria:
    max_mode_log_odds_delta_nats: float = 0.05
    minimum_pairwise_preference_nats: float = 0.5


def contract():
    return {
        "schema": SCHEMA,
        "stage": "P0_SYNTHETIC_CONTRACT_ONLY",
        "model": dict(MODEL),
        "semantic_ir": "SOURCE_BOUND_MINIMAL_PRONOUN_BINDING_CONTRAST",
        "removed_from_neural_prompt": [
            "domains",
            "literal_values",
            "already_resolved_csp_relations",
            "candidate_atoms",
            "evidence_alias_ledger",
        ],
        "response_semantics": {
            CODES[A_INDEX]: "LEFT_BINDING_MORE_FAITHFUL",
            CODES[B_INDEX]: "RIGHT_BINDING_MORE_FAITHFUL",
        },
        "candidate_identity_in_output_code": False,
        "candidate_code_permutations": 0,
        "pair_orientations": "BOTH",
        "pairwise_preference": "D(i,j)=(L(i,j)-L(j,i))/2",
        "winner_rule": "UNIQUE_CONDORCET_ABOVE_MARGIN",
        "modes": ["batch_all", "reverse_batch_all"],
        "forward_calls_per_item": 2,
        "criteria": asdict(Criteria()),
        "generation": False,
        "retry": False,
        "hidden_reference_access": False,
        "numeric_regeneration": False,
        "p19_result_rescued": False,
        "p19_opened_tasks_model_score_reuse": False,
        "p19_batch_order_development_observation": "8/8 EXACT THREE_MODE SCORE EQUALITY",
        "future_actual_requires_new_registered_tasks": True,
        "actual_gemma_run": "NOT_RUN",
        "development_registration": "NOT_REGISTERED",
        "fresh_validation_registered": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "global_questions_closed": [],
    }


def _validate_source_bundle(view, parsed, bundle):
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("exact semantic view required")
    instruction = view.get("instruction")
    public = view.get("public")
    if type(instruction) is not str or not instruction:
        raise ValueError("nonempty public semantic instruction required")
    if type(public) is not dict or set(public) != {"query"}:
        raise ValueError("exact query-only public payload required")
    query = public.get("query")
    if type(query) is not str or not query:
        raise ValueError("nonempty public query required")
    expected = {"instruction": "Return a complete assignment.", "public": {"query": query}}
    if parsed != expected:
        raise ValueError("registered instruction-normalized parser view required")
    if bundle != p17_build_candidates(parsed):
        raise ValueError("source/candidate bundle drift")
    return query


def minimal_semantic_contrast(view, parsed, bundle, eligible):
    query = _validate_source_bundle(view, parsed, bundle)
    if (
        type(eligible) is not list
        or not 2 <= len(eligible) <= 4
        or eligible != sorted(set(eligible))
        or any(type(i) is not int or not 0 <= i < len(bundle["candidates"]) for i in eligible)
    ):
        raise ValueError("2..4 distinct eligible candidate indexes required")

    mentions = list(re.finditer(r"\bIt\b", query))
    if len(mentions) != 1:
        raise ValueError("exactly one source ambiguous mention required")

    candidates = [bundle["candidates"][i] for i in eligible]
    if any(c.get("route") != "CSP" for c in candidates):
        raise ValueError("P1.10 P0 requires CSP binding candidates")
    shapes = [[len(atom) for atom in c["atoms"]] for c in candidates]
    if any(shape != shapes[0] for shape in shapes[1:]):
        raise ValueError("candidate atom shape drift")

    varying = []
    for atom_index, width in enumerate(shapes[0]):
        for arg_index in range(1, width):
            values = [c["atoms"][atom_index][arg_index] for c in candidates]
            if len(set(values)) > 1:
                varying.append((atom_index, arg_index, values))
    if len(varying) != 1:
        raise ValueError("exactly one semantic binding coordinate required")

    atom_index, arg_index, refs = varying[0]
    if arg_index != 1 or candidates[0]["atoms"][atom_index][0] != "EQ":
        raise ValueError("pronoun binding must vary only in EQ left entity")
    for c in candidates[1:]:
        if c["atoms"][atom_index][0] != "EQ":
            raise ValueError("binding relation drift")

    evidence = {t["id"]: t for t in bundle["evidence"]["tokens"]}
    if len(set(refs)) != len(refs):
        raise ValueError("eligible bindings must be distinct")

    bindings = []
    for candidate_index, ref in zip(eligible, refs):
        token = evidence.get(ref)
        if not isinstance(token, dict) or token.get("kind") != "entity":
            raise ValueError("binding must be a source entity occurrence")
        bindings.append({
            "candidate_index": candidate_index,
            "entity": {
                "surface": token["surface"],
                "span": snapshot(token["span"]),
            },
        })

    mention = mentions[0]
    return {
        "instruction": view["instruction"],
        "ambiguous_mention": {
            "surface": mention.group(),
            "span": [mention.start(), mention.end()],
        },
        "bindings": bindings,
    }


def _binding_by_candidate(contrast):
    rows = contrast.get("bindings")
    if type(rows) is not list or not 2 <= len(rows) <= 4:
        raise ValueError("minimal binding list required")
    result = {}
    for row in rows:
        idx = row.get("candidate_index")
        entity = row.get("entity")
        if type(idx) is not int or idx in result or type(entity) is not dict:
            raise ValueError("unique candidate binding required")
        if set(entity) != {"surface", "span"}:
            raise ValueError("source-bound entity surface/span required")
        result[idx] = snapshot(entity)
    return result


def pair_prompt(contrast, left, right):
    bindings = _binding_by_candidate(contrast)
    if type(left) is not int or type(right) is not int or left == right or left not in bindings or right not in bindings:
        raise ValueError("distinct registered pair required")
    payload = {
        "instruction": contrast["instruction"],
        "ambiguous_mention": contrast["ambiguous_mention"],
        "left_binding": bindings[left],
        "right_binding": bindings[right],
    }
    return (
        "Choose which source-bound binding better follows the public semantic instruction. "
        "Return one code only: A means LEFT; B means RIGHT. C and D are invalid.\n"
        + canonical(payload)
    )


def oriented_pairs(eligible):
    if (
        type(eligible) is not list
        or not 2 <= len(eligible) <= 4
        or eligible != sorted(set(eligible))
    ):
        raise ValueError("2..4 sorted distinct candidates required")
    rows = []
    for left, right in combinations(eligible, 2):
        rows.append((left, right))
        rows.append((right, left))
    return tuple(rows)


def planned_cost(prefixes):
    if type(prefixes) is not tuple or not 2 <= len(prefixes) <= 12:
        raise ValueError("2..12 pairwise prefixes required")
    total = dict.fromkeys(LEDGER_KEYS, 0)
    for order in (list(range(len(prefixes))), list(reversed(range(len(prefixes))))):
        plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
        cost = plan_cost(plan, len(prefixes))
        for key, value in cost.items():
            total[key] += value
    return total


class FrozenMinimalPairwiseSelector:
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
        contrast = minimal_semantic_contrast(view, parsed, bundle, eligible)
        pairs = oriented_pairs(eligible)
        prompts = [pair_prompt(contrast, *pair) for pair in pairs]
        prefixes = tuple(tuple(self.encoder(prompt)) for prompt in prompts)

        receipt = {
            "schema": SCHEMA,
            "status": "FAILED",
            "bundle_sha256": bundle["bundle_sha256"],
            "original_view_sha256": digest(view),
            "parser_view_sha256": digest(parsed),
            "contrast_sha256": digest(contrast),
            "eligible_indexes": snapshot(eligible),
            "oriented_pairs": snapshot(pairs),
            "prompt_sha256": [digest(p) for p in prompts],
            "passes": [],
            "ledger": dict.fromkeys(LEDGER_KEYS, 0),
        }
        try:
            for mode, order in (
                ("batch_all", list(range(len(prefixes)))),
                ("reverse_batch_all", list(reversed(range(len(prefixes))))),
            ):
                plan = CodePlan(tuple(prefixes[i] for i in order), CODE_TOKEN_IDS)
                cost = plan_cost(plan, len(prefixes))
                if any(receipt["ledger"][key] + value > getattr(ScoreBudget(), key) for key, value in cost.items()):
                    raise ValueError("P1.10 scorer pre-forward cost cap")
                row = {
                    "mode": mode,
                    "batch_size": len(prefixes),
                    "order": order,
                    "prefixes": snapshot(plan.prefixes),
                    "code_ids": list(CODE_TOKEN_IDS),
                    "planned": cost,
                    "status": "STARTED",
                }
                receipt["passes"].append(row)
                left = finite(remaining_ms, True) - elapsed()
                if left <= 0:
                    raise TimeoutError("P1.10 scoring deadline")
                try:
                    output = self.backend.evaluate(plan, len(prefixes), left)
                except CodedFailure as exc:
                    row["known_partial_cost"] = snapshot(exc.known_cost)
                    for key, value in exc.known_cost.items():
                        receipt["ledger"][key] += value
                    raise
                for key, value in output["cost"].items():
                    receipt["ledger"][key] += value
                matrix = [None] * len(prefixes)
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
    contrast = minimal_semantic_contrast(view, parsed, bundle, eligible)
    pairs = oriented_pairs(eligible)
    prompts = [pair_prompt(contrast, *pair) for pair in pairs]

    if receipt.get("status") != "COMPLETE":
        raise ValueError("complete P1.10 selector receipt required")
    if receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("P1.10 bundle identity drift")
    if receipt.get("original_view_sha256") != digest(view) or receipt.get("parser_view_sha256") != digest(parsed):
        raise ValueError("P1.10 view identity drift")
    if receipt.get("contrast_sha256") != digest(contrast):
        raise ValueError("P1.10 contrast identity drift")
    if receipt.get("eligible_indexes") != eligible or receipt.get("oriented_pairs") != snapshot(pairs):
        raise ValueError("P1.10 candidate/pair coverage drift")
    if receipt.get("prompt_sha256") != [digest(p) for p in prompts]:
        raise ValueError("P1.10 prompt identity drift")
    if any(receipt.get("identity", {}).get(k) != v for k, v in MODEL.items()) or receipt.get("unchanged") is not True:
        raise ValueError("frozen core identity required")
    validate_identity(receipt["identity"])
    if receipt.get("generated_calls") != 0:
        raise ValueError("control generation forbidden")

    passes = receipt.get("passes", [])
    n = len(pairs)
    expected_modes = (
        ("batch_all", list(range(n))),
        ("reverse_batch_all", list(reversed(range(n)))),
    )
    if len(passes) != 2:
        raise ValueError("two P1.10 batch-order passes required")

    totals = dict.fromkeys(LEDGER_KEYS, 0)
    odds_by_mode = []
    base_prefixes = None
    for row, (mode, order) in zip(passes, expected_modes):
        if (
            row.get("mode") != mode
            or row.get("batch_size") != n
            or row.get("order") != order
            or row.get("status") != "COMPLETE"
            or row.get("code_ids") != list(CODE_TOKEN_IDS)
        ):
            raise ValueError("exact P1.10 execution mode required")
        plan = CodePlan(tuple(tuple(p) for p in row["prefixes"]), CODE_TOKEN_IDS)
        cost = plan_cost(plan, n)
        if row.get("planned") != cost or row.get("actual") != cost:
            raise ValueError("P1.10 exact cost coverage required")
        if type(row.get("peak_accelerator_memory_bytes")) is not int or row["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("P1.10 accelerator memory receipt required")
        for key, value in cost.items():
            totals[key] += value
        matrix = row.get("matrix")
        if type(matrix) is not list or len(matrix) != n:
            raise ValueError("P1.10 pair matrix coverage required")
        odds_by_mode.append([_log_odds(scores) for scores in matrix])

        if mode == "batch_all":
            base_prefixes = row["prefixes"]
        elif row["prefixes"] != list(reversed(base_prefixes)):
            raise ValueError("P1.10 reverse prefix identity drift")

    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(), key) for key, v in totals.items()):
        raise ValueError("P1.10 scoring ledger mismatch or cap")

    max_delta = max(abs(odds_by_mode[0][i] - odds_by_mode[1][i]) for i in range(n))
    if max_delta > criteria.max_mode_log_odds_delta_nats:
        raise ValueError("P1.10 batch/order numerical drift")

    odds = [(odds_by_mode[0][i] + odds_by_mode[1][i]) / 2.0 for i in range(n)]
    lookup = {pair: odds[i] for i, pair in enumerate(pairs)}

    preferences = {}
    for a, b in combinations(eligible, 2):
        d = (lookup[(a, b)] - lookup[(b, a)]) / 2.0
        preferences[(a, b)] = d
        preferences[(b, a)] = -d

    winners = []
    for candidate in eligible:
        margins = [preferences[(candidate, other)] for other in eligible if other != candidate]
        if all(margin > criteria.minimum_pairwise_preference_nats for margin in margins):
            winners.append((candidate, min(margins)))
    if len(winners) != 1:
        raise ValueError("P1.10 no unique confident Condorcet winner")

    selected, minimum_margin = winners[0]
    return {
        "selected_candidate": selected,
        "minimum_pairwise_preference_nats": minimum_margin,
        "pairwise_preference_nats": {
            f"{a}>{b}": preferences[(a, b)]
            for a, b in combinations(eligible, 2)
        },
        "max_mode_log_odds_delta_nats": max_delta,
        "forward_calls": totals["forward_calls"],
        "evaluated_tokens": totals["evaluated_tokens"],
    }
