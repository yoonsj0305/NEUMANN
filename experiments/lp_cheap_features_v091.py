"""Target-free linear-cost observables; no optimization or least-squares fit."""
import numpy as np
from neumann1.lp_portfolio_v084 import normalized


def features(A, b, c):
    D, b, q = normalized(A, b, c)
    m, n = D.shape
    cscale = max(1., float(np.sqrt(np.mean(q*q))))
    bscale = max(1., float(np.linalg.norm(b)))
    cols = np.column_stack((q/cscale, (q-q.mean())/cscale,
        D.T@b/bscale, D.mean(0), np.abs(D).mean(0),
        D.max(0), D.min(0), np.full(n, m/n)))
    rows = np.column_stack((b/bscale, D@q/max(1., float(np.linalg.norm(q))),
        D.mean(1), np.abs(D).mean(1), np.sqrt(np.mean(D*D, axis=1)),
        np.ones(m), np.full(m, m/n), np.ones(m)))
    if not np.isfinite(cols).all() or not np.isfinite(rows).all():
        raise ValueError('non-finite cheap features')
    return D, rows, cols
