import hashlib
import json
import pytest
from neumann1.structural_data_rights import DataUseError
from neumann1.structural_experience import problem_view, offline_experience


def asset(tmp_path, role="D"):
    raw = json.dumps({"public": {"equation": "ab,bc->ac", "shapes": [[2, 3], [3, 4]]},
                      "supplied_paths": {"gold": [[0, 1]]}, "accepted": True}).encode()
    (tmp_path / "case.json").write_bytes(raw)
    return {"role": role, "path": "case.json", "sha256": hashlib.sha256(raw).hexdigest(),
            "allowed_use": "opened_development_only", "problem_kind": "contraction", "runtime": role != "O"}


def test_public_projection_drops_supervision(tmp_path):
    record = asset(tmp_path)
    assert problem_view(tmp_path, record) == {"kind": "contraction", "equation": "ab,bc->ac", "shapes": [[2, 3], [3, 4]]}


@pytest.mark.parametrize("role,purpose", [("S", "development_problem"), ("O", "development_problem"), ("H", "development_problem"), ("D", "train"), ("D", "fresh_eval")])
def test_denied_before_payload_access(tmp_path, role, purpose):
    record = {"role": role, "path": "missing.json", "sha256": "unread", "allowed_use": "opened_development_only"}
    with pytest.raises(DataUseError, match="before payload"):
        problem_view(tmp_path, record, purpose)


def test_offline_supervision_requires_nonruntime_oracle(tmp_path):
    record = asset(tmp_path, "O")
    assert offline_experience(tmp_path, record)["accepted"]
    record["runtime"] = True
    with pytest.raises(DataUseError, match="offline only"):
        offline_experience(tmp_path, record)


def test_payload_hash_and_root_escape_rejected(tmp_path):
    record = asset(tmp_path)
    record["sha256"] = "wrong"
    with pytest.raises(DataUseError, match="identity"):
        problem_view(tmp_path, record)
    record["path"] = "../outside.json"
    with pytest.raises(DataUseError, match="escapes"):
        problem_view(tmp_path, record)
