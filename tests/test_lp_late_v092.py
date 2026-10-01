import copy,inspect
import numpy as np
import pytest
torch=pytest.importorskip('torch')
from experiments.lp_late_models_v092 import roster,LateGraphStateModel
from experiments.lp_state_models_v087 import tensor_input
from experiments.lp_cheap_features_v091 import features
from experiments import lp_late_screen_v092 as p


def test_same_parameters_two_full_updates_before_selection():
    models=roster(87001);compact,full=models['compact16'],models['full16']
    assert sum(v.numel() for v in compact.parameters())==5156
    assert all(torch.equal(v,full.state_dict()[k]) for k,v in compact.state_dict().items())
    rng=np.random.default_rng(24);m,n=5,80
    tensors=tensor_input(*features(rng.normal(size=(m,n)),rng.normal(size=m),rng.normal(size=n)))
    with torch.inference_mode():a,b=compact(*tensors),full(*tensors)
    torch.testing.assert_close(a['coarse'],b['coarse'],rtol=0,atol=0)
    assert a['state_columns']==2*m and b['state_columns']==n
    assert a['edge_multiply_terms']==m*n*16*4+m*(2*m)*16*2
    assert b['edge_multiply_terms']==m*n*16*6
    assert a['selected'].tolist()==torch.argsort(a['coarse'],descending=True,stable=True)[:2*m].tolist()
    assert all(a['scores'][i]==-1e6 for i in set(range(n))-set(a['selected'].tolist()))


def test_no_pruning_boundary_and_target_free_interface():
    models=roster(87002);rng=np.random.default_rng(32);m,n=5,5
    tensors=tensor_input(*features(rng.normal(size=(m,n)),rng.normal(size=m),rng.normal(size=n)))
    with torch.inference_mode():a,b=models['compact16'](*tensors),models['full16'](*tensors)
    torch.testing.assert_close(a['scores'],b['scores'],atol=1e-6,rtol=1e-6)
    assert list(inspect.signature(LateGraphStateModel.forward).parameters)==['self','matrix','row_features','col_features']


def fixture():
    sources=[{'id':f'train{i}'} for i in range(16)]
    records=[{'case_id':s['id'],'route':route,'repeat':i,'accepted':True,
        'total_ms':2. if route.startswith('compact16') else 10.,'execution':{'subset_accepted':True}}
        for s in sources for route in p.ROUTES for i in (-1,0,1,2)]
    return records,sources,1000.


def test_old_direct_protected_and_training_wall_paid():
    args=fixture();assert p.summarize(*args)['decision']=='ADMIT_NEW_HOLDOUT_NOT_Q3_Q4'
    for row in args[0]:
        if row['route']=='v091_full16_s87001':row['total_ms']=1.
    assert p.summarize(*args)['decision']=='STOP_LATE_PRUNING_CANDIDATE'
    args=fixture();assert p.summarize(args[0],args[1],100000.)['decision']=='STOP_LATE_PRUNING_CANDIDATE'


def test_coverage_capability_and_rescue_fail_closed():
    args=fixture();args[0][0]['accepted']=False
    assert p.summarize(*args)['decision']=='CAPABILITY_UNREACHED'
    args[0].append(copy.deepcopy(args[0][0]))
    with pytest.raises(ValueError,match='coverage'):p.summarize(*args)
    args=fixture()
    for row in args[0]:
        if row['route'].startswith('compact16'):row['execution']['subset_accepted']=False
    assert p.summarize(*args)['decision']=='STOP_LATE_PRUNING_CANDIDATE'
    assert len(p.ROUTES)*16*4==1920
