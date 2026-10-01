import json
import pytest
pytest.importorskip('torch')
from experiments.lp_graph_incremental_v095 import analyze,protocol,summarize
from neumann1.lp_input_archive_v094 import load_archive
from experiments import lp_input_probe_v094 as prior


def test_frozen_v095_incremental_value_first_replay():
    result=analyze()
    assert result['protocol']==protocol()
    assert result['decision'] in {
        'STOP_GRAPH_REFINEMENT_INFORMATION_CANDIDATE',
        'ADMIT_CLEAN_GRAPH_REFINEMENT_COST_PROTOCOL_NOT_Q3_Q4',
    }
    assert len(result['tests'])==2
    assert all(t['identical_retained_sets']==48 for t in result['tests'])
    assert all(t['hit_wins']+t['hit_losses']+t['hit_ties']==48 for t in result['tests'])
    assert result['global_q3']==result['global_q4']=='OPEN'
    print('V095_FIRST_REPLAY='+json.dumps(result,separators=(',',':')))


def test_gate_is_conjunctive_and_cannot_pass_on_recall_alone():
    probe=load_archive('docs/experiments/results/v094_first_probe.manifest.json')
    prior.validate(probe)
    original,_=prior.parents()
    result=summarize(probe,original['train_sources'])
    for t in result['tests']:
        expected=(t['certificate_gain']>=4 and t['mean_label_recall_gain']>=0.05
            and t['hit_wins']>=12 and t['hit_losses']<=6
            and t['identical_retained_sets']==48)
        assert t['passed'] is expected
