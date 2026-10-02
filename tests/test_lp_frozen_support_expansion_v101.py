import pytest

torch=pytest.importorskip("torch")

from experiments.lp_frozen_support_expansion_v101 import (
    FAMILIES,
    GROUPS,
    ROUTES,
    SEEDS,
    base_specs,
    expansion_rescue_evidence,
    protocol,
)


def test_v101_protocol_freezes_training_free_support_tournament():
    p=protocol()
    assert p["source_checkpoint"]=="v100_first_refit"
    assert p["model_seeds"]==list(SEEDS)==[100001,100002]
    assert p["families"]==list(FAMILIES)==["FIXED2","EXPAND4"]
    assert p["development_seed_base"]==101200
    assert p["development_base_cases"]==16
    assert p["development_views"]==32
    assert p["groups"]==list(GROUPS)
    assert p["fixed_support_factor"]==2
    assert p["expanded_support_factor"]==4
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["new_fitting"] is False
    assert p["checkpoint_selection"] is False
    assert p["v098_holdout_access"] is False
    assert p["fresh_holdout"] is False
    assert p["advance_q5"] is False


def test_v101_development_specs_are_new_and_factorial():
    specs=base_specs()
    assert len(specs)==16
    assert [s["seed"] for s in specs]==list(range(101200,101216))
    assert all(s["rows"]==64 for s in specs[:8])
    assert all(s["rows"]==128 for s in specs[8:])
    assert [s["condition"] for s in specs]==[1,1000]*8


def test_v101_route_roster_has_only_frozen_execution_contracts():
    assert ROUTES==(
        "DIRECT","ORACLE",
        "FIXED2_s100001","FIXED2_s100002",
        "EXPAND4_s100001","EXPAND4_s100002",
    )


def _metric(cases, fallback_free, utility, complete):
    return {
        "cases":cases,
        "fallback_free_cases":fallback_free,
        "utility_recovery":utility,
        "amortized_complete_ratio":complete,
    }


def test_v101_expand4_must_earn_authority_over_fixed2():
    overall={}
    cells={}
    for seed in SEEDS:
        fixed=f"FIXED2_s{seed}"
        expand=f"EXPAND4_s{seed}"
        overall[fixed]={}
        overall[expand]={}
        cells[fixed]={
            "m128_base":_metric(8,7,0.79,0.27),
            "m128_surface":_metric(8,7,0.79,0.26),
        }
        cells[expand]={
            "m128_base":_metric(8,8,0.90,0.22),
            "m128_surface":_metric(8,8,0.90,0.21),
        }
    evidence=expansion_rescue_evidence(overall,cells)
    assert all(row["earned"] for row in evidence.values())


def test_v101_fixed2_resampling_cannot_count_as_expansion_rescue():
    overall={}
    cells={}
    for seed in SEEDS:
        fixed=f"FIXED2_s{seed}"
        expand=f"EXPAND4_s{seed}"
        overall[fixed]={}
        overall[expand]={}
        cells[fixed]={
            "m128_base":_metric(8,8,0.90,0.20),
            "m128_surface":_metric(8,8,0.90,0.20),
        }
        cells[expand]={
            "m128_base":_metric(8,8,0.90,0.21),
            "m128_surface":_metric(8,8,0.90,0.21),
        }
    evidence=expansion_rescue_evidence(overall,cells)
    assert not any(row["earned"] for row in evidence.values())
