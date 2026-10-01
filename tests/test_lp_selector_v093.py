import copy
import numpy as np
import pytest
pytest.importorskip('torch')
from experiments import lp_feature_probe_v093 as f
from experiments import lp_selector_probe_v093 as p


def raw():
    rng=np.random.default_rng(93001)
    return dict(A=rng.normal(size=(4,64)),b=rng.normal(size=4),c=rng.normal(size=64))


def test_cg_spd_and_curvature_fail_closed():
    G=np.diag([1.,2.,4.]);rhs=np.array([1.,2.,3.])
    np.testing.assert_allclose(f.cg(lambda x:G@x,rhs,3),np.linalg.solve(G,rhs),atol=1e-12)
    with pytest.raises(np.linalg.LinAlgError):f.cg(lambda x:-x,rhs,3)
    with pytest.raises(np.linalg.LinAlgError):f.cg(lambda x:x*np.nan,rhs,3)


def test_gram_matches_qr_and_singular_is_not_repaired():
    r=raw();D,b,q=f.normalized(**r);ix=np.arange(len(q))
    a=f.dual_fit(D,q,ix,'qr');z=f.dual_fit(D,q,ix,'gram')
    np.testing.assert_allclose(a[0],z[0],atol=1e-12)
    assert a[1]==pytest.approx(z[1],abs=1e-12)
    with pytest.raises(np.linalg.LinAlgError):f.dual_fit(np.ones((4,64)),q,ix,'gram')


def test_approximate_slots_rows_and_no_lstsq(monkeypatch):
    r=raw();exact=p.prior.previous.admission.features(**r)
    monkeypatch.setattr(f,'lstsq',lambda *a,**k:pytest.fail('unregistered least squares'))
    approx=f.approximate_features(r)
    assert [x.shape for x in approx]==[(4,64),(4,8),(64,8)]
    np.testing.assert_allclose(approx[0],exact[0],atol=0,rtol=0)
    np.testing.assert_allclose(approx[1],exact[1],atol=0,rtol=0)
    np.testing.assert_allclose(approx[2][:,[0,3,4,5,6,7]],exact[2][:,[0,3,4,5,6,7]],atol=0,rtol=0)
    for policy in f.POLICIES[1:]:
        basis,short=f.indices(r,policy)
        assert len(basis)==4 and len(short)==8 and set(basis).issubset(short)


def test_positive_scaling_and_permutation_equivariance():
    r=raw();rng=np.random.default_rng(9);scale=np.exp(rng.normal(size=64));perm=rng.permutation(64)
    scaled=dict(A=r['A']*scale,c=r['c']*scale,b=r['b'])
    moved=dict(A=r['A'][:,perm],c=r['c'][perm],b=r['b'])
    for policy in f.POLICIES:
        basis,short=f.indices(r,policy)
        assert f.indices(scaled,policy)==(basis,short)
        mb,ms=f.indices(moved,policy)
        assert perm[mb].tolist()==basis and perm[ms].tolist()==short


def records():
    return [dict(case_id=f'train{i}',route=route,candidate={'accepted':False},
        basis_covers=False,shortlist_covers=False,coarse_covers=None)
        for i in range(48) for route in p.ROUTES]


def test_no_parity_no_fit_and_duplicate_fail_closed():
    rows=records();result=p.summarize(rows)
    assert result['decision']=='SELECTOR_GAP_UNRESOLVED_NO_NEW_FIT'
    assert not result['cost_claim'] and result['global_q3']==result['global_q4']=='OPEN'
    rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(ValueError,match='coverage'):p.summarize(rows)


def test_both_point_seeds_and_classical_priority():
    rows=records()
    for row in rows:
        if 'point16' in row['route'] and row['route'].startswith(('v088_exact_','v088_cg3_')):
            row['shortlist_covers']=int(row['case_id'][5:])<36
    assert p.summarize(rows)['decision']=='ADMIT_PREREGISTERED_CG3_POINT_COST_SCREEN_NOT_Q3_Q4'
    for row in rows:
        if row['route']=='qr_affine':row['shortlist_covers']=True
    assert p.summarize(rows)['decision']=='CHEAP_SHORTLIST_NEAR_SATURATION_DIAGNOSTIC_ONLY'
    for row in rows:
        if row['route']=='gram_trim':row['candidate']['accepted']=True
    assert p.summarize(rows)['decision']=='CHEAP_CERTIFICATE_NEAR_SATURATION_DIAGNOSTIC_ONLY'


def test_point_parity_tolerates_only_one_loss():
    rows=records()
    for row in rows:
        if row['route'].startswith('v088_exact_point16'):row['shortlist_covers']=True
        if row['route'].startswith('v088_cg3_point16'):row['shortlist_covers']=int(row['case_id'][5:])<47
    assert all(x['passed'] for x in p.summarize(rows)['point_parity'])
    for row in rows:
        if row['route']=='v088_cg3_point16_s87002' and row['case_id']=='train46':row['shortlist_covers']=False
    assert p.summarize(rows)['decision']=='SELECTOR_GAP_UNRESOLVED_NO_NEW_FIT'
