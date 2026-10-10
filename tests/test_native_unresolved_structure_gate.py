"""Missing/mutated evidence must never manufacture a structure-discovery PASS."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.native_unresolved_structure_gate import (
    CONDITIONS, OBLIGATIONS, gate, stored_original_certificate,
)
from neumann1.recursive_summary import identity


@pytest.mark.parametrize("missing", CONDITIONS)
def test_one_missing_condition_blocks_pass(missing):
    conditions = dict.fromkeys(CONDITIONS, True)
    conditions[missing] = None
    assert gate(conditions, True) == "UNKNOWN"


@pytest.mark.parametrize("rights", [None, False])
def test_restricted_native_failure_does_not_prove_classical_gap(rights):
    assert gate(dict.fromkeys(CONDITIONS, True), rights) == "UNKNOWN"


def test_prior_hold_is_not_overridden_by_posthoc_claims():
    assert gate(dict.fromkeys(CONDITIONS, True), True, "existing user HOLD") == "HOLD"


def test_all_four_established_conditions_only_admit_headroom_not_learning():
    assert gate(dict.fromkeys(CONDITIONS, True), True) == "PASS"


def test_truthy_numeric_or_status_fields_are_not_boolean_evidence():
    with pytest.raises(ValueError):
        gate(dict.fromkeys(CONDITIONS, 1), True)
    with pytest.raises(ValueError):
        gate(dict.fromkeys(CONDITIONS, True), "UPSTREAM_REPORTED_REALIZABLE")


def certificate_fixture():
    public, proposal = {"original_goal": "test-only"}, {"state": "test-only"}
    case = {"source": {"sha256": "source"}, "public_AST_sha256": identity(public),
            "original_hole_skeleton_implementable": False}
    cert = {"accepted": True, "status": "SOURCE_BOUND_MATHEMATICAL_GOAL_CERTIFIED",
        "proposal_sha256": identity(proposal),
        "binding": {"source_sha256": "source", "scope": "test-only",
            "assertion": {"reference": "goal"},
            "projection": {"public": public, "goal_types": ["int"], "reference_function": "goal"},
            "flatten_proof": {"accepted": True,
                "proof_records": [{"word_actual": ["left", "right"], "word_expected": ["left", "right"], "termination_status": "unsat"}],
                "clause_records": []}},
        "certificate": {"accepted": True, "status": "CERTIFIED", "problem_sha256": identity(public),
            "proposal_sha256": identity(proposal),
            "obligations": [{"obligation": name, "status": "unsat"} for name in sorted(OBLIGATIONS)]}}
    native = {"accepted": True, "Oracle_used": False, "learning_performed": False, "proposal": proposal, "mechanism": "test-only"}
    return case, cert, native


@pytest.mark.parametrize("mutation", ["source", "goal", "proposal", "unknown", "duplicate", "order", "termination", "accepted_only", "oracle"])
def test_stored_certificate_integrity_and_scope_cannot_be_replaced_by_label(mutation):
    case, cert, native = deepcopy(certificate_fixture())
    if mutation == "source":
        case["source"]["sha256"] = "changed"
    elif mutation == "goal":
        cert["binding"]["projection"]["public"]["original_goal"] = "different"
    elif mutation == "proposal":
        native["proposal"]["state"] = "changed"
    elif mutation == "unknown":
        cert["certificate"]["obligations"][0]["status"] = "unknown"
    elif mutation == "duplicate":
        cert["certificate"]["obligations"][0] = cert["certificate"]["obligations"][1]
    elif mutation == "order":
        cert["binding"]["flatten_proof"]["proof_records"][0]["word_actual"].reverse()
    elif mutation == "termination":
        cert["binding"]["flatten_proof"]["proof_records"][0]["termination_status"] = "unknown"
    elif mutation == "accepted_only":
        cert["certificate"]["obligations"] = []
    else:
        native["Oracle_used"] = True
    with pytest.raises(ValueError):
        stored_original_certificate(case, cert, native)


def test_portfolio_receipt_never_turns_saved_observations_into_fresh_tasks():
    root = Path(__file__).resolve().parents[1]
    receipt = json.loads((root / "research/development/native-unresolved-structure-gate-2026-10-10/gate_result.json").read_text(encoding="utf-8"))
    assert len(receipt["source_gates"]) == 29
    assert receipt["population"]["saved_native_observations"] == 174
    assert receipt["population"]["fresh_problems"] == 0
    assert receipt["population"]["independent_motif_count"] is None
    assert receipt["counts"] == {"HOLD": 8, "UNKNOWN": 21, "PASS": 0}
    by_path = {r["original_path"]: r for r in receipt["source_gates"]}
    restricted = by_path["benchmarks/unrealizable/po_sorted.ml"]
    assert restricted["restricted_no_lifting"] and restricted["gate_verdict"] == "UNKNOWN"
    assert restricted["equal_rights_evidence"] is False
    assert by_path["benchmarks/list/poly_no_fac.ml"]["matched_adapted_cost"] is None
    assert by_path["benchmarks/list/mps_no_sum.ml"]["conditions"]["representation_obstruction_confirmed"] is True
    assert receipt["new_synthesis_runs"] == receipt["new_proof_calls"] == receipt["new_model_calls"] == receipt["new_gpu_calls"] == receipt["paid_calls"] == 0
    assert not receipt["frontier_gap_measured"]
