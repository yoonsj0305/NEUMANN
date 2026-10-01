"""Frozen selector transfer: graph states are removed before every message."""
import torch
from experiments import lp_feature_probe_v093 as f


def features(raw):
    # A separately frozen CG5 hypothesis, not a retry of the rejected CG3 gate.
    import numpy as np
    D,b,q=f.normalized(**raw);m,n=D.shape
    y,a=f.dual_fit(D,q,np.arange(n),'cg',5)
    z=f.cg(lambda x:D@(D.T@x),b,5)
    cs=max(1.,float(np.sqrt(np.mean(q*q))));bs=max(1.,float(np.linalg.norm(b)))
    cols=np.column_stack((q/cs,(q-D.T@y-a)/cs,(D.T@z)/bs,D.T@b/bs,
        D.mean(0),np.abs(D).mean(0),np.full(n,m/n),np.ones(n)))
    rows=np.column_stack((b/bs,D@q/max(1.,float(np.linalg.norm(q))),D.mean(1),
        np.abs(D).mean(1),np.sqrt(np.mean(D*D,axis=1)),np.ones(m),np.full(m,m/n),np.ones(m)))
    if not np.isfinite(cols).all() or not np.isfinite(rows).all():raise ValueError('nonfinite CG5 features')
    return D,rows,cols


def propose(matrix,rows,cols,point,full,compact):
    """No labels; point-only remains a required strong Direct comparator."""
    m,n=matrix.shape
    score=point.head(point.cols(cols)).squeeze(1)
    if not torch.isfinite(score).all():raise ValueError('nonfinite selector')
    selected=torch.argsort(score,descending=True,stable=True)[:min(n,2*m)]
    if full is None:
        order=torch.argsort(score,descending=True,stable=True)
        return {'basis':order[:m].tolist(),'shortlist':order[:2*m].tolist(),
            'selected':selected.tolist(),'state_columns':0,'edge_multiply_terms':0}
    keep=selected if compact else torch.arange(n,device=matrix.device)
    # Preserve original observable slots; do not recompute features on a subset.
    out=full(matrix[:,keep],rows,cols[keep]);scores=out['scores']
    if not torch.isfinite(scores).all():raise ValueError('nonfinite graph')
    ix=torch.argsort(scores,descending=True,stable=True)
    return {'basis':keep[ix[:m]].tolist(),'shortlist':keep[ix[:2*m]].tolist(),
        'selected':keep.tolist(),'state_columns':out['state_columns'],
        'edge_multiply_terms':out['edge_multiply_terms']}
