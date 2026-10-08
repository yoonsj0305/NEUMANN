import hashlib
import json
import pytest

from neumann1.recurrence_data import problem_view
from neumann1.structural_data_rights import DataUseError
from neumann1.representation_program import ProgramError
from experiments.inductive_cost_cases import make_case


def asset_for(tmp_path, public):
    payload = json.dumps(public).encode()
    (tmp_path/"public.json").write_bytes(payload)
    return {"path": "public.json", "sha256": hashlib.sha256(payload).hexdigest(), "role": "D",
            "allowed_use": "opened_development_only", "problem_kind": "exact_integer_recurrence"}


def test_rights_denied_before_nonexistent_payload_access(tmp_path):
    asset = {"path": "missing.json", "role": "D", "allowed_use": "opened_development_only"}
    for role, purpose in [("D", "train"), ("D", "fresh_evaluation"), ("O", "development_problem"),
                          ("H", "development_problem"), ("S", "audit")]:
        with pytest.raises(DataUseError):
            problem_view(tmp_path, {**asset, "role": role}, purpose)


def test_public_projection_rejects_oracle_labels(tmp_path):
    public = make_case(2, -2, 8127000)[0]
    assert problem_view(tmp_path, asset_for(tmp_path, public)) == public
    with pytest.raises(ProgramError):
        problem_view(tmp_path, asset_for(tmp_path, {**public, "oracle": {"answer": 1}}))


def test_content_identity_and_root_escape_blocked(tmp_path):
    public = make_case(2, -2, 8127000)[0]
    asset = asset_for(tmp_path, public)
    with pytest.raises(DataUseError):
        problem_view(tmp_path, {**asset, "sha256": "0"*64})
    with pytest.raises(DataUseError):
        problem_view(tmp_path, {**asset, "path": "../outside.json"})
