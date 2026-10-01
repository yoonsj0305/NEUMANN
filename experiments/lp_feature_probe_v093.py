"""Observable-only linear-algebra controls; all proposals remain advisory."""
import numpy as np
from scipy.linalg import cho_factor,cho_solve,lstsq,LinAlgError
from neumann1.lp_portfolio_v084 import normalized

POLICIES=('qr_affine','gram_affine','gram_trim','cg3_affine','cg5_affine','cg3_primal')


def cg(apply,rhs,steps):
    x=np.zeros_like(rhs);r=rhs.copy();p=r.copy();rr=float(r@r)
    initial=rr
    for _ in range(steps):
        if rr<=max(1e-28,initial*1e-24):break
        Ap=apply(p);curvature=float(p@Ap)
        if not np.isfinite(curvature) or curvature<=0:raise LinAlgError('nonpositive CG curvature')
        alpha=rr/curvature;x+=alpha*p;r-=alpha*Ap
        new=float(r@r);p=r+(new/rr)*p;rr=new
    if not np.isfinite(x).all():raise LinAlgError('nonfinite CG output')
    return x


def dual_fit(D,q,indices,method,steps=3):
    E=D[:,indices];v=q[indices];mean=E.mean(1);center=E-mean[:,None]
    rhs=center@(v-v.mean())
    if method=='qr':
        fitted=lstsq(np.column_stack((E.T,np.ones(E.shape[1]))),v,cond=1e-12,
            lapack_driver='gelsy',check_finite=False)[0]
        return fitted[:-1],float(fitted[-1])
    if method=='gram':
        G=center@center.T
        y=cho_solve(cho_factor(G,check_finite=False),rhs,check_finite=False)
    elif method=='cg':y=cg(lambda x:center@(center.T@x),rhs,steps)
    else:raise ValueError('unregistered fit')
    return y,float(v.mean()-mean@y)


def indices(raw,policy):
    if policy not in POLICIES:raise ValueError('unregistered observable policy')
    D,b,q=normalized(**raw);m,n=D.shape
    if policy=='cg3_primal':
        z=cg(lambda x:D@(D.T@x),b,3);score=-(D.T@z)
    else:
        selected=np.arange(n)
        schedule=(n,max(m+1,n//2),max(m+1,n//4),max(m+1,n//8)) if policy=='gram_trim' else (n,)
        for keep in schedule:
            selected=selected[:min(n,keep)]
            method='qr' if policy=='qr_affine' else 'cg' if policy.startswith('cg') else 'gram'
            y,a=dual_fit(D,q,selected,method,5 if policy=='cg5_affine' else 3)
            score=q-D.T@y-a;selected=np.argsort(score,kind='stable')
    if not np.isfinite(score).all():raise LinAlgError('nonfinite advisory scores')
    order=np.argsort(score,kind='stable')
    return order[:m].tolist(),order[:min(n,2*m)].tolist()


def approximate_features(raw):
    """v087 feature slots, but BOTH linear solves use fixed three-step CG."""
    D,b,q=normalized(**raw);m,n=D.shape
    y,a=dual_fit(D,q,np.arange(n),'cg',3)
    z=cg(lambda x:D@(D.T@x),b,3)
    cscale=max(1.,float(np.sqrt(np.mean(q*q))));bscale=max(1.,float(np.linalg.norm(b)))
    cols=np.column_stack((q/cscale,(q-D.T@y-a)/cscale,(D.T@z)/bscale,
        D.T@b/bscale,D.mean(0),np.abs(D).mean(0),np.full(n,m/n),np.ones(n)))
    rows=np.column_stack((b/bscale,D@q/max(1.,float(np.linalg.norm(q))),
        D.mean(1),np.abs(D).mean(1),np.sqrt(np.mean(D*D,axis=1)),
        np.ones(m),np.full(m,m/n),np.ones(m)))
    if not np.isfinite(cols).all() or not np.isfinite(rows).all():raise ValueError('nonfinite approximate features')
    return D,rows,cols
