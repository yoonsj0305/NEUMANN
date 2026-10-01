"""Fixtures only: never train on experiment data or open final inputs in CI."""
import inspect
from unittest.mock import patch

import pytest
torch=pytest.importorskip('torch')
from experiments import lp_model_study_v088 as p


def fixtures():
    sources=p.specs('final')
    records=[]
    for s in sources:
        for route in p.ROUTES:
            for repeat in (-1,0,1,2):
                records.append({'case_id':s['id'],'route':route,'repeat':repeat,
                    'accepted':True,'total_ms':2. if route.startswith('compact16') else 10.,
                    'execution':{'candidate':{'accepted':True}}})
    training={r:{'fit_ms':1000.} for r in p.LEARNERS}
    return records,sources,training


def test_frozen_split_and_inference_information_boundary():
    train,final=p.specs('train'),p.specs('final')
    assert len(train)==48 and len(final)==12
    assert not {s['seed'] for s in train}&{s['seed'] for s in final}
    assert {s['rows'] for s in train}=={32,64}
    assert list(inspect.signature(p.learned_observe).parameters)==['A','b','c','model']
    assert list(inspect.signature(p.fit_one).parameters)==['model','data','seed','name']
    assert len(p.ROUTES)==16


def test_bounded_pass_still_cannot_close_global_questions():
    rows,sources,training=fixtures()
    result=p.summarize(rows,sources,training,1000.)
    assert result['decision']=='BOUNDED_CANDIDATE_ROSTER_PASS_NOT_GLOBAL_Q3_Q4'
    assert result['global_q3']==result['global_q4']=='OPEN'
    assert len(result['tests'])==4


@pytest.mark.parametrize('fault',['strong_direct','slow','basis','amortization','capability','coverage'])
def test_adversarial_candidate_gate(fault):
    rows,sources,training=fixtures()
    for r in rows:
        if fault=='strong_direct' and r['route'].startswith('point16'): r['total_ms']=1.
        if fault=='slow' and r['route'].startswith('compact16'): r['total_ms']=9.
        if fault=='basis' and r['route'].startswith('compact16'): r['execution']['candidate']['accepted']=False
    if fault=='amortization':
        for fit in training.values(): fit['fit_ms']=1e8
    if fault=='capability': rows[0]['accepted']=False
    if fault=='coverage':
        with pytest.raises(ValueError): p.summarize(rows[:-1],sources,training,1000.)
        return
    assert p.summarize(rows,sources,training,1000.)['decision'] in (
        'FIRST_LEARNED_CANDIDATE_GATE_FAILED','CAPABILITY_UNREACHED')


def test_compact_discrete_selection_has_supervised_coarse_gradients():
    model=p.roster()['compact16']
    output=model(torch.randn(2,32),torch.randn(2,8),torch.randn(32,8))
    objective=p.loss(output,torch.tensor([0,1]),torch.zeros(32),torch.zeros(2))
    objective.backward()
    assert model.coarse.weight.grad is not None
    assert torch.isfinite(model.coarse.weight.grad).all()


def test_first_runner_refuses_existing_directory(tmp_path):
    import benchmark_v088 as runner
    with patch('sys.argv',['benchmark_v088.py',str(tmp_path)]), \
         patch.object(p,'run_study',side_effect=AssertionError('first fitting forbidden')):
        with pytest.raises(SystemExit): runner.main()


def test_retained_first_study_replays_and_rejects_evidence_corruption():
    from pathlib import Path
    from neumann1.lp_model_study_archive_v088 import load_study
    report=load_study(Path(__file__).resolve().parents[1]/'docs/experiments/results/v088_completed.manifest.json')
    with patch.object(p,'generate',side_effect=AssertionError('no input regeneration')), \
         patch.object(p,'roster',side_effect=AssertionError('no model execution')), \
         patch.object(p.storage,'candidate_once',side_effect=AssertionError('no solve')):
        p.validate_report(report)
        assert len(report['records'])==768 and all(r['accepted'] for r in report['records'])
        assert report['summary']['decision']=='FIRST_LEARNED_CANDIDATE_GATE_FAILED'
        r=report['records'][0]; old=r['witness']['x'][0]; r['witness']['x'][0]=old+100.
        with pytest.raises(ValueError,match='witness'): p.validate_report(report)
        r['witness']['x'][0]=old
        fit=report['training']['compact16_s87001']; old=fit['weights_sha256'];fit['weights_sha256']='wrong'
        with pytest.raises(ValueError,match='checkpoint'): p.validate_report(report)
        fit['weights_sha256']=old
        old=report['summary']['tests'][0]['classical_ratio'];report['summary']['tests'][0]['classical_ratio']=0.
        with pytest.raises(ValueError,match='gate'): p.validate_report(report)
        report['summary']['tests'][0]['classical_ratio']=old


def test_archive_loader_rejects_duplicate_and_modified_parts(tmp_path):
    import hashlib,json
    from neumann1.lp_model_study_archive_v088 import load_study
    data=b'fixture';(tmp_path/'part').write_bytes(data)
    part={'name':'part','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    manifest={'format':'neumann.lp-first-model-study.archive.v1',
              'preregistration_head':'e3d7042d57b872ab61756c3b4103607c2f3e43cf','rerun':False,
              'parts':[part,part]}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='duplicate'): load_study(path)
    manifest['parts']=[part];path.write_text(json.dumps(manifest));(tmp_path/'part').write_bytes(b'broken')
    with pytest.raises(ValueError,match='part integrity'): load_study(path)
