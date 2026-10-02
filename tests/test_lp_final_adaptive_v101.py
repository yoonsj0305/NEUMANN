import pytest

pytest.importorskip("torch")

from experiments.lp_final_adaptive_v101 import GROUPS, MODEL_SEEDS, ROUTES, protocol, specs


def test_v101_is_final_training_free_local_gate():
    p=protocol()
    assert p["model_seeds"]==[100001,100002]
    assert p["development_seed_base"]==100300
    assert p["development_base_cases"]==16
    assert p["development_views"]==32
    assert p["static_support_factor"]==2
    assert p["adaptive_support_factors"]==[2,4]
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["new_fitting"] is False
    assert p["threshold_change"] is False
    assert p["v098_holdout_access"] is False
    assert p["fresh_holdout"] is False
    assert p["advance_q5"] is False


def test_v101_new_development_specs_are_frozen():
    xs=specs()
    assert len(xs)==16
    assert [x["seed"] for x in xs]==list(range(100300,100316))
    assert all(x["rows"]==64 for x in xs[:8])
    assert all(x["rows"]==128 for x in xs[8:])
    assert [x["condition"] for x in xs]==[1,1000]*8


def test_v101_routes_compare_static_and_adaptive_only():
    assert GROUPS==("m64_base","m64_surface","m128_base","m128_surface")
    assert MODEL_SEEDS==(100001,100002)
    assert ROUTES==(
        "DIRECT","ORACLE",
        "STATIC_s100001","STATIC_s100002",
        "ADAPTIVE_s100001","ADAPTIVE_s100002",
    )
