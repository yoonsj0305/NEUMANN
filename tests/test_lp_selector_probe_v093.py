import copy,json
from pathlib import Path
from unittest.mock import patch
import pytest
pytest.importorskip('torch')
from experiments import lp_selector_probe_v093 as p
from neumann1.lp_selector_archive_v093 import load_probe

MANIFEST=Path('docs/experiments/results/v093_first_probe.manifest.json')


@pytest.fixture(scope='module')
def report():return load_probe(MANIFEST)


def test_first_probe_replay_without_execution(report):
    with (patch.object(p.prior.old,'fit_one',side_effect=AssertionError('no fitting')),
        patch.object(p.prior,'solve_shortlist_checked',side_effect=AssertionError('no optimizer')),
        patch.object(p.prior.old,'generate',side_effect=AssertionError('no generation')),
        patch.object(p,'approximate_features',side_effect=AssertionError('no features')),
        patch.object(p,'indices',side_effect=AssertionError('no proposal')),
        patch('experiments.lp_late_models_v092.LateGraphStateModel.forward',side_effect=AssertionError('no inference')),
        patch('experiments.lp_state_models_v087.GraphStateModel.forward',side_effect=AssertionError('no inference')),
        patch('experiments.lp_state_models_v087.PointwiseModel.forward',side_effect=AssertionError('no inference'))):
        p.validate(report)
    assert len(report['records'])==1824
    assert sum(r['candidate']['accepted'] for r in report['records'])==82
    assert report['summary']['decision']=='SELECTOR_GAP_UNRESOLVED_NO_NEW_FIT'
    assert [x['passed'] for x in report['summary']['point_parity']]==[False,True]
    assert not any(r['proposal_error'] for r in report['records'])


@pytest.mark.parametrize('field',['protocol','source','checkpoint','indices','coverage','witness','verdict','feature_error'])
def test_corrupt_probe_rejected(report,field):
    r=copy.deepcopy(report)
    if field=='protocol':r['protocol']['maximum_parity_loss']=2
    elif field=='source':r['sources'][0]['sha256']='0'*64
    elif field=='checkpoint':r['weights_sha256']['v088']['point16_s87001']='0'*64
    elif field=='indices':r['records'][0]['basis'][0]=-1
    elif field=='coverage':r['records'][0]['shortlist_covers']=not r['records'][0]['shortlist_covers']
    elif field=='witness':
        row=next(x for x in r['records'] if x['candidate']['accepted'])
        row['candidate']['witness']['x']=[0.]*len(row['candidate']['witness']['x'])
    elif field=='verdict':r['summary']['decision']='ADMIT_PREREGISTERED_CG3_POINT_COST_SCREEN_NOT_Q3_Q4'
    elif field=='feature_error':r['feature_errors'][0]['primal_relative_l2']=-1.
    with pytest.raises(ValueError):p.validate(r)


def test_unsafe_part_rejected(tmp_path):
    m=json.loads(MANIFEST.read_text());m['parts'][0]['name']='../escape'
    path=tmp_path/'bad.json';path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='unsafe'):load_probe(path)
