"""Opened M106 certificate-economics diagnostic, not a transfer rerun.

Existing original LP verification, native execution and support expansion are
reused. Sparse refitting and KKT certificate recovery are classical numerical
adapters, not learned NEUMANN discovery. Oracle labels are confined to C/D/E.
No training, model forward, problem generator or sealed evidence is used.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/experiments/results/m106_bp_transfer_first'
CONTRACT = ROOT / 'docs/experiments/bp_certificate_diagnostic.preregister.json'
HEAD = 'fb23dca002bbd50c96e0c766369269a0b7fcc7a6'
REPORT_SHA = 'fd0f069bb43c8f4f471578de35a6f70af2c418b46b701260f12cd1d27bebd6b8'
ROUTES = ('A_NATIVE', 'A_IPM', 'A_DUAL', 'A_SPGL1',
          'B_RETAINED_s100001', 'B_RETAINED_s100002',
          'C_ORACLE_PADDED', 'D_ORACLE_SPARSE', 'E_ORACLE_SPARSE_DUAL')
BUDGET_S = 5.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ms(start):
    return (perf_counter_ns() - start) / 1e6


def schedule():
    rng = random.Random(106208)
    case_ids = [f'm106_bp_k{k}_r{r}' for k in (8, 16, 32, 64) for r in range(4)]
    rows = []
    for repeat in (-1, 0, 1, 2):
        block = [(c, route, repeat) for c in case_ids for route in ROUTES]
        rng.shuffle(block)
        rows.extend(block)
    return rows


def science():
    """Import only after attempt reservation / contract pin verification."""
    global np, la, linprog, LinearOperator, checker, native, adaptive
    import numpy as np
    from scipy import linalg as la
    from scipy.optimize import linprog
    from scipy.sparse.linalg import LinearOperator
    from neumann1.lp_certificate_v081 import verify_standard_form_certificate as checker
    from neumann1.lp_native_warm_start_v086 import solve_native_checked as native
    from neumann1.lp_q34_support_v097 import adaptive_support_checked as adaptive


def single_thread_lp(*args, **kwargs):
    from scipy.optimize import OptimizeWarning
    from warnings import catch_warnings, filterwarnings
    kwargs['options'] = {**kwargs.get('options', {}), 'threads': 1, 'parallel': False}
    with catch_warnings():
        filterwarnings('ignore', message='Unrecognized options detected:.*', category=OptimizeWarning)
        return linprog(*args, **kwargs)


def sparse_checked(raw, indices, *, budget_s, free_dual=None):
    """Refit a proposed support; obtain a full original dual before acceptance.

    First try the classical minimum-norm KKT dual. If it fails the unchanged
    original verifier, delegate dual feasibility to HiGHS. No new optimizer.
    D and the SPGL1 comparator receive identical certificate-repair rights.
    """
    start = perf_counter_ns()
    A, b, c = (raw[k] for k in ('A', 'b', 'c'))
    if (type(indices) is not list or not 0 < len(indices) <= A.shape[1]
            or len(set(indices)) != len(indices)
            or any(type(i) is not int or not 0 <= i < A.shape[1] for i in indices)):
        raise ValueError('valid nonempty unique original support required')
    if not math.isfinite(budget_s) or budget_s <= 0:
        raise ValueError('positive finite budget required')
    stages, attempts = [], []

    def charge(name, f):
        t = perf_counter_ns()
        try:
            return f()
        finally:
            stages.append({'stage': name, 'ms': ms(t)})

    S = A[:, indices]
    small = charge('primal_refit', lambda: la.lstsq(S, b, lapack_driver='gelsy')[0])
    x = np.zeros(A.shape[1]); x[indices] = small
    if free_dual is not None:
        y = np.asarray(free_dual, dtype=float)
        dual_method = 'FREE_RETAINED_OPTIMAL_DUAL_ORACLE'
    else:
        y = charge('minimum_norm_dual', lambda: la.lstsq(S.T, c[indices], lapack_driver='gelsy')[0])
        dual_method = 'minimum_norm_KKT'
    cert = charge('original_verification', lambda: checker(**raw, x=x, y=y))
    attempts.append({'method': dual_method, 'certificate': cert})
    if not cert['accepted'] and free_dual is None and ms(start) < budget_s * 1000:
        left = budget_s - ms(start) / 1000
        result = charge('full_dual_feasibility_LP', lambda: single_thread_lp(
            np.zeros(A.shape[0]), A_ub=A.T, b_ub=c,
            A_eq=S.T, b_eq=c[indices], bounds=(None, None), method='highs-ds',
            options={'time_limit': left, 'primal_feasibility_tolerance': 1e-9,
                     'dual_feasibility_tolerance': 1e-9, 'presolve': True}))
        if result.success:
            y = result.x
            cert = charge('original_verification', lambda: checker(**raw, x=x, y=y))
        attempts.append({'method': 'full_dual_feasibility_LP', 'status': int(result.status),
                         'message': str(result.message), 'certificate': cert if result.success else None})
    witness = {'x': x.tolist(), 'y': y.tolist()}
    return {'accepted': bool(cert['accepted'] and ms(start) <= budget_s * 1000),
            'witness': witness, 'certificate': cert, 'indices': indices,
            'stages': stages, 'attempts': attempts, 'total_ms': ms(start),
            'free_dual_used': free_dual is not None}


def scipy_direct(raw, kind, budget_s):
    start = perf_counter_ns()
    if kind == 'A_IPM':
        r = single_thread_lp(raw['c'], A_eq=raw['A'], b_eq=raw['b'], bounds=(0, None),
                    method='highs-ipm', options={'time_limit': budget_s, 'presolve': True})
        witness = {'x': r.x.tolist(), 'y': r.eqlin.marginals.tolist()} if r.success else None
    else:
        # Classical dual LP; -inequality marginals recover original primal.
        r = single_thread_lp(-raw['b'], A_ub=raw['A'].T, b_ub=raw['c'], bounds=(None, None),
                    method='highs-ds', options={'time_limit': budget_s, 'presolve': True})
        witness = {'x': (-r.ineqlin.marginals).tolist(), 'y': r.x.tolist()} if r.success else None
    solve_ms = ms(start); v = perf_counter_ns()
    cert = checker(**raw, **witness) if witness else None
    return {'accepted': bool(cert and cert['accepted'] and ms(start) <= budget_s * 1000),
            'witness': witness, 'certificate': cert, 'solver_status': int(r.status),
            'solve_ms': solve_ms, 'verify_ms': ms(v), 'total_ms': ms(start)}


def spgl_direct(raw, budget_s):
    from spgl1 import spg_bp
    start = perf_counter_ns(); A = raw['A']; half = A.shape[1] // 2
    if (A.shape[1] != 2 * half or not np.array_equal(A[:, half:], -A[:, :half])
            or not np.array_equal(raw['c'], np.ones(A.shape[1]))):
        raise ValueError('SPGL1 requires verified signed-pair L1 grammar')
    X = A[:, :half]
    counts = {'forward': 0, 'transpose': 0}

    def multiply(v, transpose=False):
        if ms(start) >= budget_s * 1000:
            raise TimeoutError('SPGL1 shared request budget')
        counts['transpose' if transpose else 'forward'] += 1
        return (X.T if transpose else X) @ v

    op = LinearOperator(X.shape, matvec=multiply,
                        rmatvec=lambda v: multiply(v, True), dtype=np.float64)
    beta, residual, gradient, info = spg_bp(
        op, raw['b'], verbosity=0, bp_tol=1e-9, opt_tol=1e-9,
        iter_lim=2000, max_matvec=8000)
    discovery_ms = ms(start)
    threshold = 1e-6 * max(1., float(np.max(np.abs(beta))))
    indices = [int(i if value > 0 else i + half) for i, value in enumerate(beta) if abs(value) > threshold]
    left = budget_s - ms(start) / 1000
    polished = sparse_checked(raw, indices, budget_s=left) if indices and left > 0 else None
    return {'accepted': bool(polished and polished['accepted'] and ms(start) <= budget_s * 1000),
            'witness': polished['witness'] if polished else None,
            'certificate': polished['certificate'] if polished else None,
            'discovery_ms': discovery_ms, 'polish': polished, 'matvec': counts,
            'spgl1_status': int(info['stat']), 'iterations': int(info['niters']),
            'total_ms': ms(start), 'oracle_access': False}


def native_result(raw, budget_s):
    r = native(**raw, cold_fallback=False, budget_s=budget_s)
    r['witness'] = r['attempts'][-1]['witness'] if r['attempts'] else None
    return r


def execute_path(raw, route, budget_s, *, retained_ranking=None, oracle_support=None, oracle_dual=None):
    if route == 'A_NATIVE':
        return native_result(raw, budget_s)
    if route in ('A_IPM', 'A_DUAL'):
        return scipy_direct(raw, route, budget_s)
    if route == 'A_SPGL1':
        return spgl_direct(raw, budget_s)
    if route.startswith('B_RETAINED'):
        return adaptive(**raw, ranking=retained_ranking, factors=(2, 4), budget_s=budget_s)
    if route == 'C_ORACLE_PADDED':
        selected = set(oracle_support)
        ranking = list(oracle_support) + [i for i in range(raw['A'].shape[1]) if i not in selected]
        return adaptive(**raw, ranking=ranking, factors=(2, 4), budget_s=budget_s)
    if route in ('D_ORACLE_SPARSE', 'E_ORACLE_SPARSE_DUAL'):
        return sparse_checked(raw, oracle_support, budget_s=budget_s,
                              free_dual=oracle_dual if route.startswith('E_') else None)
    raise ValueError('unknown registered route')


def prepare(ev):
    if sha(SOURCE / 'report.json') != REPORT_SHA:
        raise ValueError('frozen opened report hash drift')
    report = json.loads((SOURCE / 'report.json').read_bytes())
    manifest = json.loads((SOURCE / 'sources.json').read_bytes())
    if report['sources_sha256'] != ev.digest(ev.canonical(manifest)):
        raise ValueError('original source manifest binding')
    events, terminal = ev.read_events(SOURCE)
    if ([e['payload'] for e in events if e['kind'] == 'observation'] != report['records']
            or terminal['report_sha256'] != ev.digest(ev.canonical(report))):
        raise ValueError('original first event/report binding')
    entries = {e['metadata']['id']: e for e in manifest['cases']}
    labels = {}
    for cid, entry in entries.items():
        source = ev.unpack_case(SOURCE, entry['identity']); raw = decode(source)
        retained = [r for r in report['records'] if r['case_id'] == cid and r['phase'] == 'timed' and r['repeat'] == 0]
        w = next(r['witness'] for r in retained if r['route'] == 'NATIVE')
        if not checker(**raw, **w)['accepted']:
            raise ValueError('retained Native is not optimal authority')
        # Exact nonzero support of one retained optimum, not planted labels/unique optimum.
        labels[cid] = {'support': [i for i, v in enumerate(w['x']) if v != 0], 'dual': w['y'],
                       'rankings': {r['route'].split('_s')[-1]: r['ranking'] for r in retained if r['route'].startswith('EXPAND4')}}
    return entries, labels


def decode(source):
    import base64
    return {k: np.frombuffer(base64.b64decode(v['data'], validate=True), dtype=v['dtype']).reshape(v['shape']).copy()
            for k, v in source['arrays'].items()}


def summarize(records, shared_startup_ms, setup_ms):
    if [(r['case_id'], r['route'], r['repeat']) for r in records] != schedule():
        raise ValueError('missing/replaced/extra observations')
    cells = []
    for cid in sorted({r['case_id'] for r in records}):
        costs = {}
        for route in ROUTES:
            rows = [r for r in records if r['case_id'] == cid and r['route'] == route]
            warm_ms = statistics.median(r['query_ms'] for r in rows if r['repeat'] >= 0)
            costs[route] = {'all_verified': all(r['accepted'] for r in rows), 'warm_query_ms': warm_ms,
                            'cold_q1_ms': warm_ms + shared_startup_ms + setup_ms,
                            'amortized_operational_q10000_ms': warm_ms + (shared_startup_ms + setup_ms) / 10000}
        strong = min(c['amortized_operational_q10000_ms'] for r, c in costs.items()
                     if r.startswith('A_') and c['all_verified']) if any(r.startswith('A_') and c['all_verified'] for r, c in costs.items()) else None
        ratios = {r: strong / c['amortized_operational_q10000_ms'] if strong is not None and c['all_verified'] else None
                  for r, c in costs.items() if not r.startswith('A_')}
        cells.append({'case_id': cid, 'costs': costs, 'strong_native_envelope_ms': strong, 'strong_native_over_candidate': ratios})
    results = {}
    for route in ROUTES[4:]:
        values = [c['strong_native_over_candidate'][route] for c in cells]
        comparable = [v for v in values if v is not None]
        results[route] = {'comparable_originals': len(comparable), 'originals': 16,
                          'geomean_over_completed': math.exp(statistics.mean(math.log(v) for v in comparable)) if comparable else None,
                          'tenfold_originals': sum(v >= 10 for v in comparable),
                          'all_sixteen_comparable': len(comparable) == 16,
                          'screen': 'HEADROOM_CONFIRMED' if len(comparable) == 16 and math.exp(statistics.mean(math.log(v) for v in comparable)) >= 10 and sum(v >= 10 for v in comparable) >= 13 else ('NO_REGISTERED_TENFOLD_HEADROOM' if len(comparable) == 16 else 'INCOMPLETE')}
    return {'cells': cells, 'screening': results, 'observations': len(records),
            'independent_originals': 16, 'fresh_problems': 0, 'new_model_forwards': 0,
            'learned_discovery_cost': 'UNKNOWN; B is retained-ranking FREE-DISCOVERY lower bound',
            'lifecycle_investment': 'UNKNOWN; only actual shared startup and local dependency setup amortized',
            'global_questions_closed': [], 'learning_admitted': False}


def run(args):
    from experiments.q5_register import evidence_module
    ev = evidence_module(); spec = json.loads(CONTRACT.read_bytes())
    if not spec.get('frozen') or spec['runner_sha256'] != sha(__file__) or spec['contract_sha256_in_receipt_required'] is not True:
        raise ValueError('must arm exact preregistration before any performance measurement')
    for rel, pin in spec['source_pins'].items():
        if sha(ROOT / rel) != pin:
            raise ValueError('registered source drift: ' + rel)
    for rel, pin in spec['dependency_pins'].items():
        if sha(Path(args.dependencies) / rel) != pin:
            raise ValueError('registered native dependency drift: ' + rel)
    if spec['routes'] != list(ROUTES) or spec['scheduled_observations'] != len(schedule()):
        raise ValueError('protocol coverage drift')
    attempt = ev.Attempt(args.directory, 'opened_bp_certificate_economics', HEAD)
    wall = perf_counter_ns(); records = []
    try:
        sys.path.insert(0, args.dependencies)
        science()
        import highspy, scipy, spgl1, numpy
        from threadpoolctl import threadpool_limits, threadpool_info
        import platform
        with threadpool_limits(1):
            entries, labels = prepare(ev)
            startup = (perf_counter_ns() - args.launch_ns) / 1e6
            environment = {'python': platform.python_version(), 'platform': platform.platform(),
                           'cpu': os.environ.get('PROCESSOR_IDENTIFIER'), 'logical_cpus': os.cpu_count(),
                           'numpy': numpy.__version__, 'scipy': scipy.__version__, 'highspy': highspy.Highs().version(),
                           'spgl1': '0.0.3', 'threadpools': threadpool_info()}
            attempt.append('preregistered', {'contract_sha256': sha(CONTRACT), 'contract': spec, 'environment': environment,
                                            'shared_startup_ms': startup, 'label_preparation': 'offline retained certified witness; NOT learned discovery'})
            attempt.append('timing_window_start', {'observations': len(schedule()), 'serial': True})
            for cid, route, repeat in schedule():
                if ms(wall) > spec['whole_execution_budget_s'] * 1000:
                    raise TimeoutError('registered whole diagnostic budget')
                attempt.append('observation_start', {'case_id': cid, 'route': route, 'repeat': repeat})
                began = perf_counter_ns(); execution = fallback = None; error = None
                source = ev.unpack_case(SOURCE, entries[cid]['identity']); raw = decode(source)
                decode_ms = ms(began)
                label = labels[cid]
                try:
                    left = BUDGET_S - ms(began) / 1000
                    execution = execute_path(raw, route, left,
                        retained_ranking=label['rankings'][route.split('_s')[-1]] if route.startswith('B_') else None,
                        oracle_support=label['support'] if route.startswith(('C_', 'D_', 'E_')) else None,
                        oracle_dual=label['dual'] if route.startswith('E_') else None)
                except Exception as exc:
                    error = type(exc).__name__ + ': ' + str(exc)
                candidate_accepted = bool(execution and execution['accepted'])
                witness = execution.get('witness') if execution else None
                if not candidate_accepted and ms(began) < BUDGET_S * 1000:
                    fallback = native_result(raw, BUDGET_S - ms(began) / 1000)
                    witness = fallback['witness']
                verify_start = perf_counter_ns()
                cert = checker(**raw, **witness) if witness else None
                independent_verify_ms = ms(verify_start)
                row = {'case_id': cid, 'route': route, 'repeat': repeat, 'source_identity': entries[cid]['identity'],
                       'decode_ms': decode_ms, 'execution': execution, 'fallback': fallback,
                       'candidate_accepted': candidate_accepted, 'candidate_error': error,
                       'witness': witness, 'independent_certificate': cert, 'independent_verify_ms': independent_verify_ms,
                       'oracle_support_supplied': route.startswith(('C_', 'D_', 'E_')),
                       'oracle_dual_supplied': route.startswith('E_'), 'retained_model_ranking': route.startswith('B_')}
                # Charge response serialization; durable scientific archiving follows the request timer.
                response = ev.canonical({'witness': witness, 'certificate': cert,
                                         'candidate_accepted': candidate_accepted, 'error': error})
                row['response_bytes'] = len(response)
                row['query_ms'] = ms(began)
                row['accepted'] = bool(cert and cert['accepted'] and row['query_ms'] <= BUDGET_S * 1000)
                identity = ev.pack_case(args.directory, f'observation-{len(records):04d}.json.gz', row)
                attempt.append('observation', {'case_id': cid, 'route': route, 'repeat': repeat, 'identity': identity})
                records.append(row)
                if len(records) % 36 == 0:
                    print(json.dumps({'progress': len(records), 'expected': len(schedule()), 'wall_seconds': ms(wall)/1000}), flush=True)
            attempt.append('timing_window_end', {'observations': len(records)})
        summary = summarize(records, startup, spec['measured_dependency_setup_ms'])
        report = {'contract_sha256': sha(CONTRACT), 'environment': environment, 'shared_startup_ms': startup,
                  'summary': summary, 'query_budget_s': BUDGET_S, 'total_research_wall_ms': ms(wall),
                  'new_model_forwards': 0, 'new_tasks_generated': 0, 'historical_verdicts_changed': False}
        ev.write_json(Path(args.directory) / 'report.json', report)
        attempt.finish('completed', observations=len(records), report_sha256=ev.digest(ev.canonical(report)))
        print(json.dumps(summary['screening'], indent=2))
    except BaseException as exc:
        attempt.finish('failed_no_replacement', observations=len(records), error=type(exc).__name__ + ': ' + str(exc))
        raise


def replay(directory):
    """Independent original-goal replay; no optimizer, SPGL1 or model calls."""
    from experiments.q5_register import evidence_module
    from threadpoolctl import threadpool_limits
    from unittest.mock import patch
    ev = evidence_module(); directory = Path(directory)
    events, terminal = ev.read_events(directory)
    report = json.loads((directory / 'report.json').read_bytes())
    contract = next(e['payload']['contract'] for e in events if e['kind'] == 'preregistered')
    if (terminal['status'] != 'completed' or terminal['report_sha256'] != ev.digest(ev.canonical(report))
            or next(e['payload']['contract_sha256'] for e in events if e['kind'] == 'preregistered') != report['contract_sha256']):
        raise ValueError('first result/report/contract binding drift')
    records = []
    with threadpool_limits(1), patch('scipy.optimize.linprog', side_effect=AssertionError('no optimizer replay')):
        for event in events:
            if event['kind'] != 'observation': continue
            row = ev.unpack_case(directory, event['payload']['identity'])
            if any(row[k] != event['payload'][k] for k in ('case_id', 'route', 'repeat')):
                raise ValueError('observation identity drift')
            raw = decode(ev.unpack_case(SOURCE, row['source_identity']))
            certificate = checker(**raw, **row['witness']) if row['witness'] else None
            if certificate != row['independent_certificate']:
                raise ValueError('independent original certificate drift')
            expected = bool(certificate and certificate['accepted'] and row['query_ms'] <= BUDGET_S * 1000)
            if expected != row['accepted']:
                raise ValueError('invalid or late output accepted')
            records.append(row)
        summary = summarize(records, report['shared_startup_ms'], contract['measured_dependency_setup_ms'])
        if summary != report['summary']:
            raise ValueError('summary/coverage/cost drift')
    return {'status': 'PASS', 'observations': len(records),
            'original_witnesses_checked': sum(bool(r['witness']) for r in records),
            'final_original_valid_in_budget': sum(r['accepted'] for r in records),
            'new_solver_calls': 0, 'new_model_forwards': 0, 'first_result_not_replaced': True}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--directory', required=True); p.add_argument('--dependencies', required=True)
    p.add_argument('--launch-ns', required=True, type=int)
    run(p.parse_args())
