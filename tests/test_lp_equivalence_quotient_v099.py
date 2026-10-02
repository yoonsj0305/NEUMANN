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
    assert result["decision"]=="ADMIT_QUOTIENT_POINT_REFIT_ON_OPENED_DEV"
    s=result["summary"]
    assert s["current_max_abs_drift"]==pytest.approx(0.1723346053014952,abs=1e-15)
    assert s["quotient_max_abs_drift"]==pytest.approx(1.7763568394002505e-15,abs=1e-18)
    assert s["current_point_support_exact"]=={"87001":48,"87002":48}
    assert s["current_point_support_exact_rate"]=={
        "87001":pytest.approx(1/3),"87002":pytest.approx(1/3)}
    assert s["current_point_support_mean_jaccard"]["87001"]==pytest.approx(0.9921867373935545)
    assert s["current_point_support_mean_jaccard"]["87002"]==pytest.approx(0.9968925992181806)
    assert s["quotient_first6_global_std"]==pytest.approx([
        0.730681082307796,0.3615646404029828,0.008748418851157933,
        0.15349722001747448,0.065206613572109,0.030038880663674584])
    assert s["slot6_median_m32"]==pytest.approx(0.8067152319655222)
    assert s["slot6_median_m64"]==pytest.approx(0.8020933978900535)
    assert s["slot6_size_ratio"]==pytest.approx(1.0057622143351717)
    assert s["finite"] is True
    print("V099_QUOTIENT_AUDIT="+__import__("json").dumps(
        s,sort_keys=True,separators=(",",":")))


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
