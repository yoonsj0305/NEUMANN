import pytest

pytest.importorskip("torch")

from experiments.lp_final_holdout_v102 import GROUPS, MODEL_SEEDS, ROUTES, protocol


def test_v102_final_eval_is_frozen_adaptive_only():
    p=protocol()
    assert p["views"]==48
    assert p["cases_per_cell"]==12
    assert p["model_seeds"]==[100001,100002]
    assert p["adaptive_support_factors"]==[2,4]
    assert p["warmups"]==1 and p["repeats"]==3
    assert p["order_seed"]==102991
    assert p["budget_s"]==5.0
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["new_fitting"] is False
    assert p["threshold_change"] is False
    assert p["support_width_sweep"] is False
    assert p["v098_holdout_access"] is False
    assert p["v101_development_access"] is False
    assert p["second_holdout_authorized"] is False


def test_v102_final_routes_have_no_static_or_new_model_family():
    assert GROUPS==("m64_base","m64_surface","m128_base","m128_surface")
    assert MODEL_SEEDS==(100001,100002)
    assert ROUTES==(
        "DIRECT","ORACLE","ADAPTIVE_s100001","ADAPTIVE_s100002",
    )
