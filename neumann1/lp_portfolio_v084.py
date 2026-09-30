"""Opened classical LP screen, with retained inputs and solver-free witness replay."""
from __future__ import annotations

import base64
import hashlib
import math
import os
import platform
import random
import warnings
from statistics import geometric_mean, median
from time import perf_counter_ns

import numpy as np
import scipy
from scipy.linalg import LinAlgWarning, lstsq, lu_factor, lu_solve, qr
from scipy.optimize import OptimizeWarning, linprog
import threadpoolctl
from threadpoolctl import threadpool_limits

from . import lp_basis_headroom_v082 as base
from . import lp_discovery_v083 as previous
from .lp_certificate_v081 import verify_standard_form_certificate

SEED_BASE, ORDER_SEED, REPEATS = 84100, 84991, 3
FORMS = ('raw', 'normalized')
ROUTES = (*base.DIRECT_METHODS, 'norm_control', 'scale_portfolio')
CUTOFF = 1e-12


def specifications():
    return tuple({**s, 'seed': s['seed'] - previous.SEED_BASE + SEED_BASE}
                 for s in previous.specifications())


def protocol():
    return {'seed_base': SEED_BASE, 'order_seed': ORDER_SEED, 'repeats': REPEATS,
            'forms': list(FORMS), 'routes': list(ROUTES),
            'runtime': base.protocol()['runtime'], 'openblas_coretype': 'HASWELL',
            'native_threads': 1, 'native_parallel': False, 'native_time_limit_s': 5.,
            'lstsq_driver': 'gelsy', 'lstsq_cond': CUTOFF,
            'trim_divisors': [2, 4, 8], 'final_trim_size': 'm',
            'max_candidates': 7, 'geomean_max': .5,
            'ratio_win': .8, 'min_wins': 8, 'min_no_fallback': 8,
            'q3': 'OPEN', 'q4': 'OPEN'}


def normalized(A, b, c):
    A, b, c = (np.asarray(a, dtype=np.float64) for a in (A, b, c))
    if A.ndim != 2 or min(A.shape) <= 0:
        raise ValueError('invalid matrix')
    m, n = A.shape
    if n < m or b.shape != (m,) or c.shape != (n,):
        raise ValueError('invalid dimensions')
    if not all(np.all(np.isfinite(a)) for a in (A, b, c)):
        raise ValueError('non-finite coefficients')
    lengths = np.linalg.norm(A, axis=0)
    if np.any(lengths <= 0) or not np.all(np.isfinite(lengths)):
        raise ValueError('zero/non-finite column norm')
    D, q = A / lengths, c / lengths
    if not np.all(np.isfinite(q)):
        raise ValueError('non-finite normalized cost')
    return D, b, q


def propose(A, b, c):
    """No metadata, optimizer, oracle or learned parameters are accepted."""
    D, b, q = normalized(A, b, c)
    m, n = D.shape
    proposals, seen = [], set()

    def add(name, indices):
        identity = tuple(sorted(map(int, indices)))
        if identity not in seen:
            proposals.append((name, np.asarray(identity, dtype=np.int64)))
            seen.add(identity)

    selected = np.arange(n)
    for name, keep in [('dual_all', n), ('dual_half', max(m, n // 2)),
                       ('dual_quarter', max(m, n // 4)),
                       ('dual_eighth', max(m, n // 8)), ('dual_m', m)]:
        selected = selected[:keep]
        dual = lstsq(D[:, selected].T, q[selected], cond=CUTOFF,
                     lapack_driver='gelsy', check_finite=False)[0]
        selected = np.argsort(np.abs(q - D.T @ dual), kind='stable')
        add(name, selected[:m])
    primal = lstsq(D, b, cond=CUTOFF, lapack_driver='gelsy', check_finite=False)[0]
    order = np.argsort(-primal, kind='stable')
    add('primal_top', order[:m])
    shortlist = order[:min(n, 2 * m)]
    pivots = qr(D[:, shortlist], mode='economic', pivoting=True,
                check_finite=False)[2]
    add('primal_shortlist_qr', shortlist[pivots[:m]])
    return proposals


def candidate_once(raw, indices, name):
    start = perf_counter_ns()
    try:
        indices = base._validate_basis(raw, indices)
        with warnings.catch_warnings():
            warnings.simplefilter('error', LinAlgWarning)
            factor = lu_factor(raw['A'][:, indices], check_finite=False)
        x = np.zeros(raw['A'].shape[1], dtype=np.float64)
        x[indices] = lu_solve(factor, raw['b'], check_finite=False)
        y = lu_solve(factor, raw['c'][indices], trans=1, check_finite=False)
        solve_ms = base._elapsed_ms(start)
        check = perf_counter_ns()
        certificate = verify_standard_form_certificate(**raw, x=x, y=y)
        verify_ms = base._elapsed_ms(check)
        return {'method': name, 'indices': indices.tolist(),
                'accepted': bool(certificate['accepted']), 'certificate': certificate,
                'witness': {'x': x.tolist(), 'y': y.tolist()},
                'solve_ms': solve_ms, 'verify_ms': verify_ms,
                'total_ms': base._elapsed_ms(start), 'error': None}
    except Exception as exc:
        return {'method': name, 'indices': np.asarray(indices).tolist(),
                'accepted': False, 'certificate': None, 'witness': None,
                'solve_ms': None, 'verify_ms': None,
                'total_ms': base._elapsed_ms(start), 'error': f'{type(exc).__name__}: {exc}'}


def direct_once(raw, method):
    if method not in base.DIRECT_METHODS:
        raise ValueError('undeclared native route')
    start = perf_counter_ns()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Unrecognized options detected:.*',
                                    category=OptimizeWarning)
            result = linprog(raw['c'], A_eq=raw['A'], b_eq=raw['b'], bounds=(0, None),
                             method=method, options={'presolve': True, 'threads': 1,
                                                     'parallel': False, 'time_limit': 5.})
        solve_ms = base._elapsed_ms(start)
        check = perf_counter_ns()
        witness = ({'x': result.x.tolist(), 'y': result.eqlin.marginals.tolist()}
                   if result.success else None)
        certificate = (verify_standard_form_certificate(**raw, **witness)
                       if witness is not None else None)
        verify_ms = base._elapsed_ms(check)
        return {'method': method, 'accepted': bool(certificate and certificate['accepted']),
                'solver_status': int(result.status), 'solver_message': str(result.message),
                'certificate': certificate, 'witness': witness,
                'solve_ms': solve_ms, 'verify_ms': verify_ms,
                'total_ms': base._elapsed_ms(start), 'error': None}
    except Exception as exc:
        return {'method': method, 'accepted': False, 'solver_status': None,
                'solver_message': None, 'certificate': None, 'witness': None,
                'solve_ms': None, 'verify_ms': None, 'total_ms': base._elapsed_ms(start),
                'error': f'{type(exc).__name__}: {exc}'}


def discovery_once(A, b, c, *, policy='scale_portfolio'):
    if policy not in ('scale_portfolio', 'norm_control'):
        raise ValueError('undeclared proposal policy')
    start = perf_counter_ns()
    raw = {'A': A, 'b': b, 'c': c}
    proposal_start = perf_counter_ns()
    proposal_error = None
    try:
        proposals = (propose(A, b, c) if policy == 'scale_portfolio'
                     else previous.propose(A, b, c))
    except Exception as exc:
        proposals = []
        proposal_error = f'{type(exc).__name__}: {exc}'
    proposal_ms = base._elapsed_ms(proposal_start)
    attempts = []
    for name, indices in proposals:
        attempt = candidate_once(raw, indices, name)
        attempts.append(attempt)
        if attempt['accepted']:
            break
    fallback_used = not attempts or not attempts[-1]['accepted']
    fallback = direct_once(raw, 'highs') if fallback_used else None
    winner = fallback if fallback_used else attempts[-1]
    return {'method': policy, 'proposal_ms': proposal_ms, 'proposal_error': proposal_error,
            'proposed_count': len(proposals), 'attempts': attempts,
            'fallback_used': fallback_used, 'fallback': fallback,
            'accepted': winner['accepted'], 'certificate': winner['certificate'],
            'witness': winner['witness'], 'total_ms': base._elapsed_ms(start)}


def observe(raw, route):
    if route in base.DIRECT_METHODS:
        return direct_once(raw, route)
    return discovery_once(**raw, policy=route)


def encode_array(value):
    value = np.ascontiguousarray(value, dtype='<f8')
    return {'dtype': '<f8', 'shape': list(value.shape),
            'data': base64.b64encode(value.tobytes()).decode('ascii')}


def decode_array(encoded, shape):
    if set(encoded) != {'dtype', 'shape', 'data'} or encoded['dtype'] != '<f8' or encoded['shape'] != list(shape):
        raise ValueError('array schema/shape drift')
    data = base64.b64decode(encoded['data'], validate=True)
    if len(data) != math.prod(shape) * 8:
        raise ValueError('array byte count drift')
    value = np.frombuffer(data, dtype='<f8').reshape(shape)
    if not np.all(np.isfinite(value)):
        raise ValueError('non-finite retained input')
    return value


def input_digest(raw):
    return hashlib.sha256(''.join(base._array_digest(raw[k]) for k in ('A', 'b', 'c')).encode()).hexdigest()


def summarize(records, warmups):
    for rows, timed in ((records, True), (warmups, False)):
        expected = {(s['id'], r, i) for s in specifications() for r in ROUTES
                    for i in (range(REPEATS) if timed else (-1,))}
        seen = set()
        for row in rows:
            repeat = row['repeat'] if timed else -1
            key = (row['case_id'], row['route_id'], repeat)
            if type(repeat) is not int or key not in expected or key in seen:
                raise ValueError('coverage identity drift')
            if type(row['accepted']) is not bool or type(row['total_ms']) not in (int, float) or not math.isfinite(row['total_ms']) or row['total_ms'] <= 0:
                raise ValueError('invalid acceptance/cost')
            seen.add(key)
        if seen != expected:
            raise ValueError('incomplete coverage')
    warm = {(r['case_id'], r['route_id']): r for r in warmups}
    cells, capable = [], True
    for spec in specifications():
        groups = {r: [x for x in records if x['case_id'] == spec['id'] and x['route_id'] == r] for r in ROUTES}
        costs = {r: median(x['total_ms'] for x in groups[r])
                 for r in ROUTES if warm[(spec['id'], r)]['accepted'] and all(x['accepted'] for x in groups[r])}
        native = {r: costs[r] for r in base.DIRECT_METHODS if r in costs}
        capable &= bool(native) and 'scale_portfolio' in costs
        reference = min(native.values()) if native else None
        cells.append({'case_id': spec['id'], 'form': spec['form'],
                      'width_factor': spec['width_factor'], 'eligible_route_medians_ms': costs,
                      'best_native': min(native, key=native.get) if native else None,
                      'ratios': {r: costs[r] / reference if reference else None for r in costs},
                      'portfolio_no_fallback': not any(x['fallback_used'] for x in
                          [warm[(spec['id'], 'scale_portfolio')], *groups['scale_portfolio']])})
    summary = {'q3': 'OPEN', 'q4': 'OPEN', 'cells': cells}
    if not capable:
        return {**summary, 'decision': 'CAPABILITY_UNREACHED'}
    forms = {}
    for form in FORMS:
        expanded = [c for c in cells if c['form'] == form and c['width_factor'] == 16]
        ratio = geometric_mean(c['ratios']['scale_portfolio'] for c in expanded)
        wins = sum(c['ratios']['scale_portfolio'] <= .8 for c in expanded)
        no_fallback = sum(c['portfolio_no_fallback'] for c in expanded)
        forms[form] = {'geomean_ratio': ratio, 'twenty_percent_wins': wins,
                       'no_fallback_cases': no_fallback,
                       'gate_pass': ratio <= .5 and wins >= 8 and no_fallback >= 8}
    decision = ('CLASSICAL_PORTFOLIO_CONSUMES_MATCHED_HEADROOM'
                if all(x['gate_pass'] for x in forms.values()) else 'RAW_ONLY_CLASSICAL_GAIN'
                if forms['raw']['gate_pass'] else 'RESIDUAL_HEADROOM_UNRESOLVED_NOT_LEARNING_ADMISSION')
    return {**summary, 'forms': forms, 'decision': decision}


def run_audit():
    versions = {'python_major_minor': list(map(int, platform.python_version_tuple()[:2])),
                'numpy': np.__version__, 'scipy': scipy.__version__,
                'threadpoolctl': threadpoolctl.__version__}
    env = base.single_thread_environment()
    if versions != protocol()['runtime'] or not env['declared_single_thread'] or os.environ.get('OPENBLAS_CORETYPE') != 'HASWELL':
        raise RuntimeError('frozen runtime/thread/dispatch boundary drift')
    records, warmups, sources = [], [], []
    with threadpool_limits(limits=1):
        pools = threadpoolctl.threadpool_info()
        if not pools or any(p['num_threads'] != 1 for p in pools):
            raise RuntimeError('actual numerical thread count drift')
        for spec in specifications():
            started = perf_counter_ns()
            raw, digest = previous.generate_case(spec)
            setup_ms = base._elapsed_ms(started)
            sources.append({**spec, 'raw_sha256': digest, 'setup_ms': setup_ms,
                            'arrays': {k: encode_array(v) for k, v in raw.items()}})
            for route in ROUTES:
                warmups.append({'case_id': spec['id'], 'route_id': route, **observe(raw, route)})
            schedule = [(r, i) for r in ROUTES for i in range(REPEATS)]
            random.Random(ORDER_SEED + spec['seed'] + spec['width_factor'] + FORMS.index(spec['form'])).shuffle(schedule)
            for route, repeat in schedule:
                records.append({'case_id': spec['id'], 'route_id': route, 'repeat': repeat,
                                **observe(raw, route)})
    return {'experiment': 'v0.0.84 scale-invariant classical portfolio', 'protocol': protocol(),
            'environment': {**env, **versions, 'platform': platform.platform(),
                            'openblas_coretype': os.environ['OPENBLAS_CORETYPE'], 'threadpools': pools},
            'sources': sources, 'warmups': warmups, 'records': records,
            'summary': summarize(records, warmups)}


def _check_record(row, raw):
    if type(row['accepted']) is not bool:
        raise ValueError('invalid acceptance type')
    for k, v in row.items():
        if k.endswith('_ms') and v is not None and (type(v) not in (int, float) or not math.isfinite(v) or v < 0):
            raise ValueError('invalid stage cost')
    if row['witness'] is not None:
        try:
            fresh = verify_standard_form_certificate(**raw, **row['witness'])
        except (TypeError, ValueError) as exc:
            raise ValueError('invalid retained witness') from exc
        if row['accepted'] != fresh['accepted'] or row['certificate']['accepted'] != fresh['accepted']:
            raise ValueError('witness/certificate acceptance drift')
    elif row['accepted'] or row['certificate'] is not None:
        raise ValueError('missing witness')
    if 'attempts' not in row:
        if row['error'] is None and row['total_ms'] < row['solve_ms'] + row['verify_ms']:
            raise ValueError('omitted solve/check cost')
        return
    limit = 7 if row['method'] == 'scale_portfolio' else 2
    if type(row['proposed_count']) is not int or not 0 <= len(row['attempts']) <= row['proposed_count'] <= limit:
        raise ValueError('proposal budget drift')
    if type(row['fallback_used']) is not bool or any(a['accepted'] for a in row['attempts'][:-1]):
        raise ValueError('invalid continuation/fallback')
    charged = row['proposal_ms'] + sum(a['total_ms'] for a in row['attempts'])
    identities = set()
    for attempt in row['attempts']:
        _check_record(attempt, raw)
        indices = base._validate_basis(raw, np.asarray(attempt['indices']))
        identity = tuple(sorted(map(int, indices)))
        if identity in identities:
            raise ValueError('duplicate attempted basis')
        identities.add(identity)
    if row['fallback_used']:
        if row['attempts'] and row['attempts'][-1]['accepted']:
            raise ValueError('fallback after verified candidate')
        winner = row['fallback']
        _check_record(winner, raw)
        charged += winner['total_ms']
    else:
        if row['fallback'] is not None or not row['attempts']:
            raise ValueError('missing winner/unexecuted fallback')
        winner = row['attempts'][-1]
    if not row['fallback_used'] and not winner['accepted']:
        raise ValueError('rejected candidate without fallback')
    if any(row[k] != winner[k] for k in ('accepted', 'certificate', 'witness')) or row['total_ms'] < charged:
        raise ValueError('winner/cost drift')


def validate_archive(report):
    if report['protocol'] != protocol():
        raise ValueError('protocol drift')
    env = report['environment']
    if any(env[k] != v for k, v in protocol()['runtime'].items()) or not env['declared_single_thread'] or env['openblas_coretype'] != 'HASWELL':
        raise ValueError('runtime drift')
    if not env['threadpools'] or any(p['num_threads'] != 1 for p in env['threadpools']):
        raise ValueError('actual pool metadata drift')
    if len(report['sources']) != len(specifications()):
        raise ValueError('source count drift')
    inputs = {}
    for source, spec in zip(report['sources'], specifications()):
        if any(source[k] != v for k, v in spec.items()) or set(source['arrays']) != {'A', 'b', 'c'}:
            raise ValueError('source schema drift')
        if type(source['setup_ms']) not in (int, float) or not math.isfinite(source['setup_ms']) or source['setup_ms'] < 0:
            raise ValueError('invalid setup cost')
        m, n = spec['rows'], spec['cols']
        raw = {k: decode_array(source['arrays'][k], shape)
               for k, shape in (('A', (m, n)), ('b', (m,)), ('c', (n,)))}
        if input_digest(raw) != source['raw_sha256']:
            raise ValueError('retained input hash drift')
        inputs[spec['id']] = raw
    summary = summarize(report['records'], report['warmups'])
    for row in [*report['warmups'], *report['records']]:
        if row['method'] != row['route_id']:
            raise ValueError('route label drift')
        _check_record(row, inputs[row['case_id']])
    if summary != report['summary']:
        raise ValueError('summary drift')
