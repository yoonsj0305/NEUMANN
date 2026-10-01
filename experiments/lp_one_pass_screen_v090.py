"""Explicit opened-training screen; import never fits or times a model."""
import math
import random
from statistics import median, geometric_mean
from time import perf_counter_ns
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from experiments import lp_shortlist_study_v089 as previous
from experiments.lp_shortlist_screen_v089 import restore_models, raw_source
from experiments.lp_state_models_v087 import tensor_input
from experiments.lp_one_pass_v090 import early_indices, observe
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

EARLY=tuple('early_'+r for r in previous.old.LEARNERS)
ROUTES=previous.ROUTES+EARLY


def protocol():
    return {'schema':'neumann.lp-one-pass-screen.v1','source_sha256':
        '9fa7e160a0264cb22475c98eae9ce8b43d8de4c31146ee1c2004476efe349661',
        'split':'opened_v088_train_first16','runtime':previous.admission.RUNTIME,
        'cases':16,'routes':list(ROUTES),'warmups':1,'repeats':3,'order_seed':90991,
        'ratio_max':.8,'minimum_wins':12,'minimum_no_full_rescue':12,
        'amortization_queries':10000,'budget_s':5.,'new_fitting':False,
        'global_q3':'OPEN','global_q4':'OPEN'}


def summarize(records,sources,training,setup_ms,parity):
    ids=[s['id'] for s in sources]
    expected={(case,r,i) for case in ids for r in ROUTES for i in (-1,0,1,2)}
    keys=[(r['case_id'],r['route'],r['repeat']) for r in records]
    if len(ids)!=16 or len(set(ids))!=16 or len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError('screen coverage drift')
    if any(type(r['accepted']) is not bool or not math.isfinite(r['total_ms']) or r['total_ms']<=0 for r in records):
        raise ValueError('invalid screen cost')
    parity_keys={(p['case_id'],p['seed']) for p in parity}
    if len(parity)!=32 or parity_keys!={(case,seed) for case in ids for seed in previous.old.SEEDS}:
        raise ValueError('parity coverage drift')
    if not all(r['accepted'] for r in records):
        return {'decision':'CAPABILITY_UNREACHED','global_q3':'OPEN','global_q4':'OPEN'}
    if not all(p['early']==p['retained'] for p in parity):
        return {'decision':'RETAINED_SET_PARITY_FAILED','global_q3':'OPEN','global_q4':'OPEN'}
    costs={(case,route):median(r['total_ms'] for r in records if r['case_id']==case and
           r['route']==route and r['repeat']>=0) for case in ids for route in ROUTES}
    direct=[r for r in ROUTES if r not in previous.CLASSICS and 'compact16' not in r]
    tests=[]
    for seed in previous.old.SEEDS:
        original=f'compact16_s{seed}';candidate='early_'+original
        fit=setup_ms+training[original]['fit_ms']
        cr=[];dr=[];orr=[];am=[];no_rescue=0
        for case in ids:
            c=costs[case,candidate]; classic=min(costs[case,r] for r in previous.CLASSICS)
            cr.append(c/classic);dr.append(c/min(costs[case,r] for r in direct))
            orr.append(c/costs[case,original]);am.append((c+fit/10000.)/classic)
            no_rescue+=int(all((r.get('execution') or {}).get('subset_accepted',False)
                              for r in records if r['case_id']==case and r['route']==candidate))
        ratios=[geometric_mean(v) for v in (cr,dr,orr,am)]
        wins=[sum(x<=.8 for x in v) for v in (cr,dr,orr)]
        tests.append({'seed':seed,'classical_ratio':ratios[0],'direct_ratio':ratios[1],
            'original_compact_ratio':ratios[2],'amortized_classical_ratio':ratios[3],
            'wins':wins,'no_full_rescue_cases':no_rescue,
            'passed':max(ratios)<=.8 and min(wins)>=12 and no_rescue>=12})
    return {'decision':'ADMIT_NEW_EXECUTOR_HOLDOUT_NOT_Q3_Q4' if all(t['passed'] for t in tests)
            else 'STOP_ONE_PASS_CANDIDATE','tests':tests,'global_q3':'OPEN','global_q4':'OPEN'}


def run(checkpoint):
    import os,sys,scipy,highspy
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    env={'python':list(sys.version_info[:2]),'numpy':np.__version__,'scipy':scipy.__version__,
         'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if env!=protocol()['runtime'] or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':
        raise RuntimeError('screen runtime drift')
    started=perf_counter_ns()
    original=load_study('docs/experiments/results/v088_completed.manifest.json')
    models=restore_models(original['training'])
    report={'protocol':protocol(),'environment':env,'sources':original['train_sources'][:16],
            'training_setup_ms':original['training_setup_ms'],'training_fit_ms':
            {k:v['fit_ms'] for k,v in original['training'].items()},'records':[],
            'parity':[],'loading_ms':(perf_counter_ns()-started)/1e6,'stage':'loaded_opened_train'}
    checkpoint(report)
    with threadpool_limits(1):
        raws={s['id']:raw_source(s) for s in report['sources']}
        for case,raw in raws.items():
            tensors=tensor_input(*previous.admission.features(**raw))
            with torch.inference_mode():
                for seed in previous.old.SEEDS:
                    model=models[f'compact16_s{seed}']
                    report['parity'].append({'case_id':case,'seed':seed,
                        'early':early_indices(model,*tensors),
                        'retained':model(*tensors)['selected'].tolist()})
        report['stage']='parity_complete';checkpoint(report)
        for repeat in (-1,0,1,2):
            order=[(case,r) for case in raws for r in ROUTES]
            random.Random(90991+repeat).shuffle(order)
            for case,route in order:
                raw=raws[case]
                if route.startswith('early_'):row=observe(raw,models[route[6:]])
                elif route=='scale_portfolio':row=previous.storage.discovery_once(**raw)
                elif route in previous.old.CLASSICS:row=previous.admission.observe(raw,route,None,{})
                else:row=previous.observe(raw,route,models.get(route))
                record={'case_id':case,'route':route,'repeat':repeat,**row}
                report['records'].append(record);checkpoint({'stage':'observation','record':record})
            print('repeat',repeat,'records',len(report['records']),flush=True)
        report['summary']=summarize(report['records'],report['sources'],original['training'],
                                   report['training_setup_ms'],report['parity'])
        report['stage']='completed';checkpoint(report)
    return report


def validate(report):
    if report['protocol']!=protocol() or report['environment']!=protocol()['runtime'] or report['stage']!='completed':
        raise ValueError('screen protocol drift')
    original=load_study('docs/experiments/results/v088_completed.manifest.json')
    if (report['sources']!=original['train_sources'][:16] or
        report['training_setup_ms']!=original['training_setup_ms'] or
        report['training_fit_ms']!={k:v['fit_ms'] for k,v in original['training'].items()}):
        raise ValueError('opened source or frozen fit drift')
    raws={s['id']:raw_source(s) for s in report['sources']}
    for row in report['records']:
        raw=raws[row['case_id']]
        if row['accepted'] and (row['total_ms']>5000. or row['witness'] is None or
                not verify_standard_form_certificate(**raw,**row['witness'])['accepted']):
            raise ValueError('accepted witness drift')
        execution=row.get('execution');answer=row.get('answer')
        if answer and verify_standard_form_certificate(**raw,**answer['witness'])['accepted']!=answer['certificate']['accepted']:
            raise ValueError('rejected answer drift')
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
    if report['summary']!=summarize(report['records'],report['sources'],original['training'],
                                   report['training_setup_ms'],report['parity']):
        raise ValueError('screen summary drift')
