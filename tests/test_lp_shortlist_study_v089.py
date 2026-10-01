import inspect
from unittest.mock import patch
import pytest
pytest.importorskip('torch')
from experiments import lp_shortlist_study_v089 as p


def fixtures():
    sources=p.specs()
    rows=[{'case_id':s['id'],'route':route,'repeat':repeat,'accepted':True,
           'total_ms':2. if route.startswith('compact16') else 10.,
           'execution':{'subset_accepted':True},'answer':None}
           for s in sources for route in p.ROUTES for repeat in (-1,0,1,2)]
    return rows,sources,{r:{'fit_ms':1000.} for r in p.old.LEARNERS}


def test_new_split_and_equal_execution_authority():
    assert len(p.ROUTES)==20
    assert not {s['seed'] for s in p.specs()} & {s['seed'] for s in p.old.specs('final')+p.old.specs('train')}
    assert list(inspect.signature(p.observe).parameters)==['raw','route','model']
    assert p.protocol()['new_fitting'] is False


def test_bounded_pass_is_not_global_closure():
    rows,sources,training=fixtures(); result=p.summarize(rows,sources,training,1000.)
    assert result['decision']=='BOUNDED_SHORTLIST_ROSTER_PASS_NOT_GLOBAL_Q3_Q4'
    assert result['global_q3']==result['global_q4']=='OPEN'


@pytest.mark.parametrize('fault',['cheap_classic','cheap_direct','slow','fallback','amortization','capability','coverage'])
def test_gate_cannot_be_weakened(fault):
    rows,sources,training=fixtures()
    for row in rows:
        if fault=='cheap_classic' and row['route']=='short_centred_thin': row['total_ms']=1.
        if fault=='cheap_direct' and row['route'].startswith('point16'): row['total_ms']=1.
        if fault=='slow' and row['route'].startswith('compact16'): row['total_ms']=9.
        if fault=='fallback' and row['route'].startswith('compact16'): row['execution']['subset_accepted']=False
    if fault=='amortization':
        for fit in training.values(): fit['fit_ms']=1e8
    if fault=='capability': rows[0]['accepted']=False
    if fault=='coverage':
        with pytest.raises(ValueError): p.summarize(rows[:-1],sources,training,1000.)
        return
    assert p.summarize(rows,sources,training,1000.)['decision'] in ('FROZEN_CHECKPOINT_SHORTLIST_GATE_FAILED','CAPABILITY_UNREACHED')


def test_first_runner_refuses_overwrite(tmp_path):
    import benchmark_v089 as runner
    with patch('sys.argv',['benchmark_v089.py',str(tmp_path)]), \
         patch.object(p,'run_study',side_effect=AssertionError('final forbidden')):
        with pytest.raises(SystemExit): runner.main()


def test_retained_first_shortlist_replay_never_executes_model_or_solver():
    from neumann1.lp_shortlist_archive_v089 import load_study
    report=load_study('docs/experiments/results/v089_completed.manifest.json')
    with patch.object(p.old,'generate',side_effect=AssertionError('final generation forbidden')), \
         patch.object(p,'restore_models',side_effect=AssertionError('model execution forbidden')), \
         patch.object(p,'solve_shortlist_checked',side_effect=AssertionError('solver forbidden')):
        p.validate_report(report)
        assert len(report['records'])==960
        assert report['summary']['global_q3']==report['summary']['global_q4']=='OPEN'
        row=next(r for r in report['records'] if r['accepted'])
        old=row['witness']['x'][0]; row['witness']['x'][0]=old+100.
        with pytest.raises(ValueError,match='witness'): p.validate_report(report)
        row['witness']['x'][0]=old
        old=report['training_setup_ms'];report['training_setup_ms']+=1.
        with pytest.raises(ValueError,match='training'): p.validate_report(report)
        report['training_setup_ms']=old
        old=report['summary']['decision'];report['summary']['decision']='FAKE_PASS'
        with pytest.raises(ValueError,match='summary'): p.validate_report(report)
        report['summary']['decision']=old


def test_shortlist_archive_duplicate_parts_rejected(tmp_path):
    import hashlib,json
    from neumann1.lp_shortlist_archive_v089 import load_study
    data=b'fixture';(tmp_path/'part').write_bytes(data)
    part={'name':'part','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    manifest={'format':'neumann.lp-shortlist-study.archive.v1',
              'preregistration_head':'b2e73ef6410adb07bebef484e2ba5299163cdaa1',
              'rerun':False,'parts':[part,part]}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='duplicate'):load_study(path)
