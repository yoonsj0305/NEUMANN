import copy

import pytest

from neumann1.control_plane_p11 import CODES
from neumann1.control_plane_p12 import CODE_TOKEN_IDS
from neumann1.control_plane_p19 import (
    Criteria, contract, planned_cost, proposition_prompt, validate_selection,
)
from neumann1.control_plane_p18_semantic import build_semantic_bundle
from experiments.control_plane_p18_registration import registration


def _b_row():
    _, rows, _ = registration()
    return rows[4]


def _receipt(row, preferred=1, strength=2.0, other=-2.0):
    parsed, bundle = build_semantic_bundle(row["view"])
    eligible = [0, 1]
    prompts = [proposition_prompt(row["view"], parsed, bundle, i) for i in eligible]
    prefixes = [tuple(range(1, 4 + i)) for i in range(len(eligible))]

    # A-B log odds: preferred positive, other negative.
    matrix = []
    for i in range(len(eligible)):
        if i == preferred:
            matrix.append([-0.1, -0.1-strength, -5.0, -5.0])
        else:
            matrix.append([-0.1-strength, -0.1, -5.0, -5.0])

    passes = []
    for mode, size, order in (
        ("batch_all", 2, [0, 1]),
        ("unbatched1", 1, [0, 1]),
        ("reverse_batch_all", 2, [1, 0]),
    ):
        ordered_prefixes = [prefixes[i] for i in order]
        ordered_matrix = [matrix[i] for i in order]
        # Receipt matrices are canonical candidate order after backend reorder.
        canonical_matrix = [None] * 2
        for i, scores in zip(order, ordered_matrix):
            canonical_matrix[i] = scores
        from neumann1.control_plane_p11 import CodePlan, plan_cost
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
        "prompt_sha256": [digest(p) for p in prompts],
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


def test_contract_removes_candidate_code_permutations():
    c = contract()
    assert c["response_semantics"][CODES[0]] == "FAITHFUL"
    assert c["response_semantics"][CODES[1]] == "NOT_FAITHFUL"
    assert c["candidate_identity_in_output_code"] is False
    assert c["candidate_code_permutations"] == 0
    assert c["actual_gemma_run"] == "NOT_RUN"


def test_prompt_has_fixed_semantics_and_candidate_local_identity():
    row = _b_row()
    parsed, bundle = build_semantic_bundle(row["view"])
    p0 = proposition_prompt(row["view"], parsed, bundle, 0)
    p1 = proposition_prompt(row["view"], parsed, bundle, 1)
    assert "A means FAITHFUL; B means NOT_FAITHFUL" in p0
    assert "A means FAITHFUL; B means NOT_FAITHFUL" in p1
    assert p0 != p1
    assert "expected_candidate" not in p0
    assert "semantic_grounding" not in p0


def test_planned_forward_calls_are_k_plus_two():
    for k in (2, 3, 4):
        prefixes = tuple((1, 2, 3 + i) for i in range(k))
        assert planned_cost(prefixes)["forward_calls"] == k + 2


def test_selection_uses_fixed_candidate_log_odds():
    row = _b_row()
    parsed, bundle, eligible, receipt = _receipt(row, preferred=1)
    got = validate_selection(row["view"], parsed, bundle, eligible, receipt)
    assert got["selected_candidate"] == 1
    assert got["forward_calls"] == 4
    assert got["margin_nats"] > 0.5


def test_low_candidate_margin_abstains():
    row = _b_row()
    parsed, bundle, eligible, receipt = _receipt(row, preferred=1, strength=0.2)
    with pytest.raises(ValueError, match="candidate margin failure"):
        validate_selection(row["view"], parsed, bundle, eligible, receipt)


def test_batch_order_drift_abstains():
    row = _b_row()
    parsed, bundle, eligible, receipt = _receipt(row, preferred=1)
    receipt = copy.deepcopy(receipt)
    # Change candidate 1 B score only in the reverse mode while keeping
    # every log probability nonpositive.
    receipt["passes"][2]["matrix"][1][1] += 0.2
    with pytest.raises(ValueError, match="numerical drift"):
        validate_selection(row["view"], parsed, bundle, eligible, receipt)
