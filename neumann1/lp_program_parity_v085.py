"""Supplied-head LP attribution boundary, not a trained model or speed audit.

Both adapters have the same checked execution authority. Stable outcomes keep
the actual witnesses and call ledger but deliberately exclude elapsed times.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import warnings
from pathlib import Path

import numpy as np
import scipy
import threadpoolctl
from threadpoolctl import threadpool_limits

from . import lp_portfolio_v084 as source
from .lp_certificate_v081 import verify_standard_form_certificate

SOURCE_JSON_SHA256 = '10ad3cad8ad5c7f2543c333ce72f484f6747767828dc76e842795940603177c9'
DECISION = 'LP_BASIS_ONLY_Q4_ATTRIBUTION_REJECTED'


def protocol():
    return {'schema': 'neumann.lp-program-parity.v1',
            'source_json_sha256': SOURCE_JSON_SHA256,
            'source_repeat': 0, 'source_routes': ['norm_control', 'scale_portfolio'],
            'diagnostic_native_fallback': False, 'timing_evidence': False,
            'trained_model': False, 'q3': 'OPEN', 'q4': 'OPEN'}


def load_source(path):
    """Integrity-check the preregistered JSON identity, not just any manifest."""
    path = Path(path)
    if json.loads(path.read_text())['json_sha256'] != SOURCE_JSON_SHA256:
        raise ValueError('not the preregistered v084 first archive')
    return source.load_retained_archive(path)


def _basis(raw, indices):
    m, n = raw['A'].shape
    if (type(indices) is not list or len(indices) != m or
            any(type(i) is not int or not 0 <= i < n for i in indices) or
            len(set(indices)) != m):
        raise ValueError('invalid basis head')
    return list(indices)


def _head(raw, head):
    if type(head) is dict and set(head) == {'basis'}:
        return 'basis', _basis(raw, head['basis'])
    if type(head) is dict and set(head) == {'abstain'} and head['abstain'] is True:
        return 'abstain', None
    raise ValueError('invalid head syntax')


def decode_tool_program(raw, head):
    """Closed instructions only; invalid model syntax also fails closed."""
    try:
        kind, indices = _head(raw, head)
    except (TypeError, ValueError):
        return {'op': 'reject_checked'}
    return ({'op': 'solve_basis_checked', 'basis': indices} if kind == 'basis'
            else {'op': 'native_checked'})


def _basis_once(raw, indices, ledger):
    """Same v084 LU/reconstruction/check algorithm, without a latency timer."""
    ledger['basis_calls'] += 1
    try:
        index = np.asarray(indices, dtype=np.int64)
        with warnings.catch_warnings():
            warnings.simplefilter('error', source.LinAlgWarning)
            factor = source.lu_factor(raw['A'][:, index], check_finite=False)
        x = np.zeros(raw['A'].shape[1], dtype=np.float64)
        x[index] = source.lu_solve(factor, raw['b'], check_finite=False)
        y = source.lu_solve(factor, raw['c'][index], trans=1, check_finite=False)
        ledger['original_certificate_calls'] += 1
        certificate = verify_standard_form_certificate(**raw, x=x, y=y)
        return {'method': 'basis', 'indices': indices, 'accepted': certificate['accepted'],
                'certificate': certificate, 'witness': {'x': x.tolist(), 'y': y.tolist()}, 'error': None}
    except Exception as exc:
        return {'method': 'basis', 'indices': indices, 'accepted': False,
                'certificate': None, 'witness': None, 'error': f'{type(exc).__name__}: {exc}'}


def _native_once(raw, ledger):
    ledger['native_calls'] += 1
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Unrecognized options detected:.*',
                                    category=source.OptimizeWarning)
            result = source.linprog(raw['c'], A_eq=raw['A'], b_eq=raw['b'], bounds=(0, None),
                                    method='highs', options={'presolve': True, 'threads': 1,
                                                            'parallel': False, 'time_limit': 5.})
        witness = ({'x': result.x.tolist(), 'y': result.eqlin.marginals.tolist()}
                   if result.success else None)
        certificate = None
        if witness is not None:
            ledger['original_certificate_calls'] += 1
            certificate = verify_standard_form_certificate(**raw, **witness)
        return {'method': 'highs', 'accepted': bool(certificate and certificate['accepted']),
                'solver_status': int(result.status), 'certificate': certificate,
                'witness': witness, 'error': None}
    except Exception as exc:
        return {'method': 'highs', 'accepted': False, 'solver_status': None,
                'certificate': None, 'witness': None, 'error': f'{type(exc).__name__}: {exc}'}


def _execute(raw, kind, indices, native_fallback):
    if type(native_fallback) is not bool:
        raise ValueError('fallback authority must be explicit bool')
    ledger = {'basis_calls': 0, 'native_calls': 0,
              'original_certificate_calls': 0, 'decode_rejections': int(kind == 'reject')}
    candidate = native = None
    if kind == 'basis':
        candidate = _basis_once(raw, indices, ledger)
    accepted = bool(candidate and candidate['accepted'])
    fallback_used = native_fallback and not accepted
    if fallback_used:
        native = _native_once(raw, ledger)
        accepted = native['accepted']
    status = ('VERIFIED' if accepted else 'INVALID_HEAD' if kind == 'reject'
              else 'ABSTAIN' if kind == 'abstain' and not fallback_used else 'REJECTED')
    return {'status': status, 'accepted': accepted, 'candidate': candidate,
            'native': native, 'fallback_used': fallback_used, 'ledger': ledger}


def structural_route(A, b, c, head, *, native_fallback=True):
    raw = {'A': A, 'b': b, 'c': c}
    try:
        kind, indices = _head(raw, head)
    except (TypeError, ValueError):
        kind, indices = 'reject', None
    return _execute(raw, kind, indices, native_fallback)


def execute_tool_program(A, b, c, program, *, native_fallback=True):
    raw = {'A': A, 'b': b, 'c': c}
    kind, indices = 'reject', None
    if type(program) is dict:
        if set(program) == {'op', 'basis'} and program['op'] == 'solve_basis_checked':
            try:
                indices = _basis(raw, program['basis'])
                kind = 'basis'
            except (TypeError, ValueError):
                pass
        elif set(program) == {'op'} and program['op'] == 'native_checked':
            kind = 'abstain'
    return _execute(raw, kind, indices, native_fallback)


def direct_tool_program_route(A, b, c, head, *, native_fallback=True):
    raw = {'A': A, 'b': b, 'c': c}
    return execute_tool_program(**raw, program=decode_tool_program(raw, head),
                                native_fallback=native_fallback)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def prepare_pairs(original):
    """Read retained arrays/attempts only, without generation or any solver."""
    inputs = {}
    for s in original['sources']:
        m, n = s['rows'], s['cols']
        raw = {k: source.decode_array(s['arrays'][k], shape)
               for k, shape in (('A', (m, n)), ('b', (m,)), ('c', (n,)))}
        if s['id'] in inputs or source.input_digest(raw) != s['raw_sha256']:
            raise ValueError('source identity drift')
        inputs[s['id']] = raw
    groups, seen_rows = {}, set()
    for row in original['records']:
        if row['repeat'] != 0 or row['route_id'] not in protocol()['source_routes']:
            continue
        row_id = (row['case_id'], row['route_id'])
        if row_id in seen_rows or row['case_id'] not in inputs:
            raise ValueError('duplicate/unknown source record')
        seen_rows.add(row_id)
        for attempt in row['attempts']:
            basis = sorted(_basis(inputs[row['case_id']], attempt['indices']))
            key = (row['case_id'], tuple(basis))
            groups.setdefault(key, []).append({'route': row['route_id'], 'method': attempt['method']})
    if seen_rows != {(case, route) for case in inputs for route in protocol()['source_routes']}:
        raise ValueError('first-repeat source coverage drift')
    pairs = [{'case_id': case, 'input_sha256': source.input_digest(inputs[case]),
              'basis_sha256': _digest(list(basis)), 'head': {'basis': list(basis)},
              'provenance': groups[(case, basis)]}
             for case, basis in sorted(groups)]
    return inputs, pairs


def summarize(records):
    if not records:
        raise ValueError('empty diagnostic')
    agreement = sum(r['neumann'] == r['direct'] for r in records)
    return {'pairs': len(records), 'agreement': agreement,
            'neumann_accepted': sum(r['neumann']['accepted'] for r in records),
            'direct_accepted': sum(r['direct']['accepted'] for r in records),
            'decision': DECISION if agreement == len(records) else 'PARITY_BUG_OR_CONTRACT_MISMATCH',
            'q3': 'OPEN', 'q4': 'OPEN'}


def run_diagnostic(original):
    source.validate_archive(original)
    inputs, pairs = prepare_pairs(original)
    environment = {'python': platform.python_version(), 'numpy': np.__version__,
                   'scipy': scipy.__version__, 'threadpoolctl': threadpoolctl.__version__,
                   'openblas_coretype': os.environ.get('OPENBLAS_CORETYPE')}
    if (any(environment[k] != v for k, v in source.protocol()['runtime'].items()) or
            environment['openblas_coretype'] != 'HASWELL'):
        raise RuntimeError('use frozen Python/package runtime and HASWELL dispatch')
    records = []
    with threadpool_limits(limits=1):
        environment['threadpools'] = threadpoolctl.threadpool_info()
        if not environment['threadpools'] or any(p['num_threads'] != 1 for p in environment['threadpools']):
            raise RuntimeError('actual native pools must be single-threaded')
        for pair in pairs:
            raw = inputs[pair['case_id']]
            records.append({**pair, 'direct_program': decode_tool_program(raw, pair['head']),
                            'neumann': structural_route(**raw, head=pair['head'], native_fallback=False),
                            'direct': direct_tool_program_route(**raw, head=pair['head'], native_fallback=False)})
    return {'protocol': protocol(), 'environment': environment,
            'records': records, 'summary': summarize(records)}


def _check_outcome(outcome, raw, head):
    expected_keys = {'status', 'accepted', 'candidate', 'native', 'fallback_used', 'ledger'}
    if (set(outcome) != expected_keys or type(outcome['accepted']) is not bool or
            outcome['fallback_used'] is not False or outcome['native'] is not None):
        raise ValueError('diagnostic authority/acceptance drift')
    candidate = outcome['candidate']
    if (type(candidate) is not dict or set(candidate) !=
            {'method', 'indices', 'accepted', 'certificate', 'witness', 'error'} or
            candidate['method'] != 'basis' or candidate['indices'] != head['basis'] or
            type(candidate['accepted']) is not bool):
        raise ValueError('candidate schema/basis drift')
    witness, certificate = candidate['witness'], candidate['certificate']
    if witness is not None:
        if candidate['error'] is not None or type(certificate) is not dict:
            raise ValueError('witness/error drift')
        fresh = verify_standard_form_certificate(**raw, **witness)
        # Exact witnesses are retained. Numerical diagnostic scalars can vary
        # across BLAS dispatch; acceptance is the frozen certificate contract.
        if (candidate['accepted'] != fresh['accepted'] or certificate['accepted'] != fresh['accepted'] or
                set(certificate) != set(fresh) or certificate['schema'] != fresh['schema'] or
                any(certificate[k] != fresh[k] for k in ('rows', 'cols', 'atol', 'rtol'))):
            raise ValueError('original witness/certificate drift')
    elif candidate['accepted'] or certificate is not None or not isinstance(candidate['error'], str):
        raise ValueError('missing rejected witness/error')
    ledger = {'basis_calls': 1, 'native_calls': 0,
              'original_certificate_calls': int(certificate is not None), 'decode_rejections': 0}
    if (outcome['ledger'] != ledger or any(type(v) is not int for v in outcome['ledger'].values()) or
            outcome['accepted'] != candidate['accepted'] or outcome['status'] !=
            ('VERIFIED' if candidate['accepted'] else 'REJECTED')):
        raise ValueError('execution ledger/status drift')


def validate_archive(report, original):
    """Solver-free replay; production callers load original via load_source."""
    if report['protocol'] != protocol():
        raise ValueError('protocol drift')
    env = report['environment']
    if (any(env[k] != v for k, v in source.protocol()['runtime'].items()) or
            env['openblas_coretype'] != 'HASWELL' or not env['threadpools'] or
            any(p['num_threads'] != 1 for p in env['threadpools'])):
        raise ValueError('environment drift')
    inputs, pairs = prepare_pairs(original)
    if len(report['records']) != len(pairs):
        raise ValueError('pair coverage drift')
    for record, pair in zip(report['records'], pairs):
        if (set(record) != set(pair) | {'direct_program', 'neumann', 'direct'} or
                any(record[k] != v for k, v in pair.items())):
            raise ValueError('source/basis/provenance drift')
        raw = inputs[pair['case_id']]
        if record['direct_program'] != decode_tool_program(raw, pair['head']):
            raise ValueError('closed program drift')
        for route in ('neumann', 'direct'):
            _check_outcome(record[route], raw, pair['head'])
    if report['summary'] != summarize(report['records']):
        raise ValueError('summary/agreement drift')
