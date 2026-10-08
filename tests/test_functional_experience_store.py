from pathlib import Path
import hashlib,json
import pytest
from neumann1.functional_experience_store import ExperienceStore
from neumann1.structural_data_rights import DataUseError


def store(tmp_path,role='O',runtime=False,path='missing.json'):
    index={'records':[{'record_id':'x','assets':{'proposal':{'role':role,'runtime':runtime,'path':path,'sha256':'0'*64,'allowed_use':'opened_development_only'}}}]}
    b=json.dumps(index).encode();(tmp_path/'index.json').write_bytes(b)
    return ExperienceStore(tmp_path,hashlib.sha256(b).hexdigest())


@pytest.mark.parametrize('purpose',['train','fresh_evaluation','runtime_oracle','development_problem'])
def test_oracle_refusal_precedes_payload_io(tmp_path,purpose):
    s=store(tmp_path)
    with pytest.raises(DataUseError,match='role/purpose denied'):s.view('x','proposal',purpose)


def test_sealed_never_read(tmp_path):
    s=store(tmp_path,role='S')
    with pytest.raises(DataUseError):s.view('x','proposal','audit')


def test_offline_oracle_cannot_claim_runtime(tmp_path):
    s=store(tmp_path,runtime=True)
    with pytest.raises(DataUseError,match='offline only'):s.view('x','proposal','offline_oracle')


def test_escape_rejected_before_read(tmp_path):
    s=store(tmp_path,path='../outside.json')
    with pytest.raises(DataUseError,match='escapes'):s.view('x','proposal','offline_oracle')


def test_identical_source_experiences_cannot_silently_overwrite_ids(tmp_path):
    raw=json.dumps({'records':[{'record_id':'same','assets':{}},{'record_id':'same','assets':{}}]}).encode()
    (tmp_path/'index.json').write_bytes(raw)
    with pytest.raises(DataUseError,match='Duplicate record identifiers'):
        ExperienceStore(tmp_path,hashlib.sha256(raw).hexdigest())
