"""Integration fail-closed checks, not new Q6 capability evidence."""
from neumann1.q6.api import structural_transport


def test_unsupported_target_returns_unknown_without_source_queries():
    called = []
    r = structural_transport([], {"in_types": ["Graph"], "out_type": "Graph", "train": []},
                             source_authority=lambda a: called.append(a))
    assert r["verification_status"] == "UNKNOWN" and not called
    assert r["failure_reason"] == "unsupported_observation_representation"


def test_hidden_receiver_labels_do_not_enter_matching():
    r = structural_transport([], {"in_types": ["I"], "out_type": "I", "train": [], "test": ["secret"]},
                             source_authority=lambda a: True)
    assert r["verification_status"] == "UNKNOWN"
    assert r["failure_reason"] == "receiver_TEST_not_authorized_for_inference"


def test_missing_evidence_is_unknown_not_an_unverified_success():
    r = structural_transport([{}], {"in_types": ["I"], "out_type": "I", "train": [((1,), 2)]},
                             source_authority=lambda a: False)
    assert r["verification_status"] == "UNKNOWN"
    assert r["failure_reason"] == "no_independently_admitted_source_artifact"
