from experiments.einsum_full_model_screen import select,worker
import json
import pytest


def record(shapes,equation='ab,bc->ac'):
    return {'member':'sample.pkl','name':'sample','status':'NON_EXECUTING_METADATA_EXTRACTED','equation':equation,'shapes':shapes}


def test_selection_ignores_teacher_paths_and_answers():
    r=record([[2,3],[3,4]]);r.update(provided_paths={'hidden':'not a valid path'},provided_result_sum='secret')
    a,d=select([r]);assert a==[r];assert d[0]['status']=='PUBLIC_SHAPE_SELECTED'


def test_failed_and_large_inputs_preserved():
    failed={'member':'bad.pkl','status':'NOT_EXTRACTED'}
    large=record([[4000,4000],[4000,4000]])
    a,d=select([failed,large]);assert not a;assert len(d)==2;assert all(x['status']=='NOT_SELECTED'for x in d)


def test_public_worker_rejects_oracle_envelope_before_planning(tmp_path):
    p=tmp_path/'input.json';p.write_text(json.dumps({'equation':'a->','shapes':[[2]],'provided_path':[[0]]}))
    with pytest.raises(ValueError,match='Public equation/shapes only'):worker(p,'greedy',19,tmp_path/'result.json')
    assert not(tmp_path/'result.json').exists()


def test_public_worker_certifies_same_output_indices(tmp_path):
    p=tmp_path/'input.json';p.write_text(json.dumps({'equation':'ab,bc->ac','shapes':[[2,3],[3,4]]}))
    out=tmp_path/'result.json';worker(p,'greedy',19,out);r=json.loads(out.read_text())
    assert r['status']=='CERTIFIED_DENSE_MODEL_ONLY';assert r['certificate']['ordered_output']=='ac'
