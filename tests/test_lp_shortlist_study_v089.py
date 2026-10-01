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
