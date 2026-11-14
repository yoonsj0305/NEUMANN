"""Fail-closed source rights regression tests for external-original G1."""
from research.q3.discovery_policy.original_source_information_rights_gate_20261028 import (
    EvidenceKind,audited_rights,request_arbitrary_target_label,
    choose_feedback_channel,counterexample_is_not_gold_label)
SHA="0"*64

def test_bv_pbe_1000_examples_are_not_arbitrary_target_oracle():
    r=audited_rights(EvidenceKind.FINITE_LABELED_EXAMPLES,1000,SHA)
    assert r.supplied_example_count==1000
    assert not r.can_request_arbitrary_intended_target_label
    assert not request_arbitrary_target_label(r,8888)["has_gold_label"]
    assert choose_feedback_channel(r)=="CHECK_PUBLISHED_EXAMPLES_ONLY"

def test_string_pbe_two_consistent_programs_cannot_produce_gold_target():
    r=audited_rights(EvidenceKind.FINITE_LABELED_EXAMPLES,3,SHA)
    result=request_arbitrary_target_label(r,"hello ")
    assert result["status"]=="HOLD_MISSING_INTENDED_TARGET_ORACLE"
    assert "target_output" not in result

def test_universal_formula_cex_is_not_hidden_intended_target():
    r=audited_rights(EvidenceKind.UNIVERSAL_FORMULA,0,SHA)
    x=counterexample_is_not_gold_label(r,{"x":5})
    assert x["status"]=="FORMULA_VIOLATION_ASSIGNMENT_ONLY"
    assert x["intended_target_output_known"] is False

def test_inductive_vcs_do_not_imply_target_invariant_values():
    r=audited_rights(EvidenceKind.INDUCTIVE_TRANSITION_SYSTEM,0,SHA)
    assert choose_feedback_channel(r)=="CHECK_THREE_INDUCTIVE_VCS_OR_REACHABLE_UNSAFETY"
    assert not request_arbitrary_target_label(r,{"s":0})["has_gold_label"]

def test_cannot_pass_unverifiable_original_fingerprint():
    try:
        audited_rights(EvidenceKind.FINITE_LABELED_EXAMPLES,3,"fake_sha")
    except ValueError:
        pass
    else:raise AssertionError("accepted fake provenance")

def test_oracle_requires_explicit_actual_callable():
    r=audited_rights(EvidenceKind.FINITE_LABELED_EXAMPLES,3,SHA)
    try:
        request_arbitrary_target_label(r,"hello ","not_callable")
    except TypeError:
        pass
    else:raise AssertionError("accepted fake oracle")

def test_explicit_external_oracle_is_distinct_from_source():
    r=audited_rights(EvidenceKind.FINITE_LABELED_EXAMPLES,3,SHA)
    oracle=lambda x: x.upper()
    x=request_arbitrary_target_label(r,"hello ",oracle)
    assert x["status"]=="AUTHORIZED_GOLD_LABEL_RETURNED"
    assert x["target_output"]=="HELLO "
    assert not r.can_request_arbitrary_intended_target_label

def test_unknown_source_rights_stay_hold():
    r=audited_rights(EvidenceKind.UNKNOWN,0,SHA)
    assert choose_feedback_channel(r)=="HOLD_UNKNOWN_INFORMATION_RIGHTS"
    assert not r.has_candidate_verifier
