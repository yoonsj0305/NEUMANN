"""Frozen-checkpoint new-executor study; no fitting and no v088 final reuse."""
import math
import random
from statistics import geometric_mean, median
from time import perf_counter_ns

import numpy as np
import torch
from scipy.linalg import lstsq
from threadpoolctl import threadpool_limits

from experiments import lp_model_study_v088 as old
from experiments.lp_shortlist_screen_v089 import restore_models, raw_source
from experiments.lp_state_models_v087 import tensor_input
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_shortlist_v089 import solve_shortlist_checked

SHORTLIST_CLASSICS = ('short_centred', 'short_primal', 'short_centred_thin', 'short_portfolio_union')
CLASSICS = old.CLASSICS + SHORTLIST_CLASSICS
ROUTES = CLASSICS + old.LEARNERS


def protocol():
    return {'schema': 'neumann.lp-shortlist-study.v1', 'runtime': admission.RUNTIME,
            'old_checkpoint_json_sha256': '9fa7e160a0264cb22475c98eae9ce8b43d8de4c31146ee1c2004476efe349661',
            'new_fitting': False, 'final_seed_base': 89900, 'final_cases': 12,
            'groups': ['iid', 'size_surface_shift'], 'threads': 1, 'order_seed': 89991,
            'warmups': 1, 'repeats': 3, 'budget_s': 5., 'routes': list(ROUTES),
            'shortlist': 'top min(n,2m) refined scores; compact == retained coarse 2m',
            'shared_authority': 'restricted native LP + original full certificate + paid cold rescue',
            'ratio_max': .8, 'minimum_wins_per_group': 4, 'minimum_no_full_fallback_per_group': 4,
            'amortization_queries': 10000, 'seeds': list(old.SEEDS),
            'scope': 'new executor with frozen v088 weights, constructed LP roster only',
            'v088_gate': 'FAILED_UNCHANGED', 'global_q3': 'OPEN', 'global_q4': 'OPEN'}


def specs():
    return [{**s, 'seed': 89900+i, 'id': f'short_final{i}'}
            for i, s in enumerate(old.specs('final'))]


def observe(raw, route, model=None):
    started = perf_counter_ns()
    m = raw['A'].shape[0]
    answer = None
    if route == 'short_portfolio_union':
        indices = sorted({int(i) for _, proposal in storage.propose(**raw) for i in proposal})
    elif route == 'short_centred_thin':
        D, _, q = storage.normalized(**raw)
        affine = lstsq(np.column_stack((D.T, np.ones(D.shape[1]))), q,
                       cond=1e-12, lapack_driver='gelsy', check_finite=False)[0]
        residual = q-D.T@affine[:-1]-affine[-1]
        indices = np.argsort(residual, kind='stable')[:2*m].tolist()
    else:
        D, rows, cols = admission.features(**raw)
        if route == 'short_centred':
            indices = np.argsort(cols[:, 1], kind='stable')[:2*m].tolist()
        elif route == 'short_primal':
            indices = np.argsort(-cols[:, 2], kind='stable')[:2*m].tolist()
        else:
            tensors = tensor_input(D, rows, cols)
            with torch.inference_mode(): out = model(*tensors)
            indices = torch.argsort(out['scores'], descending=True, stable=True)[:2*m].tolist()
            lengths = np.linalg.norm(raw['A'], axis=0)
            bscale = max(1., float(np.linalg.norm(raw['b'])))
            cscale = max(1., float(np.sqrt(np.mean((raw['c']/lengths)**2))))
            witness = {'x': (out['x'].numpy()*bscale/lengths).tolist(),
                       'y': (out['y'].numpy()*cscale).tolist()}
            answer = {'witness': witness,
                      'certificate': verify_standard_form_certificate(**raw, **witness)}
    proposal_ms = (perf_counter_ns()-started)/1e6
    execution = None
    accepted = bool(answer and answer['certificate']['accepted'])
    witness = answer['witness'] if accepted else None
    remaining = 5.-(perf_counter_ns()-started)/1e9
    if not accepted and remaining > 0:
        execution = solve_shortlist_checked(**raw, indices=indices, budget_s=remaining)
        accepted, witness = execution['accepted'], execution['witness']
    elapsed = (perf_counter_ns()-started)/1e6
    return {'accepted': bool(accepted and elapsed<=5000.), 'total_ms': elapsed,
            'proposal_ms': proposal_ms, 'answer': answer, 'execution': execution,
            'witness': witness, 'indices': indices}


def summarize(records, sources, training, setup_ms):
    expected = {(s['id'], route, repeat) for s in sources for route in ROUTES for repeat in (-1,0,1,2)}
    keys = [(r['case_id'],r['route'],r['repeat']) for r in records]
    if len(sources)!=12 or len(set(keys))!=len(keys) or set(keys)!=expected:
        raise ValueError('study coverage drift')
    if any(type(r['accepted']) is not bool or not math.isfinite(r['total_ms']) or r['total_ms']<=0 for r in records):
        raise ValueError('cost evidence drift')
    if not all(r['accepted'] for r in records):
        return {'decision':'CAPABILITY_UNREACHED', 'global_q3':'OPEN', 'global_q4':'OPEN'}
    costs = {(s['id'],route): median(r['total_ms'] for r in records
             if r['case_id']==s['id'] and r['route']==route and r['repeat']>=0)
             for s in sources for route in ROUTES}
    tests=[]
    for seed in old.SEEDS:
        compact, full = f'compact16_s{seed}', f'full16_s{seed}'
        fit = setup_ms+training[compact]['fit_ms']
        for group in ('iid','size_surface_shift'):
            ids=[s['id'] for s in sources if s['group']==group]
            if len(ids)!=6: raise ValueError('group coverage drift')
            cr=[]; lr=[]; ar=[]; am=[]; no_fallback=0
            for case in ids:
                cost=costs[case,compact]; classic=min(costs[case,r] for r in CLASSICS)
                direct=min(costs[case,r] for r in old.LEARNERS if not r.startswith('compact16'))
                cr.append(cost/classic); lr.append(cost/direct); ar.append(cost/costs[case,full])
                am.append((cost+fit/10000.)/classic)
                no_fallback += int(all((r.get('answer') and r['answer']['certificate']['accepted'])
                    or (r.get('execution') and r['execution']['subset_accepted'])
                    for r in records if r['case_id']==case and r['route']==compact))
            ratios=[geometric_mean(values) for values in (cr,lr,ar,am)]
            wins=[sum(x<=.8 for x in values) for values in (cr,lr,ar)]
            tests.append({'seed':seed,'group':group,'classical_ratio':ratios[0],
                'best_learned_direct_ratio':ratios[1],'own_no_compression_ratio':ratios[2],
                'training_amortized_classical_ratio_at_10000':ratios[3],
                'wins':wins,'no_full_fallback_cases':no_fallback,
                'passed': max(ratios)<=.8 and min(wins)>=4 and no_fallback>=4})
    return {'decision': 'BOUNDED_SHORTLIST_ROSTER_PASS_NOT_GLOBAL_Q3_Q4' if all(t['passed'] for t in tests)
            else 'FROZEN_CHECKPOINT_SHORTLIST_GATE_FAILED', 'tests':tests,
            'global_q3':'OPEN','global_q4':'OPEN'}


def run_study(checkpoint):
    import os, sys, scipy, highspy
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    env={'python':list(sys.version_info[:2]),'numpy':np.__version__,'scipy':scipy.__version__,
         'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if env!=admission.RUNTIME or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':
        raise RuntimeError('runtime drift')
    loading_started=perf_counter_ns()
    retained=load_study('docs/experiments/results/v088_completed.manifest.json')
    models=restore_models(retained['training'])
    loading_ms=(perf_counter_ns()-loading_started)/1e6
    report={'protocol':protocol(),'environment':env,'training':retained['training'],
            'training_setup_ms':retained['training_setup_ms'],'sources':[],'records':[],
            'checkpoint_loading_ms':loading_ms, 'stage':'checkpoints_restored_final_unopened'}
    checkpoint(report)
    with threadpool_limits(1):
        inputs={}
        for spec in specs():
            raw,label=old.generate(spec); inputs[spec['id']]=raw
            report['sources'].append(old.packed_source(spec,raw,label))
        report['stage']='new_final_inputs_frozen'; checkpoint(report)
        for repeat in (-1,0,1,2):
            order=[(case,route) for case in inputs for route in ROUTES]
            random.Random(89991+repeat).shuffle(order)
            for case,route in order:
                raw=inputs[case]
                if route=='scale_portfolio': row=storage.discovery_once(**raw)
                elif route in old.CLASSICS: row=admission.observe(raw,route,None,{})
                else: row=observe(raw,route,models.get(route))
                report['records'].append({'case_id':case,'route':route,'repeat':repeat,**row})
                checkpoint({'stage':'observation','record':report['records'][-1]})
            report['stage']=f'new_final_repeat_{repeat}'; checkpoint(report)
            print(report['stage'],len(report['records']),flush=True)
        report['summary']=summarize(report['records'],report['sources'],report['training'],report['training_setup_ms'])
        report['stage']='completed'; checkpoint(report)
    return report


def validate_report(report):
    if report['protocol']!=protocol() or report['stage']!='completed': raise ValueError('protocol drift')
    raws={s['id']:raw_source(s) for s in report['sources']}
    if [{k:s[k] for k in spec} for s,spec in zip(report['sources'],specs())]!=specs():
        raise ValueError('new split drift')
    for row in report['records']:
        raw=raws[row['case_id']]
        if row['accepted'] and (row['witness'] is None or not verify_standard_form_certificate(**raw,**row['witness'])['accepted']):
            raise ValueError('accepted witness drift')
        execution=row.get('execution')
        if execution and execution['subset_accepted']:
            small=execution['restricted']['attempts'][-1]['witness']; x=np.zeros(raw['A'].shape[1])
            x[execution['indices']]=small['x']
            if not verify_standard_form_certificate(**raw,x=x,y=small['y'])['accepted']:
                raise ValueError('restricted original certificate drift')
        if execution and row['total_ms']+1e-6 < row['proposal_ms']+execution['total_ms']:
            raise ValueError('complete cost ledger drift')
    if report['summary']!=summarize(report['records'],report['sources'],report['training'],report['training_setup_ms']):
        raise ValueError('summary drift')
