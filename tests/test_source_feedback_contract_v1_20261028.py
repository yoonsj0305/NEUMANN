"""No user-supplied target oracle can be invented from formal specs."""
import pytest
from research.q3.discovery_policy.source_feedback_contract_v1_20261028 import (
    FeedbackKind,SourceKind,MissingSourceRight,audit_form_counts,
    oracle_counterexample_is_a_true_label)

def make_pairs(kind="PBE"):
    if kind=="PBE":
        return [("synth-fun","(synth-fun f ((s String)) String)"),
                ("constraint",'(constraint (= (f "fox") ""))'),
                ("constraint",'(constraint (= (f "The quick fox") "The"))')]
    if kind=="INV":
        return [("synth-inv","(synth-inv inv ((x Int)))"),
                ("inv-constraint","(inv-constraint inv pre trans post)")]
    if kind=="LIA":
        return [("synth-fun","(synth-fun f ((x Int)) Int)"),
                ("declare-var","(declare-var x Int)"),
                ("constraint","(constraint (>= (f x) x))")]
    if kind=="BV":
        return [("synth-fun","(synth-fun f ((x (_ BitVec 64))) (_ BitVec 64))"),
                ("constraint","(constraint (= (f #x0000000000000001) #x0000000000000002))")]
    raise ValueError(kind)

def test_source_string_examples_not_target_oracle():
    x=audit_form_counts(make_pairs())
    assert x.source_kind==SourceKind.PBE_GROUND_EXAMPLES
    assert x.original_ground_example_count==2
    assert x.authorize(FeedbackKind.SOURCE_EXAMPLE)
    with pytest.raises(MissingSourceRight):
        x.authorize(FeedbackKind.TRUE_TARGET_OUTPUT)

def test_source_examples_do_not_grant_general_formal_counterexample():
    x=audit_form_counts(make_pairs("PBE"))
    with pytest.raises(MissingSourceRight):
        x.authorize(FeedbackKind.CANDIDATE_COUNTEREXAMPLE)

def test_inductive_original_has_vc_not_true_invariant_labels():
    x=audit_form_counts(make_pairs("INV"))
    assert x.source_kind==SourceKind.INDUCTIVE_INVARIANT
    assert x.authorize(FeedbackKind.CANDIDATE_COUNTEREXAMPLE)
    with pytest.raises(MissingSourceRight):
        x.authorize(FeedbackKind.TRUE_TARGET_OUTPUT)

def test_LIA_universal_counterexample_is_not_target_label():
    x=audit_form_counts(make_pairs("LIA"))
    assert x.source_kind==SourceKind.FORMAL_SYNTHESIS
    assert x.authorize(FeedbackKind.CANDIDATE_COUNTEREXAMPLE)
    with pytest.raises(MissingSourceRight):
        x.authorize(FeedbackKind.TRUE_TARGET_OUTPUT)

def test_pbe_bitvector_finite_examples_not_full_truth_table():
    x=audit_form_counts(make_pairs("BV"))
    assert x.source_kind==SourceKind.PBE_GROUND_EXAMPLES
    assert not x.original_full_truth_table_available

def test_counterexample_not_gold_supervision():
    assert not oracle_counterexample_is_a_true_label(
        {"x":3,"violated":"INDUCTIVE_CONSECUTION","candidate_prediction":False})

def test_absent_source_constraints_is_unknown_and_denied():
    x=audit_form_counts([("synth-fun","(synth-fun f ((x Int)) Int)")])
    assert x.source_kind==SourceKind.MIXED_OR_UNPARSED
    with pytest.raises(MissingSourceRight):
        x.authorize(FeedbackKind.TRUE_TARGET_OUTPUT)

def test_finite_string_witness_is_not_ideal_answer():
    x=audit_form_counts(make_pairs("PBE"))
    assert not x.has_true_target_output_oracle
    assert not oracle_counterexample_is_a_true_label(
        {"input":"hello ","program1":"hello","program2":"hello "})
