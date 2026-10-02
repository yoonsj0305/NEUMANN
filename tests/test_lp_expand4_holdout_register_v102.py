import pytest

from experiments.lp_expand4_holdout_register_v102 import (
    GROUPS,
    base_specs,
    protocol,
    view_specs,
)


def test_v102_source_protocol_is_frozen_without_model_or_timing_authority():
    p=protocol()
    assert p["seed_base"]==102200
    assert p["base_cases"]==24
    assert p["views"]==48
    assert p["groups"]=={g:12 for g in GROUPS}
    assert p["surface_seed_offset"]==300000
    assert p["model_access"] is False
    assert p["timing"] is False
    assert p["route_evaluation"] is False
    assert p["v098_holdout_access"] is False


def test_v102_fresh_specs_are_new_balanced_and_paired():
    base=base_specs()
    assert len(base)==24
    assert [s["seed"] for s in base]==list(range(102200,102224))
    assert all(s["rows"]==64 for s in base[:12])
    assert all(s["rows"]==128 for s in base[12:])
    assert [s["condition"] for s in base]==[1,1000]*12
    views=view_specs()
    assert len(views)==48
    assert {v["group"] for v in views}==set(GROUPS)
    for pair in {v["pair_id"] for v in views}:
        rows=[v for v in views if v["pair_id"]==pair]
        assert len(rows)==2
        assert {v["surface"] for v in rows}=={False,True}
