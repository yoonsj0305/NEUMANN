import hashlib
import json
import pytest
from experiments.recursive_summary_cases import lifted_prefix
from neumann1.recursive_summary import SummaryError
from neumann1.recursive_summary_data import problem_view
from neumann1.structural_data_rights import DataUseError


def asset(tmp_path,public):
    data=json.dumps(public).encode();(tmp_path/"public.json").write_bytes(data)
    return {"role":"D","allowed_use":"opened_development_only","problem_kind":"integer_list_right_fold",
            "path":"public.json","sha256":hashlib.sha256(data).hexdigest()}


def test_denied_roles_before_any_payload_read(tmp_path):
    for role,purpose in [("D","train"),("D","fresh_eval"),("O","development_problem"),("F","development_problem"),("S","audit")]:
        with pytest.raises(DataUseError):problem_view(tmp_path,{"role":role,"path":"absent"},purpose)


def test_public_does_not_include_supervision(tmp_path):
    public=lifted_prefix()[0]
    assert problem_view(tmp_path,asset(tmp_path,public))==public
    with pytest.raises(SummaryError):problem_view(tmp_path,asset(tmp_path,{**public,"answers":[1]}))


def test_identity_and_paths_are_bounded(tmp_path):
    row=asset(tmp_path,lifted_prefix()[0])
    for changed in [{"sha256":"0"*64},{"path":"../escape.json"}]:
        with pytest.raises(DataUseError):problem_view(tmp_path,{**row,**changed})
