import copy
import numpy as np
import pytest

torch=pytest.importorskip('torch')
from experiments.lp_cheap_features_v091 import features
from experiments.lp_cheap_screen_v091 import summarize, ROUTES, old, protocol


def test_no_least_squares_or_optimizer(monkeypatch):
    import scipy.linalg
    import scipy.optimize
    def forbidden(*args,**kwargs):raise AssertionError('forbidden feature solver')
    monkeypatch.setattr(np.linalg,'lstsq',forbidden)
    monkeypatch.setattr(scipy.linalg,'lstsq',forbidden)
    monkeypatch.setattr(scipy.optimize,'linprog',forbidden)
    rng=np.random.default_rng(19);A=rng.normal(size=(5,17));b=rng.normal(size=5);c=rng.normal(size=17)
    D,r,f=features(A,b,c)
    assert r.shape==(5,8) and f.shape==(17,8)
    np.testing.assert_allclose(f[:,2],D.T@b/max(1,np.linalg.norm(b)))
    assert np.isfinite(r).all() and np.isfinite(f).all()


def test_column_permutation_and_positive_scaling():
    rng=np.random.default_rng(21);A=rng.normal(size=(7,31));b=rng.normal(size=7);c=rng.normal(size=31)
    D,r,f=features(A,b,c);p=rng.permutation(31);s=np.exp(rng.uniform(-2,2,size=31))
    E,u,g=features(A[:,p]*s,b,c[p]*s)
    np.testing.assert_allclose(E,D[:,p],atol=1e-14)
    np.testing.assert_allclose(u,r,atol=1e-14)
    np.testing.assert_allclose(g,f[p],atol=1e-14)


def fixture():
    sources=[{'id':f'train{i}'} for i in range(16)]
    records=[]
    for s in sources:
        for route in ROUTES:
            for repeat in (-1,0,1,2):
                records.append({'case_id':s['id'],'route':route,'repeat':repeat,
                    'accepted':True,'total_ms':2. if route.startswith('compact16') else 5.,
                    'execution':{'subset_accepted':True}})
    training={f'compact16_s{seed}':{'fit_ms':100.} for seed in old.SEEDS}
    return records,sources,training,10.


def test_complete_paired_gate_and_strong_direct():
    args=fixture();result=summarize(*args)
    assert result['decision']=='ADMIT_PREREGISTERED_HOLDOUT_NOT_Q3_Q4'
    assert result['global_q3']==result['global_q4']=='OPEN'
    for row in args[0]:
        if row['route']=='point16_s87002':row['total_ms']=1.
    assert summarize(*args)['decision']=='STOP_CHEAP_FEATURE_CANDIDATE'


def test_coverage_duplicate_and_failed_capability():
    args=fixture();args[0][0]['accepted']=False
    assert summarize(*args)['decision']=='CAPABILITY_UNREACHED'
    args[0].append(copy.deepcopy(args[0][0]))
    with pytest.raises(ValueError,match='coverage'):summarize(*args)


def test_rescue_and_paid_fit_cannot_be_ignored():
    args=fixture()
    for row in args[0]:
        if row['route'].startswith('compact16'):row['execution']['subset_accepted']=False
    assert summarize(*args)['decision']=='STOP_CHEAP_FEATURE_CANDIDATE'
    args=fixture()
    for t in args[2].values():t['fit_ms']=100000.
    assert summarize(*args)['decision']=='STOP_CHEAP_FEATURE_CANDIDATE'
    assert len(protocol()['routes'])*16*4==1408
