import copy

import pytest

from neumann1.control_plane_p11 import CodePlan, CODES, plan_cost
from neumann1.control_plane_p12 import CODE_TOKEN_IDS
from neumann1.control_plane_p19_balanced import (
    contract, planned_cost, polarity_prompt, prompt_rows, validate_selection,
)
from neumann1.control_plane_p18_semantic import build_semantic_bundle
from experiments.control_plane_p18_registration import registration


def _b_row():
    _, rows, _ = registration()
    return rows[4]


def _code_scores(log_odds):
    if log_odds >= 0:
        return [-0.1, -0.1-log_odds, -5.0, -5.0]
    return [-0.1+log_odds, -0.1, -5.0, -5.0]


def _receipt(row, preferred=1, strength=2.0, label_bias=0.0):
    parsed, bundle = build_semantic_bundle(row["view"])
    eligible = [0, 1]
    rows = prompt_rows(row["view"], parsed, bundle, eligible)
    prefixes = [tuple(range(1, 4+i)) for i in range(len(rows))]

    matrix = []
    for entry in rows:
        is_preferred = entry["candidate_index"] == preferred
        if entry["claim"] == "FAITHFUL":
            semantic = strength if is_preferred else -strength
        else:
            semantic = -strength if is_preferred else strength
        matrix.append(_code_scores(label_bias + semantic))

    passes = []
    n = len(rows)
    for mode, size, order in (
        ("batch4", 4, list(range(n))),
        ("unbatched1", 1, list(range(n))),
        ("reverse_batch4", 4, list(reversed(range(n)))),
    ):
        ordered_prefixes = [prefixes[i] for i in order]
        ordered_matrix = [matrix[i] for i in order]
        canonical_matrix = [None] * n
        for i, scores in zip(order, ordered_matrix):
            canonical_matrix[i] = list(scores)
        plan = CodePlan(tuple(ordered_prefixes), CODE_TOKEN_IDS)
        cost = plan_cost(plan, size)
        passes.append({
            "mode": mode,
            "batch_size": size,
            "order": order,
            "prefixes": ordered_prefixes,
            "code_ids": list(CODE_TOKEN_IDS),
            "planned": cost,
            "actual": cost,
            "status": "COMPLETE",
            "matrix": canonical_matrix,
            "peak_accelerator_memory_bytes": 1,
        })

    ledger = {k: 0 for k in passes[0]["actual"]}
    for p in passes:
        for k, v in p["actual"].items():
            ledger[k] += v

    from neumann1.control_plane_v1 import digest
    from neumann1.control_plane_p1_contract import MODEL
    receipt = {
        "status": "COMPLETE",
        "bundle_sha256": bundle["bundle_sha256"],
        "original_view_sha256": digest(row["view"]),
        "parser_view_sha256": digest(parsed),
        "eligible_indexes": eligible,
        "row_keys": [[entry["candidate_index"], entry["claim"]] for entry in rows],
        "prompt_sha256": [digest(entry["prompt"]) for entry in rows],
        "identity": {
            **MODEL,
            "device_type": "cuda",
            "device_name": "Tesla T4",
            "evidence_kind": "actual_frozen_model",
            "framework": "torch-2.11.0+cu128/transformers-5.16.1",
            "torchvision": "0.26.0+cu128",
        },
        "unchanged": True,
        "generated_calls": 0,
        "passes": passes,
        "ledger": ledger,
    }
    return parsed, bundle, eligible, receipt


def test_contract_balances_fixed_yes_no_prior():
    c = contract()
    assert c["response_semantics"][CODES[0]] == "YES"
    assert c["response_semantics"][CODES[1]] == "NO"
    assert c["fixed_additive_ab_prior_cancels"] is True
    assert c["candidate_code_permutations"] == 0
    assert c["p18_shape_planned_forward_calls"] == 38
    assert c["actual_gemma_run"] == "NOT_RUN"


def test_prompts_have_complementary_claims_and_fixed_response_semantics():
    row = _b_row()
    parsed, bundle = build_semantic_bundle(row["view"])
    positive = polarity_prompt(row["view"], parsed, bundle, 0, "FAITHFUL")
    negative = polarity_prompt(row["view"], parsed, bundle, 0, "NOT_FAITHFUL")
    assert "A means YES; B means NO" in positive
    assert "A means YES; B means NO" in negative
    assert "is faithful" in positive
    assert "is not faithful" in negative
    assert positive != negative
    assert "expected_candidate" not in positive
    assert "semantic_grounding" not in positive


def test_planned_forward_counts_match_balanced_formula():
    expected = {2: 6, 3: 10, 4: 12}
    for k, forwards in expected.items():
        prefixes = tuple((1, 2, 3+i) for i in range(2*k))
        assert planned_cost(prefixes)["forward_calls"] == forwards
    assert sum(expected[k] for k in (2, 3, 4, 3)) == 38


def test_balanced_selection_picks_preferred_candidate():
    row = _b_row()
    parsed, bundle, eligible, receipt = _receipt(row, preferred=1)
    got = validate_selection(row["view"], parsed, bundle, eligible, receipt)
    assert got["selected_candidate"] == 1
    assert got["forward_calls"] == 6
    assert got["margin_nats"] > 0.5
    assert got["candidate_balanced_score_nats"]["1"] > 0


def test_fixed_additive_label_bias_cancels_from_balanced_score():
    row = _b_row()
    parsed, bundle, eligible, base = _receipt(row, preferred=1, label_bias=0.0)
    got0 = validate_selection(row["view"], parsed, bundle, eligible, base)

    parsed, bundle, eligible, biased = _receipt(row, preferred=1, label_bias=0.7)
    got1 = validate_selection(row["view"], parsed, bundle, eligible, biased)

    assert got0["selected_candidate"] == got1["selected_candidate"] == 1
    assert got0["candidate_balanced_score_nats"] == pytest.approx(
        got1["candidate_balanced_score_nats"]
    )
    assert got0["margin_nats"] == pytest.approx(got1["margin_nats"])


def test_low_balanced_margin_abstains():
    row = _b_row()
    parsed, bundle, eligible, receipt = _receipt(row, preferred=1, strength=0.2)
    with pytest.raises(ValueError, match="candidate margin failure"):
        validate_selection(row["view"], parsed, bundle, eligible, receipt)


def test_balanced_batch_order_drift_abstains():
    row = _b_row()
    parsed, bundle, eligible, receipt = _receipt(row, preferred=1)
    receipt = copy.deepcopy(receipt)
    # Candidate 1 FAITHFUL row is canonical row 2. Alter B while preserving
    # nonpositive log probabilities; balanced score shifts by 0.1 nat.
    receipt["passes"][2]["matrix"][2][1] += 0.2
    with pytest.raises(ValueError, match="numerical drift"):
        validate_selection(row["view"], parsed, bundle, eligible, receipt)
