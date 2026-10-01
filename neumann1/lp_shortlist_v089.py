"""Shared restricted-LP execution, accepted only against the full original LP."""
import math
from time import perf_counter_ns

import numpy as np

from .lp_certificate_v081 import verify_standard_form_certificate
from .lp_native_warm_start_v086 import solve_native_checked, _raw


def solve_shortlist_checked(A, b, c, indices, *, budget_s=5.):
    started = perf_counter_ns()
    if type(budget_s) not in (int, float) or not math.isfinite(budget_s) or budget_s <= 0:
        raise ValueError('positive finite budget required')
    A, b, c = _raw(A, b, c)
    m, n = A.shape
    valid = (type(indices) is list and m <= len(indices) <= n
             and all(type(i) is int and 0 <= i < n for i in indices)
             and len(set(indices)) == len(indices))
    restricted = original_certificate = witness = fallback = None
    remaining = lambda: budget_s - (perf_counter_ns()-started)/1e9
    if valid and remaining() > 0:
        restricted = solve_native_checked(A[:, indices], b, c[indices], budget_s=remaining())
        if restricted['accepted']:
            small = restricted['attempts'][-1]['witness']
            x = np.zeros(n)
            x[indices] = small['x']
            witness = {'x': x.tolist(), 'y': small['y']}
            # A feasible reduced optimum is NOT necessarily an original optimum.
            original_certificate = verify_standard_form_certificate(A, b, c, **witness)
    subset_accepted = bool(original_certificate and original_certificate['accepted'])
    if not subset_accepted and remaining() > 0:
        fallback = solve_native_checked(A, b, c, budget_s=remaining())
        if fallback['accepted']:
            witness = fallback['attempts'][-1]['witness']
    elapsed = (perf_counter_ns()-started)/1e6
    return {'accepted': bool((subset_accepted or fallback and fallback['accepted'])
                             and elapsed <= budget_s*1000.),
            'valid_shortlist': valid, 'indices': indices, 'restricted': restricted,
            'original_certificate': original_certificate, 'subset_accepted': subset_accepted,
            'fallback': fallback, 'fallback_used': fallback is not None,
            'witness': witness, 'total_ms': elapsed, 'budget_s': budget_s}
