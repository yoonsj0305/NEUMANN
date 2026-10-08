import hashlib
import json
from pathlib import Path

import pytest

from neumann1.structural_data_rights import DataUseError, LineageGuard, load_json_view


def record(group="base", exposed=True, composition=None):
    return {"equivalence_group": group, "source_artifact_sha256": "a" * 64,
            "training_exposure": exposed, "transformation_ancestry": composition}


def test_sealed_read_denied_before_io(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise AssertionError("sealed payload was touched")
    monkeypatch.setattr(Path, "read_bytes", fail)
    with pytest.raises(DataUseError):
        load_json_view(tmp_path, {"role": "S", "path": "sealed.json"}, "audit")


@pytest.mark.parametrize("role,purpose", [("H", "development_problem"),
    ("O", "development_problem"), ("D", "offline_oracle"), ("D", "train"), ("D", "fresh_eval")])
def test_wrong_role_or_stage_denied(tmp_path, role, purpose):
    with pytest.raises(DataUseError):
        load_json_view(tmp_path, {"role": role, "path": "never-read.json"}, purpose)


def test_public_view_excludes_hidden_answer_and_seed(tmp_path):
    payload = {"arrays": {"A": [[1]], "b": [2], "c": [1]},
               "label": {"witness": {"x": [2]}}, "seed": 42, "basis": [0]}
    raw = json.dumps(payload).encode()
    (tmp_path / "source.json").write_bytes(raw)
    asset = {"role": "D", "allowed_use": "opened_development_only",
             "path": "source.json", "sha256": hashlib.sha256(raw).hexdigest()}
    assert load_json_view(tmp_path, asset, "development_problem") == payload["arrays"]
    asset["sha256"] = "0" * 64
    with pytest.raises(DataUseError, match="identity"):
        load_json_view(tmp_path, asset, "development_problem")


def test_equivalent_views_cannot_cross_split():
    guard = LineageGuard()
    guard.register(record(exposed=False), "train")
    with pytest.raises(DataUseError, match="cross partition"):
        guard.register(record(exposed=False), "novel_motif")


def test_old_holdout_is_not_fresh_for_new_architecture():
    with pytest.raises(DataUseError, match="historically exposed"):
        LineageGuard().register(record(), "novel_motif")


@pytest.mark.parametrize("reverse", [False, True])
def test_composition_split_independent_of_registration_order(reverse):
    guard = LineageGuard()
    train = record("train-root", False, ["A", "B"])
    evaluation = record("new-root", False, ["A", "B"])
    first, second = ((evaluation, "unseen_composition"), (train, "train")) if reverse else ((train, "train"), (evaluation, "unseen_composition"))
    guard.register(*first)
    with pytest.raises(DataUseError):
        guard.register(*second)


def test_unseen_composition_of_seen_primitives_is_allowed():
    guard = LineageGuard()
    guard.register(record("a", False, ["A"]), "train")
    guard.register(record("b", False, ["B"]), "train")
    guard.register(record("ab-new", False, ["A", "B"]), "unseen_composition")

