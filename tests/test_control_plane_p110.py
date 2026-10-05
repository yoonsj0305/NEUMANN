import copy

import pytest

from neumann1.control_plane_p1_contract import MODEL
from neumann1.control_plane_p11 import CodePlan, CODES, plan_cost
from neumann1.control_plane_p12 import CODE_TOKEN_IDS
from neumann1.control_plane_p19_semantic import build_bundle
from neumann1.control_plane_p110 import (
    contract, minimal_semantic_contrast, oriented_pairs, pair_prompt,
    planned_cost, validate_selection,
)
from experiments.control_plane_p19_registration import registration
from neumann1.control_plane_v1 import digest


def _row(index=0):
    _, rows, _ = registration()
    return rows[index]


def _identity():
    return {
        **MODEL,
        "device_type": "cuda",
        "device_name": "Tesla T4",
        "evidence_kind": "actual_frozen_model",
        "framework": "torch-2.11.0+cu128/transformers-5.16.1",
        "torchvision": "0.26.0+cu128",
    }


def _scores(log_odds):
    if log_odds >= 0:
        return [-0.1, -0.1-log_odds, -8.0, -8.0]
    return [-0.1+log_odds, -0.1, -8.0, -8.0]


def _receipt(row, utilities, global_a_bias=5.0):
    parsed, bundle = build_bundle(row["view"])
    eligible = list(range(len(bundle["candidates"])))
    contrast = minimal_semantic_contrast(row["view"], parsed, bundle, eligible)
    pairs = oriented_pairs(eligible)
    prompts = [pair_prompt(contrast, *pair) for pair in pairs]
    prefixes = [tuple(range(1, 6+i)) for i in range(len(pairs))]

    matrix = []
    for left, right in pairs:
        # Shared A-token bias is deliberately present in both orientations.
        # Symmetrization must cancel it and recover utility(left)-utility(right).
        matrix.append(_scores(global_a_bias + utilities[left] - utilities[right]))

    passes = []
    for mode, order in (
        ("batch_all", list(range(len(pairs)))),
        ("reverse_batch_all", list(reversed(range(len(pairs))))),
    ):
        ordered_prefixes = [prefixes[i] for i in order]
        plan = CodePlan(tuple(ordered_prefixes), CODE_TOKEN_IDS)
        cost = plan_cost(plan, len(prefixes))
        passes.append({
            "mode": mode,
            "batch_size": len(prefixes),
            "order": order,
            "prefixes": ordered_prefixes,
            "code_ids": list(CODE_TOKEN_IDS),
            "planned": cost,
            "actual": cost,
            "status": "COMPLETE",
            "matrix": [list(scores) for scores in matrix],
            "peak_accelerator_memory_bytes": 1,
        })

    ledger = {k: 0 for k in passes[0]["actual"]}
    for p in passes:
        for k, v in p["actual"].items():
            ledger[k] += v

    return parsed, bundle, eligible, {
        "status": "COMPLETE",
        "bundle_sha256": bundle["bundle_sha256"],
        "original_view_sha256": digest(row["view"]),
        "parser_view_sha256": digest(parsed),
        "contrast_sha256": digest(contrast),
        "eligible_indexes": eligible,
        "oriented_pairs": [list(p) for p in pairs],
        "prompt_sha256": [digest(p) for p in prompts],
        "identity": _identity(),
        "unchanged": True,
        "generated_calls": 0,
        "passes": passes,
        "ledger": ledger,
    }


def test_contract_is_minimal_pairwise_and_never_reuses_p19_scores():
    c = contract()
    assert c["semantic_ir"] == "SOURCE_BOUND_MINIMAL_PRONOUN_BINDING_CONTRAST"
    assert c["response_semantics"][CODES[0]] == "LEFT_BINDING_MORE_FAITHFUL"
    assert c["response_semantics"][CODES[1]] == "RIGHT_BINDING_MORE_FAITHFUL"
    assert c["candidate_code_permutations"] == 0
    assert c["forward_calls_per_item"] == 2
    assert c["p19_opened_tasks_model_score_reuse"] is False
    assert c["actual_gemma_run"] == "NOT_RUN"


def test_minimal_contrast_deletes_resolved_csp_structure():
    row = _row(0)
    parsed, bundle = build_bundle(row["view"])
    contrast = minimal_semantic_contrast(row["view"], parsed, bundle, [0, 1])
    assert set(contrast) == {"instruction", "ambiguous_mention", "bindings"}
    assert contrast["ambiguous_mention"]["surface"] == "It"
    assert [b["entity"]["surface"] for b in contrast["bindings"]] == ["X", "Y"]
    raw = str(contrast)
    assert "DOMAIN" not in raw
    assert "NE" not in raw
    assert set(contrast["bindings"][0]["entity"]) == {"surface", "span"}
    assert "value" not in contrast["bindings"][0]["entity"]


def test_pair_prompt_uses_fixed_left_right_semantics_only():
    row = _row(0)
    parsed, bundle = build_bundle(row["view"])
    contrast = minimal_semantic_contrast(row["view"], parsed, bundle, [0, 1])
    p01 = pair_prompt(contrast, 0, 1)
    p10 = pair_prompt(contrast, 1, 0)
    assert "A means LEFT; B means RIGHT" in p01
    assert p01 != p10
    assert "differs from" not in p01
    assert "{7,9}" not in p01


def test_planned_cost_is_two_forwards_for_two_to_four_candidates():
    for k in (2, 3, 4):
        n = k * (k - 1)
        prefixes = tuple((1, 2, 3+i) for i in range(n))
        cost = planned_cost(prefixes)
        assert cost["forward_calls"] == 2
        assert cost["input_rows"] == 2*n


def test_symmetric_pairwise_cancels_large_global_a_token_bias():
    row = _row(1)  # three candidates
    parsed, bundle, eligible, receipt = _receipt(
        row,
        utilities={0: 0.0, 1: 2.0, 2: -1.0},
        global_a_bias=5.0,
    )
    got = validate_selection(row["view"], parsed, bundle, eligible, receipt)
    assert got["selected_candidate"] == 1
    assert got["minimum_pairwise_preference_nats"] > 0.5
    assert got["forward_calls"] == 2


def test_no_confident_condorcet_winner_abstains():
    row = _row(1)
    parsed, bundle, eligible, receipt = _receipt(
        row,
        utilities={0: 0.0, 1: 0.2, 2: 0.1},
        global_a_bias=5.0,
    )
    with pytest.raises(ValueError, match="no unique confident Condorcet winner"):
        validate_selection(row["view"], parsed, bundle, eligible, receipt)


def test_reverse_batch_numerical_drift_abstains():
    row = _row(0)
    parsed, bundle, eligible, receipt = _receipt(
        row,
        utilities={0: 1.0, 1: 0.0},
        global_a_bias=5.0,
    )
    receipt = copy.deepcopy(receipt)
    receipt["passes"][1]["matrix"][0][1] -= 0.2
    with pytest.raises(ValueError, match="numerical drift"):
        validate_selection(row["view"], parsed, bundle, eligible, receipt)
