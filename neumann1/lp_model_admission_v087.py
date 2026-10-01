"""A first, opened-development admission screen; not a learned Q3/Q4 result."""
from __future__ import annotations

import math
import platform
import random
from statistics import geometric_mean, median
from time import perf_counter_ns

import numpy as np
import scipy
from scipy.linalg import lstsq
from threadpoolctl import threadpool_info, threadpool_limits

from . import lp_portfolio_v084 as storage
from .lp_program_parity_v085 import load_source
from .lp_native_warm_start_v086 import solve_native_checked
from .lp_certificate_v081 import verify_standard_form_certificate

SOURCE_SHA = '10ad3cad8ad5c7f2543c333ce72f484f6747767828dc76e842795940603177c9'
ROUTES = ('highs', 'highs-ds', 'highs-ipm', 'native_cold',
          'centred_residual', 'minimum_norm_primal', 'portfolio_warm',
          'perfect_compact16', 'perfect_full16')
RUNTIME = {'python': [3, 12], 'numpy': '2.3.5', 'scipy': '1.17.0',
           'torch': '2.14.0+cpu', 'highspy': '1.15.1'}


def protocol():
    return {'schema': 'neumann.lp-model-admission.v1', 'source_sha256': SOURCE_SHA,
            'source_form': 'normalized', 'source_cases': 24, 'expanded_cases': 12,
            'repeats': 3, 'warmups': 1, 'order_seed': 87991, 'runtime': RUNTIME,
            'threads': 1, 'budget_s': 5., 'candidate_columns': 'min(n,2m)',
            'model_seed': 87001, 'model_widths': [16, 128], 'model_layers': 3,
            'parameter_cap': 400000, 'total_cost_ratio_max': .5,
            'saving_ratio': .8, 'minimum_wins': 8, 'cheap_exact_max': 7,
            'forward_compact_full_ratio_max': .8,
            'training': {'examples': 48, 'epochs': 12, 'max_s_per_model': 240.,
                         'seeds': [87001, 87002], 'lr': .001, 'optimizer': 'Adam',
                         'train_rows': [32, 64], 'final_rows': [128],
                         'supervision': ['basis', 'primal', 'dual'],
                         'final_gate_cost_ratio': .8, 'final_exact_verification': True},
            'trained': False, 'q3': 'OPEN', 'q4': 'OPEN'}


def features(A, b, c):
    """Both learned and classical routes may use these paid observable features.

The centred affine fit exploits the *known constructed* positive-slack family.
It is intentionally a strong generator-aware control, not a novel algorithm.
"""
    D, b, q = storage.normalized(A, b, c)
    m, n = D.shape
    affine = lstsq(np.column_stack((D.T, np.ones(n))), q, cond=1e-12,
                   lapack_driver='gelsy', check_finite=False)[0]
    residual = q - D.T @ affine[:-1] - affine[-1]
    primal = lstsq(D, b, cond=1e-12, lapack_driver='gelsy', check_finite=False)[0]
    cscale, bscale = max(1., float(np.sqrt(np.mean(q*q)))), max(1., float(np.linalg.norm(b)))
    cols = np.column_stack((q/cscale, residual/cscale, primal/bscale,
                           D.T @ b/bscale, D.mean(0), np.abs(D).mean(0),
                           np.full(n, m/n), np.ones(n)))
    rows = np.column_stack((b/bscale, D @ q/max(1., float(np.linalg.norm(q))),
                           D.mean(1), np.abs(D).mean(1),
                           np.sqrt(np.mean(D*D, axis=1)), np.ones(m),
                           np.full(m, m/n), np.ones(m)))
    if not np.all(np.isfinite(cols)) or not np.all(np.isfinite(rows)):
        raise ValueError('non-finite paid features')
    return D, rows, cols


def classic_propose(A, b, c, policy):
    if policy == 'portfolio_warm':
        return storage.propose(A, b, c)[0][1].tolist()
    _, _, f = features(A, b, c)
    if policy == 'centred_residual':
        return np.argsort(f[:, 1], kind='stable')[:A.shape[0]].tolist()
    if policy == 'minimum_norm_primal':
        return np.argsort(-f[:, 2], kind='stable')[:A.shape[0]].tolist()
    raise ValueError('unregistered deterministic policy')


def checked_head(raw, indices, budget_s=5.):
    """Shared authority: cheap LU/certificate, then *same basis* native repair.

Native repair and any cold rescue pay one remaining original deadline. This
primitive is available equally to every learned executable comparator.
"""
    if not math.isfinite(budget_s) or budget_s <= 0:
        raise ValueError('positive remaining deadline required')
    started = perf_counter_ns()
    candidate = storage.candidate_once(raw, np.asarray(indices), 'checked_basis')
    native = None
    if not candidate['accepted']:
        remaining = budget_s - (perf_counter_ns() - started)/1e9
        if remaining > 0:
            native = solve_native_checked(**raw, head={'basis': list(indices)}, budget_s=remaining)
    witness = candidate['witness'] if candidate['accepted'] else (
        native['attempts'][-1]['witness'] if native and native['accepted'] else None)
    accepted = bool(candidate['accepted'] or native and native['accepted'])
    elapsed = (perf_counter_ns() - started)/1e6
    return {'accepted': accepted and elapsed <= budget_s*1000., 'candidate': candidate,
            'native': native, 'witness': witness, 'total_ms': elapsed,
            'budget_s': budget_s, 'fallback_used': native is not None}


def observe(raw, route, oracle, models):
    started = perf_counter_ns()
    if route in ('highs', 'highs-ds', 'highs-ipm'):
        row = storage.direct_once(raw, route)
        elapsed = (perf_counter_ns()-started)/1e6
        return {'total_ms': elapsed, 'accepted': row['accepted'] and elapsed <= 5000.,
                'witness': row['witness'], 'direct': row, 'proposal_ms': 0., 'forward_ms': None}
    if route == 'native_cold':
        row = solve_native_checked(**raw)
        witness = row['attempts'][-1]['witness'] if row['accepted'] else None
        elapsed = (perf_counter_ns()-started)/1e6
        return {'total_ms': elapsed, 'accepted': row['accepted'] and elapsed <= 5000.,
                'witness': witness, 'direct': row, 'proposal_ms': 0., 'forward_ms': None}
    proposal_started = perf_counter_ns()
    forward_ms, states, terms = None, None, None
    if route.startswith('perfect_'):
        # Non-deployable admission diagnostic: pay real untrained forward cost,
        # discard its output and inject a certified oracle basis. No accuracy claim.
        import torch
        from experiments.lp_state_models_v087 import tensor_input
        D, rows, cols = features(**raw)
        tensors = tensor_input(D, rows, cols)
        forward_started = perf_counter_ns()
        with torch.inference_mode():
            output = models[route.removeprefix('perfect_')](*tensors)
        forward_ms = (perf_counter_ns()-forward_started)/1e6
        states, terms = output['state_columns'], output['edge_multiply_terms']
        indices = oracle
    else:
        indices = classic_propose(**raw, policy=route)
    proposal_ms = (perf_counter_ns()-proposal_started)/1e6
    remaining = 5. - (perf_counter_ns()-started)/1e9
    if remaining <= 0:
        return {'total_ms': (perf_counter_ns()-started)/1e6, 'accepted': False,
                'witness': None, 'proposal_ms': proposal_ms, 'forward_ms': forward_ms,
                'state_columns': states, 'edge_multiply_terms': terms,
                'proposal_deadline_exhausted': True}
    result = checked_head(raw, indices, remaining)
    elapsed = (perf_counter_ns()-started)/1e6
    return {'total_ms': elapsed, 'accepted': result['accepted'] and elapsed <= 5000.,
            'witness': result['witness'], 'execution': result, 'proposal_ms': proposal_ms,
            'forward_ms': forward_ms, 'state_columns': states, 'edge_multiply_terms': terms}


def prepare(original):
    inputs, selected = {}, []
    for source in original['sources']:
        if source['form'] != 'normalized':
            continue
        m, n = source['rows'], source['cols']
        raw = {k: storage.decode_array(source['arrays'][k], shape)
               for k, shape in (('A', (m, n)), ('b', (m,)), ('c', (n,)))}
        if storage.input_digest(raw) != source['raw_sha256']:
            raise ValueError('source identity drift')
        # Recover an exact support only from a retained independently checked
        # source optimum. This oracle never enters any observable proposer.
        observed = next(r for r in original['records'] if r['case_id'] == source['id']
                        and r['route_id'] == 'highs' and r['repeat'] == 0)
        witness = observed['witness']
        if not verify_standard_form_certificate(**raw, **witness)['accepted']:
            raise ValueError('retained oracle witness rejected')
        basis = np.flatnonzero(np.asarray(witness['x']) > 1e-8).tolist()
        if len(basis) != m or not storage.candidate_once(raw, np.asarray(basis), 'oracle_setup')['accepted']:
            raise ValueError('no unambiguous certified basis for diagnostic')
        inputs[source['id']] = (raw, basis)
        selected.append({'id': source['id'], 'rows': m, 'cols': n,
                         'expanded': source['width_factor'] == 16,
                         'sha256': source['raw_sha256']})
    if len(inputs) != 24 or sum(s['expanded'] for s in selected) != 12:
        raise ValueError('frozen opened corpus coverage drift')
    return inputs, selected


def summarize(records, sources):
    if (not records or len(sources) != 24 or sum(s['expanded'] for s in sources) != 12
            or len({s['id'] for s in sources}) != len(sources)):
        raise ValueError('missing records/duplicate sources')
    expected = {(s['id'], r, i) for s in sources for r in ROUTES for i in (-1, 0, 1, 2)}
    seen = set()
    for row in records:
        key = row['case_id'], row['route'], row['repeat']
        if key not in expected or key in seen:
            raise ValueError('coverage drift')
        seen.add(key)
        if type(row['accepted']) is not bool or not math.isfinite(row['total_ms']) or row['total_ms'] < 0:
            raise ValueError('invalid capability/cost record')
    if seen != expected:
        raise ValueError('incomplete first audit')
    if not all(r['accepted'] for r in records):
        return {'decision': 'CAPABILITY_UNREACHED', 'q3': 'OPEN', 'q4': 'OPEN'}
    by = {(s['id'], route): median(r['total_ms'] for r in records if
          r['case_id'] == s['id'] and r['route'] == route and r['repeat'] >= 0)
          for s in sources for route in ROUTES}
    ratios, forward_ratios, cheap_hits, cells = [], [], 0, []
    for s in sources:
        if not s['expanded']:
            continue
        case = s['id']
        reference = min(by[case, route] for route in ROUTES if not route.startswith('perfect_'))
        cf = median(r['forward_ms'] for r in records if r['case_id'] == case and
                    r['route'] == 'perfect_compact16' and r['repeat'] >= 0)
        ff = median(r['forward_ms'] for r in records if r['case_id'] == case and
                    r['route'] == 'perfect_full16' and r['repeat'] >= 0)
        if min(reference, cf, ff) <= 0:
            raise ValueError('zero time cannot support a ratio')
        ratio = by[case, 'perfect_compact16']/reference
        cheap = any(all(r['execution']['candidate']['accepted'] for r in records
                       if r['case_id'] == case and r['route'] == route)
                    for route in ('centred_residual', 'minimum_norm_primal', 'portfolio_warm'))
        cheap_hits += int(cheap)
        ratios.append(ratio)
        forward_ratios.append(cf/ff)
        cells.append({'case_id': case, 'perfect_complete_best_direct_ratio': ratio,
                      'compact_full_forward_ratio': cf/ff, 'cheap_exact': cheap})
    if not ratios:
        raise ValueError('no expanded evidence')
    allowed = (geometric_mean(ratios) <= .5 and sum(r <= .8 for r in ratios) >= 8
               and cheap_hits <= 7 and geometric_mean(forward_ratios) <= .8)
    return {'decision': 'ADMIT_BOUNDED_MODEL_FITTING_NOT_Q3_Q4_PASS' if allowed else
            'REJECT_THIS_MODEL_TASK_BEFORE_FITTING',
            'perfect_complete_best_direct_geomean': geometric_mean(ratios),
            'twenty_percent_wins': sum(r <= .8 for r in ratios),
            'cheap_exact_expanded': cheap_hits,
            'compact_full_forward_geomean': geometric_mean(forward_ratios),
            'cells': cells, 'q3': 'OPEN', 'q4': 'OPEN'}


class AuditInterrupted(RuntimeError):
    def __init__(self, error, partial):
        super().__init__(f'{type(error).__name__}: {error}')
        self.partial = partial


def run_audit(original):
    import torch
    import highspy
    from experiments.lp_state_models_v087 import roster
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    environment = {'python': list(__import__('sys').version_info[:2]),
                   'numpy': np.__version__, 'scipy': scipy.__version__,
                   'torch': torch.__version__, 'highspy': highspy.Highs().version(),
                   'python_full': platform.python_version()}
    if any(environment[k] != v for k, v in RUNTIME.items()):
        raise RuntimeError('runtime drift before first audit')
    models = roster()
    model_parameters = {name: sum(p.numel() for p in model.parameters()) for name, model in models.items()}
    if max(model_parameters.values()) > 400000:
        raise RuntimeError('model parameter cap exceeded')
    records = []
    with threadpool_limits(limits=1):
        inputs, sources = prepare(original)
        environment['threadpools'] = threadpool_info()
        if any(pool['num_threads'] != 1 for pool in environment['threadpools']):
            raise RuntimeError('thread drift')
        try:
            for repeat in (-1, 0, 1, 2):
                schedule = [(case, route) for case in inputs for route in ROUTES]
                random.Random(87991 + repeat).shuffle(schedule)
                for case, route in schedule:
                    raw, oracle = inputs[case]
                    row = observe(raw, route, oracle, models)
                    records.append({'case_id': case, 'route': route, 'repeat': repeat, **row})
                print(f'completed repeat {repeat}: {len(records)} observations', flush=True)
        except BaseException as exc:
            raise AuditInterrupted(exc, {'protocol': protocol(), 'environment': environment,
                'sources': sources, 'model_parameters': model_parameters, 'records': records,
                'interrupted_at': {'case_id': case, 'route': route, 'repeat': repeat}}) from exc
    return {'protocol': protocol(), 'environment': environment, 'sources': sources,
            'model_parameters': model_parameters, 'records': records,
            'summary': summarize(records, sources)}


def validate_archive(report, original):
    """Solver/model-free original-witness replay; never regenerate timing inputs."""
    if report['protocol'] != protocol():
        raise ValueError('protocol drift')
    if any(report['environment'].get(k) != v for k, v in RUNTIME.items()):
        raise ValueError('recorded runtime drift')
    if not report['environment']['threadpools'] or any(
            p['num_threads'] != 1 for p in report['environment']['threadpools']):
        raise ValueError('recorded thread drift')
    if set(report['model_parameters']) != {'compact16', 'full16', 'point16', 'full128'} or any(
            type(v) is not int or not 0 < v <= 400000 for v in report['model_parameters'].values()):
        raise ValueError('parameter budget drift')
    # Decode only; do not call prepare() here because its oracle LU is setup work.
    raw = {}
    for s in original['sources']:
        if s['form'] == 'normalized':
            m, n = s['rows'], s['cols']
            raw[s['id']] = {k: storage.decode_array(s['arrays'][k], shape)
                           for k, shape in (('A', (m,n)), ('b', (m,)), ('c', (n,)))}
    if len(raw) != 24 or {s['id'] for s in report['sources']} != set(raw):
        raise ValueError('source coverage drift')
    for s in report['sources']:
        source = next(t for t in original['sources'] if t['id'] == s['id'])
        if (storage.input_digest(raw[s['id']]) != s['sha256'] or s['sha256'] != source['raw_sha256']
                or s['rows'] != source['rows'] or s['cols'] != source['cols']
                or s['expanded'] != (source['width_factor'] == 16)):
            raise ValueError('input identity drift')
    for r in report['records']:
        original_raw = raw[r['case_id']]
        if not math.isfinite(r['proposal_ms']) or not 0 <= r['proposal_ms'] <= r['total_ms']:
            raise ValueError('proposal cost drift')
        if r['accepted'] and r['total_ms'] > 5000.:
            raise ValueError('late acceptance')
        if r['accepted']:
            if r['witness'] is None or not verify_standard_form_certificate(**original_raw, **r['witness'])['accepted']:
                raise ValueError('original witness rejected')
        if 'execution' in r:
            execution = r['execution']
            if r['accepted'] != (execution['accepted'] and r['total_ms'] <= 5000.) or r['witness'] != execution['witness']:
                raise ValueError('execution acceptance drift')
            if r['proposal_ms'] < 0 or r['total_ms'] + 1e-9 < r['proposal_ms'] + execution['total_ms']:
                raise ValueError('omitted paid work')
            candidate = execution['candidate']
            if not 0 < execution['budget_s'] <= 5. - r['proposal_ms']/1000. + 1e-9:
                raise ValueError('proposal work omitted from deadline')
            if execution['accepted'] and execution['total_ms'] > execution['budget_s']*1000.:
                raise ValueError('late execution acceptance')
            native = execution['native']
            if execution['fallback_used'] != (native is not None):
                raise ValueError('native fallback ledger drift')
            if native:
                if native['accepted'] and not verify_standard_form_certificate(
                        **original_raw, **native['attempts'][-1]['witness'])['accepted']:
                    raise ValueError('native original witness rejected')
                if execution['total_ms'] + 1e-9 < candidate['total_ms'] + native['total_ms']:
                    raise ValueError('omitted native fallback work')
            if candidate['witness'] is not None:
                fresh = verify_standard_form_certificate(**original_raw, **candidate['witness'])
                if candidate['accepted'] != fresh['accepted']:
                    raise ValueError('rejected/accepted candidate witness drift')
        if r['route'].startswith('perfect_'):
            if not math.isfinite(r['forward_ms']) or not 0 <= r['forward_ms'] <= r['proposal_ms']:
                raise ValueError('forward cost drift')
            m, n = original_raw['A'].shape
            expected = min(n, 2*m) if r['route'] == 'perfect_compact16' else n
            if r['state_columns'] != expected or r['edge_multiply_terms'] != 2*m*n*16 + 4*m*expected*16:
                raise ValueError('model state/computation trace drift')
    if report['summary'] != summarize(report['records'], report['sources']):
        raise ValueError('summary drift')
