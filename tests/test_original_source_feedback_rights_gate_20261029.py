"""Test no oracle data leakage from original source constraints."""
import pytest
from research.q3.discovery_policy.original_source_feedback_rights_gate_20261029 import (
    SourceFeedback,SourceKind,author_rights,require_feedback,
    original_frozen16_rights_summary)

def test_sygus_pbe_examples_are_not_oracle_for_new_inputs():
    r=author_rights(SourceKind.EXPLICIT_PBE,3)
    assert r.permits(SourceFeedback.ORIGINAL_EXAMPLE)
    assert not r.permits(SourceFeedback.ARBITRARY_TARGET_OUTPUT)

def test_no_hallucinated_target_on_unlabeled_string():
    r=author_rights(SourceKind.EXPLICIT_PBE,3)
    with pytest.raises(PermissionError,match="SOURCE_FEEDBACK_NOT_GROUNDED"):
        require_feedback(r,SourceFeedback.ARBITRARY_TARGET_OUTPUT)

def test_symbolic_counterexample_is_not_target_oracle():
    r=author_rights(SourceKind.UNIVERSAL_SYMBOLIC)
    assert r.permits(SourceFeedback.FULL_SYMBOLIC_COUNTEREXAMPLE)
    assert not r.permits(SourceFeedback.ARBITRARY_TARGET_OUTPUT)

def test_invariant_counterexample_is_not_correct_invariant_label():
    r=author_rights(SourceKind.INVARIANT_VC)
    assert r.permits(SourceFeedback.INDUCTIVE_VC_COUNTEREXAMPLE)
    assert not r.permits(SourceFeedback.ARBITRARY_TARGET_OUTPUT)
    assert not r.permits(SourceFeedback.FULL_SYMBOLIC_COUNTEREXAMPLE)

def test_no_examples_without_examples():
    assert not author_rights(SourceKind.EXPLICIT_PBE,0).permits(
        SourceFeedback.ORIGINAL_EXAMPLE)

def test_reject_negative_example_counts():
    with pytest.raises(ValueError):
        author_rights(SourceKind.EXPLICIT_PBE,-1)

def test_original_four_track_types_all_disallow_arbitrary_oracle():
    assert len(original_frozen16_rights_summary())==4
    assert all(not r.permits(SourceFeedback.ARBITRARY_TARGET_OUTPUT)
               for r in original_frozen16_rights_summary().values())

def test_valid_only_grounded_source_feedback():
    r=author_rights(SourceKind.EXPLICIT_PBE,3)
    assert require_feedback(r,SourceFeedback.ORIGINAL_EXAMPLE)
