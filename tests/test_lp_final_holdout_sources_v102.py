from experiments.lp_final_holdout_sources_v102 import GROUPS, protocol, specs


def test_v102_final_holdout_registration_is_model_free_and_frozen():
    p=protocol()
    assert p["seed_base"]==100500
    assert p["base_cases"]==24
    assert p["views"]==48
    assert p["surface_seed_offset"]==400000
    assert p["width_factor"]==16
    assert p["groups"]==list(GROUPS)
    assert p["model_access"] is False
    assert p["candidate_inference"] is False
    assert p["timing"] is False
    assert p["route_evaluation"] is False
    assert p["v098_holdout_access"] is False
    assert p["v101_development_access"] is False


def test_v102_final_holdout_specs_use_only_new_seeds():
    xs=specs()
    assert len(xs)==24
    assert [x["seed"] for x in xs]==list(range(100500,100524))
    assert all(x["rows"]==64 and x["cols"]==1024 for x in xs[:12])
    assert all(x["rows"]==128 and x["cols"]==2048 for x in xs[12:])
    assert [x["condition"] for x in xs]==[1,1000]*12
