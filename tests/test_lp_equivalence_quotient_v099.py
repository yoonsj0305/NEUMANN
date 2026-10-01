import pytest

pytest.importorskip("torch")

from experiments.lp_equivalence_quotient_v099 import (
    VIEWS,
    analyze,
    protocol,
    quotient_columns,
)


def test_v099_protocol_freezes_representation_audit_before_result():
    p=protocol()
    assert p["opened_sources"]==48
    assert p["views"]==list(VIEWS)
    assert p["metamorphic_seed_base"]==99900
    assert p["quotient_drift_max"]==1e-8
    assert p["channel_std_min"]==1e-8
    assert p["size_slot_ratio_max"]==1.20
    assert p["new_fitting"] is False
    assert p["solver_calls"] is False
    assert p["labels_used"] is False
    assert p["v098_holdout_access"] is False


def test_v099_quotient_audit_uses_only_opened_development_and_is_label_free():
    result=analyze()
    assert result["new_fitting"] is False
    assert result["solver_calls"]==0
    assert result["labels_used"] is False
    assert result["v098_holdout_access"] is False
    assert result["global_q3"]==result["global_q4"]=="OPEN"
    assert result["summary"]["equivalent_views"]==48*3
    assert len(result["records"])==48*3
    assert result["decision"] in {
        "ADMIT_QUOTIENT_POINT_REFIT_ON_OPENED_DEV",
        "REJECT_QUOTIENT_REPRESENTATION_BEFORE_TRAINING",
    }
    print("V099_QUOTIENT_AUDIT="+__import__("json").dumps(
        result["summary"],sort_keys=True,separators=(",",":")))


def test_quotient_columns_have_fixed_point_shape_on_tiny_input():
    import numpy as np
    raw={
        "A":np.array([[1.0,0.5,-0.25],[0.25,-1.0,0.75]]),
        "b":np.array([1.0,-0.5]),
        "c":np.array([1.0,2.0,3.0]),
    }
    D,cols=quotient_columns(raw)
    assert D.shape==(2,3)
    assert cols.shape==(3,8)
    assert np.isfinite(cols).all()
