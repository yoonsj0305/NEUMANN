"""Fixed first retraining on opened data, never final generation or CI fitting."""
import math
import random
from statistics import median, geometric_mean
from time import perf_counter_ns
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from experiments import lp_model_study_v088 as old
from experiments import lp_shortlist_study_v089 as previous
from experiments.lp_shortlist_screen_v089 import raw_source, restore_models
from experiments.lp_state_models_v087 import roster, tensor_input
from experiments.lp_cheap_features_v091 import features
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_shortlist_v089 import solve_shortlist_checked
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

CHEAP_CLASSICS = ('cheap_cost', 'cheap_correlation')
CLASSICS = previous.CLASSICS + CHEAP_CLASSICS
ROUTES = CLASSICS + old.LEARNERS


def protocol():
    return {'schema':'neumann.lp-cheap-feature-screen.v1',
        'source_sha256':'9fa7e160a0264cb22475c98eae9ce8b43d8de4c31146ee1c2004476efe349661',
        'runtime':previous.admission.RUNTIME, 'openblas_coretype':'HASWELL',
        'train_split':'all_48_opened_v088_train', 'screen_split':'first16_of_same_train',
        'models':list(old.NAMES), 'seeds':list(old.SEEDS), 'epochs':12,
        'optimizer':'Adam', 'lr':.001, 'fit_seconds_cap':240., 'parameter_cap':400000,
        'loss':old.protocol()['loss'], 'checkpoint':'last epoch only',
        'features':'column-normalized moments, cost, centered cost, b correlation; no LS',
        'executor':'refined top2m, restricted native, full original certificate, paid rescue',
        'routes':list(ROUTES), 'cases':16, 'warmups':1, 'repeats':3,
        'order_seed':91991, 'budget_s':5., 'ratio_max':.8, 'minimum_wins':12,
        'minimum_no_full_rescue':12, 'amortization_queries':10000,
        'final_evaluation':False, 'global_q3':'OPEN', 'global_q4':'OPEN'}


def observe(raw, route, model=None):
    started = perf_counter_ns()
    D, rows, cols = features(**raw)
    m, n = D.shape
    output = None
    if route == 'cheap_cost':
        indices = np.argsort(cols[:,0], kind='stable')[:2*m].tolist()
    elif route == 'cheap_correlation':
        indices = np.argsort(-cols[:,2], kind='stable')[:2*m].tolist()
    else:
        with torch.inference_mode():
            output = model(*tensor_input(D, rows, cols))
            scores = output['scores']
            indices = (torch.argsort(scores, descending=True, stable=True)[:2*m].tolist()
                       if torch.isfinite(scores).all() else [])
    proposal_ms = (perf_counter_ns()-started)/1e6
    remaining = 5.-proposal_ms/1000.
    execution = (solve_shortlist_checked(**raw, indices=indices, budget_s=remaining)
                 if remaining>0 else None)
    total_ms = (perf_counter_ns()-started)/1e6
    return {'accepted':bool(execution and execution['accepted'] and total_ms<=5000.),
        'total_ms':total_ms, 'proposal_ms':proposal_ms, 'execution':execution,
        'witness':execution['witness'] if execution else None, 'indices':indices,
        'state_columns':output['state_columns'] if output else None,
        'edge_multiply_terms':output['edge_multiply_terms'] if output else None}


def summarize(records, sources, training, setup_ms):
    ids = [s['id'] for s in sources]
    keys = [(r['case_id'],r['route'],r['repeat']) for r in records]
    expected = {(case,route,i) for case in ids for route in ROUTES for i in (-1,0,1,2)}
    if len(ids)!=16 or len(set(ids))!=16 or len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError('screen coverage drift')
    if any(type(r['accepted']) is not bool or not math.isfinite(r['total_ms']) or r['total_ms']<=0 for r in records):
        raise ValueError('invalid cost record')
    if not all(r['accepted'] for r in records):
        return {'decision':'CAPABILITY_UNREACHED','global_q3':'OPEN','global_q4':'OPEN'}
    costs = {(case,route):median(r['total_ms'] for r in records
        if r['case_id']==case and r['route']==route and r['repeat']>=0)
        for case in ids for route in ROUTES}
    direct = [r for r in old.LEARNERS if not r.startswith('compact16')]
    tests = []
    for seed in old.SEEDS:
        compact, full = f'compact16_s{seed}', f'full16_s{seed}'
        fit_ms = setup_ms+training[compact]['fit_ms']
        cr, dr, fr, ar = [],[],[],[]
        no_rescue = 0
        for case in ids:
            c = costs[case,compact]; classic = min(costs[case,r] for r in CLASSICS)
            cr.append(c/classic); dr.append(c/min(costs[case,r] for r in direct))
            fr.append(c/costs[case,full]); ar.append((c+fit_ms/10000.)/classic)
            no_rescue += int(all((r.get('execution') or {}).get('subset_accepted',False)
                for r in records if r['case_id']==case and r['route']==compact))
        ratios = [geometric_mean(v) for v in (cr,dr,fr,ar)]
        wins = [sum(x<=.8 for x in v) for v in (cr,dr,fr)]
        tests.append({'seed':seed, 'classical_ratio':ratios[0], 'direct_ratio':ratios[1],
            'own_full_ratio':ratios[2], 'amortized_classical_ratio':ratios[3],
            'wins':wins, 'no_full_rescue_cases':no_rescue,
            'passed':max(ratios)<=.8 and min(wins)>=12 and no_rescue>=12})
    return {'decision':'ADMIT_PREREGISTERED_HOLDOUT_NOT_Q3_Q4' if all(t['passed'] for t in tests)
        else 'STOP_CHEAP_FEATURE_CANDIDATE', 'tests':tests,'global_q3':'OPEN','global_q4':'OPEN'}


def run(checkpoint):
    import os, sys, scipy, highspy
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    env = {'python':list(sys.version_info[:2]), 'numpy':np.__version__,
        'scipy':scipy.__version__, 'torch':torch.__version__, 'highspy':highspy.Highs().version()}
    if env!=protocol()['runtime'] or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':
        raise RuntimeError('runtime drift')
    original = load_study('docs/experiments/results/v088_completed.manifest.json')
    report = {'protocol':protocol(), 'environment':env, 'train_sources':original['train_sources'],
        'sources':original['train_sources'][:16], 'training':{}, 'records':[], 'stage':'opened_train'}
    checkpoint(report)
    with threadpool_limits(1):
        started = perf_counter_ns(); data = []
        for source in report['train_sources']:
            raw = raw_source(source)
            x, y = old.scaled_targets(raw, source['label'])
            data.append((tensor_input(*features(**raw)), torch.tensor(source['label']['indices']),
                torch.tensor(x,dtype=torch.float32), torch.tensor(y,dtype=torch.float32)))
        report['training_setup_ms'] = (perf_counter_ns()-started)/1e6
        for seed in old.SEEDS:
            for name, model in roster(seed).items():
                key = f'{name}_s{seed}'
                report['training'][key] = old.fit_one(model,data,seed,name)
                report['stage'] = 'fit_'+key; checkpoint(report)
                print(report['stage'],report['training'][key]['fit_ms'],flush=True)
                if not report['training'][key]['completed']:
                    raise RuntimeError('first fit incomplete; no retry')
        models = restore_models(report['training'])
        raws = {s['id']:raw_source(s) for s in report['sources']}
        report['stage'] = 'weights_frozen'; checkpoint(report)
        for repeat in (-1,0,1,2):
            order = [(case,route) for case in raws for route in ROUTES]
            random.Random(91991+repeat).shuffle(order)
            for case,route in order:
                raw = raws[case]
                if route in old.LEARNERS or route in CHEAP_CLASSICS:
                    row = observe(raw,route,models.get(route))
                elif route=='scale_portfolio':row=previous.storage.discovery_once(**raw)
                elif route in old.CLASSICS:row=previous.admission.observe(raw,route,None,{})
                else:row=previous.observe(raw,route)
                record = {'case_id':case,'route':route,'repeat':repeat,**row}
                report['records'].append(record); checkpoint({'stage':'observation','record':record})
            print('repeat',repeat,'records',len(report['records']),flush=True)
        report['summary']=summarize(report['records'],report['sources'],report['training'],report['training_setup_ms'])
        report['stage']='completed';checkpoint(report)
    return report


def validate(report):
    if report['protocol']!=protocol() or report['environment']!=protocol()['runtime'] or report['stage']!='completed':
        raise ValueError('protocol drift')
    original = load_study('docs/experiments/results/v088_completed.manifest.json')
    if report['train_sources']!=original['train_sources'] or report['sources']!=original['train_sources'][:16]:
        raise ValueError('source drift')
    models=restore_models(report['training'])
    for key, model in models.items():
        t=report['training'][key]
        if (not t['completed'] or t['parameters']!=sum(p.numel() for p in model.parameters())
            or t['parameters']>400000 or not 0<t['fit_ms']<=240000.
            or [e['epoch'] for e in t['epochs']]!=list(range(1,13))
            or any(not math.isfinite(e['mean_loss']) for e in t['epochs'])):
            raise ValueError('fitting drift')
    if not math.isfinite(report['training_setup_ms']) or report['training_setup_ms']<=0:
        raise ValueError('training setup drift')
    raws={s['id']:raw_source(s) for s in report['sources']}
    for row in report['records']:
        raw=raws[row['case_id']]
        if row['accepted'] and (row['total_ms']>5000. or row['witness'] is None or
            not verify_standard_form_certificate(**raw,**row['witness'])['accepted']):
            raise ValueError('accepted witness drift')
        execution=row.get('execution')
        if execution and row['total_ms']+1e-6<row['proposal_ms']+execution['total_ms']:
            raise ValueError('complete ledger drift')
        if execution and 'subset_accepted' in execution:
            if execution['original_certificate']:
                small=execution['restricted']['attempts'][-1]['witness'];x=np.zeros(raw['A'].shape[1])
                x[execution['indices']]=small['x']
                accepted=verify_standard_form_certificate(**raw,x=x,y=small['y'])['accepted']
                if accepted!=execution['subset_accepted'] or accepted!=execution['original_certificate']['accepted']:
                    raise ValueError('omitted-variable rejection drift')
            for native,restricted in ((execution['restricted'],True),(execution['fallback'],False)):
                if not native:continue
                ix=execution['indices'];target={'A':raw['A'][:,ix],'b':raw['b'],'c':raw['c'][ix]} if restricted else raw
                for attempt in native['attempts']:
                    witness,cert=attempt['witness'],attempt['certificate']
                    if cert and (witness is None or verify_standard_form_certificate(**target,**witness)['accepted']!=cert['accepted']):
                        raise ValueError('native witness drift')
                if native['total_ms']+1e-6<sum(s['ms'] for a in native['attempts'] for s in a['stages']):
                    raise ValueError('native ledger drift')
    if report['summary']!=summarize(report['records'],report['sources'],report['training'],report['training_setup_ms']):
        raise ValueError('summary drift')
