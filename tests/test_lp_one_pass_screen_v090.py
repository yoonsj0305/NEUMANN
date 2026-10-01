import inspect
from unittest.mock import patch
import pytest
pytest.importorskip('torch')
from experiments import lp_one_pass_screen_v090 as p


def fixture():
    sources=[{'id':f'train{i}'} for i in range(16)]
    rows=[{'case_id':s['id'],'route':route,'repeat':repeat,'accepted':True,
           'total_ms':2. if route.startswith('early_compact') else 10.,
           'execution':{'subset_accepted':True}}
          for s in sources for route in p.ROUTES for repeat in (-1,0,1,2)]
    training={r:{'fit_ms':1000.} for r in p.previous.old.LEARNERS}
    parity=[{'case_id':s['id'],'seed':seed,'early':[0,1],'retained':[0,1]}
            for s in sources for seed in p.previous.old.SEEDS]
    return rows,sources,training,1000.,parity


def test_shared_advisory_api_and_bounded_screen_scope():
    assert list(inspect.signature(p.observe).parameters)==['raw','model']
    assert len(p.ROUTES)==28
    result=p.summarize(*fixture())
    assert result['decision']=='ADMIT_NEW_EXECUTOR_HOLDOUT_NOT_Q3_Q4'
    assert result['global_q3']==result['global_q4']=='OPEN'


@pytest.mark.parametrize('fault',['cheap_direct','cheap_classic','no_saving','rescue','amortization','capability','parity'])
def test_closed_thresholds_reject_faults(fault):
    rows,sources,training,setup,parity=fixture()
    if fault=='cheap_direct':
        for r in rows:
            if r['route'].startswith('early_point16'):r['total_ms']=1.
    if fault=='cheap_classic':
        for r in rows:
            if r['route']=='short_centred_thin':r['total_ms']=1.
    if fault=='no_saving':
        for r in rows:
            if r['route'].startswith('early_compact'):r['total_ms']=9.
    if fault=='rescue':
        for r in rows:
            if r['route'].startswith('early_compact'):r['execution']['subset_accepted']=False
    if fault=='amortization':
        for fit in training.values():fit['fit_ms']=1e8
    if fault=='capability':rows[0]['accepted']=False
    if fault=='parity':parity[0]['early']=[2,3]
    assert p.summarize(rows,sources,training,setup,parity)['decision'] in (
        'STOP_ONE_PASS_CANDIDATE','CAPABILITY_UNREACHED','RETAINED_SET_PARITY_FAILED')


def test_missing_observation_or_duplicate_parity_refused():
    rows,sources,training,setup,parity=fixture()
    with pytest.raises(ValueError,match='coverage'):p.summarize(rows[:-1],sources,training,setup,parity)
    parity[0]=parity[1]
    with pytest.raises(ValueError,match='coverage'):p.summarize(rows,sources,training,setup,parity)


def test_first_runner_refuses_overwriting(tmp_path):
    import benchmark_v090
    with patch('sys.argv',['benchmark_v090.py',str(tmp_path)]), \
         patch.object(p,'run',side_effect=AssertionError('timing forbidden')):
        with pytest.raises(SystemExit):benchmark_v090.main()


def test_retained_screen_replay_does_not_time_fit_solve_or_generate():
    from neumann1.lp_one_pass_archive_v090 import load_screen
    report=load_screen('docs/experiments/results/v090_first_screen.manifest.json')
    with patch.object(p,'restore_models',side_effect=AssertionError('inference forbidden')), \
         patch.object(p,'observe',side_effect=AssertionError('timing forbidden')), \
         patch.object(p.previous.old,'generate',side_effect=AssertionError('generation forbidden')):
        p.validate(report)
        assert len(report['records'])==1792
        assert report['summary']['decision']=='STOP_ONE_PASS_CANDIDATE'
        row=report['records'][0];old=row['witness']['x'][0];row['witness']['x'][0]+=100.
        with pytest.raises(ValueError,match='witness'):p.validate(report)
        row['witness']['x'][0]=old
        old=report['training_fit_ms']['compact16_s87001'];report['training_fit_ms']['compact16_s87001']+=1.
        with pytest.raises(ValueError,match='fit'):p.validate(report)
        report['training_fit_ms']['compact16_s87001']=old
        old=report['summary']['decision'];report['summary']['decision']='FAKE_PASS'
        with pytest.raises(ValueError,match='summary'):p.validate(report)
        report['summary']['decision']=old


def test_archive_part_identity_rejected(tmp_path):
    import hashlib,json
    from neumann1.lp_one_pass_archive_v090 import load_screen
    data=b'fixture';(tmp_path/'part').write_bytes(data)
    part={'name':'part','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    m={'format':'neumann.lp-one-pass-screen.archive.v1',
       'preregistration_head':'905deacd02fefc9bd06dc4bf94216d81b6da2510','rerun':False,'parts':[part,part]}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='duplicate'):load_screen(path)
    m['parts']=[{**part,'sha256':'0'*64}];path.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='integrity'):load_screen(path)
