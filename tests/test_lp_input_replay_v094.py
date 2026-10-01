import copy,json
from unittest.mock import patch
from pathlib import Path
import pytest
pytest.importorskip('torch')
from experiments import lp_input_probe_v094 as p,lp_input_cost_v094 as c
from neumann1.lp_input_archive_v094 import load_archive


def test_first_probe_and_cost_replay_without_execution():
    probe=load_archive('docs/experiments/results/v094_first_probe.manifest.json')
    cost=load_archive('docs/experiments/results/v094_first_cost.manifest.json')
    with (patch.object(p,'features',side_effect=AssertionError('no features')),
        patch.object(p,'propose',side_effect=AssertionError('no inference')),
        patch.object(c,'observe',side_effect=AssertionError('no execution')),
        patch.object(c,'solve_shortlist_checked',side_effect=AssertionError('no optimizer')),
        patch.object(c.old.old,'fit_one',side_effect=AssertionError('no fit'))):
        p.validate(probe);c.validate(cost)
    assert len(probe['records'])==288
    assert all(t['passed'] for t in probe['summary']['tests'])
    assert len(cost['records'])==1984 and all(r['accepted'] for r in cost['records'])
    assert not any(t['passed'] for t in cost['summary']['tests'])
    assert cost['summary']['global_q3']==cost['summary']['global_q4']=='OPEN'
    bad=copy.deepcopy(probe);bad['records'][0]['edge_multiply_terms']+=1
    with pytest.raises(ValueError,match='state'):p.validate(bad)
    bad=copy.deepcopy(cost);bad['summary']['tests'][0]['passed']=True
    with pytest.raises(ValueError,match='summary'):c.validate(bad)


def test_timing_confounded_archive_cannot_be_promoted(tmp_path):
    root=Path('docs/experiments/results');m=json.loads((root/'v094_first_cost.manifest.json').read_text())
    m['positive_cost_claim_allowed']=True
    for part in m['parts']:(tmp_path/part['name']).symlink_to((root/part['name']).resolve())
    path=tmp_path/'bad.json';path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='timing'):load_archive(path)
