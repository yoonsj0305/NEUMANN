import copy,json
from pathlib import Path
from unittest.mock import patch
import pytest
pytest.importorskip('torch')
from experiments import lp_late_screen_v092 as p
from neumann1.lp_late_archive_v092 import load_screen

MANIFEST=Path('docs/experiments/results/v092_first_screen.manifest.json')


@pytest.fixture(scope='module')
def report():return load_screen(MANIFEST)


def test_first_late_screen_replay_without_execution(report):
    with (patch.object(p.prior.old,'fit_one',side_effect=AssertionError('no fitting')),
        patch.object(p.prior,'solve_shortlist_checked',side_effect=AssertionError('no solver')),
        patch.object(p.prior.old,'generate',side_effect=AssertionError('no generation')),
        patch('experiments.lp_late_models_v092.LateGraphStateModel.forward',side_effect=AssertionError('no inference')),
        patch('experiments.lp_state_models_v087.GraphStateModel.forward',side_effect=AssertionError('no inference')),
        patch('experiments.lp_state_models_v087.PointwiseModel.forward',side_effect=AssertionError('no inference'))):
        p.validate(report)
    assert len(report['records'])==1920 and all(r['accepted'] for r in report['records'])
    assert report['summary']['decision']=='STOP_LATE_PRUNING_CANDIDATE'
    assert [t['no_full_rescue_cases'] for t in report['summary']['tests']]==[2,0]


@pytest.mark.parametrize('field',['protocol','source','wall','checkpoint','edge','witness','verdict'])
def test_corrupt_evidence_rejected(report,field):
    r=copy.deepcopy(report)
    if field=='protocol':r['protocol']['minimum_wins']=0
    elif field=='source':r['sources'][0]['seed']+=1
    elif field=='wall':r['training_phase_ms']=1.
    elif field=='checkpoint':r['training']['compact16_s87001']['weights_sha256']='0'*64
    elif field=='edge':
        row=next(x for x in r['records'] if x['route']=='compact16_s87001');row['edge_multiply_terms']+=1
    elif field=='witness':r['records'][0]['witness']['x']=[0.]*len(r['records'][0]['witness']['x'])
    elif field=='verdict':r['summary']['decision']='ADMIT_NEW_HOLDOUT_NOT_Q3_Q4'
    with pytest.raises(ValueError):p.validate(r)


def test_unsafe_archive_part_rejected(tmp_path):
    m=json.loads(MANIFEST.read_text());m['parts'][0]['name']='../escape'
    path=tmp_path/'bad.json';path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='unsafe'):load_screen(path)
