import copy
from pathlib import Path
from unittest.mock import patch
import pytest
pytest.importorskip('torch')
from experiments import lp_cheap_screen_v091 as p
from neumann1.lp_cheap_archive_v091 import load_screen

MANIFEST=Path('docs/experiments/results/v091_first_screen.manifest.json')


@pytest.fixture(scope='module')
def report():return load_screen(MANIFEST)


def test_retained_first_fit_replay_without_models_or_solvers(report):
    with (patch.object(p.old,'fit_one',side_effect=AssertionError('no fitting')),
         patch.object(p,'solve_shortlist_checked',side_effect=AssertionError('no solver')),
         patch('experiments.lp_state_models_v087.GraphStateModel.forward',side_effect=AssertionError('no inference')),
         patch('experiments.lp_state_models_v087.PointwiseModel.forward',side_effect=AssertionError('no inference')),
         patch.object(p.old,'generate',side_effect=AssertionError('no generation'))):
        p.validate(report)
    assert len(report['records'])==1408
    assert all(r['accepted'] for r in report['records'])
    assert report['summary']['decision']=='STOP_CHEAP_FEATURE_CANDIDATE'
    assert all(t['no_full_rescue_cases']==0 and not t['passed'] for t in report['summary']['tests'])


@pytest.mark.parametrize('field',['summary','sources','training','witness','ledger','state'])
def test_corrupt_retained_evidence_rejected(report,field):
    r=copy.deepcopy(report)
    if field=='summary':r['summary']['decision']='ADMIT_PREREGISTERED_HOLDOUT_NOT_Q3_Q4'
    elif field=='sources':r['sources'][0]['seed']+=1
    elif field=='training':r['training']['compact16_s87001']['fit_ms']=0.
    elif field=='witness':r['records'][0]['witness']['x']=[0.]*len(r['records'][0]['witness']['x'])
    elif field=='ledger':
        row=next(x for x in r['records'] if x.get('execution'));row['total_ms']=.000001
    elif field=='state':
        row=next(x for x in r['records'] if x['route'].startswith('compact16'));row['state_columns']+=1
    with pytest.raises(ValueError):p.validate(r)


def test_archive_unsafe_part_name(tmp_path):
    import json
    m=json.loads(MANIFEST.read_text());m['parts'][0]['name']='../outside'
    path=tmp_path/'bad.json';path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='unsafe'):load_screen(path)
