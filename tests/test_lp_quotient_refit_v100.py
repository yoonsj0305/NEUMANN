import pytest

torch=pytest.importorskip("torch")

from experiments.lp_quotient_refit_v100 import (
    GROUPS,
    KINDS,
    MODEL_SEEDS,
    ROUTES,
    SupportMLP,
    base_specs,
    protocol,
)


def test_v100_protocol_is_frozen_before_first_fit():
    p=protocol()
    assert p["train_sources"]==48
    assert p["model_seeds"]==list(MODEL_SEEDS)==[100001,100002]
    assert p["kinds"]==list(KINDS)==["OLD_CG5","QUOTIENT"]
    assert p["parameters"]==433
    assert p["epochs"]==12
    assert p["lr"]==0.001
    assert p["positive_weight"]==15.0
    assert p["development_seed_base"]==100200
    assert p["development_base_cases"]==16
    assert p["development_views"]==32
    assert p["groups"]==list(GROUPS)
    assert p["support_factor"]==2
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["v088_final_access"] is False
    assert p["v098_holdout_access"] is False
    assert p["fresh_holdout"] is False
    assert p["advance_q5"] is False


def test_v100_matched_support_model_has_exact_budget():
    for seed in MODEL_SEEDS:
        model=SupportMLP(seed)
        assert sum(p.numel() for p in model.parameters())==433


def test_v100_development_factorial_specs_are_frozen_without_generation():
    specs=base_specs()
    assert len(specs)==16
    assert [s["seed"] for s in specs]==list(range(100200,100216))
    assert all(s["rows"]==64 for s in specs[:8])
    assert all(s["rows"]==128 for s in specs[8:])
    assert [s["condition"] for s in specs]==[1,1000]*8


def test_v100_routes_are_matched_old_vs_quotient_only():
    assert ROUTES==(
        "DIRECT","ORACLE",
        "OLD_CG5_s100001","OLD_CG5_s100002",
        "QUOTIENT_s100001","QUOTIENT_s100002",
    )
