import pytest
torch=pytest.importorskip('torch')
from experiments.lp_state_models_v087 import GraphStateModel,PointwiseModel
from experiments.lp_input_compaction_v094 import propose


def test_real_input_state_and_edge_removal_same_weights():
    torch.manual_seed(94001);m,n=4,64
    A,rows,cols=torch.randn(m,n),torch.randn(m,8),torch.randn(n,8)
    point,full=PointwiseModel(16).eval(),GraphStateModel(16,False).eval()
    seen=[]
    hook=full.register_forward_pre_hook(lambda module,args:seen.append(tuple(args[0].shape)))
    with torch.inference_mode():
        small=propose(A,rows,cols,point,full,True)
        direct=propose(A,rows,cols,point,full,False)
        only=propose(A,rows,cols,point,None,False)
    hook.remove()
    assert seen==[(m,2*m),(m,n)]
    assert small['state_columns']==2*m and direct['state_columns']==n
    assert small['edge_multiply_terms']==direct['edge_multiply_terms']/8
    assert set(small['basis']).issubset(small['selected'])
    assert set(small['shortlist'])==set(only['shortlist'])
    assert len(set(small['basis']))==m


def test_nonfinite_selector_fails_closed():
    p=PointwiseModel(16);p.head.bias.data.fill_(float('nan'))
    with pytest.raises(ValueError,match='selector'):
        propose(torch.ones(2,32),torch.ones(2,8),torch.ones(32,8),p,None,False)


def test_frozen_gate_requires_both_seeds_and_rejects_duplicates():
    from experiments.lp_input_probe_v094 import summarize,ROUTES
    import copy
    reference={'summary':{'routes':{f'v088_exact_point16_s{s}':
        {'shortlist_covers':46,'basis_certified':0} for s in (87001,87002)}}}
    records=[{'case_id':f'train{i}','route':route,'shortlist_covers':i<46,
        'candidate':{'accepted':False},'edge_multiply_terms':1 if route.startswith('compact') else 8}
        for i in range(48) for route in ROUTES]
    result=summarize(records,reference)
    assert all(t['passed'] for t in result['tests'])
    for row in records:
        if row['route']=='point_s87001' and row['case_id'] in ('train44','train45'):
            row['shortlist_covers']=False
    assert summarize(records,reference)['decision']=='STOP_FROZEN_INPUT_COMPACTION_NO_NEW_FIT'
    with pytest.raises(ValueError,match='coverage'):
        summarize(records+[copy.deepcopy(records[0])],reference)


def test_cost_gate_protects_point_only_direct():
    from experiments.lp_input_cost_v094 import ROUTES,summarize
    sources=[{'id':f'train{i}'} for i in range(16)]
    records=[{'case_id':s['id'],'route':r,'repeat':i,'accepted':True,
        'total_ms':1. if 'point' in r else 2. if 'compact' in r else 4.,
        'candidate':{'accepted':True},'execution':None}
        for s in sources for r in ROUTES for i in (-1,0,1,2)]
    result=summarize(records,sources,0.)
    assert all(t['ratios'][3]==2. for t in result['tests'])
    assert not any(t['passed'] for t in result['tests'])
    assert result['decision']=='STOP_FROZEN_INPUT_COMPACTION_COST_CANDIDATE'
    assert result['global_q3']==result['global_q4']=='OPEN'
