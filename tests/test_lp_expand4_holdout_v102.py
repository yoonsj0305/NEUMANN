import pytest

torch=pytest.importorskip("torch")

from experiments.lp_expand4_holdout_v102 import (
    GROUPS,
    ROUTES,
    SEEDS,
    protocol,
)


def test_v102_eval_protocol_freezes_only_expansion_candidate():
    p=protocol()
    assert p["source_manifest"]=="docs/experiments/results/v102_fresh_sources.manifest.json"
    assert p["authority_manifest"]=="docs/experiments/results/v101_first_expansion.manifest.json"
    assert p["source_views"]==48
    assert p["groups"]==list(GROUPS)
    assert p["routes"]==list(ROUTES)
    assert p["model_seeds"]==list(SEEDS)==[100001,100002]
    assert p["fixed_support_factor"]==2
    assert p["expanded_support_factor"]==4
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["new_fitting"] is False
    assert p["checkpoint_selection"] is False
    assert p["support_factor_tuning"] is False
    assert p["v098_holdout_access"] is False
    assert p["final_q34_holdout"] is True


def test_v102_route_roster_excludes_stopped_controls():
    assert ROUTES==(
        "DIRECT","ORACLE","EXPAND4_s100001","EXPAND4_s100002"
    )
    assert not any("FIXED2" in r for r in ROUTES)
    assert not any("OLD_CG5" in r for r in ROUTES)


def test_v102_archived_training_identity_normalizes_json_seed_keys_only():
    from experiments.lp_expand4_holdout_v102 import authority_and_models
    authority,models,training=authority_and_models()
    assert set(training)=={100001,100002}
    assert set(models)=={100001,100002}
    assert {str(k):v for k,v in training.items()}=={
        str(k):v for k,v in authority["training_identity"].items()
    }


def test_v102_invalid_first_evaluation_is_preserved_as_zero_observation_failure():
    import json
    from pathlib import Path
    notice=json.loads(Path(
        "docs/experiments/results/v102_invalid_first_evaluation_attempt.json"
    ).read_text())
    assert notice["status"]=="INVALID_PRE_MEASUREMENT_AUTHORITY_KEY_NORMALIZATION"
    assert notice["route_observations"]==0
    assert notice["timing_observations"]==0
    assert notice["warmups_completed"]==0
    assert notice["result_archive_created"] is False
    assert notice["favorable_rerun"] is False
