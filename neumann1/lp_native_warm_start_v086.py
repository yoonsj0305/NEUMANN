"""Equal-authority native basis repair; an interface, not learning admission.

The supplied head is advisory. Only the original-LP certificate can accept
a result. No hidden basis, target answer or generator metadata is received.
"""
from __future__ import annotations

import math
from time import perf_counter_ns

import numpy as np
from scipy.sparse import csc_matrix

from .lp_certificate_v081 import verify_standard_form_certificate


def _raw(A, b, c):
    A, b, c = (np.asarray(v, dtype=np.float64) for v in (A, b, c))
    if (A.ndim != 2 or min(A.shape) <= 0 or b.shape != (A.shape[0],)
            or c.shape != (A.shape[1],)
            or not all(np.all(np.isfinite(v)) for v in (A, b, c))):
        raise ValueError('finite original standard-form LP required')
    return A, b, c


def decode_basis(head, rows, cols):
    if type(head) is dict and head == {'abstain': True} and type(head['abstain']) is bool:
        return 'ABSTAIN', None
    if (type(head) is not dict or set(head) != {'basis'}
            or type(head['basis']) is not list or len(head['basis']) != rows
            or any(type(i) is not int or i < 0 or i >= cols for i in head['basis'])
            or len(set(head['basis'])) != rows):
        return 'INVALID_HEAD', None
    return 'BASIS', head['basis']


def _check_status(status, highspy, operation):
    if status != highspy.HighsStatus.kOk:
        raise RuntimeError(f'{operation}: {status}')


def _attempt(A, b, c, indices, deadline_ns):
    import highspy  # Optional dependency; missing package is not a rejected LP.

    stages = []
    ledger = {'native_run_calls': 0, 'set_basis_calls': 0, 'certificate_calls': 0}
    witness, certificate, error, model_status, iterations = None, None, None, None, None

    def charge(name, function):
        start = perf_counter_ns()
        try:
            return function()
        finally:
            stages.append({'stage': name, 'ms': (perf_counter_ns() - start) / 1e6})

    try:
        def setup():
            h = highspy.Highs()
            for key, value in (('output_flag', False), ('threads', 1),
                               ('parallel', 'off'), ('solver', 'simplex'),
                               ('presolve', 'on'), ('random_seed', 0)):
                _check_status(h.setOptionValue(key, value), highspy, key)
            m, n = A.shape
            matrix = csc_matrix(A)
            lp = highspy.HighsLp()
            lp.num_col_, lp.num_row_ = n, m
            lp.col_cost_ = c
            lp.col_lower_, lp.col_upper_ = np.zeros(n), np.full(n, highspy.kHighsInf)
            lp.row_lower_, lp.row_upper_ = b, b
            lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
            lp.a_matrix_.start_ = matrix.indptr
            lp.a_matrix_.index_ = matrix.indices
            lp.a_matrix_.value_ = matrix.data
            _check_status(h.passModel(lp), highspy, 'passModel')
            return h

        h = charge('model_setup', setup)
        if indices is not None:
            def supply():
                basis = highspy.HighsBasis()
                selected = set(indices)
                basis.col_status = [highspy.HighsBasisStatus.kBasic if j in selected
                                    else highspy.HighsBasisStatus.kLower for j in range(A.shape[1])]
                # Equality-row logical variables are nonbasic at their fixed bounds.
                basis.row_status = [highspy.HighsBasisStatus.kLower] * A.shape[0]
                ledger['set_basis_calls'] += 1
                _check_status(h.setBasis(basis), highspy, 'setBasis')
            charge('basis_supply', supply)

        def solve():
            remaining = (deadline_ns - perf_counter_ns()) / 1e9
            if remaining <= 0:
                raise TimeoutError('complete-path budget exhausted before native run')
            _check_status(h.setOptionValue('time_limit', remaining), highspy, 'time_limit')
            ledger['native_run_calls'] += 1
            _check_status(h.run(), highspy, 'run')
            return h.getModelStatus(), h.getSolution(), h.getInfo()

        status, solution, info = charge('native_solve', solve)
        model_status = h.modelStatusToString(status)
        iterations = int(info.simplex_iteration_count)
        if status == highspy.HighsModelStatus.kOptimal and solution.value_valid and solution.dual_valid:
            witness = {'x': list(solution.col_value), 'y': list(solution.row_dual)}

            def verify():
                ledger['certificate_calls'] += 1
                return verify_standard_form_certificate(A, b, c, **witness)

            certificate = charge('original_verification', verify)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
    return {'warm_start': indices is not None, 'basis': indices,
            'accepted': bool(error is None and certificate is not None and certificate['accepted']),
            'witness': witness, 'certificate': certificate, 'model_status': model_status,
            'simplex_iterations': iterations, 'error': error, 'stages': stages, 'ledger': ledger}


def solve_native_checked(A, b, c, *, head=None, cold_fallback=True, budget_s=5.0):
    """Cold native or supplied-basis native repair, with the same verifier.

This timer starts before conversion/decoding; it includes model setup, basis
supply, failed attempts and verification. It excludes upstream proposal work
and imports already paid by the caller. Add those costs for a full model gate.
The deadline is shared across warm and cold runs. Verification is synchronous
and can overrun it; late valid witnesses are retained but never accepted.
Every call creates a fresh solver: no uncharged persistent factorization reuse.
"""
    started = perf_counter_ns()
    if (type(budget_s) not in (int, float) or not math.isfinite(budget_s)
            or budget_s <= 0 or type(cold_fallback) is not bool):
        raise ValueError('positive finite budget and explicit fallback policy required')
    # Import failures must remain dependency failures, not reported solver results.
    import highspy  # noqa: F401
    A, b, c = _raw(A, b, c)
    deadline = started + int(budget_s * 1e9)
    kind, indices = ('COLD', None) if head is None else decode_basis(head, *A.shape)
    attempts = []
    if kind in ('COLD', 'BASIS') or cold_fallback:
        attempts.append(_attempt(A, b, c, indices, deadline))
    if (kind == 'BASIS' and attempts and not attempts[-1]['accepted']
            and cold_fallback and perf_counter_ns() < deadline):
        attempts.append(_attempt(A, b, c, None, deadline))
    total_ms = (perf_counter_ns() - started) / 1e6
    exceeded = total_ms > budget_s * 1000
    accepted = bool(attempts and attempts[-1]['accepted'] and not exceeded)
    return {'head_kind': kind, 'accepted': accepted,
            'status': 'VERIFIED' if accepted else ('BUDGET_EXCEEDED' if exceeded else 'REJECTED'),
            'fallback_used': bool(kind in ('ABSTAIN', 'INVALID_HEAD') and attempts
                                  or len(attempts) > 1),
            'budget_s': budget_s, 'total_ms': total_ms, 'attempts': attempts,
            'ledger': {key: sum(a['ledger'][key] for a in attempts)
                       for key in ('native_run_calls', 'set_basis_calls', 'certificate_calls')}}
