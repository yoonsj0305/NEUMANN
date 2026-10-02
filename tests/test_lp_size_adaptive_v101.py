import pytest

torch=pytest.importorskip("torch")

from experiments.lp_size_adaptive_v101 import (
    MODEL_SEEDS,
    ROUTES,
    diagnose_v100,
    development_specs,
    protocol,
    restore_models,
    summarize,
)
from neumann1.lp_quotient_refit_archive_v100 import load_first_refit


def test_v101_protocol_is_frozen_before_first_screen():
    p=protocol()
    assert p["model_seeds"]==[100001,100002]
    assert p["development_seed_base"]==101200
    assert p["development_cases"]==16
    assert p["rows"]==128
    assert p["width_factor"]==16
    assert p["conditions"]==[1,1000]
    assert p["warmups"]==1 and p["repeats"]==3
    assert p["order_seed"]==101991
    assert p["fixed_support_factor"]==2
    assert p["adaptive_factors"]==[2,4]
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["new_fitting"] is False
    assert p["optimizer_calls"] is False
    assert p["v098_holdout_access"] is False
    assert p["fresh_holdout"] is False
    assert p["advance_q5"] is False
    assert ROUTES==(
        "DIRECT","ORACLE",
        "FIXED2_s100001","FIXED2_s100002",
        "ADAPT24_s100001","ADAPT24_s100002",
    )


def test_v101_new_m128_development_specs_are_frozen_without_generation():
    specs=development_specs()
    assert len(specs)==16
    assert [s["seed"] for s in specs]==list(range(101200,101216))
    assert all(s["rows"]==128 for s in specs)
    assert [s["condition"] for s in specs]==[1,1000]*8


def test_v101_restores_exact_frozen_quotient_checkpoints_without_fit():
    v100=load_first_refit("docs/experiments/results/v100_first_refit.manifest.json")
    models=restore_models(v100)
    assert set(models)==set(MODEL_SEEDS)
    assert all(sum(p.numel() for p in model.parameters())==433 for model in models.values())


def test_v101_retained_v100_diagnosis_uses_only_archive():
    diag=diagnose_v100()
    assert set(diag)=={"100001","100002"}
    for row in diag.values():
        assert len(row["pairs"])==8
        assert row["all_pair_supports_identical"] is True
        assert row["full_fallback_pairs"]>=1


def _fake_records(fixed_post=30.0,adapt_post=18.0,fixed_fallback=True,adapt_fallback=False):
    sources=[{
        "id":f"v101_dev{i:02d}","rows":128,"condition":(1,1000)[i%2],
        "seed":101200+i,"cols":2048,"basis":list(range(128)),
        "sha256":f"{i:064x}",
    } for i in range(16)]
    rows=[]
    for repeat in (-1,0,1,2):
        for source in sources:
            for route in ROUTES:
                if route=="DIRECT":
                    proposal,post,invest,fallback,subset,expanded=0.0,100.0,0.0,False,False,False
                    ranking=None
                elif route=="ORACLE":
                    proposal,post,invest,fallback,subset,expanded=0.0,10.0,0.0,False,True,False
                    ranking=None
                elif route.startswith("FIXED2_"):
                    proposal,post,invest,fallback,subset,expanded=2.0,fixed_post,0.1,fixed_fallback,not fixed_fallback,False
                    ranking=list(range(2048))
                else:
                    proposal,post,invest,fallback,subset,expanded=2.0,adapt_post,0.1,adapt_fallback,True,True
                    ranking=list(range(2048))
                rows.append({
                    "case_id":source["id"],"source_sha256":source["sha256"],
                    "condition":source["condition"],"route":route,"repeat":repeat,
                    "accepted":True,"proposal_ms":proposal,"post_ms":post,
                    "total_ms":proposal+post,"amortized_investment_ms":invest,
                    "fallback_used":fallback,"subset_accepted":subset,
                    "expanded_to_4m":expanded,"ranking":ranking,
                })
    return rows,sources


def test_v101_summary_admits_only_real_adaptive_rescue():
    rows,sources=_fake_records()
    result=summarize(rows,sources)
    assert result["decision"]=="ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_ADAPTIVE_QUOTIENT"
    assert result["adaptive_development_pass"] is True
    assert all(x["adaptive_promoted"] for x in result["seed_tests"].values())


def test_v101_summary_stops_family_if_adaptive_still_falls_back():
    rows,sources=_fake_records(adapt_fallback=True)
    result=summarize(rows,sources)
    assert result["decision"]=="STOP_QUOTIENT_POINT_SUPPORT_FAMILY"
    assert result["adaptive_development_pass"] is False
